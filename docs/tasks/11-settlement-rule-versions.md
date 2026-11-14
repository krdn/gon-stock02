# Issue #11 — 결제 규정의 과거 적용 버전과 예외 대조

- [현재 사용자 지시/한 단계 승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873439384) · [직전 결과](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873377124) · [Issue #11](https://github.com/krdn/gon-stock02/issues/11).
- 허용 목록/마지막 단계: `11-settlement-rule-versions-20261114` 하나. 전환 ID는 `issue11-settlement-rule-versions-20261114`, 최초 전환 담당은 `01a1d8c5-8628-7101-87cb-daabc2312d13`다. 실제 담당·기준SHA/blob·탭은 최신 유효 pending/started에서 대조한다.
- 직전 PR #27은 main `5e78184907d44b5db0512fa8ce45132fef2634aa`에 병합됐다. PR/main 각각92테스트·wheel/sdist·구성CI와 main/변경4blob 원격 일치를 확인했다. 현재 작업 문서 반영 후 새 기준을 pending에 고정한다.
- 세션 판단: 2026-11-14T06:54:33.225Z의 최근 입력241,718/모델 컨텍스트475,000(50.9%), 최근 출력737토큰. 정확한 실시간 잔여량이 아니다. 누적total9,124,272는 반복입력/캐시를 포함한 집계다. 완료 단계 경계에서 새 세션을 선택했으며 주간 사용97%와 혼동하지 않는다.

## 이번 실행 결과

- 담당 `01a1d8db-9cee-75d1-88f2-b9e11d0785e1`은 [started](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873522719)의 Herdr탭 `tb9083b67219f97e5add45c268003d8329`/t63·자기ID/read_thread·기준HEAD/blob·별도변경을 대조했다. 첫 대기 종료 후 부모의 같은 세션 재개 지시를 받고 조사했다.
- [규정 증거](../evidence/settlement-rule-versions-2026-11-14.json) · [조사 설명](../research/data-contract-2026-11.md#2026-11-14-결제-규정의-버전과-예외): 새 KRX 법무포털에서 시장규정/세칙21개·청산결제규정/세칙5개, 한국투자 공개약관2개를 확보했다. 일반안내·금융위 원문3개는 재사용했다.
- 보통거래의 휴장일 일수 제외와 비상 결제일 변경, 휴장일 청산업무 허용 및 특정 당일결제 예외를 구분했다. 유가증권2405의 표제/부칙 시행일 상충·2433의 시행령 공포 조건은null/HOLD이며 대상7일에 연결된다. 공개약관은 현재 모의계좌 적용을 입증하지 않는다.
- 날짜별 직접 결제 근거 신규0일·대상15일 null/HOLD다. 대상 사이 모든 버전/연혁 완전성·최초 공표/정정 이력·날짜별 예외 발동·계좌 적용은 미검증이다. 코드 없는 조사이므로 로컬 코드테스트·외부리뷰를 자동 추가하지 않는다. JSON·출처/원문해시·기존19파일 불변·상대링크·정상PR/필수CI·main/변경blob 대조 결과는 Issue11 최종 인계에 남긴다.
- 남은 입력은 날짜별 KRX/증권사 직접 결제 자료, 상충/조건부 시행 원문, 해당 거래의 예외·모의계좌 적용이다. 승인된 마지막 단계에서 종료하며 자동 재개·추가 세션은 없다. Issue11OPEN·기업행동8건HOLD·주문OFF·`backtest_ready=false`를 유지한다.

## 시작 조건: Herdr 실제 새 탭

부모가 create_thread를 한 번 호출하고, 새 Herdr탭 ‘결제 규정 적용 대조 (#11)’에 **동일 세션ID를 초기 작업 프롬프트 없이 codex resume로 표시**한다. `herdr-app ls/status`·터미널 foreground resumeID/cwd·실제 앱 렌더링을 확인한 뒤 `tab_verified=true`, `next_thread_id`, `herdr_space_id`, `herdr_tab_id`, `herdr_terminal_id`가 있는 started를 게시한다. 생성 결과 불명확 시 중복 생성하지 않는다.

자식은 자기 CODEX_THREAD_ID·앱read_thread·started의ID/탭·기준HEAD/blob·기존 별도 변경을 대조한 후에만 공개 조사/편집한다. 그 전에는 지정 인계 읽기만 허용한다. started가 없으면5초 간격 최대3회 재조회 후 대기 종료하고, 부모의 같은 세션 재개 메시지를 기다린다. 새 세션을 다시 만들지 않는다. 부모는 생성 후 공유파일/Git index 변경을 끝낸다.

## 조사 범위와 완료 조건

직전 증거의 미확정15일은 `2025-12-25`, `2026-01-01`, `2026-02-16`, `2026-02-17`, `2026-02-18`, `2026-03-02`, `2026-05-01`, `2026-05-05`, `2026-05-25`, `2026-07-17`, `2026-08-17`, `2026-09-24`, `2026-09-25`, `2026-10-05`, `2026-10-09`다.

- KRX 일반 안내의 근거 업무규정·시행세칙·개정/시행일을 새 공식 식별자로 확인한다. 대상15일의 적용 구간과 휴장일 결제 제외/예외를 대조한다. 한국투자 공개 국내주식 규정이 연결될 때만 계좌 적용의 남은 조건을 기록한다. 인증·계좌 조회는 하지 않는다.
- 일반 안내·원규정/버전·날짜별 직접 출력·규정에 의한 계산·현재 계좌 적용을 구분한다. URL·공표/시행/확인시각·식별자/해시·날짜별 판정/남은조건을 새 `docs/evidence/settlement-rule-versions-2026-11-14.json`에 기록한다. 미확보·상충은null/HOLD다. 현재 일반 안내를 과거에 소급하거나 공휴일/일봉부재만으로 결제일을 확정하지 않는다.
- 이미 확보한 KRX 일반 안내와 금융위 설/추석 원문·해시는 재사용한다. 이전 KRX 날짜행/빈본문·PDF 미확보·접근거부, KIND0건, 한국투자 목록 오류이동문/삼성410·유안타 제목검색66건을 같은 조건으로 반복하지 않는다. 새 원규정·개정 식별자/공식 출력이 있을 때 새로 조회한다. 검색 결과를 공지 부재로 판단하지 않는다.
- 대상집합·출처/해시·기존 원본/증거 불변·JSON/상대링크를 검사한다. 정상브랜치/PR/필수CI·main SHA/변경blob 원격 대조·Issue11 결과인계 후 이번 단계에서 종료한다. 코드 없는 조사에 로컬 코드테스트·외부리뷰를 자동 추가하지 않는다.
- 실제 계좌차감·배당권리일·원천징수·수정주가·봉완전성·정지없음·백테스트적격으로 확대하지 않는다. Issue11OPEN·첫기준만완료·기업행동8건HOLD·주문OFF·backtest_ready=false를 유지한다.

## 필수 읽기와 소유권

AGENTS.md → docs/WORKFLOW.md → docs/STATE.md → 이 파일 → [세션 절차](../operations/session-handoff.md). 이어서 아래 지정 부분과 Issue11의 이번 authorization/pending/started·직전 결과·관련 PR/CI만 읽는다. 전체 과거 대화/로그/작업 파일을 다시 읽지 않는다.

- [결제 증거](../evidence/settlement-reconciliation-2026-11-14.json)의 `inputs`, `public_sources`, `date_results`, `inherited_settlement_annotations`, `prior_failures_reused`, `summary`만 우선 확인한다. `access_attempts`는 새 경로 중복 여부 확인이 필요할 때 읽는다. 이 파일의 SHA256은 부모가 pending에 고정한다.
- [조사 문서](../research/data-contract-2026-11.md)의 ‘2026-11-14 잔여15일의 결제 근거 대조’만 읽는다. 증거에 고정된 로컬 공개 원문은 필요할 때 읽는다. 이전 증거는 해시·지정 연결 부분만 확인한다.

자식 소유는 이 파일·STATE 해당요약·조사 문서 새부분·위 새 규정 증거 네파일이다. 부모는 생성 전에 이 파일과 STATE만 저장한다. 기존 원본/증거/예측은 보존한다. `?? .infisical.yaml`은 기존 별도 변경이며 내용 미열람·미수정·미stage를 지킨다. 주문·인증브로커·실계좌·유료자료·Evolve·코드구현·백테스트·다른이슈재실행·추가후속세션은 금지다.
