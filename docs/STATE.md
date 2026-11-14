# 현재 작업과 인수인계

- 현재 작업: [Issue #11](https://github.com/krdn/gon-stock02/issues/11) · [두 규정 시행일 원문 대조](tasks/11-settlement-effective-boundaries.md)의 공개 조사를 마쳤다. [새 증거](evidence/settlement-effective-boundaries-2026-11-14.json)는 KRX HWP4개를 포함한 신규 본문12개·재사용 HTML2개다. 2405 개정문01-29/전문01-28 상충,2433의04-28 공포 기록·전재 부칙 확인/원공포안 미확보를 구분했다. 두 확정 경계는null/HOLD·전체15일 결제HOLD·모의계좌 적용0일이다. 기존20파일·원본17일·06-03/12-31 주석은 보존했다. PR/필수CI·main/변경4blob의 전달 결과는 Issue11 최종 댓글이 기준이다.
- 새 세션 필수 읽기: AGENTS.md → docs/WORKFLOW.md → 이 파일 → 지정된 작업 파일과 그 필수 자료. 전체 과거 대화·작업 기록·로그를 반복 읽지 않는다.
- 자동 전환: [운영 절차](operations/session-handoff.md) · [이번 승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6874555756) · [tab_verified=true started](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6874642086). 담당 `01a1d932-726e-72a2-beef-be572df35510`은 실제 새 Herdr탭/t64·동일ID·기준HEAD/blob/별도변경을 대조한 뒤 재개했다. 전환ID=`issue11-settlement-effective-boundaries-20261114`, 승인된 마지막 한 단계의 결과 인계 후 종료한다. 추가세션·다른 이슈 재실행·자동 재개는 금지다.
- 공통 목표·결정: 4종목 단기 전략 모의 검증, [3단계 계획](plans/short-term-trading-2026-11.md). 주문 OFF, 백테스트 HOLD, 실주문·추가 유료 지출 범위 밖. `.infisical.yaml`은 기존 별도 변경으로 보존한다.
- 남은 계약 검증: 과거 날짜별 세션·종목별 정지·기업행동·봉 확정·같은 계좌 비용·장중 실제 수신. 첫 수용 기준 외 네 기준은 미완료다. 이번 조사에서는 공개 자료만 조회했고 인증 브로커 호출·주문은 0건이다. 재개 시 [단계 기록](tasks/11-data-contract-next.md), [수신 운영](operations/minute-capture.md), 최신 Issue #11/PR/CI를 확인하며 자동 재개하지 않는다.
- 대기 작업: [Issue #5](https://github.com/krdn/gon-stock02/issues/5) 실제 모의 접수·체결·취소. 재개 시 [주문 운영](operations/paper-order-ledger.md)과 [리뷰](reviews/paper-order-ledger-2026-11-13.md)를 읽고 공식 개장일·시간을 재확인한다. 기존 주문 0건이며 자동 재개하지 않는다.
- 이전 Evolve 경로: [Issue #14](https://github.com/krdn/gon-stock02/issues/14) · [기록](tasks/14-evolve-runtime.md). Linux 차단 기록을 보존하며 현재 사용자 결정에 따라 사용하지 않는다.
- 이전 전체 인계: [보존 문서](tasks/project-baseline-2026-11-14.md). 불일치나 추가 근거가 필요할 때만 읽는다. 원래 내용은 보존했고 상대 링크만 새 위치에 맞췄다.
