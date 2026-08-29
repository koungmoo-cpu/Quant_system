import React, { useState, useEffect } from 'react';
import { useStore } from '../store/useStore';
import './PerformanceStats.css';

const PerformanceStats: React.FC = () => {
  const { performanceData, fetchPerformanceData } = useStore();
  const [initialCapital, setInitialCapital] = useState<number>(10000000);

  useEffect(() => {
    fetchPerformanceData(initialCapital);
  }, []);

  const handleExport = () => {
    window.open('https://ai-stock-backend-108832568469.asia-northeast3.run.app/api/trades/export', '_blank');
  };

  const handleCalculate = () => {
    fetchPerformanceData(initialCapital);
  };

  if (!performanceData) {
    return <div className="perf-loading">Loading performance data...</div>;
  }

  const { total_metrics, strategy_metrics } = performanceData;

  return (
    <div className="perf-container">
      <div className="perf-header">
        <div style={{display: 'flex', alignItems: 'center', gap: '15px'}}>
          <h2>계좌 성과 추적 엔진 📈</h2>
          <button onClick={handleExport} style={{background: '#3b82f6', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontSize: '13px', fontWeight: 'bold'}}>⬇️ 매매 기록 엑셀(CSV) 다운로드</button>
        </div>
        <div className="capital-input-group">
          <label htmlFor="capital-input">초기 투자금(₩):</label>
          <input 
            id="capital-input"
            type="number" 
            value={initialCapital}
            onChange={(e) => setInitialCapital(Number(e.target.value) || 0)}
            step="1000000"
          />
          <button onClick={handleCalculate} className="calc-btn">계산</button>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-title">CAGR (연평균 수익률)</div>
          <div className={`metric-value ${total_metrics.cagr >= 0 ? 'positive' : 'negative'}`}>
            {total_metrics.cagr.toFixed(2)}%
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">MDD (최대 낙폭)</div>
          <div className="metric-value negative">
            -{total_metrics.mdd.toFixed(2)}%
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">총 누적 수익</div>
          <div className={`metric-value ${total_metrics.total_profit >= 0 ? 'positive' : 'negative'}`}>
            {total_metrics.total_profit > 0 ? '+' : ''}{total_metrics.total_profit.toLocaleString()}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">승률 (Win Rate)</div>
          <div className="metric-value neutral">
            {total_metrics.win_rate.toFixed(1)}%
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">Profit Factor</div>
          <div className="metric-value neutral">
            {total_metrics.profit_factor === 999.9 ? '∞' : total_metrics.profit_factor.toFixed(2)}
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-title">평균 손익비</div>
          <div className="metric-value neutral">
            {total_metrics.risk_reward_ratio === 999.9 ? '∞' : total_metrics.risk_reward_ratio.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="strategy-section">
        <h3>🔥 전략별 통계 비교</h3>
        {Object.keys(strategy_metrics).length === 0 ? (
          <p className="no-strategy">기록된 전략 데이터가 없습니다.</p>
        ) : (
          <div className="strategy-grid">
            {Object.entries(strategy_metrics).map(([strategy, metrics]) => (
              <div key={strategy} className="strategy-card">
                <h4>{strategy || '미분류 전략'}</h4>
                <div className="s-metric">
                  <span>거래 횟수:</span> <strong>{metrics.total_trades}회</strong>
                </div>
                <div className="s-metric">
                  <span>승률:</span> <strong>{metrics.win_rate.toFixed(1)}%</strong>
                </div>
                <div className="s-metric">
                  <span>손익비:</span> <strong>{metrics.risk_reward_ratio === 999.9 ? '∞' : metrics.risk_reward_ratio.toFixed(2)}</strong>
                </div>
                <div className="s-metric">
                  <span>총 수익:</span> 
                  <strong className={metrics.total_profit >= 0 ? 'positive' : 'negative'}>
                    {metrics.total_profit > 0 ? '+' : ''}{metrics.total_profit.toLocaleString()}
                  </strong>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceStats;
