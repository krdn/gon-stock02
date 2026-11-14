'use strict';

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const number = (value, digits = 0) => value == null ? '—' : Number(value).toLocaleString('ko-KR', {maximumFractionDigits: digits});
const percent = (value) => `${number(Number(value) * 100, 2)}%`;
const time = (value) => value ? new Date(value).toLocaleString('ko-KR', {timeZone: 'Asia/Seoul', hour12: false}) : '기록 없음';
const state = {overview: null, bundle: '', symbol: '005930', timeframe: '1d', series: null, page: 0, request: 0, controller: null, refresh: 0, start: '', end: ''};
const titles = {
  dashboard: ['오늘의 워크스페이스', '네 종목의 관측 기록과 검증 상태를 한눈에 확인하세요.'],
  data: ['데이터 탐색', '수집 묶음의 범위, 무결성, 사용 조건을 확인하세요.'],
  risk: ['위험 계산', '손실 여유와 비용을 반영해 진입 시나리오를 검토하세요.'],
  ledger: ['모의 주문 장부', '저장된 주문 상태와 확인된 체결 수량을 살펴보세요.'],
};
const errors = {
  integrity_failed: '파일이 수집 당시 해시와 다르거나 읽을 수 없습니다. 원본을 확인한 후 다시 불러오세요.',
  invalid_data: '저장 자료의 형식이 올바르지 않습니다. 해당 수집 묶음을 확인하세요.',
  bundle_not_found: '수집 묶음이 없거나 경로·이름이 허용되지 않습니다. 목록을 새로고침하고 경로를 확인하세요. 이름은 history- 또는 minute-capture- 뒤에 영문·숫자·밑줄·하이픈을 사용합니다.',
  invalid_date_range: '시작일은 종료일보다 늦을 수 없습니다.',
  file_unavailable: '필요한 파일을 읽을 수 없습니다.',
  invalid_policy: '위험 정책 파일을 확인해 주세요.',
  unsafe_path: '허용된 데이터 폴더 밖의 파일은 읽을 수 없습니다.',
  too_many_rows: '한 묶음에서 읽을 수 있는 100,000행을 초과했습니다.',
  file_too_large: '한 파일에서 읽을 수 있는 64MB를 초과했습니다.',
};
const riskReasons = {
  execution_gate_closed: '위험 한도 내 시나리오입니다. 실제 시세·계좌 확인과 주문 실행은 수행하지 않았습니다.',
  loss_limit: '일일 손실 또는 누적 낙폭 한도에 도달했습니다.',
  position_limit: '동시 보유 종목 수 한도를 초과합니다.',
  entry_limit: '종목별 하루 진입 횟수 한도에 도달했습니다.',
  minimum_lot_exceeds_limit: '남은 자금 또는 손실 여유로는 1주를 배정할 수 없습니다.',
  invalid_numbers: '금액과 손절 기준을 확인하세요. 진입가는 0보다 커야 하고, 손절가는 진입가보다 낮아야 합니다. 최고 평가액은 현재 평가액 이상이어야 합니다.',
  invalid_positions: '보유 수와 노출 금액을 확인하세요. 종목 노출은 전체 노출 이하여야 합니다.',
  invalid_policy: '현재 위험 정책에 유효하지 않은 값이 있습니다.',
  instrument_or_environment_blocked: '현재 정책에서 허용하지 않는 종목 또는 환경입니다.',
  invalid_input: '입력한 운용 상태와 정책을 확인하세요.',
};

async function api(path, options = {}) {
  const response = await fetch(path, {cache: 'no-store', ...options});
  let body;
  try { body = await response.json(); } catch { throw new Error('서버 응답을 읽을 수 없습니다. 다시 시도해 주세요.'); }
  if (!response.ok) {
    const reason = body.detail;
    throw new Error(errors[reason] || (Array.isArray(reason) ? '입력값을 확인하세요. 금액은 0 이상의 유한한 숫자여야 합니다.' : '요청을 처리하지 못했습니다. 서버와 자료 상태를 확인해 주세요.'));
  }
  return body;
}

function showError(selector, message) {
  const target = $(selector);
  target.textContent = message || '';
  target.hidden = !message;
}

function navigate(event) {
  const requested = location.hash.slice(1);
  const page = Object.hasOwn(titles, requested) ? requested : 'dashboard';
  $$('.page').forEach((element) => { element.hidden = element.id !== page; });
  $$('[data-nav]').forEach((link) => {
    const active = link.dataset.nav === page;
    link.classList.toggle('active', active);
    if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
  });
  $('#page-title').textContent = titles[page][0];
  $('#page-description').textContent = titles[page][1];
  $('#breadcrumb').textContent = $(`[data-nav="${page}"]`).textContent.trim();
  if (event) { $('#main').focus({preventScroll: true}); window.scrollTo(0, 0); }
  if (page === 'ledger') loadLedger();
}

function delta(rows) {
  if (rows.length < 2) return {label: '비교 관측 없음', className: 'muted'};
  if (rows.at(-1).zero_price || rows.at(-2).zero_price) return {label: '0가격 포함 · 등락 비교 제외', className: 'muted'};
  const change = Number(rows.at(-1).close) - Number(rows.at(-2).close);
  return {label: `${change > 0 ? '+' : ''}${number(change)} (${change > 0 ? '+' : ''}${number(change / Number(rows.at(-2).close) * 100, 2)}%)`, className: change > 0 ? 'up' : change < 0 ? 'down' : 'muted'};
}

function renderOverview(data) {
  const p = data.policy;
  const selected = data.bundles.find((bundle) => bundle.id === state.bundle);
  const count = selected?.datasets.reduce((sum, row) => sum + (Number(row.rows) || 0), 0) || 0;
  const metrics = [
    ['가상 운용자금', number(p.initial_capital_krw), '원', '위험 정책 기준 · 실제 계좌 잔고 아님', '₩'],
    ['1회 손실 예산', number(Number(p.initial_capital_krw) * Number(p.risk_per_trade)), '원', `초기 자금의 ${percent(p.risk_per_trade)} · 상태에 따라 축소`, '◇'],
    ['일일 손실 한도', number(Number(p.initial_capital_krw) * Number(p.daily_loss_limit)), '원', `초기 자금 기준 ${percent(p.daily_loss_limit)} · 정책 한도`, '↘'],
    ['수집 기록', number(count), '행', '선택 묶음의 기록 건수 · 완전성 미검증', '▤'],
  ];
  $('#metrics').innerHTML = metrics.map(([label, value, unit, note, icon]) => `<article class="metric"><div class="metric-label">${escapeHtml(label)}<span class="metric-icon" aria-hidden="true">${icon}</span></div><div class="metric-value">${value}<small>${unit}</small></div><div class="metric-note">${escapeHtml(note)}</div></article>`).join('');
  $('#bundle-select').innerHTML = data.bundles.length ? data.bundles.map((bundle) => `<option value="${escapeHtml(bundle.id)}"${bundle.id === state.bundle ? ' selected' : ''}>${escapeHtml(bundle.id)}${bundle.collection_complete === true ? '' : bundle.collection_complete === false ? ' · 부분/미완료' : ' · 상태 확인 불가'}</option>`).join('') : '<option value="">수집 자료 없음</option>';
  $('#bundle-select').disabled = !data.bundles.length;
  $('#updated-at').textContent = `화면 갱신 ${time(data.generated_at)} KST`;
  $('#policy-values').innerHTML = [
    ['1회 위험 비율', percent(p.risk_per_trade)], ['일일 손실 한도', percent(p.daily_loss_limit)],
    ['누적·최고점 낙폭 한도', percent(p.drawdown_limit)], ['종목별 투자 상한', percent(p.max_symbol_allocation)],
    ['전체 투자 상한', percent(p.max_gross_allocation)], ['최대 보유 종목', `${p.max_positions}종목`],
    ['종목별 하루 진입', `${p.max_entries_per_symbol_per_day}회`],
  ].map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`).join('');
  if (!$('#risk-state-fields').children.length) initRisk(p, data.symbols);
  renderBundles(data.bundles);
}

function renderBundles(bundles) {
  $('#data-empty').hidden = !!bundles.length;
  $('#bundle-list').innerHTML = bundles.map((bundle) => {
    const matched = bundle.integrity === 'matched';
    const rows = bundle.datasets.map((row) => `<tr><td>${escapeHtml(state.overview.symbols[row.symbol] || row.symbol)}</td><td>${row.timeframe === '1d' ? '일봉' : '1분봉'}</td><td class="num">${number(row.rows)}</td><td>${escapeHtml(row.first || '—')}<br>${escapeHtml(row.last || '—')}</td><td>${row.contract_mock_supported ? '지원' : '모의 미지원'}</td><td class="num">${row.candidate_missing_minutes == null ? '—' : number(row.candidate_missing_minutes)}</td><td><span class="badge ${row.status === 'read_ok' || row.status === 'completed' ? 'green' : 'amber'}">${row.status === 'read_ok' || row.status === 'completed' ? '수집 응답 있음' : '부분 / 미완료'}</span></td></tr>`).join('');
    return `<article class="panel bundle-card"><div class="panel-head"><div><p class="eyebrow">${bundle.kind === 'capture' ? 'MINUTE CAPTURE' : 'HISTORICAL DATA'}</p><h2>${escapeHtml(bundle.id)}</h2></div><div><span class="badge ${matched ? 'green' : 'red'}">${matched ? '저장 파일 일치' : '파일 확인 필요'}</span><button class="button secondary" data-open-bundle="${escapeHtml(bundle.id)}" ${matched ? '' : 'disabled'}>차트 보기 ↗</button></div></div><div class="bundle-meta"><span>수집 종료 ${escapeHtml(time(bundle.finished_at))}</span><span>${bundle.collection_complete === true ? '수집 루프 완료' : bundle.collection_complete === false ? '수집 미완료' : '수집 상태 확인 불가'}</span><span class="badge amber">백테스트 HOLD</span></div>${bundle.error ? `<p class="notice error">${escapeHtml(errors[bundle.error] || '수집 묶음을 확인하세요.')}</p>` : ''}${rows ? `<div class="table-scroll" tabindex="0" role="region" aria-label="${escapeHtml(bundle.id)} 수집 현황"><table><caption class="skip">종목별 수집 상태</caption><thead><tr><th>종목</th><th>주기</th><th class="num">행 수</th><th>관측 시작 / 종료</th><th>API 계약</th><th class="num">결측 후보</th><th>수집 상태</th></tr></thead><tbody>${rows}</tbody></table></div>` : ''}<div class="file-checks">${Object.entries(bundle.file_checks || {}).map(([file, check]) => `<span class="badge ${check === 'matched' ? 'neutral' : 'red'}">${escapeHtml(file)} · ${check === 'matched' ? 'SHA-256 일치' : '확인 실패'}</span>`).join('')}</div><p class="muted">완전성·봉 확정 미검증. 결측 후보는 휴일·무거래·정지를 확정한 결과가 아닙니다.</p></article>`;
  }).join('');
}

function params(symbol = state.symbol, includeDates = true) {
  const query = new URLSearchParams({bundle: state.bundle, symbol, timeframe: state.timeframe});
  if (includeDates && state.start) query.set('start', state.start);
  if (includeDates && state.end) query.set('end', state.end);
  return query;
}

async function refreshSeries() {
  const request = ++state.request;
  state.controller?.abort();
  state.controller = new AbortController();
  const signal = state.controller.signal;
  state.series = null;
  state.page = 0;
  showError('#series-error', '');
  $('#chart').onpointermove = $('#chart').onpointerleave = null;
  $('#chart').innerHTML = '<p class="muted">관측 자료를 불러오는 중…</p>';
  $('#chart-price').textContent = '—';
  $('#chart-date').textContent = '';
  $('#chart-change').textContent = '';
  $('#bar-table').innerHTML = '';
  $('#download').setAttribute('aria-disabled', 'true');
  $('#download').removeAttribute('href');
  $('#row-count').textContent = '';
  $('#table-page').textContent = '';
  $('#prev-page').disabled = $('#next-page').disabled = true;
  $('#chart-title').textContent = `${state.overview?.symbols[state.symbol] || '종목'} · ${state.timeframe === '1d' ? '일봉' : '1분봉'}`;
  filterStatus();
  $$('[data-timeframe]').forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.timeframe === state.timeframe)));
  if (!state.overview) return;
  const focusedSymbol = document.activeElement?.closest('#watchlist button')?.dataset.symbol;
  $('#watchlist').innerHTML = Object.entries(state.overview.symbols).map(([symbol, name]) => `<button type="button" class="stock ${symbol === state.symbol ? 'active' : ''}" data-symbol="${symbol}" aria-pressed="${symbol === state.symbol}"><span class="stock-title">${escapeHtml(name)}<span class="tiny-badge">KRX</span></span><span class="stock-code">${symbol}</span><span class="stock-price" id="price-${symbol}">—</span><span class="stock-change muted" id="change-${symbol}">관측 조회 중</span><span class="stock-date" id="date-${symbol}"></span></button>`).join('');
  if (focusedSymbol) $(`#watchlist [data-symbol="${focusedSymbol}"]`)?.focus({preventScroll: true});
  if (!state.bundle) {
    $('#chart').innerHTML = '<div class="empty"><h2>저장된 시세가 없습니다</h2><p>수집 자료를 연결하면 차트와 표가 나타납니다.</p></div>';
    $('#chart-caption').textContent = '가상 시세를 생성하지 않습니다.';
    Object.keys(state.overview.symbols).forEach((symbol) => { $(`#change-${symbol}`).textContent = '관측 없음'; });
    return;
  }
  const queries = Object.keys(state.overview.symbols).map(async (symbol) => {
    try {
      const result = await api(`/api/series?${params(symbol)}`, {signal});
      if (request !== state.request) return;
      const rows = result.rows;
      const change = delta(rows);
      $(`#price-${symbol}`).textContent = rows.length ? rows.at(-1).zero_price ? '가격 확인 필요' : `${number(rows.at(-1).close)}원` : '—';
      $(`#change-${symbol}`).textContent = rows.length ? change.label : '선택 구간 관측 없음';
      $(`#change-${symbol}`).className = `stock-change ${change.className}`;
      $(`#date-${symbol}`).textContent = rows.length ? `${rows.at(-1).time.replace('T', ' ').replace('+09:00', '')} 기준` : '';
      if (symbol === state.symbol) {
        state.series = result;
        renderChart();
        renderTable();
        $('#download').href = `/api/export.csv?${params()}`;
        $('#download').setAttribute('aria-disabled', String(!rows.length));
      }
    } catch (error) {
      if (error.name === 'AbortError' || request !== state.request) return;
      $(`#change-${symbol}`).textContent = '자료 확인 필요';
      if (symbol === state.symbol) {
        showError('#series-error', error.message);
        $('#chart').innerHTML = '<div class="empty"><h2>이 자료를 표시할 수 없습니다</h2><p>아래 오류를 확인하거나 다른 수집 묶음을 선택해 주세요.</p></div>';
        $('#chart-caption').textContent = '자료 오류 · 이전 차트는 표시하지 않습니다.';
      }
    }
  });
  await Promise.all(queries);
}

function renderChart() {
  if (!state.series) return;
  const all = state.series.rows;
  const limit = $('#chart-range').value;
  const rows = limit === 'all' ? all : all.slice(-Number(limit));
  const chart = $('#chart');
  chart.onpointermove = chart.onpointerleave = null;
  if (!rows.length) {
    chart.innerHTML = '<div class="empty"><h2>선택 구간에 관측이 없습니다</h2><p>날짜 범위나 시세 주기를 변경해 주세요.</p></div>';
    $('#chart-caption').textContent = '누락 구간을 임의 가격으로 채우지 않습니다.';
    return;
  }
  const latest = rows.at(-1), change = delta(rows);
  $('#chart-price').textContent = latest.zero_price ? '가격 확인 필요' : `${number(latest.close)}원`;
  $('#chart-change').textContent = change.label;
  $('#chart-change').className = change.className;
  $('#chart-date').textContent = `${latest.time.replace('T', ' ').replace('+09:00', '')} 기준`;
  const width = 680, height = 260, left = 9, right = 68, top = 14, bottom = 196;
  const valid = rows.filter((row) => !row.zero_price);
  if (!valid.length) {
    chart.innerHTML = '<div class="empty"><h2>유효한 가격 관측이 없습니다</h2><p>0가격 기록은 표와 CSV에 보존합니다.</p></div>';
    $('#chart-caption').textContent = `0가격 관측 ${number(rows.length)}개 · 시세와 등락 계산에서 제외`;
    return;
  }
  const max = Math.max(...valid.map((row) => Number(row.high)));
  const min = Math.min(...valid.map((row) => Number(row.low)));
  const padding = (max - min) * 0.12 || max * 0.01 || 1;
  const lower = min - padding, upper = max + padding;
  const x = (index) => left + (index + 0.5) * (width - left - right) / rows.length;
  const y = (value) => top + (upper - Number(value)) / (upper - lower) * (bottom - top);
  const volumeMax = Math.max(...rows.map((row) => Number(row.volume)), 1);
  let markup = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(state.series.name)} ${rows.length}개 관측의 가격과 거래량. 상세 값은 아래 표에서 확인할 수 있습니다.">`;
  for (let i = 0; i <= 4; i++) {
    const value = lower + (upper - lower) * i / 4, yy = y(value);
    markup += `<line class="chart-grid" x1="${left}" x2="${width - right}" y1="${yy}" y2="${yy}"/><text x="${width - right + 12}" y="${yy + 4}">${number(value)}</text>`;
  }
  if (rows.length > 120) {
    // Break the line at invalid prices; never draw a fabricated fall to zero.
    const segment = (points) => points.length === 1
      ? `<circle cx="${points[0].split(',')[0]}" cy="${points[0].split(',')[1]}" r="2.5" fill="#14654e"/>`
      : `<polyline class="chart-line" points="${points.join(' ')}"/>`;
    let points = [];
    rows.forEach((row, index) => {
      if (row.zero_price) {
        if (points.length) markup += segment(points);
        points = [];
      } else points.push(`${x(index)},${y(row.close)}`);
    });
    if (points.length) markup += segment(points);
  }
  rows.forEach((row, index) => {
    if (row.zero_price) return;
    const xx = x(index), candleWidth = Math.max(1, (width - left - right) / rows.length * 0.55);
    const color = Number(row.close) >= Number(row.open) ? '#c35d60' : '#5981ae';
    if (rows.length <= 120) {
      markup += `<g><title>${escapeHtml(row.time)} · 시가 ${number(row.open)} · 고가 ${number(row.high)} · 저가 ${number(row.low)} · 종가 ${number(row.close)} · 거래량 ${number(row.volume)}</title><line stroke="${color}" x1="${xx}" x2="${xx}" y1="${y(row.high)}" y2="${y(row.low)}"/><rect fill="${color}" x="${xx - candleWidth / 2}" y="${Math.min(y(row.open), y(row.close))}" width="${candleWidth}" height="${Math.max(1, Math.abs(y(row.open) - y(row.close)))}"/></g>`;
    }
    const volumeHeight = Number(row.volume) / volumeMax * 29;
    markup += `<rect class="chart-volume" x="${xx - candleWidth / 2}" y="${234 - volumeHeight}" width="${candleWidth}" height="${volumeHeight}"/>`;
  });
  const indices = [...new Set([0, Math.floor((rows.length - 1) / 2), rows.length - 1])];
  indices.forEach((index, n) => {
    const label = state.timeframe === '1d' ? rows[index].time.slice(2).replaceAll('-', '.') : rows[index].time.slice(5, 16).replace('T', ' ');
    markup += `<text text-anchor="${n === 0 ? 'start' : n === indices.length - 1 ? 'end' : 'middle'}" x="${x(index)}" y="254">${escapeHtml(label)}</text>`;
  });
  markup += `<line id="chart-crosshair" class="chart-hover" x1="0" x2="0" y1="${top}" y2="235" visibility="hidden"/></svg>`;
  chart.innerHTML = markup;
  const caption = `${number(rows.length)}개 관측 · ${rows.length > 120 ? '종가선' : 'OHLC 캔들'} / 거래량 · 관측 순서 간격 · 원주가 · 봉 확정 미검증${valid.length < rows.length ? ` · 0가격 ${number(rows.length - valid.length)}개 제외` : ''}`;
  $('#chart-caption').textContent = caption;
  chart.onpointermove = (event) => {
    const box = chart.querySelector('svg').getBoundingClientRect();
    const relative = (event.clientX - box.left) / box.width * width;
    const index = Math.max(0, Math.min(rows.length - 1, Math.floor((relative - left) / (width - left - right) * rows.length)));
    const row = rows[index], line = $('#chart-crosshair');
    line.setAttribute('x1', x(index)); line.setAttribute('x2', x(index)); line.setAttribute('visibility', 'visible');
    $('#chart-caption').textContent = row.zero_price ? `${row.time.replace('T', ' ')} · 0가격 관측 · 시세 계산 제외` : `${row.time.replace('T', ' ')} · 시 ${number(row.open)} / 고 ${number(row.high)} / 저 ${number(row.low)} / 종 ${number(row.close)} · 거래량 ${number(row.volume)} · 관측 ${row.versions}회`;
  };
  chart.onpointerleave = () => { $('#chart-crosshair')?.setAttribute('visibility', 'hidden'); $('#chart-caption').textContent = caption; };
}

function renderTable() {
  const rows = state.series?.rows || [];
  const pages = Math.max(1, Math.ceil(rows.length / 20));
  state.page = Math.min(state.page, pages - 1);
  const visible = [...rows].reverse().slice(state.page * 20, (state.page + 1) * 20);
  $('#row-count').textContent = `봉 ${number(rows.length)}개 · 관측 ${number(state.series?.observations || 0)}회`;
  $('#bar-table').innerHTML = visible.length ? `<table><thead><tr><th scope="col">관측 시각 (KST)</th><th scope="col" class="num">시가</th><th scope="col" class="num">고가</th><th scope="col" class="num">저가</th><th scope="col" class="num">종가</th><th scope="col" class="num">거래량</th><th scope="col">확정</th></tr></thead><tbody>${visible.map((row) => `<tr><td>${escapeHtml(row.time.replace('T', ' ').replace('+09:00', ''))}</td>${['open', 'high', 'low', 'close', 'volume'].map((key) => `<td class="num">${number(row[key])}</td>`).join('')}<td><span class="badge ${row.zero_price ? 'red' : 'neutral'}">${row.zero_price ? '0가격 주의' : '미검증'}</span></td></tr>`).join('')}</tbody></table>` : '<div class="empty">표시할 관측 데이터가 없습니다.</div>';
  $('#table-page').textContent = `${state.page + 1} / ${pages} 페이지 · 최신 관측부터 표시`;
  $('#prev-page').disabled = state.page === 0;
  $('#next-page').disabled = state.page >= pages - 1;
}

function filterStatus() {
  const pending = $('#date-start').value !== state.start || $('#date-end').value !== state.end;
  const message = `적용 구간: ${state.start || '처음'} ~ ${state.end || '마지막'}${pending ? ' · 날짜가 변경되었습니다. 기간 적용을 눌러 주세요.' : ''}`;
  if ($('#filter-status').textContent !== message) $('#filter-status').textContent = message;
}

function initRisk(policy, symbols) {
  $('#risk-symbol').innerHTML = Object.entries(symbols).map(([symbol, name]) => `<option value="${symbol}">${escapeHtml(name)}</option>`).join('');
  const initial = policy.initial_capital_krw;
  const fields = [
    ['equity', '현재 가상 평가액', initial], ['day_open_equity', '일 시작 가상 평가액', initial],
    ['peak_equity', '최고 가상 평가액', initial], ['cash', '사용 가능 현금', initial],
    ['gross_exposure', '전체 보유·대기 노출', '0'], ['symbol_exposure', '해당 종목 노출', '0'],
    ['reserved_loss_krw', '보유·대기 예약 손실', '0'], ['positions', '보유 종목 수', '0'],
    ['entries_today', '오늘 해당 종목 진입 수', '0'],
  ];
  $('#risk-state-fields').innerHTML = fields.map(([name, label, value]) => `<label>${label}<span>${name === 'positions' || name === 'entries_today' ? '개 / 회' : '원'}</span><input type="number" name="${name}" min="0" max="${name === 'positions' || name === 'entries_today' ? '100' : '1000000000000'}" step="1" value="${escapeHtml(value)}" required></label>`).join('');
}

let riskRequest = 0;
async function calculate(event) {
  event.preventDefault();
  const form = event.currentTarget, button = form.querySelector('button[type=submit]');
  const input = Object.fromEntries(new FormData(form));
  const request = ++riskRequest;
  input.positions = Number(input.positions); input.entries_today = Number(input.entries_today);
  button.disabled = true;
  $('#risk-result').innerHTML = '<p role="status">위험 한도를 계산하고 있습니다…</p>';
  try {
    const result = await api('/api/risk', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(input)});
    if (request !== riskRequest) return;
    $('#risk-result').innerHTML = `<p class="eyebrow">SIMULATION RESULT</p><span class="badge ${result.risk_passed ? 'green' : 'amber'}">${result.risk_passed ? '가정 내 위험 한도 충족' : '배정 차단'}</span><div class="result-number">${number(result.quantity ?? 0)}<small>주</small></div><h2>${result.risk_passed ? '시나리오 배정 수량' : '진입 조건을 확인하세요'}</h2><p class="muted">${escapeHtml(riskReasons[result.reason] || result.reason)}</p>${result.planned_loss_krw != null ? `<div class="result-loss"><span>비용 포함 계획 손실</span><strong>${number(result.planned_loss_krw, 2)}원</strong></div>` : ''}<p class="muted">새 시세·거래 가능 시장 가정 / 입력 비용 적용<br>주문 실행 OFF · 저장된 시세와 자동 연결하지 않음</p>`;
  } catch (error) {
    if (request !== riskRequest) return;
    $('#risk-result').innerHTML = `<p class="eyebrow">INPUT CHECK</p><h2>계산할 수 없습니다</h2><p role="alert">${escapeHtml(error.message)}</p>`;
  } finally { button.disabled = false; }
}

let ledgerRequest = 0;
async function loadLedger() {
  const request = ++ledgerRequest;
  $('#ledger-content').innerHTML = '<p role="status" class="muted">저장 장부를 읽는 중…</p>';
  try {
    const data = await api('/api/ledger');
    if (request !== ledgerRequest) return;
    if (data.status !== 'ok') {
      const title = data.reason === 'multiple_ledgers' ? '조회할 장부를 선택해야 합니다' : data.status === 'error' ? '장부를 읽지 못했습니다' : '연결된 주문 장부가 없습니다';
      const detail = data.reason === 'multiple_ledgers' ? '여러 장부가 있습니다. 서버를 --ledger 옵션으로 실행해 사용할 파일을 지정하세요.' : data.status === 'error' ? '장부 파일 또는 잠금 상태를 확인한 뒤 새로고침해 주세요. 파일을 새로 만들거나 변경하지 않았습니다.' : '기존 모의 주문 장부가 생성되면 조회할 수 있습니다. 빈 장부나 잔고 0으로 간주하지 않습니다.';
      $('#ledger-content').innerHTML = `<div class="empty"><h2>${title}</h2><p>${detail}</p></div>`;
      return;
    }
    const labels = {SUBMITTING: '제출 중', OPEN: '접수', PARTIAL: '부분체결', FILLED: '체결', CANCELED: '취소', REJECTED: '거부', UNKNOWN: '응답 불명', CANCEL_SUBMITTING: '취소 요청 중', CANCEL_PENDING: '취소 확인 중'};
    $('#ledger-content').innerHTML = `<div class="panel-head"><h2>저장된 주문 이력</h2><span class="badge neutral">읽기 전용</span></div><div class="ledger-metrics"><div><strong>${number(data.total)}</strong><span>장부의 전체 주문</span></div><div><strong>${data.blocked_reason ? '확인 필요' : '없음'}</strong><span>저장된 차단 사유</span></div></div>${data.blocked_reason ? `<p class="notice error">기록된 차단 사유: ${escapeHtml(data.blocked_reason)}</p>` : ''}${data.orders.length ? `<div class="table-scroll" tabindex="0" role="region" aria-label="데이터 표"><table><thead><tr><th>주문일</th><th>종목</th><th>구분</th><th class="num">주문 / 체결 / 잔량</th><th class="num">지정가</th><th>상태</th></tr></thead><tbody>${data.orders.map((row) => `<tr><td>${escapeHtml(row.day)}</td><td>${escapeHtml(row.name)}</td><td>${row.side === 'buy' ? '매수' : '매도'}</td><td class="num">${number(row.quantity)} / ${number(row.filled)} / ${number(row.remaining)}</td><td class="num">${number(row.price)}</td><td><span class="badge ${row.state === 'UNKNOWN' ? 'red' : 'neutral'}">${escapeHtml(labels[row.state] || row.state)}</span></td></tr>`).join('')}</tbody></table></div>` : '<div class="empty"><h2>아직 기록된 모의 주문이 없습니다</h2><p>연결된 장부의 주문은 0건입니다. 현재 브로커 계좌를 조회한 결과는 아닙니다.</p></div>'}<p class="ledger-note">최근 ${data.limit}건까지 표시 · 마지막 주문 이벤트 ${escapeHtml(time(data.last_event_at))} · 현재 브로커 대조 미수행</p>`;
  } catch (error) {
    if (request === ledgerRequest) $('#ledger-content').innerHTML = `<p role="alert" class="notice error">${escapeHtml(error.message)}</p>`;
  }
}

async function refresh() {
  const request = ++state.refresh;
  $('#refresh').disabled = true;
  $('#loading').hidden = false;
  showError('#global-error', '');
  try {
    const data = await api('/api/overview');
    if (request !== state.refresh) return;
    state.overview = data;
    if (!data.bundles.some((bundle) => bundle.id === state.bundle)) state.bundle = data.bundles.find((bundle) => bundle.integrity === 'matched' && bundle.collection_complete)?.id || data.bundles[0]?.id || '';
    renderOverview(data);
    await refreshSeries();
    if (location.hash === '#ledger') await loadLedger();
  } catch (error) {
    showError('#global-error', `${error.message} 기존 화면이 있다면 마지막 성공 시점의 자료입니다.`);
  } finally {
    if (request === state.refresh) { $('#refresh').disabled = false; $('#loading').hidden = true; }
  }
}

window.addEventListener('hashchange', navigate);
$('#refresh').addEventListener('click', refresh);
$('#bundle-select').addEventListener('change', (event) => { state.bundle = event.target.value; renderOverview(state.overview); refreshSeries(); });
$('#watchlist').addEventListener('click', (event) => { const button = event.target.closest('[data-symbol]'); if (button) { state.symbol = button.dataset.symbol; refreshSeries(); } });
$$('[data-timeframe]').forEach((button) => button.addEventListener('click', () => { state.timeframe = button.dataset.timeframe; refreshSeries(); }));
$('#chart-range').addEventListener('change', renderChart);
$('#date-filter').addEventListener('submit', (event) => { event.preventDefault(); state.start = $('#date-start').value; state.end = $('#date-end').value; refreshSeries(); });
$('#date-filter').addEventListener('input', filterStatus);
$('#reset-dates').addEventListener('click', () => { state.start = state.end = $('#date-start').value = $('#date-end').value = ''; refreshSeries(); });
$('#prev-page').addEventListener('click', () => { state.page--; renderTable(); });
$('#next-page').addEventListener('click', () => { state.page++; renderTable(); });
$('#bundle-list').addEventListener('click', (event) => { const button = event.target.closest('[data-open-bundle]'); if (button) { state.bundle = button.dataset.openBundle; renderOverview(state.overview); refreshSeries(); location.hash = 'dashboard'; window.scrollTo(0, 0); } });
$('#risk-form').addEventListener('submit', calculate);
$('#risk-form').addEventListener('input', () => {
  riskRequest++;
  $('#risk-result').innerHTML = '<p class="eyebrow">SIMULATION RESULT</p><h2>입력값이 변경되었습니다</h2><p class="muted">위험 한도 계산을 눌러 현재 입력으로 다시 계산해 주세요.</p>';
});
$('#download').addEventListener('click', (event) => { if ($('#download').getAttribute('aria-disabled') === 'true') event.preventDefault(); });
navigate();
refresh();
