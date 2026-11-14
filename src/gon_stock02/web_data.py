"""Read-only adapters for the local research workspace. No broker clients."""

from contextlib import closing
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from gon_stock02.kis import SYMBOLS
from gon_stock02.history import SEOUL


class DataError(Exception):
    pass


MAX_BYTES = 64 * 1024 * 1024
MAX_ROWS = 100_000
POLICY_FIELDS = (
    'version', 'environment', 'initial_capital_krw', 'risk_per_trade',
    'daily_loss_limit', 'drawdown_limit', 'max_symbol_allocation',
    'max_gross_allocation', 'max_positions', 'max_entries_per_symbol_per_day',
    'max_quote_age_seconds', 'order_submission_enabled',
)


def read_bytes(path, root):
    if not path.resolve().is_relative_to(root.resolve()):
        raise DataError('unsafe_path')
    try:
        with path.open('rb') as source:
            data = source.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise DataError('file_too_large')
        return data
    except OSError:
        raise DataError('file_unavailable') from None


def read_json(path, root):
    try:
        value = json.loads(read_bytes(path, root))
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (ValueError, UnicodeError):
        raise DataError('invalid_data') from None


def policy_at(root):
    policy = read_json(root / 'config/paper.json', root)
    if any(key not in policy for key in POLICY_FIELDS):
        raise DataError('invalid_policy')
    try:
        ratios = [Decimal(str(policy[key])) for key in (
            'risk_per_trade', 'daily_loss_limit', 'drawdown_limit',
            'max_symbol_allocation', 'max_gross_allocation')]
        capital = Decimal(str(policy['initial_capital_krw']))
        if (policy['environment'] != 'mock' or type(policy['order_submission_enabled']) is not bool
                or not capital.is_finite() or not 0 < capital <= Decimal('1e12')
                or any(not value.is_finite() or not 0 < value <= 1 for value in ratios)
                or any(type(policy[key]) is not int or policy[key] <= 0 for key in (
                    'max_positions', 'max_entries_per_symbol_per_day', 'max_quote_age_seconds'))):
            raise ValueError
    except (ValueError, TypeError, InvalidOperation):
        raise DataError('invalid_policy') from None
    return policy


def bundle_path(root, bundle_id):
    if not re.fullmatch(r'(?:history|minute-capture)-[A-Za-z0-9_-]{1,100}', bundle_id):
        raise DataError('bundle_not_found')
    path = root / bundle_id
    if not path.is_dir() or not path.resolve().is_relative_to(root.resolve()):
        raise DataError('bundle_not_found')
    return path


def bundle_info(root, bundle_id):
    path = bundle_path(root, bundle_id)
    manifest = read_json(path / 'manifest.json', root)
    capture = bundle_id.startswith('minute-capture-')
    filename = 'observations.jsonl' if capture else 'bars.jsonl'
    if manifest.get('environment') != 'mock' or manifest.get('market_requested') != 'KRX':
        raise DataError('unsupported_bundle')
    checks = {}
    files = {}
    hashes = manifest.get('sha256', {})
    if not isinstance(hashes, dict):
        raise DataError('invalid_data')
    for name in ('pages.jsonl', filename):
        try:
            data = read_bytes(path / name, root)
            checks[name] = 'matched' if hashlib.sha256(data).hexdigest() == hashes.get(name) else 'mismatch'
            if name == filename:
                files[name] = data
        except DataError as exc:
            checks[name] = str(exc)
    datasets = manifest.get('datasets', {} if capture else [])
    if capture:
        if not isinstance(datasets, dict) or any(not isinstance(v, dict) for v in datasets.values()):
            raise DataError('invalid_data')
        summaries = [{'symbol': symbol, 'timeframe': '1m',
                      'rows': values.get('observations', 0), 'status': manifest.get('status', 'incomplete'),
                      'contract_mock_supported': True}
                     for symbol, values in datasets.items() if symbol in SYMBOLS]
    else:
        if not isinstance(datasets, list) or any(not isinstance(v, dict) for v in datasets):
            raise DataError('invalid_data')
        fields = ('symbol', 'timeframe', 'rows', 'first', 'last', 'status', 'zero_price_rows',
                  'candidate_missing_minutes', 'reason')
        summaries = [{**{key: row.get(key) for key in fields},
                      # The early manifests predate the corrected broker contract.
                      'contract_mock_supported': row.get('timeframe') == '1d'}
                     for row in datasets if row.get('symbol') in SYMBOLS]
    return {'id': bundle_id, 'kind': 'capture' if capture else 'history',
            'started_at': manifest.get('started_at'), 'finished_at': manifest.get('finished_at'),
            'collection_complete': manifest.get('collection_complete') is True,
            'status': manifest.get('status', 'completed' if manifest.get('collection_complete') is True else 'incomplete'),
            'integrity': 'matched' if all(v == 'matched' for v in checks.values()) else 'failed',
            'file_checks': checks, 'datasets': summaries, 'backtest_ready': False,
            'coverage_verified': False, 'bar_finality_verified': False}, files.get(filename)


def list_bundles(root):
    bundles = []
    paths = sorted({*root.glob('history-*/manifest.json'), *root.glob('minute-capture-*/manifest.json')})
    for manifest in paths:
        try:
            info, _ = bundle_info(root, manifest.parent.name)
            bundles.append(info)
        except DataError as exc:
            bundles.append({'id': manifest.parent.name,
                            'kind': 'capture' if manifest.parent.name.startswith('minute-capture-') else 'history',
                            'collection_complete': None, 'status': 'unknown',
                            'integrity': 'failed', 'error': str(exc), 'datasets': []})
    return sorted(bundles, key=lambda item: (str(item.get('finished_at') or ''), item['id']), reverse=True)


def numeric(value):
    try:
        if not isinstance(value, (str, int)) or isinstance(value, bool):
            raise ValueError
        parsed = Decimal(value)
        if not parsed.is_finite() or not 0 <= parsed <= Decimal('1e18'):
            raise ValueError
        return str(parsed)
    except (ValueError, InvalidOperation):
        raise DataError('invalid_data') from None


def series(root, bundle_id, symbol, timeframe, start=None, end=None):
    if symbol not in SYMBOLS or timeframe not in ('1d', '1m'):
        raise DataError('invalid_selection')
    if start and end and start > end:
        raise DataError('invalid_date_range')
    info, data = bundle_info(root, bundle_id)
    if info['integrity'] != 'matched':
        raise DataError('integrity_failed')
    selected = {}
    count = 0
    try:
        for index, line in enumerate(data.splitlines()):
            if index >= MAX_ROWS:
                raise DataError('too_many_rows')
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError
            if row.get('symbol') != symbol or row.get('timeframe') != timeframe:
                continue
            stamp = row['time']
            if not isinstance(stamp, str):
                raise ValueError
            if timeframe == '1d':
                day = date.fromisoformat(stamp)
                if stamp != day.isoformat():
                    raise ValueError
            else:
                parsed = datetime.fromisoformat(stamp)
                if parsed.utcoffset() is None or parsed.second or parsed.microsecond:
                    raise ValueError
                parsed = parsed.astimezone(SEOUL)
                stamp = parsed.isoformat()
                day = parsed.date()
            if (start and day < start) or (end and day > end):
                continue
            values = {key: numeric(row[key]) for key in ('open', 'high', 'low', 'close', 'volume')}
            o, h, low, c = (Decimal(values[k]) for k in ('open', 'high', 'low', 'close'))
            volume = Decimal(values['volume'])
            if volume != volume.to_integral_value() or low > min(o, h, c) or h < max(o, low, c):
                raise ValueError
            if min(o, h, low, c) == 0 and volume > 0:
                raise ValueError
            candle = {'symbol': symbol, 'timeframe': timeframe, 'time': stamp, **values,
                      'zero_price': min(o, h, low, c) == 0, 'finality': 'unverified',
                      'strategy_eligible': False, 'versions': 1}
            if info['kind'] == 'capture':
                receipt = datetime.fromisoformat(row['received_at'])
                if receipt.utcoffset() is None or type(row['sequence']) is not int or row['sequence'] < 1:
                    raise ValueError
                candle.update(received_at=receipt.isoformat(), sequence=row['sequence'])
            previous = selected.get(stamp)
            if previous:
                if info['kind'] != 'capture':
                    raise ValueError
                versions = previous['versions'] + 1
                if (candle['sequence'], candle['received_at']) < (previous['sequence'], previous['received_at']):
                    previous['versions'] = versions
                    count += 1
                    continue
                candle['versions'] = versions
            selected[stamp] = candle
            count += 1
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise DataError('invalid_data') from None
    return {'bundle': info, 'symbol': symbol, 'name': SYMBOLS[symbol], 'timeframe': timeframe,
            'observations': count, 'rows': sorted(selected.values(), key=lambda row: row['time']),
            'view': 'latest_observed_revision', 'backtest_ready': False}


def ledger_snapshot(state_root, explicit_path=None):
    paths = [explicit_path] if explicit_path else sorted(state_root.glob('*/orders.sqlite3'))
    if not paths or not paths[0].is_file():
        return {'status': 'unavailable', 'orders': [], 'reason': 'ledger_not_found'}
    if len(paths) != 1:
        return {'status': 'unavailable', 'orders': [], 'reason': 'multiple_ledgers'}
    path = paths[0]
    if not explicit_path and not path.resolve().is_relative_to(state_root.resolve()):
        return {'status': 'unavailable', 'orders': [], 'reason': 'unsafe_path'}
    try:
        with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
            db.row_factory = sqlite3.Row
            db.execute('PRAGMA query_only=ON')
            db.execute('BEGIN')
            total = db.execute('SELECT count(*) FROM orders').fetchone()[0]
            rows = db.execute('SELECT day, state, details, filled, canceled, remaining, amount, reason '
                              'FROM orders ORDER BY rowid DESC LIMIT 200').fetchall()
            orders = []
            for row in rows:
                details = json.loads(row['details'])
                if details['symbol'] not in SYMBOLS or details['side'] not in ('buy', 'sell'):
                    raise ValueError
                orders.append({key: row[key] for key in ('day', 'state', 'filled', 'canceled', 'remaining')} |
                              {'symbol': details['symbol'], 'name': SYMBOLS[details['symbol']], 'side': details['side'],
                               'quantity': numeric(details['quantity']), 'price': numeric(details['price']),
                               'amount': numeric(row['amount'])})
            blocked = db.execute("SELECT value FROM metadata WHERE key='blocked_reason'").fetchone()
            last = db.execute('SELECT max(at) FROM events').fetchone()[0]
            reason = json.loads(blocked[0]) if blocked else None
            known_reasons = {'balance_mismatch', 'external_order', 'order_quantity_regression',
                             'unknown_submission', 'negative_ledger_position', 'invalid_order_dates',
                             'rate_limited', 'network_error', 'timeout', 'authentication_failed',
                             'invalid_cancel_link', 'order_missing', 'order_attributes_changed',
                             'order_quantity_mismatch', 'fill_amount_mismatch', 'terminal_order_changed',
                             'initial_account_not_empty', 'capital_exhausted'}
            if reason is not None and (not isinstance(reason, str) or reason not in known_reasons):
                reason = 'ledger_blocked'
            return {'status': 'ok', 'orders': orders, 'total': total, 'limit': 200,
                    'blocked_reason': reason, 'last_event_at': last,
                    'broker_reconciled_now': False}
    except (OSError, sqlite3.Error, ValueError, KeyError, TypeError, DataError):
        return {'status': 'error', 'orders': [], 'reason': 'ledger_read_failed'}
