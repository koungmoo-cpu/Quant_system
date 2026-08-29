import React from 'react';
import './TradingPlaybook.css';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

const TradingPlaybook: React.FC<Props> = ({ isOpen, onClose }) => {
  return (
    <div className={`playbook-overlay ${isOpen ? 'open' : ''}`} onClick={onClose}>
      <div className={`playbook-panel ${isOpen ? 'open' : ''}`} onClick={(e) => e.stopPropagation()}>
        <div className="playbook-header">
          <h2>AI 퀀트 대시보드 실전 매매 매뉴얼</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        
        <div className="playbook-content">
          <div className="principle-box">
            <h3>💡 트레이더 절대 원칙</h3>
            <p>
              본 시스템은 마크 미너비니와 크리스천 쿨라매기의 정량적 돌파 매매를 100% 기계적으로 수행합니다.<br/>
              <strong>"대시보드의 진입가와 손절가는 절대적이며, 개인의 감정이나 예측을 섞지 마십시오."</strong>
            </p>
          </div>

          <div className="principle-box" style={{ marginTop: '16px', background: 'rgba(59, 130, 246, 0.1)', borderLeft: '4px solid #3b82f6' }}>
            <h3>🧠 AI 스코어와 셋업 활용 가이드</h3>
            <p style={{ marginBottom: '8px' }}>
              <strong>"특정 셋업(전략) 1가지만 파고들어 투자하는 것은 대찬성, 하지만 점수를 구성하는 4가지 팩터 중 1가지만 보고 투자하는 것은 위험합니다."</strong>
            </p>
            <ul style={{ paddingLeft: '20px', lineHeight: '1.6', fontSize: '0.95rem' }}>
              <li style={{ marginBottom: '8px' }}>
                <strong>🔥 5가지 셋업 (집중 공략 권장)</strong><br/>
                VCP, EP, Breakout 등 여러 전략 중 <strong>본인의 성향에 맞는 1가지 셋업만 선택하여 마스터</strong>하는 것을 강력히 권장합니다. (예: 장중 대응이 어려운 직장인은 VCP, 실적시즌 승부는 EP)
              </li>
              <li style={{ marginBottom: '8px' }}>
                <strong>📊 4가지 AI 스코어 항목 (조합 필수)</strong><br/>
                스코어(20점 만점)는 <strong>상대강도, 거래량, 50일선 이격도, 변동성 수렴</strong> 4가지를 합산합니다. 하나만 보면 추격 매수(상대강도만 높을 때)나 돈이 묶이는(수렴만 할 때) 리스크가 생기므로, <strong>모든 톱니바퀴가 완벽하게 맞물린(15점 이상) 종목</strong>을 노려야 리스크가 최소화됩니다.
              </li>
              <li>
                <strong>💡 100% 활용 팁:</strong> 대시보드에서 본인이 선호하는 셋업(예: Breakout) 탭을 선택한 뒤, <strong>그 중 AI 스코어가 15점 이상인 종목</strong>을 최종 타겟으로 삼으세요!
              </li>
            </ul>
          </div>

          <div className="track-box track-minervini">
            <h3>🛡️ 트랙 A: 미너비니 셋업 (VCP, Power Play, Pullback Bounce)</h3>
            <p className="track-desc">시장 주도주가 변동성을 줄이며 힘을 응축하다가 폭발하는 시점을 노립니다. 장 초반의 속임수(휩쏘)에 당하지 않는 것이 핵심입니다.</p>
            <ul>
              <li><strong>매매 타이밍:</strong> 프리마켓 (장 시작 전)</li>
              <li><strong>대응 전략:</strong> <span className="highlight">[관망 금지 / 기계적 자동매수]</span></li>
              <li><strong>주문 셋팅:</strong> 장 시작 전(밤 10시경), 대시보드 스캐너가 제시한 '진입 기준가(Entry Pivot)'를 확인합니다.</li>
              <li><strong>자동감시주문:</strong> HTS/MTS에 "해당 가격 이상 돌파 시 즉시 시장가 매수(Buy Stop)"를 예약합니다.</li>
              <li><strong>손절 셋팅:</strong> 체결 시 대시보드의 '손절가(Stop-Loss)'에 도달하면 전량 매도되도록 조건을 함께 셋팅합니다.</li>
              <li><strong>수면/본업:</strong> 장이 열리면 첫 30분은 절대 차트를 보지 마십시오. 세력의 흔들기에 예약 주문을 취소하는 실수를 막아야 합니다.</li>
            </ul>
          </div>

          <div className="track-box track-qullamaggie">
            <h3>🔥 트랙 B: 쿨라매기 EP (어닝 갭상승 / 모멘텀 폭발)</h3>
            <p className="track-desc">어닝 서프라이즈 등 강력한 호재로 갭상승을 띄우고, 당일 엄청난 거래량과 함께 치솟는 종목에 올라탑니다.</p>
            <ul>
              <li><strong>매매 타이밍:</strong> 장 시작 후 30분 (한국 시간 밤 10:30 ~ 11:00)</li>
              <li><strong>대응 전략:</strong> <span className="highlight">[30분 관망 후 ORB 돌파 진입]</span></li>
              <li><strong>관망 (Wait):</strong> 장 개장 직후(10:30)부터 30분 동안은 주가가 위아래로 요동치며 당일의 '초기 박스권'을 만듭니다. 이때는 진입하지 않고 관찰만 합니다.</li>
              <li><strong>고점 확인:</strong> 밤 11시 정각, 지난 30분 동안 형성된 '당일 최고점 가격(High of the Day)'을 확인합니다.</li>
              <li><strong>자동감시주문:</strong> 그 30분 최고점 가격을 '새로운 진입 기준가'로 삼아, 이를 뚫고 올라갈 때 시장가로 자동 매수(Buy Stop)되도록 주문을 넣습니다.</li>
              <li><strong>손절 셋팅:</strong> 당일 형성된 최저점(또는 대시보드 제시가)을 손절가로 설정하고 취침합니다.</li>
            </ul>
          </div>

          <div className="track-box track-qullamaggie">
            <h3>🏄‍♂️ 트랙 C: 쿨라매기 Breakout (단기 박스권 돌파)</h3>
            <p className="track-desc">단기 이동평균선(10일/20일선)을 타고 며칠간 쉬어가던 종목이 다시 추세를 이어가는 찰나를 노립니다.</p>
            <ul>
              <li><strong>매매 타이밍:</strong> 프리마켓 또는 장중</li>
              <li><strong>대응 전략:</strong> <span className="highlight">[전일 고가 돌파 시 기계적 매수]</span></li>
              <li><strong>주문 셋팅:</strong> 대시보드가 제시한 진입가(보통 최근 3일 내 최고가)를 확인합니다.</li>
              <li><strong>자동감시주문:</strong> 미너비니 셋업과 동일하게, 해당 가격 돌파 시 시장가 매수되도록 미리 주문을 걸어둡니다.</li>
              <li><strong>손절 셋팅:</strong> 진입 캔들의 저점 또는 10일/20일선 이탈 가격을 손절가로 타이트하게 설정합니다.</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TradingPlaybook;
