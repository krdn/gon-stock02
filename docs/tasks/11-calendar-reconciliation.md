# Issue #11 — 미분류 평일의 시장 일정 대조

- 기준 이슈: https://github.com/krdn/gon-stock02/issues/11
- 사용자 범위/최초 전환 담당: [authorization](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6872736436), 현재 세션 `01a1d7da-b8cf-7031-ac86-0b8c5a680972`.
- 승인 목록과 마지막 단계: `11-calendar-reconciliation-20261114` 한 단계. 전환 ID는 `issue11-calendar-reconciliation-20261114`다. 실제 담당 ID·기준 SHA·인계 blob·별도 변경은 Issue #11의 최신 유효 pending/started 댓글이 기준이다.
- 직전 완료: [PR #23](https://github.com/krdn/gon-stock02/pull/23), main `7126555c936828e4e65bc28d309de0902c380901`, [최종 결과](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6872683756). PR/main의 테스트92개·wheel/sdist·구성 CI가 성공했다. 인계 문서 반영 후 기준은 pending 댓글에서 다시 확인한다.
- 세션 결정: 2026-11-14 05:53:43Z 기록의 최근 요청 입력221,710/컨텍스트 한도475,000토큰(약46.7%)을 확인했다. 완료 단계 경계에서 새 세션을 사용한다. 한도 도달·정확한 현재 잔여량·비용 절감의 측정은 아니다.

## 수행 범위와 완료 조건

보존 일봉에 없는 평일을 날짜별 공식 시장 일정과 대조한다. 원본의 `raw_checks.absent_weekdays_unclassified`는17일이다. 앞선 연말 공지로 확인한2025-12-31을 제외한 다음16일이 이번 대상이다.

`2025-12-25`, `2026-01-01`, `2026-02-16`, `2026-02-17`, `2026-02-18`, `2026-03-02`, `2026-05-01`, `2026-05-05`, `2026-05-25`, `2026-06-03`, `2026-07-17`, `2026-08-17`, `2026-09-24`, `2026-09-25`, `2026-10-05`, `2026-10-09`.

- KRX의 날짜별 시장 휴장/운영 공지와 필요한 공식 결제 자료를 확인한다. 일반 운영표·법정 공휴일·일봉 부재만으로 시장 휴장을 확정하지 않는다. 공식 증권사 공지는 그 출처와 조건을 구분한다.
- 16일 각각에 출처 URL·공표/확인 시각·식별자/해시·확인된 세션/휴장/결제 구분·판정과 남은 조건을 남긴다. 확인하지 못하거나 상충하면 null/HOLD로 둔다. 기존12-31 근거도 식별하고17일 원본 목록은 보존한다.
- 새 증거는 `docs/evidence/calendar-reconciliation-2026-11-14.json`이다. 과거 증거/원본을 덮어쓰지 않는다. 날짜 휴장 판정을 전체 봉 완전성·개별 종목 정지 없음·백테스트 적격으로 확장하지 않는다.
- 출처/해시·날짜 집합·원본 불변·JSON/상대 링크를 검사한다. 정상 브랜치/PR/CI·main 원격 확인·Issue #11 결과 인계를 마치고 이번 단계에서 종료한다. 코드 변경 없는 조사에 로컬 코드 테스트나 외부 리뷰를 자동 추가하지 않는다.

## 필수 읽기와 소유권

AGENTS.md → docs/WORKFLOW.md → docs/STATE.md → 이 파일 → [세션 절차](../operations/session-handoff.md) 순서로 읽는다. 이어서 아래 지정 부분과 Issue #11의 authorization/pending/started·최신 결과·관련 PR/CI만 확인한다. 전체 과거 대화·로그·작업 파일을 반복 읽지 않는다.

- [원본 판정](../evidence/data-contract-2026-11-13.json)의 `raw_checks.absent_weekdays_unclassified`와 입력 범위/해시.
- [배당 후속 증거](../evidence/dividend-followup-2026-11-14.json)의 `calendar_annotation`과 `public_sources` 중 `kis-yearend`.
- [조사 문서](../research/data-contract-2026-11.md)의 공개 계약 후속·거래정지 이력·남은 배당 근거 부분. KRX 직접 조회403 등 기존 실패와 미확정을 재사용한다. 같은 실패를 확인 성공으로 바꾸지 않는다.

새 세션은 자기 `CODEX_THREAD_ID`를 앱 `read_thread` 결과와 대조하고 최신 유효 started의 `next_thread_id`가 자신인지 확인한 뒤 수행한다. started가 늦으면 운영 절차의5초 간격3회 재조회 후 대기 종료한다. ID/authorization/HEAD/blob/별도 변경 불일치는 구현 전 중단한다. 기존 전환이 있으면 새 세션을 중복 생성하지 않는다.

- 소유 파일: 이 파일, `docs/research/data-contract-2026-11.md`의 새 조사 부분, 새 달력 증거, `docs/STATE.md`의 해당 작업 요약. 다른 파일·작업자의 변경을 되돌리지 않는다.
- 기존 별도 변경은 `?? .infisical.yaml`이다. 내용을 읽거나 변경·stage하지 않는다.
- 제외/중지: 주문·인증 브로커 호출·실계좌·유료 자료·Evolve·코드 구현·백테스트 실행·원본/예측 덮어쓰기·다른 이슈 재실행·후속 세션 자동 생성. 주문 OFF·`backtest_ready=false`·기업행동8건 HOLD를 유지한다.
- Issue #11은 첫 수용 기준만 완료이며 전체를 닫지 않는다. SK08-28 배당락일·주성 지급일 차이·계좌 입금/원천징수·공급자 조정·세션/정지·봉 확정/완전성·계좌 비용·장중 실증은 이번 달력 조사와 구분한다.
