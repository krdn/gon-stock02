# KRX 모의 주문·취소·대조 계약

관측: 2026-11-13 21:15~21:24 KST. 작업: `GS02-ORDER-CONTRACT-20261113`, 작성자: `ggw-gon-stock02-quant`.
결론: 취소 요청의 성공 응답은 취소 완료 증거가 아니다. 원주문·취소주문 연결, 확인수량, 잔고를 다시 대조해야 한다. 응답 불명 주문은 자동 재제출하지 않는다.
상태: 공식 문서·샘플 대조 완료. 인증·계좌 조회·주문 실행은 하지 않았다. 아래 “제안”은 문서의 보장을 넓히지 않기 위한 구현 기준이다.

## 출처와 적용 범위

- **S1** [KIS 전체 API Excel](https://apiportal.koreainvestment.com/files/download/apiCollection/API_COLLECTION): 21:15:32 재수신. 기존 `.local/research/kis/api-spec.xlsx`와 바이트 동일. SHA-256 `193c303a6580f0d5592ebf3da63af30afacbc6f281e167bd36f67a9d349e9ee0`.
- **S2** [공식 샘플 고정 revision](https://github.com/koreainvestment/open-trading-api/tree/4a51f9126e719c352072b14b7df9222cb2691720): `examples_llm/domestic_stock/{order_cash,order_rvsecncl,inquire_daily_ccld,inquire_balance}`. 아래 계약은 개인 고객·KRX·현금 지정가·3개월 이내 조회에 한정한다.
- **S3** [KIS 모의투자 필독 공지](https://apiportal.koreainvestment.com/api/forums/10000000-0000-0011-0000-000000000001/posts/a995fa1c-39a1-4c0a-a99e-838400c7a7a2), [공식 모의투자 규정 화면](https://vts3.koreainvestment.com/vts/#/rule/1), [그 화면의 공개 규정 본문 번들](https://vts3.koreainvestment.com/js/app_vts_hantoo_bundle.js): 21:16~21:18 확인. 본문 추출본과 수신 시각·해시는 `.local/research/order-contract/`에 보존했다.

## 요청 계약

공통: 호스트는 `https://openapivts.koreainvestment.com:29443`, 경로 접두사는 `/uapi/domestic-stock/v1/trading/`이다. 인증 헤더 외에 `tr_id`, 개인 고객 `custtype=P`, JSON content-type을 사용한다. `CANO`·`ACNT_PRDT_CD`는 매 요청의 필드명이며 실제값은 이 문서에 기록하지 않는다. 수량·가격은 JSON 숫자가 아닌 문자열, POST 키는 대문자다. [S1]

| 동작 | Method·경로 끝부분 | 모의 TR | 공통 계좌 필드 외 입력 |
|---|---|---|---|
| 지정가 매수·매도 | POST `order-cash` | 매수 `VTTC0012U`, 매도 `VTTC0011U` | `PDNO`, `ORD_DVSN="00"`, `ORD_QTY`, `ORD_UNPR`, `EXCG_ID_DVSN_CD="KRX"`. `SLL_TYPE`은 매도 시 `"01"` 또는 생략(일반매도). `CNDT_PRIC`은 이 범위에서 생략. |
| 원주문 잔량 전부 취소 | POST `order-rvsecncl` | `VTTC0013U` | `KRX_FWDG_ORD_ORGNO`, `ORGN_ODNO`, 원주문 `ORD_DVSN="00"`, `RVSE_CNCL_DVSN_CD="02"`, `ORD_QTY`, `ORD_UNPR`, `QTY_ALL_ORD_YN="Y"`, `EXCG_ID_DVSN_CD="KRX"`. |
| 일별주문체결 | GET `inquire-daily-ccld` | `VTTC0081R` | `INQR_STRT_DT`, `INQR_END_DT`는 YYYYMMDD. `SLL_BUY_DVSN_CD="00"` 전체, `CCLD_DVSN="00"` 전체, `INQR_DVSN="00"` 역순 또는 `"01"` 정순, `INQR_DVSN_1=""`, `INQR_DVSN_3="00"` 전체(현금 한정은 `"01"`), `EXCG_ID_DVSN_CD="KRX"`, `PDNO`, `ORD_GNO_BRNO`, `ODNO`, 두 `CTX_AREA_*100`. |
| 잔고 | GET `inquire-balance` | `VTTC8434R` | `AFHR_FLPR_YN="N"`, `OFL_YN=""`, `INQR_DVSN="01"`, `UNPR_DVSN="01"`, `FUND_STTL_ICLD_YN="N"`, `FNCG_AMT_AUTO_RDPT_YN="N"`, `PRCS_DVSN="00"`, 두 `CTX_AREA_*100`. |

위 표의 근거는 S1 해당 시트 22~44행과 S2다. 잔고 `INQR_DVSN="01"`은 대출일별이며 S1 명시값이다. S2는 종목별 `"02"`도 설명하지만 현재 Excel의 설명은 누락되어 있다. `PRCS_DVSN="00"`은 전일매매 포함이다.

전량취소의 `ORD_QTY="0"`, `ORD_UNPR="0"`은 [공식 legacy 예제의 전량 수량 0 처리](https://github.com/koreainvestment/open-trading-api/blob/4a51f9126e719c352072b14b7df9222cb2691720/legacy/Sample01/kis_domstk.py)와 [현재 전략 예제의 취소가격 0](https://github.com/koreainvestment/open-trading-api/blob/4a51f9126e719c352072b14b7df9222cb2691720/strategy_builder/core/data_fetcher.py#L679-L688)을 조합한 구현 후보다. 현재 전략 예제는 수량에 `qty`를 넣어 예제가 통일되어 있지 않다. S1은 `Y=전량`만 정의한다. 신 TR에서 0/0의 실제 접수는 장중 검증 전 미확인이다.

`ORD_GNO_BRNO`는 S1에서 필수 표시지만 S2의 전체조회 기본값은 빈 문자열이다. 주문번호를 모르면 `PDNO/ORD_GNO_BRNO/ODNO=""`로 전체 조회하는 후보를 쓴다. 특정 주문 조회는 응답의 지점·주문번호를 그대로 사용한다. 숫자로 변환해 앞자리 0을 없애지 않는다.

## 응답·연속조회

| 대상 | 필드와 의미 | 구현상 주의 |
|---|---|---|
| 공통 | `rt_cd`, `msg_cd`, `msg1` | HTTP 200만으로 성공 판정 금지. 정상 JSON·`rt_cd="0"`·필수 응답 구조를 함께 확인한다. 성공도 체결 완료를 뜻하지 않는다. |
| 신규·취소 | `output` 단일 객체의 `KRX_FWDG_ORD_ORGNO`, `ODNO`, `ORD_TMD` | S1의 신규 필드·양쪽 예시는 대문자. 취소 필드 표는 소문자다. 문서가 불일치하므로 이 세 필드에 한해 양쪽 철자를 허용하고, 동시에 다른 값이면 오류 처리할 것을 제안한다. |
| 일별 `output1[]` | `ord_dt`, `ord_gno_brno`, `odno`, `orgn_odno`, `ord_orgno` | 주문일·주문번호·채번지점으로 식별한다. `orgn_odno`는 정정/취소의 원주문 연결이다. `ord_orgno`와 채번지점을 같은 값이라고 가정하지 않는다. |
| 일별 주문 속성 | `pdno`, `sll_buy_dvsn_cd`, `ord_dvsn_cd`, `ord_qty`, `ord_unpr`, `ord_tmd` | 제출 의도와 일치하는지 확인한다. 매도 `01`, 매수 `02`. 이름 문자열로 판정하지 않는다. |
| 일별 수량 | `tot_ccld_qty` 총체결, `cncl_cfrm_qty` 취소확인, `rmn_qty` 잔여, `rjct_qty` 거부, `cncl_yn` 취소여부 | S1은 각 이름을 제공하지만 행별 합산식·반영 순서·`cncl_yn` 값의 상세 의미를 보장하지 않는다. 결측을 0으로 치환하지 않는다. |
| 일별 합계 | `output2` 객체, `tot_ord_qty`, `tot_ccld_qty` 등 | 개별 주문 상태의 근거는 `output1`이다. S1 92~94행은 영문 키와 한글 설명이 어긋나므로 비용/금액 자동 계산 근거로 사용하지 않는다. |
| 잔고 `output1[]` | `pdno`, `hldg_qty` 보유수량, `ord_psbl_qty` 주문가능수량 | 전량매도 종목이 보유수량 0으로 남을 수 있다. 보유수량만으로 매도 가능하다고 판단하지 않는다. |
| 잔고 `output2[]` | `dnca_tot_amt`, `prvs_rcdl_excc_amt`, `tot_evlu_amt` 등 | 예수금·D+2 정산금·총평가금액은 서로 다른 값이다. 총평가금액을 주문가능 현금으로 사용하지 않는다. |

근거: S1 신규 40~46행, 취소 42~48행 및 응답 예시, 일별 49~94행, 잔고 45~101행.

일별 조회는 모의 1회 최대 15건, 잔고는 최대 20건이다. 최초 `tr_cont=""`, `CTX_AREA_FK100=""`, `CTX_AREA_NK100=""`로 요청한다. 응답 헤더 `tr_cont=F/M`이면 응답 본문의 `ctx_area_fk100/ctx_area_nk100`을 다음 요청에 그대로 넣고 헤더 `tr_cont=N`으로 이어간다. `D/E`가 마지막이다. [S1, S2]

제안: 두 조회 모두 모든 페이지를 받은 뒤 대조한다. 반복 커서·페이지 제한 초과·중간 실패·알 수 없는 종료 표시는 “조회 불완전”이다. 페이지별 `output2`를 무조건 더하지 않는다. 공식 예제는 흐름 참고용이며, 일별조회 재귀 호출의 위치 인자가 함수 선언 순서와 달라 그대로 복사하지 않는다. [S2 `inquire_daily_ccld.py` 26~48, 200~204행]

## 취소·복구·매도 가능 판정

| 조건 | 확인된 계약과 제안 |
|---|---|
| 취소 `rt_cd="0"` 수신 | 응답에는 취소 완료 수량이 없다. 반환된 주문 식별자를 취소 요청 기록에 저장하고 원주문 번호를 유지한다. 대조 전 예약수량/위험예산 해제는 금지할 것을 제안한다. [S1] |
| 취소와 체결의 경합 | 원주문 및 `orgn_odno`로 연결된 행을 함께 조회한다. 취소 중 늘어난 체결은 보유분으로 반영하고, 확인된 취소수량만 해제한다. 취소 자식 행을 신규 매매처럼 합산하지 않는다. 이는 제안이며 모의 행 갱신 방식은 실증 전이다. |
| 잔량 0 | 전량체결·취소·거부가 모두 가능하므로 `rmn_qty=0` 하나로 CANCELED 판정하지 않는다. 총체결·취소확인·거부수량, 주문 연결, 잔고가 함께 설명되어야 종료한다. |
| 매도 가능수량 | 별도 `inquire-psbl-sell`은 S1상 모의 미지원이다. 모의 잔고의 `ord_psbl_qty`, 장부의 확인된 보유분에서 미완료 매도 예약을 뺀 수량을 각각 상한으로 적용할 것을 제안한다. 조회 뒤 값이 바뀔 수 있어 접수·체결을 보장하지 않는다. |
| 대조 모순 | 체결 누적 감소·속성 불일치·외부 주문·잔고 불일치·누락/음수 수량은 UNKNOWN과 신규 진입 차단으로 처리할 것을 제안한다. 두 REST 조회 사이의 원자적 스냅샷은 문서로 보장되지 않는다. |

예시(설명용): 10주 주문에서 체결 3주를 확인한 뒤 전량취소를 요청해도 보유는 0주가 아니다. 후속 조회에서 체결 4주·취소확인 6주·잔량 0주와 잔고 4주가 일치해야 그 상태를 확정한다. 이는 합성 예시이며 실제 계좌·체결 결과가 아니다.

## timeout·중복 제출·기록

S1의 개인 주문 계약에는 사용자 `idempotency key`나 클라이언트 주문 ID 필드가 없다. 헤더 `gt_uid`는 법인 전용 거래고유번호이며, 재시도 중복 제거·개인 조회 키 기능은 명시되지 않았다. 따라서 서버의 멱등 처리를 전제로 설계할 근거가 없다.

제안: POST 전에 로컬 의도 ID와 SUBMITTING을 영속화한다. 전송 후 timeout·연결 단절·잘린 응답·식별자 누락·복구된 SUBMITTING은 UNKNOWN으로 남긴다. HTTP 재시도·프로세스 재시작으로 같은 의도를 자동 재전송하지 않는다. hashkey도 중복 제거 키가 아니다.

주문번호가 없으면 해당 일자의 전체 주문을 끝까지 조회해 종목·매매방향·수량·가격·시각 후보를 찾을 수 있다. 그러나 후보 0건은 미접수를, 후보 1건은 그 요청과의 동일성을 증명하지 않는다. 동일 조건의 다른 주문·반영 지연·페이지 조회 도중 변화를 배제할 계약이 없다. 후보가 불명확하면 자동 연결·재주문을 멈추고 수동 조사한다.

[공식 인증 헬퍼](https://github.com/koreainvestment/open-trading-api/blob/4a51f9126e719c352072b14b7df9222cb2691720/examples_user/kis_auth.py#L300-L304)는 hashkey를 선택 사항으로 명시하고, POST 경로 472~474행은 해시 호출을 주석 처리한다. S1 신규·취소 요청 헤더에도 hashkey 필수 항목은 없다. 이 revision에서 생략 가능한 문서 근거는 있으나, 이번 조사에서 생략한 실제 주문은 검증하지 않았다.

S1의 `msg_cd`는 길이 8의 문자열이다. 공개 예시는 `APBK0013`, `KIOK0510`이다. 안전한 기록 제안은 `rt_cd`, 검증한 `msg_cd`, HTTP 상태, TR, 시각, 로컬 의도 ID다. 코드 형식은 구현상 `^[A-Z0-9]{1,8}$` 허용목록으로 제한하고 불일치는 원문 대신 형식 오류만 남긴다. 이 정규식은 공식 전체 코드 규격이 아니다. `msg1`·요청/응답 원문에는 계좌 등 정보가 섞일 수 있으므로 공개 기록에서 제외한다. 브로커 주문번호·연결번호는 접근 제한된 장부에만 보존한다.

## 거래 세션과 남은 확인

S3 규정은 실제 국내 주식 영업일을 따르고, 동시호가 08:30~09:00 및 15:20~15:30, 정규시장 09:00~15:30, 익일예약 15:40~익일 07:30을 안내한다. 시간외매매는 모의투자에서 불가하다고 명시한다. 예약시간은 별도 예약주문 기능의 시간이며 `order-cash` 야간 지원 근거가 아니다.

S1에 KRX 애프터마켓 주문구분 `41~47`이 나열되어도 모의 지원을 명시하지 않는다. S3 시간외 불가와 함께 읽으면 이 코드 목록만으로 모의 애프터마켓을 허용할 수 없다. S1 `EXCG_ID_DVSN_CD`는 모의 KRX만 지원한다. NXT/SOR 주문은 이 계약 밖이다.

제안: 확인된 개장일·모의 세션에만 주문한다. 평일이라는 사실만으로 개장일을 추정하지 않는다. 주말·휴장일, 특별개장일 시간 미확인, 공지와 시간표 충돌, 장 상태/시계 불명, 21시 이후에는 신규 주문을 차단한다. 09:00~15:20의 연속매매만 쓰는 것은 동시호가를 제외하는 프로젝트 선택이며 공식 전체 지원시간과 구분한다.

S1 국내휴장일조회 `TCA0903R`는 모의 미지원이고 주문 가능일 확인용 필드는 `opnd_yn`이다. 이미 승인된 경로에서 확인한 달력이나 공식 휴장/특별개장 공지가 필요하다. 해당 API도 개장 시각 자체를 보장하지 않는다. 이번 조사에서는 2026년 특별개장일별 Open API 모의 지원시간의 명시적 공지를 확보하지 못했다.

남은 실증: 신 TR 전량취소 0/0 접수, 신규/취소 응답 철자, 원주문·취소행 수량 갱신과 경합, 다중 페이지 완료, timeout 후 식별, 주문가능수량 변동이다. S3는 실제 시장의 체결 발생을 조건으로 모의 체결을 처리한다고 설명한다. 현재가보다 공격적인 가격·접수 성공만으로 즉시 체결을 주장할 수 없다. 이 보고서는 장중 모의 성공·복구 성공·수익성을 입증하지 않는다.

문서 검사: 120줄 제한·필수 계약 항목·링크 형식 확인. STE 린트는 `docs/conventions/ste100-writing.md` 부재로 실행 실패했으며 통과로 기록하지 않는다.
