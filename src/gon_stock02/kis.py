from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
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
    def __init__(self, credentials, *, transport=None):
        self.credentials = credentials
        self.http = httpx.Client(base_url=HOST, transport=transport, timeout=15,
                                 follow_redirects=False, trust_env=False)
        self.token = ""
        self.expires = 0.0
        self.next_request = 0.0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.http.close()
        self.token = ""

    def _request(self, method, path, **kwargs):
        time.sleep(max(0.0, self.next_request - time.monotonic()))
        self.next_request = time.monotonic() + 1.1
        try:
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
