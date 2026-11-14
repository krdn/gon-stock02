"""Loopback-only web UI for stored research data and hypothetical risk checks."""

import argparse
import csv
from datetime import date, datetime, timezone
from decimal import Decimal
import io
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field
from starlette.middleware.trustedhost import TrustedHostMiddleware

from gon_stock02.kis import SYMBOLS
from gon_stock02.risk import EntryState, assess_entry
from gon_stock02.web_data import DataError, POLICY_FIELDS, ledger_snapshot, list_bundles, policy_at, series


Money = Annotated[Decimal, Field(ge=0, le=Decimal('1e12'), max_digits=18, decimal_places=6)]


class RiskInput(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    symbol: Literal['005930', '000660', '009150', '036930']
    entry: Money
    stop: Money
    cost_per_share: Money
    equity: Money
    day_open_equity: Money
    peak_equity: Money
    cash: Money
    gross_exposure: Money
    symbol_exposure: Money
    reserved_loss_krw: Money
    positions: Annotated[int, Field(strict=True, ge=0, le=100)]
    entries_today: Annotated[int, Field(strict=True, ge=0, le=100)]


def create_app(root=None, *, data_root=None, state_root=None, ledger_path=None):
    root = Path(root or Path.cwd()).resolve()
    data_root = Path(data_root or root / '.local').resolve()
    state_root = Path(state_root or Path.home() / '.local/state/gon-stock02').resolve()
    assets = Path(__file__).with_name('web_static')
    app = FastAPI(title='gon-stock02', docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', '[::1]'])

    @app.middleware('http')
    async def local_access(request: Request, call_next):
        if request.client is None or request.client.host not in ('127.0.0.1', '::1'):
            return JSONResponse({'detail': 'local_access_only'}, status_code=403)
        origin = request.headers.get('origin')
        # A link from README/chat may open the public HTML shell in a new tab.
        # Data endpoints and embedded documents still require a local origin.
        entry_navigation = (request.method == 'GET' and request.url.path == '/'
                            and request.headers.get('sec-fetch-mode') == 'navigate'
                            and request.headers.get('sec-fetch-dest') == 'document')
        foreign_origin = origin and origin != str(request.base_url).rstrip('/')
        if not entry_navigation and (foreign_origin or request.headers.get('sec-fetch-site') == 'cross-site'):
            return JSONResponse({'detail': 'same_origin_required'}, status_code=403)
        if request.method == 'POST':
            size = 0
            body = []
            async for chunk in request.stream():
                size += len(chunk)
                if size > 8192:
                    return JSONResponse({'detail': 'request_too_large'}, status_code=413)
                body.append(chunk)
            request._body = b''.join(body)
        response = await call_next(request)
        response.headers.update({
            'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff',
            'Referrer-Policy': 'no-referrer', 'X-Frame-Options': 'DENY',
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'",
        })
        return response

    @app.exception_handler(DataError)
    async def data_error(request, exc):
        status = 404 if str(exc) == 'bundle_not_found' else 422
        return JSONResponse({'detail': str(exc)}, status_code=status)

    @app.get('/api/overview')
    def overview():
        policy = policy_at(root)
        return {'generated_at': datetime.now(timezone.utc).isoformat(), 'mode': 'stored_data',
                'symbols': SYMBOLS, 'policy': {k: policy[k] for k in POLICY_FIELDS},
                'bundles': list_bundles(data_root), 'order_execution_available': False,
                'backtest_ready': False}

    @app.get('/api/series')
    def get_series(bundle: str, symbol: str, timeframe: Literal['1d', '1m'] = '1d',
                   start: date | None = None, end: date | None = None):
        return series(data_root, bundle, symbol, timeframe, start, end)

    @app.get('/api/export.csv')
    def export(bundle: str, symbol: str, timeframe: Literal['1d', '1m'] = '1d',
               start: date | None = None, end: date | None = None):
        result = series(data_root, bundle, symbol, timeframe, start, end)
        output = io.StringIO(newline='')
        fields = ['symbol', 'timeframe', 'time', 'open', 'high', 'low', 'close', 'volume',
                  'versions', 'received_at', 'zero_price', 'finality', 'strategy_eligible']
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(result['rows'])
        return Response('\ufeff' + output.getvalue(), media_type='text/csv; charset=utf-8',
                        headers={'Content-Disposition': f'attachment; filename="{symbol}-{timeframe}.csv"'})

    @app.get('/api/ledger')
    def ledger():
        return ledger_snapshot(state_root, ledger_path)

    @app.post('/api/risk')
    def risk(payload: RiskInput):
        policy = policy_at(root) | {'order_submission_enabled': False}
        values = payload.model_dump()
        # Freshness and venue are explicit assumptions, never live observations.
        state = EntryState(**{key: values[key] for key in EntryState.__dataclass_fields__
                              if key in values}, quote_age_seconds=0, venue_verified=True)
        result = assess_entry(policy, state, payload.symbol, 'KRX', payload.entry,
                              payload.stop, payload.cost_per_share)
        return result | {'allowed': False, 'simulation_only': True,
                         'assumptions': ['fresh_quote', 'verified_venue', 'user_supplied_cost'],
                         'order_execution_available': False}

    @app.get('/')
    def index():
        return FileResponse(assets / 'index.html')

    app.mount('/static', StaticFiles(directory=assets), name='static')
    return app


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description='Local research web app; no broker requests or orders')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--data-root', type=Path)
    parser.add_argument('--ledger', type=Path, help='Explicit local SQLite ledger when several exist')
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')
    try:
        policy_at(args.root.resolve())
    except DataError:
        parser.error('config/paper.json is unavailable or invalid; use --root PROJECT')
    uvicorn.run(create_app(args.root, data_root=args.data_root, ledger_path=args.ledger),
                host='127.0.0.1', port=args.port, proxy_headers=False, access_log=False)
