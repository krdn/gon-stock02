from datetime import date, datetime, time, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from gon_stock02.kis import KisFailure, SYMBOLS, number


SEOUL = ZoneInfo('Asia/Seoul')
SOURCES = {
    '1d': ('inquire-daily-itemchartprice', 'FHKST03010100'),
    '1m': ('inquire-time-dailychartprice', 'FHKST03010230'),
}
RAW_FIELDS = {'stck_bsop_date', 'stck_cntg_hour', 'stck_oprc', 'stck_hgpr', 'stck_lwpr',
              'stck_clpr', 'stck_prpr', 'acml_vol', 'cntg_vol', 'acml_tr_pbmn',
              'flng_cls_code', 'mod_yn', 'prtt_rate', 'revl_issu_reas'}


def _days(start, end):
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)
            if (start + timedelta(days=offset)).weekday() < 5]


def _timestamp(row, timeframe):
    try:
        text = row['stck_bsop_date'] + (row['stck_cntg_hour'] if timeframe == '1m' else '')
        if not isinstance(text, str) or not re.fullmatch('[0-9]{14}' if timeframe == '1m' else '[0-9]{8}', text):
            raise ValueError
        stamp = datetime.strptime(text, '%Y%m%d%H%M%S' if timeframe == '1m' else '%Y%m%d').replace(tzinfo=SEOUL)
        if stamp.second:
            raise ValueError
        return stamp
    except (KeyError, TypeError, ValueError):
        raise KisFailure('invalid_history_time') from None


def _bar(row, symbol, timeframe, stamp):
    try:
        values = {name: number(row[key]) for name, key in
                  (('open', 'stck_oprc'), ('high', 'stck_hgpr'), ('low', 'stck_lwpr'),
                   ('close', 'stck_clpr' if timeframe == '1d' else 'stck_prpr'))}
        volume = number(row['acml_vol' if timeframe == '1d' else 'cntg_vol'])
        turnover = number(row['acml_tr_pbmn'])
    except (KeyError, TypeError, ValueError):
        raise KisFailure('invalid_market_data') from None
    if volume != volume.to_integral_value() or turnover != turnover.to_integral_value():
        raise KisFailure('invalid_market_data')
    zero_price = any(value == 0 for value in values.values())
    if zero_price and volume > 0:
        raise KisFailure('inconsistent_ohlc')
    if not zero_price and (values['low'] > min(values.values()) or values['high'] < max(values.values())):
        raise KisFailure('inconsistent_ohlc')
    return {'symbol': symbol, 'market_requested': 'KRX', 'timeframe': timeframe,
            'time': stamp.date().isoformat() if timeframe == '1d' else stamp.isoformat(),
            **{name: str(value) for name, value in values.items()}, 'volume': str(volume),
            'turnover' if timeframe == '1d' else 'cumulative_turnover': str(turnover),
            'zero_price': zero_price}


def _collect_series(client, symbol, timeframe, start, end, journal, bars, dataset):
    periods = [end] if timeframe == '1d' else _days(start, end)
    for day in periods:
        lower = datetime.combine(start if timeframe == '1d' else day, time.min if timeframe == '1d' else time(9), SEOUL)
        cursor = datetime.combine(day, time.min if timeframe == '1d' else time(15, 30), SEOUL)
        while cursor >= lower:
            endpoint, tr_id = SOURCES[timeframe]
            params = {'FID_COND_MRKT_DIV_CODE': 'J', 'FID_INPUT_ISCD': symbol}
            if timeframe == '1d':
                params.update(FID_INPUT_DATE_1=start.strftime('%Y%m%d'), FID_INPUT_DATE_2=cursor.strftime('%Y%m%d'),
                              FID_PERIOD_DIV_CODE='D', FID_ORG_ADJ_PRC='1')
            else:
                params.update(FID_INPUT_DATE_1=day.strftime('%Y%m%d'), FID_INPUT_HOUR_1=cursor.strftime('%H%M%S'),
                              FID_PW_DATA_INCU_YN='N', FID_FAKE_TICK_INCU_YN='')
            data, _ = client._get('/uapi/domestic-stock/v1/quotations/' + endpoint, tr_id, params)
            received = datetime.now(timezone.utc)
            rows = data.get('output2')
            if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
                raise KisFailure('invalid_history_response')
            journal.write(json.dumps({'symbol': symbol, 'timeframe': timeframe, 'endpoint': endpoint,
                                     'tr_id': tr_id, 'params': params, 'received_at': received.isoformat(),
                                     'output2': [{key: value for key, value in row.items() if key in RAW_FIELDS} for row in rows]},
                                    ensure_ascii=False) + '\n')
            journal.flush()
            dataset['pages'] += 1
            if not rows:
                break
            previous = None
            for row in rows:
                stamp = _timestamp(row, timeframe)
                if stamp > cursor or stamp > received:
                    raise KisFailure('invalid_history_time')
                if previous is not None and stamp >= previous:
                    raise KisFailure('duplicate_or_unordered_history')
                previous = stamp
                if stamp < lower:
                    dataset['outside_window_rows'] += 1
                    continue
                bars.append(_bar(row, symbol, timeframe, stamp))
            cursor = previous - (timedelta(days=1) if timeframe == '1d' else timedelta(minutes=1))


def collect_history(client, start, end, minute_start, output):
    today = datetime.now(SEOUL).date()
    if any(type(value) is not date for value in (start, end, minute_start)) or not start <= minute_start <= end <= today or (end - start).days > 365:
        raise KisFailure('invalid_history_dates')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    report = {'environment': 'mock', 'market_requested': 'KRX', 'started_at': datetime.now(timezone.utc).isoformat(),
              'request': {'start': start.isoformat(), 'end': end.isoformat(), 'minute_start': minute_start.isoformat()},
              'orders_sent': 0, 'datasets': [], 'backtest_ready': False, 'session_calendar_verified': False,
              'coverage_verified': False,
              'adjustment': 'unadjusted', 'historical_received_at_available': False,
              'contract_source': 'https://apiportal.koreainvestment.com/files/download/apiCollection/API_COLLECTION',
              'limitations': ['historical_minute_mock_unsupported', 'calendar_and_no_trade_unverified', 'corporate_actions_unverified',
                              'historical_receipt_time_unavailable', 'order_book_and_costs_unavailable',
                              'minute_turnover_is_cumulative', 'data_usage_rights_not_reviewed',
                              'current_day_finality_unverified' if end == today else 'historical_revision_possible']}
    bars = []
    stop = False
    with (output / 'pages.jsonl').open('x') as journal:
        for symbol in SYMBOLS:
            for timeframe in SOURCES:
                dataset = {'symbol': symbol, 'timeframe': timeframe, 'contract_mock_supported': timeframe == '1d',
                           'pages': 0, 'outside_window_rows': 0, 'status': 'not_run'}
                if timeframe == '1m':
                    dataset['requested_time_window'] = {'start': '09:00:00', 'end': '15:30:00',
                                                        'timezone': 'Asia/Seoul', 'calendar_adjusted': False}
                report['datasets'].append(dataset)
                if stop:
                    continue
                try:
                    _collect_series(client, symbol, timeframe, start if timeframe == '1d' else minute_start,
                                    end, journal, bars, dataset)
                    dataset['status'] = 'read_ok'
                except KisFailure as exc:
                    dataset.update(status='failed', reason=str(exc))
                    stop = str(exc) in ('rate_limited', 'authentication_failed', 'network_error', 'timeout')
    bars.sort(key=lambda bar: (bar['symbol'], bar['timeframe'], bar['time']))
    daily_dates = {bar['time'] for bar in bars if bar['timeframe'] == '1d'}
    expected_times = {f'{minute // 60:02}:{minute % 60:02}' for minute in range(9 * 60, 15 * 60 + 20)}
    for dataset in report['datasets']:
        selected = [bar for bar in bars if (bar['symbol'], bar['timeframe']) == (dataset['symbol'], dataset['timeframe'])]
        dataset.update(rows=len(selected), first=selected[0]['time'] if selected else None,
                       last=selected[-1]['time'] if selected else None,
                       zero_price_rows=sum(bar['zero_price'] for bar in selected))
        if dataset['timeframe'] == '1d':
            dates = {bar['time'] for bar in selected}
            dataset['missing_vs_other_symbols'] = sorted(daily_dates - dates)
            dataset['absent_weekdays_unclassified'] = [day.isoformat() for day in _days(start, end) if day.isoformat() not in dates]
        else:
            daily = []
            for day in _days(minute_start, end):
                day_rows = [bar for bar in selected if bar['time'][:10] == day.isoformat()]
                missing = sorted(expected_times - {bar['time'][11:16] for bar in day_rows})
                daily.append({'date': day.isoformat(), 'rows': len(day_rows), 'candidate_missing_minutes': missing})
            dataset['days'] = daily
            dataset['candidate_missing_minutes'] = sum(len(day['candidate_missing_minutes']) for day in daily)
    with (output / 'bars.jsonl').open('x') as file:
        for bar in bars:
            file.write(json.dumps(bar, ensure_ascii=False) + '\n')
    report['sha256'] = {name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in ('pages.jsonl', 'bars.jsonl')}
    report['collection_complete'] = all(dataset['status'] == 'read_ok' and dataset['rows'] > 0 for dataset in report['datasets'])
    report['structural_checks_passed'] = report['collection_complete'] and all(dataset['zero_price_rows'] == 0 for dataset in report['datasets'])
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    with (output / 'manifest.json').open('x') as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
        file.write('\n')
    return report
