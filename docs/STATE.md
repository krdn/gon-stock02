# 현재 작업과 인수인계

- 현재 기준: [Issue #11](https://github.com/krdn/gon-stock02/issues/11) · [필수 검증과 조건부 조사](tasks/11-validation-routing.md). 사용자의 2026-11-14 판단 위임에 따라 반복 공개 조사를 필수 실증과 분리했다. 이번 작업은 분리·기록이며 새 실증을 시작하지 않는다.
- 필수 대기: [#37 데이터 수신·사용 가능 구간](https://github.com/krdn/gon-stock02/issues/37), [#38 장중 모의 체결·계좌 비용](https://github.com/krdn/gon-stock02/issues/38). 공식 거래시간과 각 이슈의 실행 조건이 갖춰지면 해당 작업만 진행한다. 데이터 수신 도구의 한 번 성공은 전체 세션 검증이 아니다.
- 조건부 대기: [#39 과거 기업행동·결제·규정 근거](https://github.com/krdn/gon-stock02/issues/39). 사용할 입력에 필요하고 판정에 영향을 주며 새 확인 수단이 있을 때만 필요한 항목을 재개한다. 조건 없이 동일 검색·추가 조사·새 세션을 반복하지 않는다.
- 완료 기준: #11의 첫 기준만 완료, 나머지 네 기준은 미완료다. 기준 2·3은 #37, 기준 4는 #38, 기준 5는 #11에서 검토한다. #39를 무조건적인 선행 조건으로 두지 않으며 해당 자료를 사용할 때 필요한 검증은 유지한다.
- 최근 근거: [PR #36](https://github.com/krdn/gon-stock02/pull/36) · [결과](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6876422621) · [증거](evidence/settlement-amendment-scope-2026-11-14.json). 2405/2433 개정은 비교한 일반 주식의 휴장·결제일 산정 조문에 실질적 의존조건이 아니라는 제한적 추론이다. 날짜별 실제 결제·예외·계좌 적용은 미확정이다.
- 재개 필수 읽기: AGENTS.md → docs/WORKFLOW.md → 이 파일 → [분리표](tasks/11-validation-routing.md) → 선택한 이슈/운영 문서와 관련 PR/CI. 전체 과거 대화·조사·로그는 반복 읽지 않는다. 이전 단계의 다음 행동은 현재 분리표의 시작 조건을 적용한다.
- 공통 목표·보존: 4종목 단기 전략 모의 검증, [3단계 계획](plans/short-term-trading-2026-11.md). 주문 OFF·`backtest_ready=false`, 기업행동 8건·결제일 15일 HOLD·시행 경계 null·기존 원본/예측/증거를 유지한다. `.infisical.yaml`은 별도 변경으로 보존한다. 실계좌·추가 유료 지출·권한 확대는 범위 밖이다.
- 구현 기록: [#5](https://github.com/krdn/gon-stock02/issues/5)의 주문 장부 구현은 완료 상태를 유지한다. 남은 실제 접수·체결·취소·비용 검증은 #38에서 추적한다. 재개 시 [주문 운영](operations/paper-order-ledger.md)과 [리뷰](reviews/paper-order-ledger-2026-11-13.md)를 확인한다.
- 세션 상태: 직전 개정 범위 조사와 인계는 종료했다. 이번 분리에서 새 세션·탭·예약 실행은 만들지 않는다. 향후 승인된 단계 전환에만 [전환 절차](operations/session-handoff.md)를 적용한다.
- 이전 기록: [Evolve 제한 #14](https://github.com/krdn/gon-stock02/issues/14)는 보존하며 Evolve는 사용하지 않는다. [이전 전체 인계](tasks/project-baseline-2026-11-14.md)는 불일치나 추가 근거가 필요할 때만 읽는다.
