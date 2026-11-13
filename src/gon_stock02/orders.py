from datetime import datetime, timezone
from decimal import Decimal
import fcntl
import json
import re
import sqlite3
from zoneinfo import ZoneInfo

from gon_stock02.kis import KisFailure, OrderRejected, SYMBOLS, number
from gon_stock02.risk import EntryState, assess_entry


TERMINAL = {'FILLED', 'CANCELED', 'REJECTED'}


def trading_day():
    return datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y%m%d')


class OrderService:
    def __init__(self, client, policy):
        self.client = client
        self.policy = policy
        self.path = client.account_dir / 'orders.sqlite3'
        self.db = None
        self.lock = None

    def __enter__(self):
        self.lock = (self.client.account_dir / 'orders.lock').open('a+')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise KisFailure('account_busy') from None
        try:
            self.db = sqlite3.connect(self.path)
            self.path.chmod(0o600)
            self.db.row_factory = sqlite3.Row
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.executescript('''
                CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS orders (
                    intent TEXT PRIMARY KEY, details TEXT NOT NULL, day TEXT NOT NULL,
                    state TEXT NOT NULL, branch TEXT, order_id TEXT, cancel_id TEXT,
                    cancel_attempted INTEGER NOT NULL DEFAULT 0,
                    filled INTEGER NOT NULL DEFAULT 0, canceled INTEGER NOT NULL DEFAULT 0,
                    remaining INTEGER NOT NULL, rejected INTEGER NOT NULL DEFAULT 0,
                    amount TEXT NOT NULL DEFAULT '0', reason TEXT NOT NULL DEFAULT '');
                CREATE UNIQUE INDEX IF NOT EXISTS broker_order ON orders(day, branch, order_id);
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY, at TEXT NOT NULL, intent TEXT, state TEXT NOT NULL, reason TEXT NOT NULL);
            ''')
            with self.db:
                account = self.client.account_dir.name
                if self.meta('account') not in (None, account):
                    raise KisFailure('ledger_account_mismatch')
                self.set_meta('account', account)
                if self.meta('start') is None:
                    self.set_meta('start', trading_day())
                for row in self.db.execute("SELECT intent FROM orders WHERE state IN ('SUBMITTING', 'CANCEL_SUBMITTING')").fetchall():
                    self.update(row['intent'], state='UNKNOWN', reason='interrupted_request')
            return self
        except BaseException:
            self.__exit__()
            raise

    def __exit__(self, *args):
        if self.db is not None:
            self.db.close()
        if self.lock is not None:
            self.lock.close()

    def meta(self, key):
        row = self.db.execute('SELECT value FROM metadata WHERE key=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def set_meta(self, key, value):
        self.db.execute('INSERT OR REPLACE INTO metadata VALUES (?, ?)', (key, json.dumps(value)))

    def get(self, intent):
        row = self.db.execute('SELECT * FROM orders WHERE intent=?', (intent,)).fetchone()
        if row is None:
            return None
        return dict(row) | {'details': json.loads(row['details'])}

    def all_orders(self):
        return [self.get(row[0]) for row in self.db.execute('SELECT intent FROM orders ORDER BY rowid').fetchall()]

    def update(self, intent, **values):
        assignments = ', '.join(key + '=?' for key in values)
        self.db.execute('UPDATE orders SET ' + assignments + ' WHERE intent=?', (*values.values(), intent))
        row = self.get(intent)
        self.db.execute('INSERT INTO events(at,intent,state,reason) VALUES (?,?,?,?)',
                        (datetime.now(timezone.utc).isoformat(), intent, row['state'], row['reason']))

    def positions(self, orders=None):
        positions = {}
        for row in orders if orders is not None else self.all_orders():
            details = row['details']
            symbol = details['symbol']
            positions[symbol] = positions.get(symbol, 0) + row['filled'] * (1 if details['side'] == 'buy' else -1)
        if any(qty < 0 for qty in positions.values()):
            raise KisFailure('negative_ledger_position')
        return {symbol: qty for symbol, qty in positions.items() if qty}

    def reconcile(self):
        rows = self.all_orders()
        try:
            broker = self.client.daily_orders(self.meta('start'), trading_day())
            snapshot = self.client.account_snapshot()
            by_key = {(r['day'], r['branch'], r['order_id']): r for r in broker}
            known = {(r['day'], r['branch'], r['order_id']) for r in rows if r['order_id']}
            for row in rows:
                ack = self.meta('cancel:' + row['intent'])
                if ack is None:
                    continue
                key = (row['day'], ack['branch'], ack['order_id'])
                known.add(key)
                child = by_key.get(key)
                if child is not None and (child['parent_id'] != row['order_id'] or child['symbol'] != row['details']['symbol'] or child['side'] != row['details']['side'] or child['kind'] != '00' or child['filled'] != 0 or Decimal(child['amount']) != 0):
                    raise KisFailure('invalid_cancel_link')
            if set(by_key) - known:
                raise KisFailure('external_order')
            candidates = []
            for row in rows:
                if row['order_id'] is None:
                    if row['state'] != 'REJECTED':
                        raise KisFailure('unknown_submission')
                    candidates.append(row)
                    continue
                observed = by_key.get((row['day'], row['branch'], row['order_id']))
                if observed is None:
                    raise KisFailure('order_missing')
                detail = row['details']
                if any(observed[k] != detail[k] for k in ('symbol', 'side', 'quantity')) or Decimal(observed['price']) != Decimal(detail['price']) or observed['kind'] != '00' or int(observed['parent_id']) != 0:
                    raise KisFailure('order_attributes_changed')
                if sum(observed[k] for k in ('filled', 'canceled', 'remaining', 'rejected')) != detail['quantity']:
                    raise KisFailure('order_quantity_mismatch')
                if any(observed[k] < row[k] for k in ('filled', 'canceled', 'rejected')) or observed['remaining'] > row['remaining'] or Decimal(observed['amount']) < Decimal(row['amount']):
                    raise KisFailure('order_quantity_regression')
                if (observed['filled'] == 0) != (Decimal(observed['amount']) == 0):
                    raise KisFailure('fill_amount_mismatch')
                if observed['filled'] == detail['quantity']:
                    state = 'FILLED'
                elif observed['remaining'] == 0:
                    state = 'CANCELED' if observed['canceled'] else 'REJECTED'
                elif row['cancel_attempted']:
                    state = 'CANCEL_PENDING'
                else:
                    state = 'PARTIAL' if observed['filled'] else 'OPEN'
                if row['state'] in TERMINAL and state != row['state']:
                    raise KisFailure('terminal_order_changed')
                candidates.append(row | {k: observed[k] for k in ('filled', 'canceled', 'remaining', 'rejected', 'amount')} | {'state': state, 'reason': ''})
            positions = self.positions(candidates)
            actual = {s: h['quantity'] for s, h in snapshot['holdings'].items()}
            if positions != actual:
                raise KisFailure('balance_mismatch')
            baseline = self.meta('baseline_equity')
            if baseline is None:
                if rows or broker or actual:
                    raise KisFailure('initial_account_not_empty')
                baseline = snapshot['equity']
            initial = number(self.policy['initial_capital_krw'], positive=True)
            equity = initial + Decimal(snapshot['equity']) - Decimal(baseline)
            if equity <= 0:
                raise KisFailure('capital_exhausted')
            with self.db:
                for row in candidates:
                    self.update(row['intent'], **{k: row[k] for k in ('state', 'filled', 'canceled', 'remaining', 'rejected', 'amount', 'reason')})
                self.set_meta('baseline_equity', baseline)
                if self.meta('equity_day') != trading_day():
                    self.set_meta('day_open_equity', self.meta('last_equity') or str(equity))
                    self.set_meta('equity_day', trading_day())
                self.set_meta('last_equity', str(equity))
                self.set_meta('peak_equity', str(max(equity, Decimal(self.meta('peak_equity') or initial))))
                self.set_meta('blocked_reason', None)
            self.snapshot = snapshot
            return {'consistent': True, 'orders_checked': len(rows), 'positions_checked': len(positions), 'orders_sent': 0}
        except KisFailure as exc:
            with self.db:
                self.set_meta('blocked_reason', str(exc))
            return {'consistent': False, 'reason': str(exc), 'orders_sent': 0}

    def _quote_age(self, quote, symbol):
        try:
            now = datetime.now(timezone.utc)
            event, received = (datetime.fromisoformat(quote[k]) for k in ('event_time', 'received_at'))
            age, receipt_age = (now - event).total_seconds(), (now - received).total_seconds()
            limit = self.policy['max_quote_age_seconds']
            if quote['symbol'] != symbol or quote['venue'] != 'KRX' or quote['tr_id'] != 'H0STCNT0' or quote['halt_code'] != 'N' or quote['hour_class'] != '0':
                raise KisFailure('unverified_quote')
            if not 0 <= receipt_age <= age <= limit or not 0 < number(quote['bid']) <= number(quote['ask']):
                raise KisFailure('stale_or_invalid_quote')
            return age
        except (KeyError, TypeError, ValueError):
            raise KisFailure('invalid_quote') from None

    def _check_session(self, session):
        try:
            now = datetime.now(ZoneInfo('Asia/Seoul'))
            opens, closes, checked = (datetime.fromisoformat(session[k]) for k in ('opens_at', 'closes_at', 'checked_at'))
            if not isinstance(session['source'], str) or not session['source'].startswith('https://'):
                raise KisFailure('unverified_session')
            if not now.replace(hour=9, minute=0, second=0, microsecond=0) <= opens <= now < closes <= now.replace(hour=15, minute=20, second=0, microsecond=0):
                raise KisFailure('outside_verified_session')
            if not 0 <= (now-checked).total_seconds() <= 86400:
                raise KisFailure('stale_session_evidence')
        except (KeyError, TypeError, ValueError):
            raise KisFailure('invalid_session_evidence') from None

    def _preflight(self, quote, symbol, session):
        self._check_session(session)
        return self._quote_age(quote, symbol)

    def _entry_state(self, symbol, age):
        holdings = self.snapshot['holdings']
        gross = sum(Decimal(h['value']) for h in holdings.values())
        equity = Decimal(self.meta('last_equity'))
        exposure = holdings.get(symbol, {}).get('value', '0')
        orders = self.all_orders()
        reserved = Decimal(0)
        for held, quantity in self.positions().items():
            unit_losses = [max(Decimal(0), Decimal(r['details']['price']) - Decimal(r['details']['stop'])) + Decimal(r['details']['cost'])
                           for r in orders if r['details']['symbol'] == held and r['details']['side'] == 'buy' and r['filled']]
            reserved += max(unit_losses) * quantity
        return EntryState(str(equity), self.meta('day_open_equity'), self.meta('peak_equity'),
                          str(max(Decimal(0), min(Decimal(self.snapshot['cash']), equity-gross))), str(gross), exposure,
                          len(holdings), sum(r['day'] == trading_day() and r['details']['symbol'] == symbol and r['details']['side'] == 'buy' and (r['state'] != 'REJECTED' or r['filled'] > 0) for r in orders),
                          age, True, str(reserved))

    def submit(self, *, intent, symbol, side, quantity, price, stop, cost, quote, session=None):
        if not isinstance(intent, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', intent) or symbol not in SYMBOLS or side not in ('buy', 'sell') or type(quantity) is not int or not 1 <= quantity <= 9999999999:
            raise KisFailure('invalid_order')
        price, stop, cost = (str(number(v, positive=i == 0)) for i, v in enumerate((price, stop, cost)))
        if Decimal(price) != Decimal(price).to_integral_value():
            raise KisFailure('invalid_limit_price')
        details = dict(symbol=symbol, side=side, quantity=quantity, price=price, stop=stop, cost=cost)
        existing = self.get(intent)
        if existing is not None:
            if existing['details'] != details:
                raise KisFailure('intent_conflict')
            return existing
        if self.policy.get('order_submission_enabled') is not True or self.policy.get('environment') != 'mock' or symbol not in self.policy.get('symbols', []) or 'KRX' not in self.policy.get('paper_order_venues', []):
            raise KisFailure('execution_gate_closed')
        self._check_session(session)
        if not self.reconcile()['consistent']:
            raise KisFailure('reconciliation_required')
        if any(r['state'] not in TERMINAL for r in self.all_orders()):
            raise KisFailure('unfinished_order')
        age = self._preflight(quote, symbol, session)
        if side == 'buy':
            decision = assess_entry(self.policy, self._entry_state(symbol, age), symbol, 'KRX', price, stop, cost)
            if not decision['allowed'] or quantity > decision['quantity']:
                raise KisFailure('entry_risk_blocked')
        elif quantity > min(self.positions().get(symbol, 0), self.snapshot['holdings'].get(symbol, {}).get('available', 0)):
            raise KisFailure('insufficient_owned_position')
        self.client.authenticate()
        with self.db:
            self.db.execute('INSERT INTO orders(intent,details,day,state,remaining) VALUES (?,?,?,?,?)',
                            (intent, json.dumps(details, sort_keys=True), trading_day(), 'SUBMITTING', quantity))
            self.update(intent, state='SUBMITTING')
            self.set_meta('session:' + intent, session)
        try:
            ack = self.client._submit_limit(symbol, side, quantity, price, before_send=lambda: self._preflight(quote, symbol, session))
        except OrderRejected:
            with self.db:
                self.update(intent, state='REJECTED', reason='broker_rejected', remaining=0, rejected=quantity)
        except KisFailure as exc:
            with self.db:
                self.update(intent, state='UNKNOWN', reason=str(exc))
        else:
            with self.db:
                self.update(intent, state='OPEN', **ack)
        return self.get(intent)

    def cancel(self, intent):
        row = self.get(intent)
        if row is None:
            raise KisFailure('unknown_intent')
        if row['state'] in TERMINAL or row['cancel_attempted']:
            return row
        if not self.reconcile()['consistent']:
            raise KisFailure('reconciliation_required')
        row = self.get(intent)
        if row['state'] in TERMINAL:
            return row
        if row['state'] not in ('OPEN', 'PARTIAL') or row['day'] != trading_day():
            raise KisFailure('cancel_requires_known_current_order')
        self.client.authenticate()
        with self.db:
            self.update(intent, state='CANCEL_SUBMITTING', cancel_attempted=1)
        try:
            ack = self.client._cancel_remaining(row['branch'], row['order_id'])
        except KisFailure as exc:
            with self.db:
                self.update(intent, state='UNKNOWN', reason=str(exc))
        else:
            with self.db:
                self.update(intent, state='CANCEL_PENDING', cancel_id=ack['order_id'])
                self.set_meta('cancel:' + intent, ack)
        return self.get(intent)
