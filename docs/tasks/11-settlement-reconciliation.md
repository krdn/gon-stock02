# Issue #11 — 남은 15일의 공식 결제 근거 대조

- [사용자 지시와 한 단계 승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873164444) · [직전 결과](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6872994237) · [Issue #11](https://github.com/krdn/gon-stock02/issues/11).
- 승인 단계/마지막 단계: `11-settlement-reconciliation-20261114` 하나. 전환 ID는 `issue11-settlement-reconciliation-20261114`다. 최초 전환 담당은 `01a1d8a7-0cc4-70a0-ba60-539eda1e2836`. 실제 담당·기준 SHA/blob·탭 ID는 해당 이슈의 최신 유효 pending/started가 기준이다.
- 이전 PR #25는 main `010a89a9c140fb2d981e4aa6a3dcfb5f897a8e71`에 병합됐다. PR/main 각92테스트·wheel/sdist·구성 CI와 원격 4파일 blob 일치를 확인했다. 새 인계 기준은 이 문서 반영 후 pending에서 고정한다.
- 세션 판단: 2026-11-14T06:29:06.816Z 기록은 최근 입력259,465/컨텍스트475,000토큰(54.6%), 최근 출력833토큰이다. 누적 total_tokens11,177,092는 반복 입력·캐시를 포함한 합계다. 현재 점유·정확한 잔여량·비용 절감의 측정은 아니다. 완료 단계 경계에서 새 세션을 사용한다.

## 시작 전 실제 탭 확인

사용자가 새 탭 생성 확인을 작업 시작 조건으로 지정했다. `create_thread` 반환만으로 Herdr 탭 생성까지 완료됐다고 표시하지 않는다.

부모는 새 세션을 한 번 만들고, Herdr `gon-stock02` space의 새 탭에 같은 세션 ID를 초기 프롬프트 없이 `codex resume`로 표시한다. `herdr-app ls/status`, 연결 터미널의 foreground resume ID, 앱 렌더링을 대조한다. 성공한 경우에만 `tab_verified=true`, `herdr_space_id`, `herdr_tab_id`, `herdr_terminal_id`, `next_thread_id`가 있는 started를 게시한다. 생성 결과가 불명확하면 중복 생성하지 않는다.

새 세션은 자기 `CODEX_THREAD_ID`와 앱 `read_thread`, started의 `next_thread_id`·`tab_verified=true`·탭/터미널, 기준 HEAD/blob·기존 별도 변경을 대조한다. 그 전에는 지정 인계 자료의 읽기 전용 점검만 허용하며 공개 조사·파일 편집을 시작하지 않는다. started가 없으면 5초 간격 최대3회 재조회 후 대기 종료한다. 부모가 확인을 마친 후 같은 세션에 재개 메시지를 보내면 다시 대조한다. 새 세션을 다시 만들지 않는다.

## 조사 범위와 완료 조건

직전 증거 `date_results`의 `broker_reported_settlement_day=null`인 아래15일을 조사한다.

`2025-12-25`, `2026-01-01`, `2026-02-16`, `2026-02-17`, `2026-02-18`, `2026-03-02`, `2026-05-01`, `2026-05-05`, `2026-05-25`, `2026-07-17`, `2026-08-17`, `2026-09-24`, `2026-09-25`, `2026-10-05`, `2026-10-09`.

- KRX·공식 증권사의 날짜별 결제 제외/순연·휴장 예외 자료를 확인한다. KRX 직접 원출력, 증권사 공지, 일반 규정과 계산, 한국투자 현재 계좌 적용을 구분한다. 휴장·일봉 부재·법정 공휴일만으로 결제일 제외를 확정하지 않는다.
- 15일 각각에 URL·공표/확인 시각·식별자/해시·명시된 시장/결제 범위·판정·남은 조건을 새 `docs/evidence/settlement-reconciliation-2026-11-14.json`에 기록한다. 미수신·상충은 null/HOLD다. 기존06-03과12-31 근거는 식별하고 기존 증거는 덮어쓰지 않는다.
- 직전 KRX 휴장 화면의 2025/2026 날짜 행 미수신, 보도자료 HTTP200 빈 본문, 연별 PDF 미확보, 일부 접근 거부와 KIND 휴장 검색0건을 재사용한다. 같은 조건의 실패를 반복하지 않는다. 다른 공식 출력·식별자가 있는 원공지를 확보할 때만 새로 확인한다. 빈 결과를 공시 부재로 판단하지 않는다.
- 출처/해시·대상 집합·이전 원본/증거 불변·JSON/상대 링크 검사를 마친다. 정상 브랜치/PR/CI·main SHA/변경 blob 원격 확인·Issue #11 결과 인계 후 이번 단계에서 종료한다. 코드 없는 조사에 로컬 코드 테스트·외부 리뷰를 자동 추가하지 않는다.
- 판정을 실제 계좌 차감·배당 권리일·원천징수·수정주가·전체 세션/봉 완전성·정지 없음·백테스트 적격으로 확대하지 않는다. Issue #11은 OPEN·첫 수용 기준만 완료 상태를 유지한다.

## 필수 읽기와 소유권

AGENTS.md → docs/WORKFLOW.md → docs/STATE.md → 이 파일 → [세션 절차](../operations/session-handoff.md). 이어서 아래 지정 부분과 Issue #11의 이번 authorization/pending/started·직전 결과·관련 PR/CI만 확인한다. 전체 과거 대화·로그·작업 파일을 재독하지 않는다.

- [달력 증거](../evidence/calendar-reconciliation-2026-11-14.json)의 `inputs`, `date_results`, `public_sources` 중 `yuanta-2026-06-03`, `inherited_year_end_annotation`, `access_attempts`, `summary`. 기준 SHA256은 `ba221a99a32073e1923d734648558da431010e9d64826b7d21e1ce41eb50f815`다.
- [조사 문서](../research/data-contract-2026-11.md)의 ‘2026-11-14 미분류 평일의 시장 일정 대조’ 부분만 읽는다. 필요할 때 증거에 고정된 로컬 공개 원문을 확인한다.

소유 파일은 이 작업 파일, docs/STATE.md 해당 요약, 조사 문서의 새 부분, 위 새 결제 증거 네 파일이다. 부모는 생성 전에 이 파일과 STATE만 저장하며, 생성 이후 공유 파일/Git index 변경을 끝낸다.

기존 별도 변경 `?? .infisical.yaml`은 내용을 읽거나 변경·stage하지 않는다. 원본·기존 증거·예측을 보존한다. 주문·인증 브로커 호출·실계좌·유료 자료·Evolve·코드 구현·백테스트 실행·다른 이슈 재실행·추가 후속 세션 생성은 금지다. 주문 OFF·`backtest_ready=false`·기업행동8건 HOLD를 유지한다.
