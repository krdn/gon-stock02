# Issue #11 — 두 규정의 시행일 원문 대조

- [이번 사용자 지시/한 단계 승인](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6874555756) · [직전 결과](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6873752270) · [Issue #11](https://github.com/krdn/gon-stock02/issues/11).
- 허용 목록/마지막 단계는 `11-settlement-effective-boundaries-20261114` 하나다. 전환ID=`issue11-settlement-effective-boundaries-20261114`, 최초 전환 담당=`01a1d8db-9cee-75d1-88f2-b9e11d0785e1`. 실제 담당·기준SHA/blob·탭은 최신 유효 pending/started에서 대조한다.
- 직전 PR29/main `8a9306714ced73ea363d7af6cafe7cb32dce38de`의 PR/main각92테스트·wheel/sdist·구성CI와 main/4blob 원격 일치를 확인했다. 규정26개·한국투자 약관2개를 확보했으나 날짜별 직접 결제 근거 신규0일·대상15일HOLD다.
- 세션 판단: 2026-11-14T08:27:35.586Z 최근 입력318,684/컨텍스트475,000=67.1%, 최근 출력744. 정확한 실시간 점유/잔여가 아니다. 누적15,547,970은 반복입력/캐시 포함이며 현재 점유·비용이 아니다. 주간98%는 별도 지표다. 완료 단계 경계에서 새 세션을 선택했다.

## 조사 전 새 탭 확인

부모는 인계PR/필수CI·mainSHA/문서blob을 확인하고 pending을 게시한다. create_thread1회·기본모델상속·fork없음으로 새 세션을 만든다. Herdr 새탭 **‘규정 시행일 원문 대조 (#11)’**에 folder=`/home/gon/llm-projects/gon-stock02`를 명시하고 같은ID를 초기작업프롬프트 없이 기본 공유서버 `codex resume`로 표시한다. 기존 space의 표시 folder가 다른 프로젝트이므로 이를 상속하지 않는다. 직전 `--no-daemon` 뷰어 잠금 실패를 반복하지 않는다. 새 독립 에이전트 실행이 아닌 앱 실행세션 표시가 목적이다.

부모는 ls/status·foreground resumeID/cwd·실제 앱 렌더링을 대조한 `tab_verified=true`, `next_thread_id`, `herdr_space_id`, `herdr_tab_id`, `herdr_terminal_id`가 있는 started를 게시한다. 자식은 자기ID/read_thread·started의ID/탭·기준HEAD/blob·기존별도변경을 대조한 뒤에만 공개조사/편집한다. 그 전에는 지정 인계 읽기만 허용한다. started가 없으면5초 간격 최대3회 재조회 후 대기 종료하고 부모의 같은 세션 명시 재개를 기다린다. 생성/탭 결과가 불명확하면 중복 생성하지 않는다. 부모는 생성 후 공유파일/Git index 변경을 끝낸다.

## 범위와 완료 조건

1. **유가증권 업무규정2405**: bookid=`210163555`, 표제/연혁 시행2026-01-29와 부칙2026-01-28의 불일치를 원개정문·개정이유·시행문 등 새 공식 식별자로 대조한다. 기존 HTML을 다시 받는 것만으로 새 독립 근거를 확보했다고 하지 않는다. 연결된 대상은2026-02-16/17/18·03-02다.
2. **타규정 개정2433**: bookid=`210200859`, 표제2026-04-28과 부칙의 ‘공고 제2026-53호 시행령 개정안 공포일’ 조건을 실제 공포된 법령/관보·부칙으로 연결한다. 개정예고와 확정 공포·시행일을 구분한다. 연결된 대상은2026-05-01/05/25다.

새 `docs/evidence/settlement-effective-boundaries-2026-11-14.json`에 두 쟁점별 URL·공식 식별자·해시·개정/공표/시행/확인시각·표제/본문의 구분·판정·남은조건을 기록한다. 최초 공표시각이 없으면null이며 개정일로 대체하지 않는다. 상충/미확보는null/HOLD다. 경계를 해소해도 날짜별 결제·예외 발동·현재 모의계좌·전체 백테스트 적격으로 올리지 않는다. 기존7일에 미치는 영향과 나머지8일을 분리하며, 전체15일의 기존 결제HOLD 판정을 보존한다.

새 원문/공식 출력 식별자를 얻었을 때만 조회한다. 이전 KRX 날짜행/빈본문/PDF·접근거부·law.krx 시간초과·rule.krx 목록GET405, KIND0건, 한국투자 오류목록/삼성410·유안타66건의 같은 조건 요청은 반복하지 않는다. 규정 포털의 공개 POST 경로는 보존본을 재사용하고 새로운 원개정문·이유·시행문을 확보할 때만 연결한다. 검색색인은 원문·부재 증거가 아니다.

두 쟁점 집합·출처/원문해시·기존20파일 불변·JSON/상대링크를 검사하고 정상브랜치/PR/필수CI·mainSHA/변경4blob 원격 대조·Issue11 결과인계 후 종료한다. 코드 없는 공개 조사에 로컬 코드테스트·외부리뷰를 자동 추가하지 않는다. 전체 계약·사용자 결과 수용을 완료로 표시하지 않는다.

## 필수 읽기와 소유권

AGENTS.md → docs/WORKFLOW.md → docs/STATE.md → 이 파일 → [세션 절차](../operations/session-handoff.md). 이어서 이번 authorization/pending/started·직전 결과·관련 PR/CI만 확인한다. 전체 과거 대화·로그·작업 파일은 다시 읽지 않는다.

- [직전 규정 증거](../evidence/settlement-rule-versions-2026-11-14.json): `inputs`, `summary`, `public_sources`의 `kospi-210163555`·`kospi-210200859`, `version_groups`/`date_results`의 위7일 연결 부분만 우선 읽는다. 나머지는 구체적인 연결 근거가 필요할 때만 읽는다. SHA256=`3f405862dd8818552bf62ef7d3c25134b04386e3f031db41b5ef2412c1395246`.
- [조사 설명](../research/data-contract-2026-11.md)의 ‘2026-11-14 결제 규정의 버전과 예외’만 읽는다. 원문은 증거에 고정된 `/mnt/data/tmp/gs02-rule-versions-20261114/kospi-210163555.html`·`kospi-210200859.html`을 필요할 때 읽는다. 기존 증거는 해시와 지정 연결 부분만 확인한다.

자식 소유는 이 파일·STATE 해당요약·조사문서 새부분·위 새 증거 네파일이다. 부모는 생성 전에 이 파일과 STATE만 저장한다. 이전19파일의 해시는 직전 증거의 `inputs.baseline_hashes`에 있으며 직전 규정 증거까지20파일을 보존한다. 기존 원본·증거·예측을 덮어쓰지 않는다. `?? .infisical.yaml`은 별도 변경이며 내용 미열람/미수정/미stage다. 주문·인증브로커·실계좌·유료자료·Evolve·코드구현·백테스트·다른이슈재실행·추가후속세션은 금지다. Issue11OPEN·첫기준만완료·기업행동8건HOLD·주문OFF·`backtest_ready=false`를 유지한다.

## 이번 단계 결과와 종료 경계

- 담당 `01a1d932-726e-72a2-beef-be572df35510`은 [started](https://github.com/krdn/gon-stock02/issues/11#issuecomment-6874642086)의 자기ID/read_thread·기준HEAD `ec22c967`·두 인계blob·별도 변경과 Herdr탭 `tb707bba429a99d032267f3ae2754e2e41`/t64·경로/foreground/화면 보존본 해시를 대조했다. 최초3회 대기는 조사·편집 없이 종료했고 부모의 같은 세션 명시재개 후 진행했다.
- [조사 설명](../research/data-contract-2026-11.md#2026-11-14-두-규정의-시행일-원문-대조) · [새 증거](../evidence/settlement-effective-boundaries-2026-11-14.json). KRX HWP4개를 포함한 신규 본문12개와 재사용 HTML2개다. 2405는 등록 개정문01-29와 전문01-28의 실제 상충이다. 2433은 공고53호→04-28 공포36288호·전재 역사법령 부칙의 연결 근거를 확보했지만 원공포안/직접 연결 미확보다. 두 확정 경계는null/HOLD, 기존7일과 나머지8일의 결제HOLD는 그대로다.
- 실패: 최초 KRX 직접 다운로드/익명 세션정보 재사용은88바이트 오류였다. 공개 화면의 파일별 익명 절차를 따른 실제 HWP와 구분했다. 법령센터 점검·KLRI400·법원 방화벽·공포안첨부 오류도 원문 확보로 표현하지 않았다. 이전 단계의 같은 실패 요청은 재실행하지 않았다.
- 검증 범위: 두 쟁점/7+8일 집합·출처/추출 해시·기존20파일 불변·JSON/상대링크·기존 조사본문 보존·diff. 로컬 코드테스트·외부리뷰는 코드 없는 공개 조사라NOT_RUN이다. 정상 PR/필수CI·mainSHA/변경4blob 원격 대조와 Issue11 최종 인계의 실제 결과는 해당 이슈 댓글에서 확인한다.
- 남은 조건: 2405 확정 시행문/정정·문서 우선순위, 2433 원공포안·예고53호와의 직접 연결, 최초 공표/정정 이력이다. 날짜별 결제·예외/계좌 적용과 다른 계약 미완료도 유지한다. 공개 조사·문서 전달 한 단계 후 종료하며, 사용자 결과 수용·Issue11 전체 완료나 다음 실행 권한으로 간주하지 않는다. 추가 세션·자동 재개는 없다.
