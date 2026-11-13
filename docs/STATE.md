# 작업 인수인계

기준: https://github.com/krdn/gon-stock02/issues

- 목표: 삼성전자·SK하이닉스·삼성전기·주성엔지니어링을 개장 전 분석하고, 당일 또는 다음 거래일까지 청산하는 전략을 모의투자로 검증한다.
- 확정 결정: 한도 내 모의 자동매매, NXT 포함, gon-stock02 전용 Buzz 채널·전문가 신규 구성, 수익과 손실의 균형 검증, 기존 구독·연결 모델 우선, 추가 유료 지출 보류.
- 사용자 위임: 2026-11-13 판단해서 진행하고 독립 리서치는 Herdr 현재 탭의 병렬 패널로 실행하도록 허용. 기존 위험 초깃값을 설정에 적용했다.
- 계획: [3단계 계획](plans/short-term-trading-2026-11.md). ① 운영 기준·연결 ② 전략·과거 구간 검증 ③ 모의 자동매매·개선.
- 위험 설정: 가상금 1,000만 원, 1회 0.25%, 하루 0.75%, 누적/낙폭 3%, 최대 2종목·종목당 25%·총 50%, 휴일 보유 금지, 종목당 하루 최대 2회 진입. 주문은 꺼둔다. 최적화·성과 검증 수치가 아니다.
- 구현: Python/uv 기반 모의 REST 조회, 시장별 WebSocket 유한시간 프로브, 비용·잔여 손실·예약 손실을 반영한 위험 수량 계산, Buzz 역할 신원 어댑터, Python CI. [실행 방법과 범위](operations/stage1-foundation.md).
- 실제 확인: 모의 인증·잔고·KRX 4종목 현재가와 각 1분봉 30개 성공. 전체 17개 조회 중 16개 성공·주성 NXT 실패. 장후 KRX 모의 WS 31건, NXT 실전 시세 WS 131건 수신, 전 대상 수신 시차 5초 이내. 정규장 혼잡 검증은 미실행. 주문 0건. [관측 기록](evidence/stage1-2026-11-13.json).
- Buzz: 비공개 전용 채널 3개·신원 9개 등록. Herdr quant/risk 2개 패널에서 `gpt-6-astra` 런타임으로 조사·회신. 작성자·파일 내용 일치 확인. 7역할 실행·상시 구독기는 미검증/미구현. [API 조사](research/kis-nxt-support-2026-11.md), [전략 검증 설계](research/validation-design-2026-11.md).
- 결정: NXT 모의 주문/WS는 문서상 미지원. 기존 실전환경 키는 NXT 시세 조회에만 사용했다. KRX 모의 체결과 NXT 가상 체결은 별도 장부로 구현해야 한다. 주성은 현재 NXT 대상 제외.
- 검증: 로컬 unittest 36개·wheel/sdist 빌드 통과. 독립 리뷰 `claude-opus-5-5 / high` 실제 반환 모델 확인. 분봉/인증실패 기록·입력 오류·자본 기준 수정 후 재검증. 수정분 리뷰에서 병합 차단 결함 없음. [리뷰 기록](reviews/stage1-2026-11-13.md). PR/CI 최종 상태는 [Issue #3](https://github.com/krdn/gon-stock02/issues/3)에서 확인한다. 계획 PR #2는 main에 병합됐다.
- 실패/제약: 일부 NXT 페이지 403은 공식 공개 자료 추가 확인으로 보완했다. STE 린트는 `docs/conventions/ste100-writing.md` 부재로 실행 불가. GitHub 연결 앱 쓰기는 403으로 실패하여 인증된 gh CLI를 사용한다. 작업 중 생성된 `.infisical.yaml`은 별도 변경으로 보존한다.
- 이전 작업 완료: [Issue #5](https://github.com/krdn/gon-stock02/issues/5) · [PR #6](https://github.com/krdn/gon-stock02/pull/6), 모의 주문 영속 장부·대조·복구. main `e1a85b0` 병합, PR/main CI 각각 2개 성공과 로컬·원격 SHA 일치를 2026-11-13 재확인했다. [운영](operations/paper-order-ledger.md). 야간 계좌 대조·재시작 조회 일치, 중간 호출 제한은 간격을 두고 해소했다. 실제 주문 0건. 접수·체결·취소 실증은 장 종료로 미실행이다.
- 현재 작업: [Issue #9](https://github.com/krdn/gon-stock02/issues/9), KRX 과거 시세 수집·품질 점검. 모의환경에서 4종목 각각 원주가 일봉 244개(2025-11-14~2026-11-13), 1분봉 1,902~1,905개(11-09~13)를 수집했다. 92페이지·8,593행의 원본/정규화 값·고유 키·해시를 재계산했다. 첫 분봉 페이지 경계 실패는 재현 테스트 후 이전 분 정각 커서로 수정했다. 전체 67개 테스트·빌드 통과. [운영](operations/historical-data.md) · [증거](evidence/historical-data-2026-11-13.json). 외부 리뷰는 `claude-opus-5-5 / high`의 5시간 사용 한도로 본문을 받지 못했다(`is_error=true`, `modelUsage={}`, 초기화 안내 23:30 KST). 다른 모델로 대체하지 않았다. [초안 PR #10](https://github.com/krdn/gon-stock02/pull/10)으로 제출했으며 최신 CI는 PR에서 확인한다. main에는 아직 반영하지 않았다.
- 데이터 제약: 주성 11-09 10:43, 11-11 09:52·09:53의 3개 분봉은 좁은 구간 재조회에서도 없었다. 무거래·공급자 누락은 구분하지 못했다. 공식 달력·봉 시각 정의·기업행동·당시 수신시각·호가·비용 검증 전이므로 `backtest_ready=false`다. 원본은 `.local/history-20261113-run2`에 보존하고 공개 기록에는 가격·계좌·인증값을 넣지 않는다.
- 미완료: 1단계 전체, 장중 실제 모의 접수·체결·취소와 수량 계약 실증, 일일 9역할 연구·스케줄, 과거 데이터·비용 검증·백테스트·수익성. 실계좌 주문·추가 유료 지출은 범위 밖이다.
- 검토 결정(2026-11-13): Claude 사용 한도 시 Argon 사용을 사용자에게 지시받았고, Argon 긴 리뷰가 본문을 반환하지 않아 최신 지시대로 `gpt-6.1-sol / high` 별도 Codex 세션 검토를 받았다. [검토 결과](reviews/paper-order-ledger-2026-11-13.md). 90일째 차단 지적은 재현했고 기존 89일 조회 범위의 제약으로 분류했다. 장기 운용 전 [Issue #7](https://github.com/krdn/gon-stock02/issues/7) 해결이 필요하다. 다른 제공자 독립 승인으로 표시하지 않는다.
- 다음 행동: 현재 데이터 수집 작업의 초안 PR/CI를 확인하고 외부 리뷰를 완료한다. Claude 제한 해제 안내는 2026-11-13 23:30 KST이며 실제 사용 가능 여부는 재시도 결과로 확인해야 한다. 필수 자료는 이 문서·Issue #9의 최신 PR/CI·[수집 운영](operations/historical-data.md)·[증거](evidence/historical-data-2026-11-13.json)다. 이후 분봉 3개 결측 후보와 달력·기업행동·비용 계약을 검증한다. 장중 주문 검증을 재개할 때만 [주문 검토](reviews/paper-order-ledger-2026-11-13.md)·[운영 절차](operations/paper-order-ledger.md)를 읽고 공식 개장일·시간을 재확인한다. 장부 입력 검증 없이 위험 계산기를 자동매매로 연결하지 않는다. 키·계좌번호를 GitHub/Buzz/문서에 기록하지 않는다.
