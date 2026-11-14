# 현재 작업과 인수인계

- 현재 작업: [Issue #11](https://github.com/krdn/gon-stock02/issues/11) · 새 세션의 [잔여15일 결제 근거 대조](tasks/11-settlement-reconciliation.md)를 준비한다. [직전 결과](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6872994237)는 PR #25/main010a89a에 반영됐고 PR/main 각92테스트·빌드·구성 CI를 통과했다. [달력 증거](evidence/calendar-reconciliation-2026-11-14.json)는 증권사 휴장16일·결제1일(06-03), KRX 직접확인0일·16일 HOLD다. 원본17일·기존12-31 주석을 보존했다. 다음 세션/탭 ID와 기준 SHA/blob은 이번 전환 댓글이 기준이다. SK08-28·주성 지급일 차이·실입금·전체 조정 계약은 미완료이며 기업행동8건 모두 HOLD다.
- 새 세션 필수 읽기: AGENTS.md → docs/WORKFLOW.md → 이 파일 → 지정된 작업 파일과 그 필수 자료. 전체 과거 대화·작업 기록·로그를 반복 읽지 않는다.
- 자동 전환: [운영 절차](operations/session-handoff.md) · [이번 사용자 지시/승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873164444). 허용 목록/마지막 단계는 `11-settlement-reconciliation-20261114` 하나, 전환 ID는 `issue11-settlement-reconciliation-20261114`다. 최근 입력259,465/컨텍스트475,000(54.6%)과 완료 경계에 따라 새 세션으로 인계한다. Herdr 실제 새 탭·연결 세션을 확인한 `tab_verified=true` started 전에는 조사를 시작하지 않는다. 이 단계 이후 추가 세션은 생성하지 않는다. Issue #16은 재실행하지 않는다.
- 공통 목표·결정: 4종목 단기 전략 모의 검증, [3단계 계획](plans/short-term-trading-2026-11.md). 주문 OFF, 백테스트 HOLD, 실주문·추가 유료 지출 범위 밖. `.infisical.yaml`은 기존 별도 변경으로 보존한다.
- 남은 계약 검증: 과거 날짜별 세션·종목별 정지·기업행동·봉 확정·같은 계좌 비용·장중 실제 수신. 첫 수용 기준 외 네 기준은 미완료다. 이번 조사에서는 공개 자료만 조회했고 인증 브로커 호출·주문은 0건이다. 재개 시 [단계 기록](tasks/11-data-contract-next.md), [수신 운영](operations/minute-capture.md), 최신 Issue #11/PR/CI를 확인하며 자동 재개하지 않는다.
- 대기 작업: [Issue #5](https://github.com/krdn/gon-stock02/issues/5) 실제 모의 접수·체결·취소. 재개 시 [주문 운영](operations/paper-order-ledger.md)과 [리뷰](reviews/paper-order-ledger-2026-11-13.md)를 읽고 공식 개장일·시간을 재확인한다. 기존 주문 0건이며 자동 재개하지 않는다.
- 이전 Evolve 경로: [Issue #14](https://github.com/krdn/gon-stock02/issues/14) · [기록](tasks/14-evolve-runtime.md). Linux 차단 기록을 보존하며 현재 사용자 결정에 따라 사용하지 않는다.
- 이전 전체 인계: [보존 문서](tasks/project-baseline-2026-11-14.md). 불일치나 추가 근거가 필요할 때만 읽는다. 원래 내용은 보존했고 상대 링크만 새 위치에 맞췄다.
