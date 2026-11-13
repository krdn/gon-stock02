from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

from gon_stock02.history import RAW_FIELDS, SEOUL, _bar, _timestamp
from gon_stock02.kis import KisFailure, SYMBOLS


def capture_minutes(client, seconds, output, *, now=None, monotonic=None, sleep=None):
    if type(seconds) is not int or not 1 <= seconds <= 120:
        raise KisFailure('invalid_capture_duration')
    now = now or (lambda: datetime.now(timezone.utc))
    monotonic = monotonic or time.monotonic
    sleep = sleep or time.sleep
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    started = now()
    capture_date = started.astimezone(SEOUL).date()
    report = {'environment': 'mock', 'market_requested': 'KRX', 'tr_id': 'FHKST03010200',
              'contract_mock_supported': True, 'status': 'running', 'seconds_requested': seconds,
              'started_at': started.isoformat(), 'capture_date': capture_date.isoformat(),
              'orders_sent': 0, 'requests_started': 0, 'responses_saved': 0,
              'datasets': {symbol: {'responses': 0, 'observations': 0} for symbol in SYMBOLS},
              'collection_complete': False, 'coverage_verified': False,
              'session_calendar_verified': False, 'halt_history_verified': False,
              'bar_finality_verified': False, 'backtest_ready': False,
              'source_files_at_start_sha256': {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                              for name in ('capture.py', 'kis.py', 'history.py')}}
    manifest = output / 'manifest.json'
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    deadline = monotonic() + seconds
    with (output / 'pages.jsonl').open('x') as journal, (output / 'observations.jsonl').open('x') as observations:
        try:
            while monotonic() < deadline:
                for symbol in SYMBOLS:
                    if monotonic() >= deadline:
                        break
                    requested = now()
                    if requested.astimezone(SEOUL).date() != capture_date:
                        raise KisFailure('capture_date_changed')
                    params = {'FID_COND_MRKT_DIV_CODE': 'J', 'FID_INPUT_ISCD': symbol,
                              'FID_INPUT_HOUR_1': requested.astimezone(SEOUL).strftime('%H%M%S'),
                              'FID_PW_DATA_INCU_YN': 'N', 'FID_ETC_CLS_CODE': ''}
                    report['requests_started'] += 1
                    data, _ = client._get('/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice',
                                          'FHKST03010200', params)
                    received = now()
                    rows = data.get('output2')
                    valid_shape = isinstance(rows, list) and all(isinstance(row, dict) for row in rows)
                    sequence = report['responses_saved'] + 1
                    journal.write(json.dumps({'sequence': sequence, 'symbol': symbol, 'params': params,
                        'requested_at': requested.isoformat(), 'received_at': received.isoformat(),
                        'output2': [{k: v for k, v in row.items() if k in RAW_FIELDS} for row in rows] if valid_shape else None},
                        ensure_ascii=False) + '\n')
                    journal.flush()
                    report['responses_saved'] += 1
                    report['datasets'][symbol]['responses'] += 1
                    if received.astimezone(SEOUL).date() != capture_date:
                        raise KisFailure('capture_date_changed')
                    if not valid_shape or not rows:
                        raise KisFailure('invalid_capture_response')
                    normalized = []
                    previous = None
                    for row in rows:
                        stamp = _timestamp(row, '1m')
                        if stamp.date() != capture_date or stamp > requested or (previous is not None and stamp >= previous):
                            raise KisFailure('invalid_capture_time')
                        previous = stamp
                        normalized.append({**_bar(row, symbol, '1m', stamp), 'sequence': sequence,
                            'requested_at': requested.isoformat(), 'received_at': received.isoformat(),
                            'available_at': received.isoformat(), 'finality': 'unverified', 'strategy_eligible': False})
                    for row in normalized:
                        observations.write(json.dumps(row, ensure_ascii=False) + '\n')
                    observations.flush()
                    report['datasets'][symbol]['observations'] += len(normalized)
                sleep(min(5, max(0, deadline - monotonic())))
            report['collection_complete'] = all(dataset['observations'] for dataset in report['datasets'].values())
            report['status'] = 'completed' if report['collection_complete'] else 'incomplete'
        except KisFailure as exc:
            report.update(status='failed', error=str(exc))
    report['finished_at'] = now().isoformat()
    report['sha256'] = {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                        for name in ('pages.jsonl', 'observations.jsonl')}
    manifest.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report
