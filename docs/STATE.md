# 현재 작업과 인수인계

- 현재 작업: [Issue #11](https://github.com/krdn/gon-stock02/issues/11) · [결제 규정 과거 버전/예외 대조](tasks/11-settlement-rule-versions.md)의 공개 조사를 마쳤다. [새 증거](evidence/settlement-rule-versions-2026-11-14.json)에 KRX 규정26개·한국투자 공개약관2개를 기록했다. 휴장일 일수 제외와 청산업무/비상결제일 변경/특정 당일결제 예외를 구분했고2405의 시행일 상충·2433의 조건부 시행 경계는HOLD다. 날짜별 직접결제근거 신규0일·15일 null/HOLD·모의계좌 적용 미확정이다. 기존19파일·원본17일·06-03/12-31 주석은 보존했다. PR/필수CI·main/변경blob 대조 결과는 Issue11 최종 인계에서 확인한다. SK08-28·주성 지급일 차이·실입금·전체조정계약·기업행동8건HOLD는 남는다.
- 새 세션 필수 읽기: AGENTS.md → docs/WORKFLOW.md → 이 파일 → 지정된 작업 파일과 그 필수 자료. 전체 과거 대화·작업 기록·로그를 반복 읽지 않는다.
- 자동 전환: [운영 절차](operations/session-handoff.md) · [이번 승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873439384) · [tab_verified=true started](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873522719). 담당 `01a1d8db-9cee-75d1-88f2-b9e11d0785e1`은 실제 Herdr새탭/t63·동일ID·기준HEAD/blob을 대조한 뒤 재개했다. 전환ID=`issue11-settlement-rule-versions-20261114`, 승인된 마지막 한 단계에서 결과를 인계하고 종료한다. 추가세션·Issue16 재실행·자동 재개는 금지다.
- 공통 목표·결정: 4종목 단기 전략 모의 검증, [3단계 계획](plans/short-term-trading-2026-11.md). 주문 OFF, 백테스트 HOLD, 실주문·추가 유료 지출 범위 밖. `.infisical.yaml`은 기존 별도 변경으로 보존한다.
- 남은 계약 검증: 과거 날짜별 세션·종목별 정지·기업행동·봉 확정·같은 계좌 비용·장중 실제 수신. 첫 수용 기준 외 네 기준은 미완료다. 이번 조사에서는 공개 자료만 조회했고 인증 브로커 호출·주문은 0건이다. 재개 시 [단계 기록](tasks/11-data-contract-next.md), [수신 운영](operations/minute-capture.md), 최신 Issue #11/PR/CI를 확인하며 자동 재개하지 않는다.
- 대기 작업: [Issue #5](https://github.com/krdn/gon-stock02/issues/5) 실제 모의 접수·체결·취소. 재개 시 [주문 운영](operations/paper-order-ledger.md)과 [리뷰](reviews/paper-order-ledger-2026-11-13.md)를 읽고 공식 개장일·시간을 재확인한다. 기존 주문 0건이며 자동 재개하지 않는다.
- 이전 Evolve 경로: [Issue #14](https://github.com/krdn/gon-stock02/issues/14) · [기록](tasks/14-evolve-runtime.md). Linux 차단 기록을 보존하며 현재 사용자 결정에 따라 사용하지 않는다.
- 이전 전체 인계: [보존 문서](tasks/project-baseline-2026-11-14.md). 불일치나 추가 근거가 필요할 때만 읽는다. 원래 내용은 보존했고 상대 링크만 새 위치에 맞췄다.
