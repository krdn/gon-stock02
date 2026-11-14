# Issue #11 — 2433의 원공포문과 예고안 연결

- [이번 사용자 지시/한 단계 승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6874896483) · [직전 결과](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6874849527) · [Issue #11](https://github.com/krdn/gon-stock02/issues/11).
- 허용 목록/마지막 단계는 `11-promulgation-provenance-20261114` 하나다. 전환ID=`issue11-promulgation-provenance-20261114`, 최초 전환담당=`01a1d932-726e-72a2-beef-be572df35510`. 실제 담당·기준SHA/blob·탭은 최신 유효 pending/started에서 대조한다.
- 선행 PR31/main `1b02b35063de3f44972f6edfa4a51bc162d4aaf2`의 PR/main각92테스트·wheel/sdist·구성CI·원격SHA/4blob·인계본문 일치를 확인했다. 2405 개정문01-29/전문01-28 상충과2433의 원공포안 미확보로 두 확정 경계는null/HOLD, 대상15일 결제HOLD다.
- 세션 판단: 2026-11-14T08:58:30.967Z 최근입력342492/모델창475000=72.1%, 최근출력916. 정확한 실시간 점유/잔여가 아니다. 누적16042117은 반복입력/캐시 포함이며 현재 점유/비용이 아니다. 주간사용99%는 별도 지표이며 새 세션이 이를 초기화하지 않는다.

## 조사 전 새 탭 확인

부모는 인계PR/필수CI·mainSHA/문서2blob을 확인하고 pending을 게시한다. create_thread1회·기본모델상속·fork없음으로 새 세션을 만든다. Herdr 새탭 **‘원공포문 연결 대조 (#11)’**에 folder=`/home/gon/llm-projects/gon-stock02`를 명시하고 같은ID를 초기작업프롬프트 없이 기본 공유서버 `codex resume`로 표시한다. 기존space 표시folder는 다른 프로젝트이므로 상속하지 않는다. hc의 독립 에이전트용 `--no-daemon` 안내를 이 동일ID 뷰어에 적용하지 않으며, 이미 확인한 잠금 실패를 반복하지 않는다.

부모는 ls/status·foreground resumeID/cwd·실제 앱렌더링을 대조한 `tab_verified=true`, `next_thread_id`, `herdr_space_id`, `herdr_tab_id`, `herdr_terminal_id`가 있는 started를 게시한다. 자식은 자기ID/read_thread·started의ID/탭·기준HEAD/blob·별도변경을 대조한 뒤에만 조사/편집한다. 그 전에는 지정 인계읽기만 허용한다. started가 없으면5초 간격 최대3회 재조회 후 대기 종료하고 부모의 같은 세션 명시재개를 기다린다. 생성/탭결과가 불명확하면 중복생성하지 않는다. 부모는 생성 후 공유파일/Gitindex 변경을 끝낸다.

## 범위와 완료 조건

대상은 **2433(bookid210200859)의 원공포문과 예고53호→대통령령36288호 직접 연결**이다. 금융위 공고53호·정부입법현황2000000324314·공단 전재 역사법령SEQ_HISTORY613586은04-28을 지지한다. 그러나 공포안첨부10725428은 오류였고 직접 동일안 연결은 미확정이다. 원관보·공포문·부칙 또는 이를 직접 연결하는 새 공식 식별자를 찾아 대조한다. 예고안과 확정 수정내용, 입법현황/후행 설명/전재 법령과 원공포문을 구분한다.

새 `docs/evidence/promulgation-provenance-2026-11-14.json`에 URL·식별자·해시·개정/예고/공포/시행/최초정보가용/확인시각·직접 연결/추론/미확보·판정·남은조건을 기록한다. 최초 공표시각이 없으면null이며 개정·공포 날짜로 대체하지 않는다. 새 근거가 부족하거나 상충하면null/HOLD를 보존한다. 관련05-01/05/25의3일과 나머지12일 영향을 분리한다. 2405를 재조사하거나 원본 판정을 덮어쓰지 않는다. 경계근거를 해소해도 날짜별 결제·예외 발동·모의계좌 적용·백테스트 계약은 별도이며 전체15일 결제HOLD를 유지한다.

새 원문/공식 출력 식별자를 얻었을 때만 조회한다. 직전 원공포안 오류·law.go.kr 점검·KLRI400·법원 방화벽과 이전 KRX/KIND/증권사 실패의 같은 조건 요청을 반복하지 않는다. 기존 원문은 보존본/해시를 재사용한다. 검색색인은 식별자 탐색용이며 원문/부재 증거가 아니다.

대상3일/나머지12일·출처/원문해시·기존21파일 불변·JSON/상대링크·기존 조사본문 보존을 검사한다. 정상브랜치/PR/필수CI·mainSHA/변경4blob 원격 대조·Issue11 결과인계 후 종료한다. 코드 없는 공개 조사에 로컬 코드테스트·외부리뷰를 자동 추가하지 않는다. 전체 계약·사용자 결과 수용을 완료로 표시하지 않는다.

## 필수 읽기와 소유권

AGENTS.md → docs/WORKFLOW.md → docs/STATE.md → 이 파일 → [세션 절차](../operations/session-handoff.md). 이어서 이번 authorization/pending/started·직전 결과·관련 PR/CI만 확인한다. 전체 과거 대화·로그·작업 파일을 다시 읽지 않는다.

- [직전 경계 증거](../evidence/settlement-effective-boundaries-2026-11-14.json): SHA256=`f6bbd44954036343da9fd6faf339015fdd898dea05ad4735239a921c5147e243`. `inputs`, `summary`, `cases`의`kospi-rule-2433`와 그`supporting_source_ids`의자료만 우선 읽는다. `inputs.baseline_hashes`20개와 이 증거까지21파일을 보존한다. 2405부분은 이번 범위에서 재조사하지 않는다.
- [조사 설명](../research/data-contract-2026-11.md)의 ‘2026-11-14 두 규정의 시행일 원문 대조’만 읽는다. 직전 원문/실패 보존본은 위 증거에 고정된 `/mnt/data/tmp/gs02-effective-boundaries-20261114/`에서 필요 항목만 읽는다.

자식 소유는 이 파일·STATE 해당요약·조사문서 새부분·위 새 증거 네파일이다. 부모는 생성 전에 이 파일과STATE만 저장한다. `?? .infisical.yaml`은 별도 변경이며 내용 미열람/미수정/미stage다. 주문·인증브로커·실계좌·유료자료·Evolve·코드구현·백테스트·다른이슈재실행·원본/예측덮어쓰기·추가후속세션은 금지다. Issue11OPEN·첫기준만완료·기업행동8건HOLD·주문OFF·`backtest_ready=false`를 유지한다.
