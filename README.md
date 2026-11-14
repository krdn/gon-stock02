# gon-stock02

삼성전자·SK하이닉스·삼성전기·주성엔지니어링의 단기매매를 한국투자증권 모의투자로 검증하는 프로젝트입니다.

[작업 규칙](docs/WORKFLOW.md) · [구성 연결](.github/project-setup.json)

[3단계 계획](docs/plans/short-term-trading-2026-11.md) · [현재 상태](docs/STATE.md)

[AI의 단계별 새 세션 전환](docs/operations/session-handoff.md) · [적용·검증 기록](docs/tasks/16-native-session-handoff.md)

1단계의 KIS 모의 조회·KRX/NXT 시세 수신·위험 계산·Buzz 연구 경로를 구현했습니다.
자동 주문·백테스트·수익성 검증은 아직 시작하지 않았습니다.

[실행 방법과 검증 범위](docs/operations/stage1-foundation.md) · [실제 검증 기록](docs/evidence/stage1-2026-11-13.json)

[KIS·NXT 지원 조사](docs/research/kis-nxt-support-2026-11.md) · [전략 후보·검증 설계](docs/research/validation-design-2026-11.md)

[모의 주문 장부·복구 운영](docs/operations/paper-order-ledger.md) · [주문 API 계약](docs/research/kis-order-contract-2026-11.md)

주문 장부와 실패 복구를 구현했으며 기본 주문은 꺼져 있습니다. 실제 접수·체결·취소는 장중 검증 전입니다.
