# 모의 주문 장부 검토 결과

사용자가 지정한 `gpt-6.1-sol / high`의 별도 Codex 세션 검토를 받았다. 지적 1건을 재현했고, 기존에 명시된 89일 조회 제한으로 분류해 [장기 운용 후속 Issue #7](https://github.com/krdn/gon-stock02/issues/7)에 남겼다. 이번 초기 장부 구현 범위의 병합 차단 사유로는 채택하지 않았다. 다른 제공자의 독립 승인이나 장기 자동 운용 통과를 뜻하지 않는다.

- 검토 대상: `caa3da25183447f241f8f0c76fb097243894a4b3`. 코드·테스트는 구현 커밋 `df661d9549caa0ffb69fd93839ad038b73b8b0bb`와 같다.
- 입력: 요구사항과 관련 코드·테스트·계약 자료 8개. SHA-256 `6834c7fda02a498d5508af53565ed5c690ad251f175799e41e4fd811e6b0710e`.
- 실행: `codex exec --ignore-user-config --ephemeral --sandbox read-only -m gpt-6.1-sol -c model_reasoning_effort='"high"'`. 종료코드 0, 리뷰 본문과 `turn.completed` 확인. 응답에 서버 반환 모델 ID는 없어 요청 설정과 실제 서버 모델 식별을 구분한다. 리뷰어는 자료만 읽었고 테스트를 실행하지 않았다.
- 지적: P2, 고정된 `metadata.start`로 인해 장부 생성 90일 후 빈 장부도 `invalid_order_dates`가 발생하고 신규 주문·취소까지 차단된다.
- 직접 재현: 기존 합성 브로커와 SQLite로 89일 대조 성공, 90일 차단, 각 재시작 후 동일 결과 확인. 모의 HTTP 주문 POST 0건, 실제 네트워크 주문 0건. 지적의 동작 자체는 수용한다.
- 판정 근거: 기존 [운영 문서](../operations/paper-order-ledger.md)는 89일 범위 초과 시 차단과 장기 이력 후속 구현을 이미 명시했다. 축약 검토 입력에는 이 운영 문서가 빠져 있었다. 현재 차단을 임의로 해제하거나 시작일을 바꾸지 않으며, 장기 운용 전에 #7을 해결해야 한다.

Claude는 최초 및 22:00 KST 재시도에서 5시간 사용 한도로 실패했다(`is_error=true`, `modelUsage={}`, 안내 초기화 23:30 KST). 이후 사용자가 Claude 한도 시 Argon 사용을 지시했고, 다시 이번 검토는 6.1 sol로 진행하도록 지정했다. 전역 모델 설정은 변경하지 않았다.

Argon은 `agy models`의 `gemini-4-argon-high`와 `high`로 요청했다. 첫 요청은 5분 `print_timeout`과 빈 본문을 반환했다. 축약 스트림 요청은 무응답으로 로컬 호출을 정리했고, 직접 호출의 짧은 probe는 7초에 `OK`를 받았지만 긴 리뷰는 사용자 전환 지시까지 본문이 없어 중단했다. Argon 리뷰 완료나 서버 모델 신원 확인으로 기록하지 않는다.

기존 구현 검증은 전체 테스트 60개·wheel/sdist 빌드, 계좌 잠금·호출 간격의 별도 프로세스 검사다. 실제 빈 모의계좌 대조·재시작 조회는 일치했고 주문은 0건이다. [조회 증거](../evidence/paper-order-ledger-2026-11-13.json). 이번 검토 후 코드는 변경하지 않았다.

실제 장중 접수·체결·취소와 신 TR 전량취소 0/0 계약은 미검증이다. STE 문서 검사는 기준 파일 부재로 미실행이다. 최종 병합·main CI·원격 검증 상태는 [Issue #5](https://github.com/krdn/gon-stock02/issues/5)와 [PR #6](https://github.com/krdn/gon-stock02/pull/6)에 남긴다.
