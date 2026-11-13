from contextlib import contextmanager
import fcntl
import hashlib
import os
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import math
import re
import subprocess
import time
from zoneinfo import ZoneInfo

import httpx


HOST = "https://openapivts.koreainvestment.com:29443"
SYMBOLS = {"005930": "삼성전자", "000660": "SK하이닉스", "009150": "삼성전기", "036930": "주성엔지니어링"}
MARKETS = {"KRX": "J", "NXT": "NX", "UNIFIED": "UN"}


class KisFailure(Exception):
    pass


class OrderRejected(KisFailure):
    pass


@dataclass(frozen=True)
class Credentials:
    app_key: str = field(repr=False)
    secret_key: str = field(repr=False)
    account: str = field(repr=False)
    product: str = field(repr=False)

    def __post_init__(self):
        if any(not isinstance(v, str) or not re.fullmatch(r"[!-~]+", v) for v in (self.app_key, self.secret_key)):
            raise KisFailure("invalid_credentials")
        if not isinstance(self.account, str) or not re.fullmatch(r"[0-9]{8}", self.account):
            raise KisFailure("invalid_credentials")
        if not isinstance(self.product, str) or not re.fullmatch(r"[0-9]{2}", self.product):
            raise KisFailure("invalid_credentials")


def load_credentials(*, runner=subprocess.run):
    return _load_credentials("mock", runner=runner)


def _load_credentials(environment, *, runner=subprocess.run):
    try:
        result = runner(["secret-tool", "lookup", "service", "gon-stock-kis", "environment", environment],
                        capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise KisFailure("credentials_unavailable")
        data = json.loads(result.stdout)
        if not isinstance(data, dict) or set(data) != {"app_key", "secret_key", "account", "product"}:
            raise KisFailure("invalid_credentials")
        return Credentials(**data)
    except KisFailure:
        raise
    except (OSError, ValueError, TypeError, subprocess.TimeoutExpired):
        raise KisFailure("credential_store_failed") from None


def number(value, *, positive=False):
    if isinstance(value, bool):
        raise KisFailure("invalid_market_data")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise KisFailure("invalid_market_data") from None
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise KisFailure("invalid_market_data")
    return result


class PaperClient:
    def __init__(self, credentials, *, transport=None, state_root=None):
        self.credentials = credentials
        self.http = httpx.Client(base_url=HOST, transport=transport, timeout=15,
                                 follow_redirects=False, trust_env=False)
        self.token = ""
        self.expires = 0.0
        identity = hashlib.sha256((HOST + credentials.account + credentials.product).encode()).hexdigest()
        root = Path(state_root) if state_root is not None else Path.home() / ".local/state/gon-stock02"
        self.account_dir = root / identity
        self.account_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.account_dir.chmod(0o700)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.http.close()
        self.token = ""

    @contextmanager
    def request_slot(self):
        with (self.account_dir / "requests.lock").open("a+") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            lock.seek(0)
            try:
                next_at = float(lock.read() or "0")
            except ValueError:
                raise KisFailure("invalid_rate_state") from None
            if not math.isfinite(next_at):
                raise KisFailure("invalid_rate_state")
            delay = max(0.0, next_at - time.time())
            if delay > 60:
                raise KisFailure("rate_clock_shift")
            time.sleep(delay)
            lock.seek(0)
            lock.truncate()
            lock.write(str(time.time() + 1.1))
            lock.flush()
            os.fsync(lock.fileno())
            yield

    def _request(self, method, path, *, before_send=None, order_write=False, **kwargs):
        try:
            with self.request_slot():
                if before_send is not None:
                    before_send()
                response = self.http.request(method, path, **kwargs)
        except httpx.TimeoutException:
            raise KisFailure("timeout") from None
        except httpx.HTTPError:
            raise KisFailure("network_error") from None
        try:
            data = response.json()
        except ValueError:
            raise KisFailure("invalid_response") from None
        if not isinstance(data, dict):
            raise KisFailure("invalid_response")
        if data.get("msg_cd") in ("EGW00133", "EGW00201") or data.get("error_code") in ("EGW00133", "EGW00201"):
            raise KisFailure("rate_limited")
        if response.status_code != 200:
            code = {429: "rate_limited", 401: "authentication_failed", 403: "authentication_failed"}.get(response.status_code, "http_error")
            raise KisFailure(code)
        if "error_code" in data or ("rt_cd" in data and data["rt_cd"] != "0"):
            if order_write and data.get("rt_cd") == "1" and re.fullmatch(r"APBK[0-9]{4}", str(data.get("msg_cd", ""))):
                raise OrderRejected("broker_rejected")
            raise KisFailure("broker_rejected")
        return data, response.headers

    def authenticate(self):
        if self.token and time.monotonic() < self.expires:
            return
        started = time.monotonic()
        data, _ = self._request("POST", "/oauth2/tokenP", json={"grant_type": "client_credentials",
                               "appkey": self.credentials.app_key, "appsecret": self.credentials.secret_key})
        token, expiry = data.get("access_token"), data.get("expires_in")
        if not isinstance(token, str) or not re.fullmatch(r"[!-~]+", token):
            raise KisFailure("invalid_token_response")
        if type(expiry) is not int or expiry <= 60 or str(data.get("token_type", "")).lower() != "bearer":
            raise KisFailure("invalid_token_response")
        self.token, self.expires = token, started + expiry - 60

    def _get(self, path, tr_id, params, *, continuation=False):
        self.authenticate()
        data, headers = self._request("GET", path, params=params, headers={
            "authorization": "Bearer " + self.token, "appkey": self.credentials.app_key,
            "appsecret": self.credentials.secret_key, "tr_id": tr_id, "custtype": "P", "tr_cont": "N" if continuation else ""})
        if data.get("rt_cd") != "0":
            raise KisFailure("invalid_response")
        return data, headers

    def quote(self, symbol, market="KRX"):
        if symbol not in SYMBOLS or market not in MARKETS:
            raise KisFailure("invalid_instrument")
        data, _ = self._get("/uapi/domestic-stock/v1/quotations/inquire-price", "FHKST01010100",
                            {"FID_COND_MRKT_DIV_CODE": MARKETS[market], "FID_INPUT_ISCD": symbol})
        output = data.get("output")
        if not isinstance(output, dict):
            raise KisFailure("invalid_market_data")
        price = number(output.get("stck_prpr"), positive=True)
        volume = number(output.get("acml_vol"))
        return {"symbol": symbol, "market_requested": market, "price": str(price), "volume": str(volume),
                "received_at": datetime.now(timezone.utc).isoformat(), "event_time": None,
                "freshness": "unverified", "venue_verified": False}

    def bars(self, symbol):
        if symbol not in SYMBOLS:
            raise KisFailure("invalid_instrument")
        cutoff = min(datetime.now(ZoneInfo("Asia/Seoul")).strftime("%H%M%S"), "153000")
        data, _ = self._get("/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice", "FHKST03010200",
                            {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol,
                             "FID_INPUT_HOUR_1": cutoff, "FID_PW_DATA_INCU_YN": "N", "FID_ETC_CLS_CODE": ""})
        rows = data.get("output2")
        if not isinstance(rows, list) or not rows or any(not isinstance(row, dict) for row in rows):
            raise KisFailure("invalid_market_data")
        received_at = datetime.now(timezone.utc)
        bars = []
        seen = set()
        for row in rows:
            try:
                raw_time = row["stck_bsop_date"] + row["stck_cntg_hour"]
                if not re.fullmatch(r"[0-9]{14}", raw_time):
                    raise KisFailure("invalid_bar_time")
                timestamp = datetime.strptime(raw_time, "%Y%m%d%H%M%S").replace(tzinfo=ZoneInfo("Asia/Seoul"))
                values = {field: str(number(row[key], positive=True)) for field, key in
                          (("open", "stck_oprc"), ("high", "stck_hgpr"), ("low", "stck_lwpr"), ("close", "stck_prpr"))}
                volume = str(number(row["cntg_vol"]))
            except (KeyError, TypeError, ValueError):
                raise KisFailure("invalid_market_data") from None
            if timestamp.date() != received_at.astimezone(ZoneInfo("Asia/Seoul")).date() or timestamp > received_at or timestamp in seen:
                raise KisFailure("invalid_bar_time")
            seen.add(timestamp)
            if Decimal(values["low"]) > min(Decimal(values["open"]), Decimal(values["close"])) or Decimal(values["high"]) < max(Decimal(values["open"]), Decimal(values["close"])):
                raise KisFailure("inconsistent_ohlc")
            bars.append({"time": timestamp.isoformat(), **values, "volume": volume})
        return {"symbol": symbol, "market_requested": "KRX", "bars": bars, "request_cutoff": cutoff,
                "received_at": received_at.isoformat(), "freshness": "unverified"}

    def balance_status(self):
        params = {"CANO": self.credentials.account, "ACNT_PRDT_CD": self.credentials.product,
                  "AFHR_FLPR_YN": "N", "OFL_YN": "", "INQR_DVSN": "02", "UNPR_DVSN": "01",
                  "FUND_STTL_ICLD_YN": "N", "FNCG_AMT_AUTO_RDPT_YN": "N", "PRCS_DVSN": "00",
                  "CTX_AREA_FK100": "", "CTX_AREA_NK100": ""}
        seen = set()
        for page in range(1, 21):
            data, headers = self._get("/uapi/domestic-stock/v1/trading/inquire-balance", "VTTC8434R", params, continuation=page > 1)
            if not isinstance(data.get("output1"), list) or not isinstance(data.get("output2"), (list, dict)):
                raise KisFailure("invalid_balance_response")
            if headers.get("tr_cont", "") not in ("F", "M"):
                return {"status": "read_ok", "pages": page, "private_values_logged": False}
            cursor = (data.get("ctx_area_fk100"), data.get("ctx_area_nk100"))
            if any(not isinstance(v, str) for v in cursor) or not any(v.strip() for v in cursor) or cursor in seen:
                raise KisFailure("invalid_balance_pagination")
            seen.add(cursor)
            params.update(CTX_AREA_FK100=cursor[0], CTX_AREA_NK100=cursor[1])
        raise KisFailure("balance_pagination_limit")

    def _post_order(self, path, tr_id, body, *, before_send=None):
        self.authenticate()
        data, _ = self._request('POST', path, order_write=True, before_send=before_send,
                               json={'CANO': self.credentials.account, 'ACNT_PRDT_CD': self.credentials.product, **body},
                               headers={'authorization': 'Bearer ' + self.token, 'appkey': self.credentials.app_key,
                                        'appsecret': self.credentials.secret_key, 'tr_id': tr_id, 'custtype': 'P'})
        output = data.get('output')
        if data.get('rt_cd') != '0' or not isinstance(output, dict):
            raise KisFailure('invalid_order_ack')
        normalized = {}
        for key in ('krx_fwdg_ord_orgno', 'odno', 'ord_tmd'):
            if key in output and key.upper() in output and output[key] != output[key.upper()]:
                raise KisFailure('invalid_order_ack')
            normalized[key] = output.get(key, output.get(key.upper()))
        output = normalized
        branch = identifier(output.get('krx_fwdg_ord_orgno'), 5)
        order_id = identifier(output.get('odno'), 10)
        if not re.fullmatch(r'[0-9]{6}', str(output.get('ord_tmd', ''))):
            raise KisFailure('invalid_order_ack')
        return {'branch': branch, 'order_id': order_id}

    def _submit_limit(self, symbol, side, quantity, price, *, before_send):
        if symbol not in SYMBOLS or side not in ('buy', 'sell') or type(quantity) is not int or not 1 <= quantity <= 9999999999:
            raise KisFailure('invalid_order')
        value = number(price, positive=True)
        if value != value.to_integral_value():
            raise KisFailure('invalid_order')
        return self._post_order('/uapi/domestic-stock/v1/trading/order-cash',
                                'VTTC0012U' if side == 'buy' else 'VTTC0011U',
                                {'PDNO': symbol, 'ORD_DVSN': '00', 'ORD_QTY': str(quantity), 'ORD_UNPR': str(value),
                                 'EXCG_ID_DVSN_CD': 'KRX', 'SLL_TYPE': '01' if side == 'sell' else ''}, before_send=before_send)

    def _cancel_remaining(self, branch, order_id):
        return self._post_order('/uapi/domestic-stock/v1/trading/order-rvsecncl', 'VTTC0013U',
                               {'KRX_FWDG_ORD_ORGNO': identifier(branch, 5), 'ORGN_ODNO': identifier(order_id, 10),
                                'ORD_DVSN': '00', 'RVSE_CNCL_DVSN_CD': '02', 'ORD_QTY': '0', 'ORD_UNPR': '0',
                                'QTY_ALL_ORD_YN': 'Y', 'EXCG_ID_DVSN_CD': 'KRX'})

    def _pages(self, path, tr_id, params):
        params = {'CANO': self.credentials.account, 'ACNT_PRDT_CD': self.credentials.product,
                  'CTX_AREA_FK100': '', 'CTX_AREA_NK100': '', **params}
        seen = set()
        for page in range(20):
            data, headers = self._get(path, tr_id, params, continuation=page > 0)
            if not isinstance(data.get('output1'), list) or any(not isinstance(r, dict) for r in data['output1']):
                raise KisFailure('invalid_account_response')
            yield data
            continuation = headers.get('tr_cont', '')
            if continuation not in ('D', 'E', 'F', 'M'):
                raise KisFailure('invalid_account_pagination')
            if continuation in ('D', 'E'):
                return
            cursor = (data.get('ctx_area_fk100'), data.get('ctx_area_nk100'))
            if any(not isinstance(v, str) for v in cursor) or not any(v.strip() for v in cursor) or cursor in seen:
                raise KisFailure('invalid_account_pagination')
            seen.add(cursor)
            params.update(CTX_AREA_FK100=cursor[0], CTX_AREA_NK100=cursor[1])
        raise KisFailure('account_pagination_limit')

    def daily_orders(self, start, end):
        try:
            first, last = (datetime.strptime(v, '%Y%m%d') for v in (start, end))
            if not 0 <= (last-first).days <= 89:
                raise ValueError()
        except (TypeError, ValueError):
            raise KisFailure('invalid_order_dates') from None
        result = []
        seen = set()
        for page in self._pages('/uapi/domestic-stock/v1/trading/inquire-daily-ccld', 'VTTC0081R',
                                {'INQR_STRT_DT': start, 'INQR_END_DT': end, 'SLL_BUY_DVSN_CD': '00', 'CCLD_DVSN': '00',
                                 'INQR_DVSN': '01', 'INQR_DVSN_3': '00', 'PDNO': '', 'ORD_GNO_BRNO': '', 'ODNO': '',
                                 'INQR_DVSN_1': '', 'EXCG_ID_DVSN_CD': 'KRX'}):
            for row in page['output1']:
                try:
                    day = row['ord_dt']
                    if not isinstance(day, str) or not re.fullmatch(r'[0-9]{8}', day) or not start <= day <= end:
                        raise KisFailure('invalid_order_date')
                    item = {'day': day, 'branch': identifier(row['ord_gno_brno'], 5), 'order_id': identifier(row['odno'], 10),
                            'parent_id': identifier(row['orgn_odno'], 10, zero=True), 'symbol': row['pdno'],
                            'side': {'01': 'sell', '02': 'buy'}[row['sll_buy_dvsn_cd']], 'kind': row['ord_dvsn_cd'],
                            'price': str(number(row['ord_unpr'])), 'amount': str(number(row['tot_ccld_amt']))}
                    for target, key in [('quantity', 'ord_qty'), ('filled', 'tot_ccld_qty'), ('canceled', 'cncl_cfrm_qty'),
                                        ('remaining', 'rmn_qty'), ('rejected', 'rjct_qty')]:
                        item[target] = quantity_value(row[key])
                    key = (day, item['branch'], item['order_id'])
                    if key in seen:
                        raise KisFailure('duplicate_order_row')
                    seen.add(key)
                    result.append(item)
                except (KeyError, TypeError):
                    raise KisFailure('invalid_order_response') from None
        return result

    def account_snapshot(self):
        holdings, summary = {}, None
        for page in self._pages('/uapi/domestic-stock/v1/trading/inquire-balance', 'VTTC8434R',
                                {'AFHR_FLPR_YN': 'N', 'OFL_YN': '', 'INQR_DVSN': '02', 'UNPR_DVSN': '01',
                                 'FUND_STTL_ICLD_YN': 'N', 'FNCG_AMT_AUTO_RDPT_YN': 'N', 'PRCS_DVSN': '00'}):
            try:
                values = page['output2']
                value = values[0] if isinstance(values, list) and len(values) == 1 else values
                current = {'equity': str(number(value['tot_evlu_amt'], positive=True)),
                           'cash': str(min(number(value['dnca_tot_amt']), number(value['prvs_rcdl_excc_amt'])))}
                if summary is not None and summary != current:
                    raise KisFailure('changing_balance_snapshot')
                summary = current
                for row in page['output1']:
                    qty = quantity_value(row['hldg_qty'])
                    if qty == 0:
                        continue
                    symbol = row['pdno']
                    if symbol in holdings or number(row['loan_amt']) != 0:
                        raise KisFailure('unsupported_balance_position')
                    available = quantity_value(row['ord_psbl_qty'])
                    if available > qty:
                        raise KisFailure('invalid_balance_quantity')
                    holdings[symbol] = {'quantity': qty, 'available': available, 'value': str(number(row['evlu_amt']))}
            except (KeyError, TypeError, IndexError):
                raise KisFailure('invalid_balance_response') from None
        return {**summary, 'holdings': holdings}


def identifier(value, length, *, zero=False):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{1,' + str(length) + '}', value) or (not zero and int(value) == 0):
        raise KisFailure('invalid_order_identifier')
    return value.zfill(length)


def quantity_value(value):
    qty = number(value)
    if qty != qty.to_integral_value() or qty > 9999999999:
        raise KisFailure('invalid_order_quantity')
    return int(qty)
