# 현재 작업과 인수인계

- 현재 작업: [Issue #11](https://github.com/krdn/gon-stock02/issues/11) · 새 세션의 [두 규정 시행일 원문 대조](tasks/11-settlement-effective-boundaries.md)를 준비한다. [직전 결과](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873752270)는 PR29/main8a93067에 반영됐고 PR/main각92테스트·wheel/sdist·구성CI 및 main/4blob 원격일치를 확인했다. [규정 증거](evidence/settlement-rule-versions-2026-11-14.json)는 KRX규정26·KIS약관2개이며2405시행일상충·2433조건부시행 경계는HOLD다. 이 두 쟁점/기존7일 영향만 새 원문으로 대조한다. 전체15일 결제HOLD·모의계좌적용미확정·기업행동8건HOLD는 유지한다. 원본17일·06-03/12-31 주석·기존20파일을 보존한다.
- 새 세션 필수 읽기: AGENTS.md → docs/WORKFLOW.md → 이 파일 → 지정된 작업 파일과 그 필수 자료. 전체 과거 대화·작업 기록·로그를 반복 읽지 않는다.
- 자동 전환: [운영 절차](operations/session-handoff.md) · [이번 사용자 지시/승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6874555756). 최근입력318,684/컨텍스트475,000=67.1%와 완료 경계에 따라 새 세션으로 인계한다. 허용목록/마지막단계=`11-settlement-effective-boundaries-20261114`, 전환ID=`issue11-settlement-effective-boundaries-20261114`, 최초담당=`01a1d8db-9cee-75d1-88f2-b9e11d0785e1`. 실제 새 Herdr탭·동일세션을 확인한tab_verified=true started 전에는 조사/편집하지 않는다. 이후 추가세션·Issue16재실행 금지다.
- 공통 목표·결정: 4종목 단기 전략 모의 검증, [3단계 계획](plans/short-term-trading-2026-11.md). 주문 OFF, 백테스트 HOLD, 실주문·추가 유료 지출 범위 밖. `.infisical.yaml`은 기존 별도 변경으로 보존한다.
- 남은 계약 검증: 과거 날짜별 세션·종목별 정지·기업행동·봉 확정·같은 계좌 비용·장중 실제 수신. 첫 수용 기준 외 네 기준은 미완료다. 이번 조사에서는 공개 자료만 조회했고 인증 브로커 호출·주문은 0건이다. 재개 시 [단계 기록](tasks/11-data-contract-next.md), [수신 운영](operations/minute-capture.md), 최신 Issue #11/PR/CI를 확인하며 자동 재개하지 않는다.
- 대기 작업: [Issue #5](https://github.com/krdn/gon-stock02/issues/5) 실제 모의 접수·체결·취소. 재개 시 [주문 운영](operations/paper-order-ledger.md)과 [리뷰](reviews/paper-order-ledger-2026-11-13.md)를 읽고 공식 개장일·시간을 재확인한다. 기존 주문 0건이며 자동 재개하지 않는다.
- 이전 Evolve 경로: [Issue #14](https://github.com/krdn/gon-stock02/issues/14) · [기록](tasks/14-evolve-runtime.md). Linux 차단 기록을 보존하며 현재 사용자 결정에 따라 사용하지 않는다.
- 이전 전체 인계: [보존 문서](tasks/project-baseline-2026-11-14.md). 불일치나 추가 근거가 필요할 때만 읽는다. 원래 내용은 보존했고 상대 링크만 새 위치에 맞췄다.
