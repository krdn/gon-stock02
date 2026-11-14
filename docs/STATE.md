# 현재 작업과 인수인계

- 현재 작업: [Issue #16](https://github.com/krdn/gon-stock02/issues/16) · [작업 기록](tasks/16-native-session-handoff.md). Evolve 없이 앱의 새 세션 자동 생성·인계를 적용한다. A→B→C 합성 실증 통과, 최종 원격 확인을 새 세션에 넘긴다. 최신 완료 상태는 이슈·연결 PR/CI가 기준이다.
- 새 세션 필수 읽기: AGENTS.md → docs/WORKFLOW.md → 이 파일 → 지정된 작업 파일과 그 필수 자료. 전체 과거 대화·작업 기록·로그를 반복 읽지 않는다.
- 자동 전환: [운영 절차](operations/session-handoff.md). 승인된 단계 검증·GitHub 인계 저장 후 AI가 다음 세션을 직접 생성한다. Issue #16이 끝나면 이번 자동화 작업은 종료한다.
- 공통 목표·결정: 4종목 단기 전략 모의 검증, [3단계 계획](plans/short-term-trading-2026-11.md). 주문 OFF, 백테스트 HOLD, 실주문·추가 유료 지출 범위 밖. `.infisical.yaml`은 기존 별도 변경으로 보존한다.
- 대기 작업: [Issue #11](https://github.com/krdn/gon-stock02/issues/11) 날짜별 공식 세션·정지·봉 확정·계좌 비용 계약. 재개 시 [후속 조사](research/data-contract-2026-11.md), [수신 운영](operations/minute-capture.md), [증거](evidence/minute-capture-2026-11-14.json), 최신 이슈/PR/CI만 먼저 확인한다. 장중 수신은 미검증이며 자동 재개하지 않는다.
- 대기 작업: [Issue #5](https://github.com/krdn/gon-stock02/issues/5) 실제 모의 접수·체결·취소. 재개 시 [주문 운영](operations/paper-order-ledger.md)과 [리뷰](reviews/paper-order-ledger-2026-11-13.md)를 읽고 공식 개장일·시간을 재확인한다. 기존 주문 0건이며 자동 재개하지 않는다.
- 이전 Evolve 경로: [Issue #14](https://github.com/krdn/gon-stock02/issues/14) · [기록](tasks/14-evolve-runtime.md). Linux 차단 기록을 보존하며 현재 사용자 결정에 따라 사용하지 않는다.
- 이전 전체 인계: [보존 문서](tasks/project-baseline-2026-11-14.md). 불일치나 추가 근거가 필요할 때만 읽는다. 원래 내용은 보존했고 상대 링크만 새 위치에 맞췄다.
