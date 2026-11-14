# 현재 작업과 인수인계

- 현재 작업: [Issue #11](https://github.com/krdn/gon-stock02/issues/11) · [2405/2433 개정 범위·결제 영향 대조](tasks/11-settlement-amendment-scope.md)의 조사 결과를 정리했다. [새 증거](evidence/settlement-amendment-scope-2026-11-14.json)는공식본문11개·업무규정177조문씩의두비교에서변경이각제18조의2/제26조뿐임을기록한다. 비교한휴장·결제일산정조문에는실질적의존조건이아니라는제한적추론이며날짜별결제승인은아니다. 기존canonical경계null·관련7일/나머지8일의전체15일결제HOLD·23파일·원본17일/06-03·12-31주석을보존한다. PR/CI/main/4blob·결과인계의최종상태는Issue11의이번결과댓글이기준이다.
- 새 세션 필수 읽기: AGENTS.md → docs/WORKFLOW.md → 이 파일 → 지정된 작업 파일과 그 필수 자료. 전체 과거 대화·작업 기록·로그를 반복 읽지 않는다.
- 세션 판단: [이번 승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6876202040)에따라부모가새세션/탭을각1회생성했다. [전환 절차](operations/session-handoff.md)와 [started](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6876271124)의자기ID`01a1d9b6-00a4-79d0-98f7-f14d5e778d2b`·HEAD/2blob·새탭‘개정 범위·결제 영향 (#11)’/`t67`·동일ID/cwd·보존렌더링/해시를대조한뒤조사했다. 전환ID=`issue11-settlement-amendment-scope-20261114`, 마지막허용단계=`11-settlement-amendment-scope-20261114` 하나다. 이후추가세션·다른이슈재실행은금지다.
- 공통 목표·결정: 4종목 단기 전략 모의 검증, [3단계 계획](plans/short-term-trading-2026-11.md). 주문 OFF, 백테스트 HOLD, 실주문·추가 유료 지출 범위 밖. `.infisical.yaml`은 기존 별도 변경으로 보존한다.
- 남은 계약 검증: 과거 날짜별 세션·종목별 정지·기업행동·봉 확정·같은 계좌 비용·장중 실제 수신. 첫 수용 기준 외 네 기준은 미완료다. 이번 조사에서는 공개 자료만 조회했고 인증 브로커 호출·주문은 0건이다. 재개 시 [단계 기록](tasks/11-data-contract-next.md), [수신 운영](operations/minute-capture.md), 최신 Issue #11/PR/CI를 확인하며 자동 재개하지 않는다.
- 대기 작업: [Issue #5](https://github.com/krdn/gon-stock02/issues/5) 실제 모의 접수·체결·취소. 재개 시 [주문 운영](operations/paper-order-ledger.md)과 [리뷰](reviews/paper-order-ledger-2026-11-13.md)를 읽고 공식 개장일·시간을 재확인한다. 기존 주문 0건이며 자동 재개하지 않는다.
- 이전 Evolve 경로: [Issue #14](https://github.com/krdn/gon-stock02/issues/14) · [기록](tasks/14-evolve-runtime.md). Linux 차단 기록을 보존하며 현재 사용자 결정에 따라 사용하지 않는다.
- 이전 전체 인계: [보존 문서](tasks/project-baseline-2026-11-14.md). 불일치나 추가 근거가 필요할 때만 읽는다. 원래 내용은 보존했고 상대 링크만 새 위치에 맞췄다.
