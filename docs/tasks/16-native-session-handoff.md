# Issue #16 — 앱 기본 기능으로 단계별 새 세션 진행

- 목표: 승인된 단계가 완료되면 AI가 인계를 저장하고 다음 새 세션을 직접 생성·시작한다. 사용자가 매번 세션을 개설하지 않는다.
- 이슈: https://github.com/krdn/gon-stock02/issues/16
- 요청 범위·유한 단계·담당자: [authorization 기록](https://github.com/krdn/gon-stock02/issues/16#issuecomment-6869846991). 단계 `16-verify` → `16-document` → `16-deliver`에서 종료한다.
- 범위: Evolve 제외, 앱 세션 생성·인계·실패 중단의 합성 검증, 프로젝트 운영 규칙 적용. 거래·백테스트 실행은 포함하지 않는다.
- 결정: 앱에 실제 `create_thread`가 있으므로 별도 실행기 구현이 필수라는 이전 판단을 정정했다. CLI 초안과 대체 모델을 사용한 12개 단위 검사는 로컬 `.local/native-loop-implementation-20261114/cli-draft`에 보존하고 제품에 반영하지 않는다.
- 적용: [운영 절차](../operations/session-handoff.md)와 AGENTS에 승인된 단계의 자동 전환을 명시했다. 매 단계에 전체 이력을 복사하지 않고 짧은 작업 문서만 전달한다.
- 독립 검토: [Fable 5.2/high 기록](../reviews/native-session-handoff-2026-11-14.md). 최초·수정분 지적을 보완했으며 마지막 수정의 외부 재승인은 받지 않았다. 실행 증거와 정적 검토를 구분한다.
- 실제 검증: 같은 프로젝트에서 사용자가 별도로 요청한 합성 A→B→C 시험을 재사용하고 산출물을 다시 대조했다. A가 직접 B를 생성했다. B는 종료코드 23에서 C를 만들지 않고 중단했다. 검증 담당 AI가 원인을 해소하고 재개 지시를 보내자 B가 새 C를 생성했다. C는 인계를 검증하고 합계 300에서 후속 결과 600을 생성했다. 세 세션 모두 완료·idle이며 입력·인계·최종 해시가 일치한다. [세션 ID와 증거](../evidence/native-session-handoff-2026-11-14.json).
- 한계: 장기 프로젝트 전체 완주, 앱 재시작 후 자동 복구, 단일 부모의 생성/기록 사이 장애·여러 부모 동시 실행에서 중복 방지, 토큰 절감률은 이번 합성 시험으로 증명되지 않는다.
- 미검증: 실제 개발 PR 반영→다음 개발 세션 실행의 전체 흐름은 운영 규칙을 적용한 상태이며 이번 합성 시험에는 GitHub 변경이 없었다. 실패 뒤 재개는 검증 담당 AI의 명시적 지시를 사용했다. 임의의 실패를 스스로 진단·복구하는 기능의 증거가 아니다.
- 다음 행동: GitHub PR/CI를 통해 규칙을 반영하고 `16-deliver`의 최종 원격 확인은 새 앱 세션에서 수행한다. 실제 반영 결과는 이슈의 최종 댓글과 연결 PR/CI가 기준이다. 그 뒤 자동화 기반 작업은 종료하며 기존 Issue #11/5 실행을 자동 재개하지 않는다.
- 필수 읽기: AGENTS.md, docs/WORKFLOW.md, docs/STATE.md, 이 작업 기록, docs/operations/session-handoff.md, Issue #16과 연결 PR/CI.

## 다음 새 세션: 16-deliver의 원격 확인

전환 ID는 `issue16-final-verify`이며 기준 이슈는 위 Issue #16이다. 이슈의 authorization·pending·started 댓글을 먼저 확인한다. started의 thread ID가 자신의 ID와 일치하고 pending에 기록된 HEAD·인계 blob ID·기존 별도 변경 목록이 맞을 때만 시작한다. 원격 문서·검사 결과를 읽는 작업이며 파일 소유 범위는 `.local/native-session-delivery-20261114/`뿐이다. 다른 세션의 파일을 수정하거나 이번 작업 이전 과제를 재개하지 않는다.

1. 연결 PR의 merge 상태와 merge commit, 원격 main HEAD, 해당 SHA의 필수 CI 결과를 조회한다. GitHub 연결 앱의 기능이 부족하거나 403이면 현재 인증된 gh CLI를 사용한다.
2. 원격 main의 AGENTS, 운영 절차, 이 작업 기록, 증거 JSON, 리뷰 기록, STATE가 로컬 HEAD의 해당 Git blob과 같은지 확인한다. 증거 JSON의 3개 세션 ID·저장된 입력과 인계 해시·300→600 결과도 다시 대조한다. 실패를 완료로 표시하지 않는다.
3. 실제 결과·SHA·CI·파일 일치를 위 소유 폴더의 `remote-verification.json`에 저장한다. `gon-github-workflow` 절차에 따라 Issue #16에 최종 결과를 전달하고 claude-mem의 `gon-stock02-native-loop` 작업을 실제 결과에 맞게 정리한다. 검증 결과와 미검증 범위를 보고한다.
4. 이 단계가 마지막이다. 다음 세션을 만들거나 거래/백테스트/기존 Issue #11·5 작업을 실행하지 않는다. 실패 시 해당 상태와 재개 지점만 기록하고 멈춘다.
