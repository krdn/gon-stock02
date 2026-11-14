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
