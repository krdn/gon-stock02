# Issue #14: 루프 구성

- 요청: 복잡한 프로젝트를 세션별로 이어 진행하는 루프를 이 프로젝트에 적용.
- 이슈: https://github.com/krdn/gon-stock02/issues/14
- 최초 기준 커밋: `655df195cff47dfcec37cb004a73c49564e0d05a`. 원격 main CI 2개 성공을 재조회했다.
- 결정: Evolve 23.2.1의 네이티브 실행기를 유지한다. 기존 분봉 수신 브랜치의 변경7개는 백업·해시를 남기고 별도 작업 경로에서 구현한다.
- 산출물: [운영](../operations/evolve-runtime.md), [실행기](../../scripts/evolve_runtime.py), [고정 원본](../../config/evolve-upstream.json), [목표](../../config/evolve-goal.md).
- 확인: 공식 파일61개의 해시를 고정했다. 실행 차단·환경변수 제외·반복 상한·기존 런타임 보존 검사13개 통과.
- 실패: 기본 `/usr/local/bin/tmux`는 libtinfo 심볼 오류. `/usr/bin/tmux 3.6`은 정상. 설치본의 Codex 모델 목록은 live 조사에서 일부 오래된 것으로 판정됐고 자동 갱신하지 않았다.
- 제한: 공식 구현이 Linux의 linked-worktree 격리를 거부한다. 자동 실행·새 세션·전체 사이클·체크포인트 실제 재개·예약 실행은 NOT_RUN. native `setup complete` 마커는 기록하지 않는다. 별도 준비 표시는 파일 설치·정책 적용만 뜻한다.
- 다음 행동: 지원되는 런타임 또는 공식 Linux 지원 버전 검증 → 작은 실제 사이클 → quota 체크포인트와 자동 재개 → 예약 활성화.
- 유지: 자동주문 OFF, 브로커 요청0건, `backtest_ready=false`. Issue #11과 장중 검증은 미완료 상태다.

- 병행 작업 반영: 분봉 수신 PR #13이 병합된 `3f0577b9961f5ba8aec1a45e9980d2288e13a0b8`로 재개 기준을 갱신했다. 기존 코드·문서를 보존해 합쳤다.
- 실제 준비: 별도 clone에 공식 파일61개를 SHA256 대조 후 설치하고 native 추천 설정을 적용했다. 단계12개 unresolved0·pin 위반0·정책 오류0·Codex API 키 경고0이다. Builder codex-tmux/balanced, Auditor claude-tmux/deep. 실제 모델 호출 증거가 아니다.
- 준비 실패: 최초 clone에 `.git/info`가 없어 실패했다. 실패 clone은 보존했고 디렉터리 생성·회귀 검사를 추가한 뒤 새 clone 준비가 성공했다.
- 추가 확인: 로컬 전체92개 테스트·sdist/wheel 빌드·문서 상대경로 검사 통과. sdist에 실행기가 포함되고 `.local`·`.env`·`.infisical.yaml`은 없다. STE lint는 표준 파일 부재로 미실행이다.
- 리뷰 보완: 준비 전 바이너리 버전 검사, 적용 후·실행 전 정책 상한 검사, 준비 표시, 런타임 밖 해시 기준, native 종료코드 보존, 생성한 개별 파일만 ignore하도록 수정했다. 실제 실행 차단은 유지한다.
