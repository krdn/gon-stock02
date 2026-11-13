# KIS·NXT 모의 지원 조사

- 작업: `GS02-P1-KIS-20261113` · 작성자: `ggw-gon-stock02-quant` · 부모: Herdr `t5h`.
- 정보 기준: 2026-11-13 15:43 KST. 개정 2: 부모가 전달한 실행 관측과 추가 공식 자료를 구분해 반영했다.
- 상태: 독립 문서 조사 완료. 작성자는 KIS 인증·시세·주문 API 호출, 계좌·인증값 접근, 성과 검증을 수행하지 않았다.
- 결과 파일: `docs/research/kis-nxt-support-2026-11.md`. 원자료·조회시각·해시는 `.local/research/kis/sources.jsonl`에 보관했다.

## 핵심 결론

1. **KIS 모의 주문과 정정취소는 KRX만 지원한다.** NXT/SOR 모의 주문은 문서상 미지원이다. 현재 Excel의 `EXCG_ID_DVSN_CD` 설명과 공식 모의 TR 전환 공지가 일치한다. [E][N]
2. **NXT·통합 WebSocket 체결가/호가는 모의 미지원이다.** KRX 실시간 체결가/호가 및 모의 체결통보는 지원한다. 과거일 분봉도 모의 미지원이다. [E]
3. **모의 REST 한도는 현재 초당 1건이다.** 공식 유량 공지는 이전 2건에서 변경됐다고 명시한다. 과거 안내를 그대로 구현하면 제한에 걸릴 수 있다. [R]
4. **주성엔지니어링은 현재 NXT 정규시장 비대상으로 판단한다(공식 자료 종합).** 2월 제외 명단에 있고, 3분기 선정 명단과 현재 전체 603종목에 없다. 부모의 NXT 현재가 실패와 부합하지만 그 오류의 직접 원인까지 입증하지는 않는다. [F][Q3][Q4][U]
5. **제안:** KRX 모의 주문 기록과 NXT 관측 시세 기반 가상 체결 기록을 분리한다. NXT 가상 체결을 KIS 모의 체결·실제 수익으로 표현하지 않는다. 주성엔지니어링은 재편입 근거 확인 전 NXT 실험에서 제외한다.

## API 지원표

판정은 문서상 지원 / 문서상 미지원 / 불명이다. 지원 판정은 실제 응답·체결 성공을 뜻하지 않는다.
`Q`는 `/uapi/domestic-stock/v1/quotations`, `T`는 `/uapi/domestic-stock/v1/trading`이다.
모의 REST는 `https://openapivts.koreainvestment.com:29443`, 모의 WebSocket은 `ws://ops.koreainvestment.com:31000`이다. [E]

| 기능 | 경로 또는 TR | 모의 판정 | 근거·제약 |
|---|---|---|---|
| REST 인증 | `POST /oauth2/tokenP` | 문서상 지원 | Excel 해당 시트 B11. 토큰 유효 24시간; 발급 제한과 재사용 규칙 적용. |
| WebSocket 접속키 | `POST /oauth2/Approval` | 문서상 지원 | Excel 해당 시트 B11. 접속키와 REST 토큰을 구분. |
| 현재가 | `Q/inquire-price` · `FHKST01010100` | 문서상 지원* | 모의 TR 명시, `FID_COND_MRKT_DIV_CODE=J/NX/UN`. |
| 호가·예상체결 | `Q/inquire-asking-price-exp-ccn` · `FHKST01010200` | 문서상 지원* | 모의 TR 명시, 시장 코드는 동일. |
| 당일 분봉 | `Q/inquire-time-itemchartprice` · `FHKST03010200` | 문서상 지원* | 1회 최대 30건; 전일 분봉 미제공. |
| 과거일 분봉 | `Q/inquire-time-dailychartprice` · `FHKST03010230` | 문서상 미지원 | 실전만 1회 최대 120건, 보관 범위 최대 1년. |
| 일·주·월·년봉 | `Q/inquire-daily-itemchartprice` · `FHKST03010100` | 문서상 지원* | 1회 최대 100건; `FID_ORG_ADJ_PRC=0` 수정주가, `1` 원주가. |
| KRX 현금 주문 | `T/order-cash` · 매수 `VTTC0012U`, 매도 `VTTC0011U` | 문서상 지원 | `EXCG_ID_DVSN_CD=KRX`; 주문유형별 모의 허용 범위는 별도 확인. |
| KRX 정정취소 | `T/order-rvsecncl` · `VTTC0013U` | 문서상 지원 | 이미 체결된 수량 취소 불가. 원주문·잔량 대조 필요. |
| NXT/SOR 주문·정정취소 | 위 두 경로의 거래소 지정 | 문서상 미지원 | 현금 시트 G38, 정정취소 시트 G40: 모의 KRX 제한. [N]도 명시. |
| 정정취소 가능 주문 조회 | `T/inquire-psbl-rvsecncl` · 실전 `TTTC0084R` | 문서상 미지원 | 모의 TR·도메인에 미지원 표시. |
| 주문·체결 조회 | `T/inquire-daily-ccld` · `VTTC0081R` / `VTSC9215R` | 문서상 지원 | 각각 3개월 이내/이전; 모의 1회 최대 15건, 연속조회 필요. |
| 잔고 조회 | `T/inquire-balance` · `VTTC8434R` | 문서상 지원 | 모의 1회 최대 20건. 시장별 평가 입력과 거래소 주문 지원은 별개. |
| KRX 체결가·호가 WS | `H0STCNT0` / `H0STASP0` | 문서상 지원 | 모의 TR·도메인 명시. |
| 모의 주문 체결통보 WS | `H0STCNI9` | 문서상 지원 | `tr_key`는 HTS ID. 구독 성공 응답과 실제 통보 수신·복호화 성공을 구분. |
| NXT 체결가·호가 WS | `H0NXCNT0` / `H0NXASP0` | 문서상 미지원 | 각 시트 B7·B11에 미지원 명시. 실전 서버는 `ws://ops.koreainvestment.com:21000`. |
| 통합 체결가·호가 WS | `H0UNCNT0` / `H0UNASP0` | 문서상 미지원 | 각 시트 B7·B11에 미지원 명시. |
| 모의 REST에서 NX·UN 실제 제공 범위 | 위 * 표시 API의 시장 입력 | 불명 | 공통 입력에는 NX·UN이 있으나 환경별 보장 범위는 별도 명시되지 않았다. 부모의 3종목 숫자 응답은 아래 제한된 관측으로 기록. |

표의 원문은 [E]의 동명 시트 B6·B7·B11·B12 및 필드 설명이다. 공식 GitHub [G]의 대응 함수와 대조했다.
시세의 `J=KRX`, `NX=NXT`, `UN=통합`은 주문의 `KRX/NXT/SOR`와 다른 코드다. 통합 시세를 조회했다고 SOR 주문·체결을 검증한 것은 아니다.
구 TR 자동 매핑은 2025년 공지에 나오지만 현재 규격은 구 TR 중단 가능성을 경고하므로 신 TR을 기준으로 삼는다. [E][N]

## 부모 실행 관측과 해석

출처는 2026-11-13 사용자가 전달한 부모의 실행 결과다. 실행 시각·요청/응답 원본은 제공되지 않았으며, 작성자는 계좌·키·다른 작업자 보고서를 열지 않았다.

| 부모가 전달한 결과 | 이 보고서의 해석 |
|---|---|
| 모의 인증·잔고·4종목 KRX 현재가/분봉 성공 | 해당 실행 성공 보고로 기록. 독립 재검증·주문 성공·성과 증거는 아님. |
| 삼성전자·SK하이닉스·삼성전기 NXT 현재가에서 숫자 응답 | 숫자 응답 관측. NXT 원천 시장(venue), 실시간성, 모든 모의 시세 지원을 확정하지 않음. |
| 주성엔지니어링 NXT 현재가 `invalid_market_data` | 실패 관측. KIS 원문 오류인지 호출자 검증 판정인지도 원본 없이는 확정하지 않음. |

**문서와 관측은 모순되지 않는다.** REST 시세 API에는 모의 TR과 NX 입력이 함께 기재되어 있다. NXT **주문**·NXT **WebSocket**의 모의 미지원은 별도 계약이다. 따라서 3종목의 REST 숫자 응답으로 미지원 주문·WS를 지원으로 바꾸거나, 주성 한 종목의 실패로 모든 모의 NXT 시세를 미지원으로 판정하지 않는다. [E][N]

## 호출·데이터 제약

- **유량:** 실전 REST 초당 18건, 모의 초당 1건, 계좌 단위 제한. 토큰·WS 접속키 발급은 각각 초당 1건이다. WS는 계좌(앱키)당 1세션, 전 상품·종류 합계 41등록이다. 신규 실전 신청은 3일간 초당 3건이며 모의는 이 신규 제한 대상이 아니다. [R][R2]
- **제안:** 같은 모의 계좌의 모든 호출을 한 큐에서 제한한다. 4종목×가격·호가 2종÷1건/초는 약 8초의 호출 예산을 사용하므로 REST 반복만으로 동시 호가를 가정하지 않는다. KRX WS 8등록+체결통보 1등록은 9등록이다. 제한 오류 시 폭주 재시도 대신 지연 재시도하고, 주문 응답이 불명확하면 재주문 전에 접수 여부를 확인한다.
- **분봉:** 당일 API에 미래 시간을 넣으면 현재 값이 채워질 수 있다. 첫 배열의 거래량은 새 분의 첫 체결 전까지 이전 분의 값일 수 있다. 완료된 봉만 신호에 쓰고 원시 시각·수신 시각을 함께 보존한다. `FID_PW_DATA_INCU_YN`을 전일 분봉 지원으로 해석하지 않는다. [E][G]
- **과거 검증:** 최대 1년은 보관 상한이며 모든 종목·거래소의 완전한 1년 자료 보장이 아니다. 수정 여부, 거래소, 세션, 결측·중복·정지 구간을 고정하고 미래 공시·사후 수정 데이터가 당시 판단에 섞이지 않게 한다. 분봉만으로 호가 대기순위·체결 가능성을 복원할 수 없다.
- **규격과 샘플 차이:** `ccnl_notice.py`의 종목코드 예시와 달리 Excel `tr_key`는 HTS ID다. `inquire_balance.py`의 `AFHR_FLPR_YN=Y` 설명도 과거 시간외 설명이 남아 있다. 현재 Excel·2026-09 공지는 `N=KRX정규장종가, X=NXT, Y=통합시세`로 정정한다. 샘플을 그대로 계약으로 사용하지 않는다. [E][G][C]
- **추가 호출 제한:** 잔고 시트는 개인 한도와 별개인 원장 총량 120 TPS 제한을 설명한다. 이는 개인 허용량이 아니며, `EGW00215` 등 원장 제한도 부모 검증에서 구분한다. [E]

## NXT 시간·종목

| 구분 | 공식 관측·판정 | 근거 |
|---|---|---|
| 평상일 정규시장 | 프리 08:00–08:50, 메인 09:00:30–15:20, 애프터 체결 15:40–20:00(호가접수 15:30부터) | [S] 변경 전 표 |
| 2026-11-19 수능일 | 프리 미운영; 메인 10:00:30–16:20; 애프터 체결 16:40–20:00(접수 16:30부터) | [S] 2026-11-05 공지 |
| 수능일 종가매매 | 접수 16:00–17:00, 체결 16:30–17:00 | [S] |
| 삼성전자 `005930` | NXT 공개 조회에 존재; 거래가능시장 `전체`, 거래불가사유 빈 값 | [U], 2026-11-13 15:15 기준 지연 자료 |
| SK하이닉스 `000660` | 위와 동일 | [U], 동일 기준 |
| 삼성전기 `009150` | 위와 동일 | [U], 동일 기준 |
| 주성엔지니어링 `036930` | **현재 NXT 정규시장 비대상으로 판단(공식 자료 종합)**. 전체 603건을 모두 수신했고 코드·표준코드·이름 모두 없음 | [U][F][Q3][Q4] |

NXT 웹 자료는 20분 지연이며, 위 세 종목도 다음 거래일의 주문 허용을 보장하지 않는다. `sources.jsonl`에 조회 날짜·종목 검색값과 원본 응답을 남겼다.
**주성 판정 근거:** 2026-02-09 공지의 첨부 Excel `2.12 부터` 시트 B48·C48에 `KR7036930006`·주성엔지니어링이 있다. 공지의 명시 제외기간은 2월 12일~6월 30일이다. 이 기간만으로 11월까지 자동 연장됐다고 해석하지 않는다. [F]
추가로 6월 26일의 3분기 선정결과 Excel 전체에서 코드·이름이 없고, 4분기는 현행 종목 유지 방침이다. 11월 13일 15:21 기준 공개 정규시장 전체 목록도 `totalCnt=records=수신건수=603`, 주성 0건, 나머지 세 종목은 각 1건이다. 이 연결 증거로 현재 비대상을 판단한다. 2025년 편입 기록은 현재 자격 증거가 아니다. [Q3][Q4][U][H]
4분기 공지는 606종목 유지 예정이었지만 이후 별도 제외 공지가 존재한다. 분기 명단만 고정하지 말고 거래일별 대상·거래정지·허용 세션을 확인한다. [U][Q4][A]
KIS 2026-09 공지는 KRX 애프터마켓과 NXT GTP 주문유형·VI/재개 단일가 변경도 설명한다. 이 변경을 모의 주문유형 지원의 증거로 확장하지 않는다. [C]

## 분리 검증 대안과 추가 권한

**제안 A — 우선 경로:** KRX 모의 주문은 KIS가 반환한 주문번호·체결·취소·잔고를 기준으로 기록한다. NXT는 별도의 `venue=NXT, execution=shadow` 기록으로 평가한다. NXT 가상 매수로 생긴 재고를 KRX 모의 매도 주문의 재고로 취급하지 않는다.

**제안 B — NXT 관측 경로:** 부모가 승인 범위 내에서 실전 API 시세 이용 등록·접속 권한을 확인한 뒤 NXT WS를 조회 전용으로 사용한다. 모의 키만으로 NXT WS를 사용할 수 있다는 근거는 없다. 과거일 분봉도 실전 시세 권한이 필요하다. 실전 키가 권한 자체로 읽기 전용이라고 가정하지 말고 실주문 경로를 실행 대상에서 제외한다. 추가 유료 데이터 계약은 이번 대안에 포함하지 않는다.

모의 REST `NX`에서 유효 시세가 확인되면 추가 실전 권한 없이 제한적인 관측 대안이 될 수 있다. 다만 초당 1건의 스냅샷으로 빠른 시장의 체결·대기순위를 검증할 수 없다. NXT 공개 웹의 지연 가격은 실시간 가상 체결 입력으로 사용하지 않는다.

가상 체결은 신호 이후 설정한 지연이 지난 시점의 NXT 매도호가(매수)·매수호가(매도)와 가용 잔량을 기준으로 제한한다. 지정가는 단순 가격 접촉을 전량 체결로 처리하지 않는다. 부분체결·미체결·호가 소멸을 기록하고, 수수료·매도세금의 해당 날짜 기준과 추가 슬리피지를 별도 반영한다. 스프레드를 호가 체결에 반영한 경우 비용으로 중복 차감하지 않는다.

**실패 조건:** 지연·단절·역전 호가, 대상 자격 미확인, 단일가·정지 처리 부재, 비용 미정이면 신규 가상 진입을 중단한다. 두 기록의 위험을 합산해 부모가 확정한 손실·노출 한도를 적용한다. 다음 거래일 청산 시도 실패는 미청산으로 남기며 임의 종가 체결로 숨기지 않는다.
**반대 근거·한계:** 별도 가상 체결은 NXT 주문 서버·취소 경쟁·실제 대기순위를 검증하지 못한다. 따라서 NXT 모의 주문 요구를 완전히 충족한 대안이 아니며, 시세 확보만으로 수익·정확도 우위를 주장할 수 없다.

## 미해결과 부모의 다음 검증

1. 이미 보고된 인증·KRX 조회를 성공 미확인 상태로 되돌리지 않는다. 추가 검증은 NXT 숫자 응답의 venue·시각·거래량·호가 의미와 UN·다른 시세 API의 범위에 집중한다. 필요하면 부모가 비밀값을 제거한 요청 메타데이터·원문 오류를 남긴다.
2. `H0STCNI9` 구독 → 모의 주문 접수/체결 통보 → REST 체결·잔고 대조 → 취소·재접속 후 복구를 검증한다. 이 보고서는 그 실행을 대신하지 않는다.
3. 모의 정정취소 가능 조회가 미지원이므로 일별주문체결·체결통보 기반 잔량 추적 대안을 검증한다. 취소와 체결의 경합을 완전히 막는다고 가정하지 않는다.
4. 주성엔지니어링은 현재 NXT 비대상으로 처리하고 공식 재편입 근거 확인 시만 해제한다. 부모의 KRX 현재가/분봉 성공과 분리한다. `invalid_market_data`의 직접 원인은 아직 미확정이다.
5. 11월 19일 특별 시간표와 다음 거래일 계산, KRX 모의 애프터마켓·주문유형·매매제한종목·비용 규칙을 확인한다. 미확정 주문유형은 실행 대상에 넣지 않는다.

## 근거와 조회시각

- [E] [KIS 전체 API Excel](https://apiportal.koreainvestment.com/files/download/apiCollection/API_COLLECTION), 2026-11-13 15:33:59 KST. 서버 파일명 `한국투자증권_오픈API_전체문서_20261113_053233.xlsx`; SHA-256 `193c303a6580f0d5592ebf3da63af30afacbc6f281e167bd36f67a9d349e9ee0`. 시트/셀은 `.local/research/kis/api-spec.json`; 추출은 `python3 .local/research/kis/extract_spec.py`.
- [G] [KIS 공식 GitHub 국내주식 원문](https://github.com/koreainvestment/open-trading-api/tree/4a51f9126e719c352072b14b7df9222cb2691720/examples_llm/domestic_stock), 2026-11-13 조회. commit `4a51f9126e719c352072b14b7df9222cb2691720`(2026-11-13 04:55:29 UTC); 대응 함수 원문 13개를 `github-sources.txt`에 보관. 파일별 조회 초 단위 시각은 미기록.
- [N] [모의투자 신규 TR 전환·넥스트레이드 미지원 공지](https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/dd2e7e20-51e8-45fd-b65a-24a128f6af34), 게시 2025-02-25, 원문 JSON 조회 2026-11-13 15:35:19 KST.
- [R] [호출 유량 공지](https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/d0d1a83f-6f8d-4437-9700-6d26702fd989), 제목 기준 2026-04-20, 원문 JSON 조회 2026-11-13 15:35:18 KST.
- [R2] [신규 고객 호출 제한 공지](https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/c1113824-17c7-47a7-b7b8-8880506a847c), 게시 2026-03-20, 원문 JSON 조회 2026-11-13 15:35:18 KST.
- [C] [KRX 애프터마켓·NXT 제도 변경](https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/26dfe350-eb72-48e5-8175-34eb27970f3e), 게시 2026-09-09, 원문 JSON 조회 2026-11-13 15:35:19 KST.
- [S] [NXT 수능일 변경 공지](https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=46&scNttCl=general), 게시 2026-11-05, 직접 HTML 조회 2026-11-13 15:33:59 KST.
- [U] [NXT 공식 정규시장 조회](https://nextrade.co.kr/menu/transactionStatusMain/menuList.do), 공개 화면의 `/brdinfoTime/brdinfoTimeList.do`로 2026-11-13 15:35:52–15:36:14 KST 개별 조회, 15:41 KST 전체 조회. `nxt-all-current.json`에 전체 603건과 `setTime=2026-11-13 15:21` 보관. 변동내역 검색 0건 자체는 제외 근거로 사용하지 않았다.
- [H] [NXT 2025-03-24 확대 공지](https://nextrade.co.kr/menu/marketInfo/view.do?scBbsKndCode=marketInfo&scNttCl=general&scNttNo=11), 2026-11-13 공식 검색 원문 확인. 주성엔지니어링의 과거 편입만 입증.
- [Q4] [NXT 4분기 대상종목 공지](https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=43&scNttCl=general), 2026-11-13 15:35:39 KST 조회.
- [A] [NXT 10월 대상종목 조정](https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=45&scNttCl=general), 2026-11-13 15:35:39 KST 조회. 듀켐바이오·범한퓨얼셀 제외 공지이며 네 대상종목의 제외 근거는 아니다.
- [F] [NXT 2026-02-09 제외 공지](https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=34&scNttCl=general)의 [50종목 첨부 Excel](https://nextrade.co.kr/comm/file/download.do?fileNo=225&fileSn=1), 2026-11-13 15:43:17 KST 조회. `2.12 부터` 시트 B48·C48. SHA-256 `1bc80af788843d9e6930f3b2e969ac37700d75642534d47c89218599c96251a2`.
- [Q3] [NXT 3분기 선정 공지](https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=40&scNttCl=general)의 [선정결과 Excel](https://nextrade.co.kr/comm/file/download.do?fileNo=269&fileSn=1), 2026-11-13 15:43:17 KST 조회. 전체 선정결과 검색, 주성 0건. SHA-256 `a2a2e87127d7a85726d5d73b77838effcc8aa780db09d06eecf643a12b9f94b9`.

웹 검색 도구는 일부 NXT 본문을 열지 못했으나 공개 HTTP로 원문을 확보했다. KIS 공지 화면은 동적이므로 화면이 사용하는 공개 게시물 JSON으로 본문을 확인했다. 타 작업자 보고서는 읽지 않았다.
검증 제약: 지정 파일 대상 `evolve docs ste-lint --strict`는 `docs/conventions/ste100-writing.md` 부재로 실행 실패했다. 이를 통과로 기록하지 않는다.

[E]: https://apiportal.koreainvestment.com/files/download/apiCollection/API_COLLECTION
[G]: https://github.com/koreainvestment/open-trading-api/tree/4a51f9126e719c352072b14b7df9222cb2691720/examples_llm/domestic_stock
[N]: https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/dd2e7e20-51e8-45fd-b65a-24a128f6af34
[R]: https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/d0d1a83f-6f8d-4437-9700-6d26702fd989
[R2]: https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/c1113824-17c7-47a7-b7b8-8880506a847c
[C]: https://apiportal.koreainvestment.com/community/10000000-0000-0011-0000-000000000001/post/26dfe350-eb72-48e5-8175-34eb27970f3e
[S]: https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=46&scNttCl=general
[U]: https://nextrade.co.kr/menu/transactionStatusMain/menuList.do
[H]: https://nextrade.co.kr/menu/marketInfo/view.do?scBbsKndCode=marketInfo&scNttCl=general&scNttNo=11
[Q4]: https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=43&scNttCl=general
[A]: https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=45&scNttCl=general
[F]: https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=34&scNttCl=general
[Q3]: https://nextrade.co.kr/menu/notice/view.do?scBbsKndCode=notice&scNttNo=40&scNttCl=general
