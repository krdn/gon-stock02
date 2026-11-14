# Issue #11 — 공개 계약 조사 재개

- 작업/기준 이슈: https://github.com/krdn/gon-stock02/issues/11
- 사용자 범위·단계·최초 담당: [authorization](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6870021801). 승인된 단계는 `11-contract-research-20261114` 하나이며 이 단계에서 종료한다.
- 전환 ID: `issue11-contract-research-20261114`. dispatch·기준 HEAD·인계 blob·기존 별도 변경·자기 세션 ID는 Issue #11의 최신 유효 pending/started 댓글에서 대조한다.
- 개발 기준: main `8acbaa1205808feb9ce5a6dc62adbda6a6bc567f`, 수신 보존 [PR #13](https://github.com/krdn/gon-stock02/pull/13)과 인계 규칙 PR #17. 이번 인계 저장 후의 기준 SHA/blob은 pending 댓글이 기준이다.
- 완료: 과거 자료 사용 조건과 KRX 모의 당일 분봉 수신 보존 구현은 전달됐다. 해당 구현의 테스트·빌드·리뷰·PR/main CI는 Issue #11과 증거에서 확인한다. 장중 실증·전체 세션·봉 확정·계좌 비용은 미완료다.
- 다음 작업: 공식 날짜별 세션·정지 자료, 봉 시각/확정 규칙, 현재 계좌 비용 규정의 확인 가능한 공식 근거를 조사한다. 주말에는 공개 자료·오프라인 증거를 사용하며 추정으로 통과시키지 않는다.
- 소유 범위: 이 작업 파일, `docs/research/data-contract-2026-11.md`, 새 `docs/evidence/data-contract-followup-2026-11-14.json`, `docs/STATE.md`의 해당 작업 요약. 다른 작업자의 변경을 되돌리지 않는다. 코드 수정이 필요하면 근거와 후속 작업으로 남긴다.
- 완료 조건: 출처·확인 시각·판정과 미확정·다음 실증 조건을 기록하고 정상 브랜치/PR/CI 경로로 전달한다. 원래 Issue #11의 수용 기준은 충족한 항목만 갱신한다. 이 조사 단계 완료로 이슈 전체를 종료하지 않는다.
- 제외/중지: 주문·인증 브로커 호출·실계좌·유료 자료·원본/예측 덮어쓰기·Evolve·다른 이슈 재실행·후속 세션 자동 생성. 주문 OFF·백테스트 HOLD 유지. 신원/authorization/HEAD/blob/별도 변경 불일치는 구현 전에 멈춘다.
- 필수 읽기: AGENTS → docs/WORKFLOW.md → docs/STATE.md → 이 파일 → [세션 절차](../operations/session-handoff.md), [후속 조사](../research/data-contract-2026-11.md), [수신 운영](../operations/minute-capture.md), [수신 증거](../evidence/minute-capture-2026-11-14.json), Issue #11의 최신 본문·댓글·관련 PR/CI. 전체 과거 대화·작업 로그는 다시 읽지 않는다.

## 조사 결과와 종료 지점

- 담당 세션 `01a1d7da-b8cf-7031-ac86-0b8c5a680972`는 [started](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6870100966), main `8417c5f27506a9ee307d3a44bf0f5293aa26c26b`, 인계 blob `ff1aa37faa2fd002af30421a84396d0930418a3d`, 기존 `?? .infisical.yaml`을 대조했다. 인계 PR #18·main CI 성공도 확인했다.
- 공개 조사 결과는 [후속 조사](../research/data-contract-2026-11.md#2026-11-14-공개-계약-후속-조사)와 [새 증거](../evidence/data-contract-followup-2026-11-14.json)에 있다. KRX 일반 운영표·11-19 특별개장 공지·정지 조회 화면·분봉 규격·공개 비용표를 확인했다.
- 과거 날짜별 세션·종목별 정지 결과·기업행동·봉 확정·같은 계좌 비용·실제 수신은 미완료다. KRX 정지 직접 조회는 403, 장후 시간은 두 증권사 공지 간 불일치다. 이 실패를 정지 없음이나 세션 완료로 바꾸지 않았다.
- 이번 문서 변경은 정상 브랜치/PR/CI로 전달하고, 최종 SHA·검사·병합 상태는 Issue #11의 단계 결과 댓글에 남긴다. Issue #11 전체는 닫지 않는다. 주문/인증 브로커 호출 0건, 주문 OFF·백테스트 HOLD다.
- 다음 행동은 조사 문서의 실증 조건을 충족하는 별도 작업이다. 이번 승인 단계는 여기서 끝나며 후속 세션을 생성하지 않는다.

## 추가 승인: 거래정지 이력 대조

- 사용자 추가 지시로 `11-halt-reconciliation-20261114` 한 단계를 [승인 기록](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6870991517)에 고정했다. 관련 근거를 가진 현재 세션에서 계속했고 새 Codex 세션은 만들지 않았다. 이전 단계의 종료 기록은 보존한다.
- 범위는 4종목×11-09~13의 공식 정지 자료와 KIND 공시 대조다. [결과](../research/data-contract-2026-11.md#2026-11-14-거래정지-이력-대조) · [증거](../evidence/halt-reconciliation-2026-11-14.json). KRX 브라우저 조회도 403으로 실패했다. KIND 공시 17건의 전체 결과 페이지를 읽었고 거래정지/재개 제목은 없었으나, 과거 정지 없음으로 판정하지 않았다.
- 20구간은 정지 여부 null·HOLD다. 날짜별 공식 정지 출력과 필요한 정지·재개 시각 대조가 남는다. SK하이닉스 주식소각 공시 제목은 기업행동 후속 단서이며 검증 완료가 아니다.
- 변경은 같은 작업 파일·조사 문서·새 정지 증거·STATE 요약 네 파일에 한정한다. 기존 `.infisical.yaml`·원본을 보존한다. PR/CI·최종 SHA와 부분 확인/차단 상태는 Issue #11의 결과 댓글에 남긴다. 주문/인증 브로커 호출 0건, 주문 OFF·백테스트 HOLD를 유지하며 이 단계에서 종료한다.
