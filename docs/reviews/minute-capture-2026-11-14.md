# 당일 분봉 수신 보존 검토

[Issue #11](https://github.com/krdn/gon-stock02/issues/11) · [운영](../operations/minute-capture.md) · [검증 증거](../evidence/minute-capture-2026-11-14.json). 2026-11-14 KST 확인.

- 중앙 설정·dry-run은 `claude-opus-5-5 / high`다. 최초·수정분 모두 실제 반환 모델 `claude-opus-5-5`, `is_error=false`, 본문과 프로세스 종료코드 0을 확인했다. 모델 대체는 없었다.
- 최초 검토: 차단/HIGH 없음. LOW는 호출 결정 시각을 전송 시각으로 오해할 수 있는 문구, 실제 슬롯 대기를 반영하지 않은 짧은 기한 테스트였다.
- 조치: `requested_at`의 뜻과 짧은 기한의 부분 수집을 명시했다. 호출 슬롯과 대체 시계를 연결한 테스트를 추가하고 cutoff 테스트를 적절한 기한으로 분리했다. 프로덕션 코드는 최초 검토 후 바꾸지 않았다.
- 수정분 검토: 두 지적 수용, 남은 차단/HIGH 없음. CLI 종료코드 분기는 최초 전체 검토에서 확인했고 수정분 입력에는 생략했다.
- 최종 로컬 검증: 새10개 포함79개 unittest·wheel/sdist 빌드 통과. 별도의 오프라인 CLI 실행도 기록 파일 생성과 모든 종목 관측을 확인했다. 이는 HTTP/시계를 대체한 실행이며 실제 장중 데이터 검증이 아니다.
- 실제 브로커 인증 요청·주문0건. 봉 확정·날짜별 달력·과거 정지·호가·비용은 미검증이다. 백테스트 보류와 모든 관측의 전략 부적격을 유지한다.
- 입력·응답·RED/GREEN 로그와 오프라인 실행 자료는 `.local/minute-capture-20261114`에 보존했다. CI·병합은 PR/Actions의 해당 SHA 결과로 별도 확인한다.

| 호출 | 입력 SHA-256 | 응답 SHA-256 |
|---|---|---|
| review | `e567cd2db57b7551f5a56a2555f5c7c555d54dc6fcb4ea501bd204e543218755` | `9e2a30aa46f1a61df5ea9a2f8f224ec410d128cdbfc54651de8891d4845f4aac` |
| review-followup | `38e0ce32fd136367ef9b8d99d04cfb7c5baece64069319ff89cd031dbc22f78e` | `d72ff598696cc2c3227aac13a2d782e5327673e70318fd98c41d1d4c0c217f68` |
