# 데이터 계약 검증 리뷰

대상: [Issue #11](https://github.com/krdn/gon-stock02/issues/11) · [조사 결과](../research/data-contract-2026-11.md). 2026-11-14 KST 확인.

- 중앙 설정과 dry-run: `claude-opus-5-5 / high`. 최초·수정분 호출 모두 실제 반환 모델 `claude-opus-5-5`, `is_error=false`, 프로세스 종료코드 0과 본문을 확인했다. 대체 모델은 사용하지 않았다.
- 최초 검토: 차단/HIGH 없음. 중간 지적 2건은 공개 원본의 현재/이전 해시 연결과 기업행동 코드명 출처였다.
- 조치: 모든 출처와 당일 묶음 해시 대조, 코드명 자동 추출, 수동 확인과 자동 검사 구분을 추가했다. 세션 표현·과거 세금 근거를 정정했다.
- 수정분 검토: 차단/HIGH 없음, 수정 수용. 이슈의 기존 요율 문구는 원격 갱신 대상이다. 조회 코드 해시는 사후 검사값이며 수집 당시 기록한 실행 증명은 아니다.
- 후속 LOW 처리: 부분 수신 건수·미실행 종목·GET 집계를 저장된 응답에서 계산하도록 했다. 실행 시점 코드 신원 미증명은 증거에 명시했다. 이 작은 기록 변경은 로컬 재검사했으며 세 번째 외부 호출은 하지 않았다.
- 로컬 검사: `uv run python .local/issue11-contract-20261113/check.py` 성공. 상대링크·JSON·diff 검사와 `gon-workflow implementation-ready .` 통과. STE lint는 `docs/conventions/ste100-writing.md` 부재로 실행 불가다.
- 이번 변경의 CI는 PR/Actions에서 별도로 확인한다. 과거 PR #10의 CI 성공을 이번 변경의 증거로 사용하지 않는다.
- 검토 입력·응답·재현 스크립트는 `.local/issue11-contract-20261113`에 보존했다. 공개 저장소에는 계좌·인증값·시세 원본을 넣지 않았다. 원본 파일의 공개 재현과 장중 수신·계좌 비용 실증은 미검증이다.

| 호출 | 입력 SHA-256 | 응답 SHA-256 |
|---|---|---|
| review | `8bc3298395f9eb84a949afd8cb7e9f41fd7ec8c634282978a869dc88a6931555` | `1667d98da0b32cd452ebbc1a776b383f0259ab7786cbe246e4b50a297d600e8c` |
| review-followup | `8178eebed09e89f5f6bcd8b1279f2fb370f94de4902e5698101e8f0c30a3cb24` | `071609c428dc381b688bf7623393bcc4e4c8b62e8b34118dae05ff6c658d2fa9` |
