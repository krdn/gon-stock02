# 루프 실행·재개

현재 상태는 **설정 적용, 자동 실행 차단**이다. Evolve 23.2.1의 Linux 작업 트리 격리 제한 때문에 이 호스트에서는 모델·사이클을 시작하지 않는다. 새 세션 실행·전체 사이클·사용량 한도 후 자동 재개는 미검증이다.

`scripts/evolve_runtime.py`는 Evolve의 네이티브 명령을 호출한다. 별도 개선 루프를 구현하지 않는다. [Issue #14](https://github.com/krdn/gon-stock02/issues/14)가 적용·검증 기준이다.

## 적용한 구성

- `prepare`: 현재 Git의 커밋된 상태를 `.local/evolve/runtime`에 독립 복제한다. 앱의 미커밋 변경·`.env`·로컬 데이터는 복사하지 않는다. 실행 목표와 원본 잠금 파일은 현재 작업 트리의 스냅샷으로 전달한다. 이미 있는 런타임은 덮어쓰지 않는다.
- `config/evolve-upstream.json`: 설치 버전과 같은 공식 커밋의 파일별 SHA256이다. 프로필·프롬프트·단계 레지스트리는 검증 후 런타임에만 설치한다.
- `setup apply --preset recommended`: 기존 구독의 추천 배치를 적용한다. 기본 Builder는 Codex, Auditor는 Claude 계열이다. 실제 배치는 `inspect`로 확인한다. 모델 목록은 자동 갱신하지 않는다. 설치 바이너리 버전을 준비 전에 확인하고 적용 후 반복·sandbox 정책 상한을 대조한다.
- 한 배치1사이클, 최대3배치·3사이클, 실패1회에서 중단한다. 범용 제공자 fallback은 끄고 필수 sandbox는 유지한다.
- 하위 실행에서 API 키와 브로커 환경변수를 제외한다. Linux에서는 정상 동작을 확인한 `/usr/bin/tmux`를 우선한다. 전역 설정·키·sudoers를 수정하지 않는다.
- [실행 목표](../../config/evolve-goal.md)는 주문 OFF·백테스트 HOLD·브로커 요청 없음·추가 지출 없음·기존 기록 보존을 요구한다. 브로커의 권한을 기술적으로 폐기하는 기능은 아니다.

## 명령

프로젝트 루트에서 실행한다. 최초 준비는 공식 고정 버전 파일을 내려받으며 기존 구독 모델 감지를 실행한다.

```sh
python scripts/evolve_runtime.py prepare
python scripts/evolve_runtime.py inspect
python scripts/evolve_runtime.py check
python scripts/evolve_runtime.py status
```

준비 성공 시 런타임에 `gon-stock02-prepared.json`을 기록한다. 이 파일은 설치 완료 표시이며 실제 실행 검증을 뜻하지 않는다. 준비 실패 시 런타임과 로그를 보존하고, 실패 디렉터리를 별도 이름으로 옮긴 뒤 다시 준비한다. 기존 디렉터리를 삭제하거나 덮어쓰지 않는다.

`check`가 성공하고 실제 사이클 검증까지 마친 지원 환경에서 다음 명령을 사용한다. 현재 Linux에서는 시작·재개 모두 종료코드3으로 차단한다.

```sh
python scripts/evolve_runtime.py start
python scripts/evolve_runtime.py stop
python scripts/evolve_runtime.py resume
python scripts/evolve_runtime.py auto-resume
```

`check`는 런타임 밖 프로젝트의 원본 잠금 파일로 무결성을 확인한다. 런타임의 정책 상한과 준비 표시도 재검사한다. native 명령의 실패 종료코드는 보존한다.

`start`는 터미널에서 전경으로 실행한다. `stop`은 진행 중인 wave 이후 멈춘다. 중단 브레이크 해제는 native `evolve loop-stop --release --project-root "$PWD/.local/evolve/runtime"`로 명시한다. `resume`는 운영자 재개라 자동 재개 횟수를 초기화한다. 예약 실행기는 `auto-resume`를 써야 기존 자동 재개 상한을 지킨다.

자동 예약은 설치·활성화하지 않았다. 알려진 quota 해제 시각과 체크포인트가 있을 때만 예약해야 하며 로그인 실패·원인 불명 실패를 반복 재시도하면 안 된다. 종료코드3은 native 오류와 자체 차단이 겹칠 수 있으므로 종료코드만으로 예약하지 않는다. 예약 실행기는 원본 프로젝트의 실행기 절대경로를 고정해야 한다. 원본 작업을 끝낸 후 런타임에 가져오는 절차도 별도 검증이 필요하다.

## 차단 근거와 해제 조건

공식 [sandbox_paths.go:61](https://github.com/mickeyyaya/evolve-loop/blob/577f1b88708154769bdcf3231bd2ae8b194f15a9/go/internal/bridge/sandbox_paths.go#L61)는 Linux의 linked-worktree Git 메타데이터 격리를 거부한다. [README](https://github.com/mickeyyaya/evolve-loop/blob/577f1b88708154769bdcf3231bd2ae8b194f15a9/README.md#known-limits)도 이를 명시한다. 따라서 현재 버전의 실제 구현 실행은 차단한다. sandbox를 끄거나 preflight를 건너뛰지 않는다.

적용 모델 목록과 Builder/Auditor 배치도 다시 확인해야 한다. 지원되는 실행환경을 확보하거나, 해당 제한을 해결한 공식 버전을 별도 검증해야 한다. 이때 고정 버전·파일 해시·실행 차단을 함께 검토하고 작은 실제 사이클과 체크포인트 재개를 확인한다. 이후에만 예약 실행을 활성화한다.

이 호스트의 native preflight는 프로필이 없는 경우에도 `0 CLI binary/binaries present`, `READY`, 종료코드0을 반환했다. 종료코드만으로 준비 완료를 판단하지 않는다. [검증 기록](../tasks/14-evolve-runtime.md)을 함께 확인한다.
