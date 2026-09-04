import React, { useState, useEffect } from 'react';
import { useStore, OwnedAsset } from '../store/useStore';
import './PortfolioTable.css'; // Reuse portfolio table styles
import './PerformanceStats.css'; // Reuse performance stats styles

const VirtualTrading: React.FC = () => {
  const { 
    virtualPortfolio, 
    fetchVirtualPortfolio, 
    updateVirtualAsset, 
    closeVirtualAsset,
    virtualPerformanceData,
    fetchVirtualPerformance
  } = useStore();

  const [closingAsset, setClosingAsset] = useState<OwnedAsset | null>(null);
  const [closeForm, setCloseForm] = useState({ sellPrice: 0, sellQuantity: 0, exitReason: 'Trailing Stop' });
  
  const [isAdding, setIsAdding] = useState(false);
  const [editForm, setEditForm] = useState<OwnedAsset | null>(null);
  const [initialCapital, setInitialCapital] = useState<number>(10000000);

  useEffect(() => {
    fetchVirtualPortfolio();
    fetchVirtualPerformance(initialCapital);
  }, [fetchVirtualPortfolio, fetchVirtualPerformance, initialCapital]);

  const handleCloseInit = (asset: OwnedAsset) => {
    setClosingAsset(asset);
    setCloseForm({ sellPrice: asset.CurrentPrice || asset.AvgPrice || 0, sellQuantity: asset.Quantity, exitReason: 'Trailing Stop' });
  };

  const submitClose = async () => {
    if (!closingAsset) return;
    if (closeForm.sellQuantity <= 0 || closeForm.sellQuantity > closingAsset.Quantity) {
      alert(`매도 수량은 1부터 ${closingAsset.Quantity} 사이여야 합니다.`);
      return;
    }
    await closeVirtualAsset(closingAsset.Ticker, closeForm.sellPrice, closeForm.sellQuantity, closeForm.exitReason, closingAsset.Strategy || 'Virtual');
    setClosingAsset(null);
    fetchVirtualPerformance(initialCapital);
  };

  const handleSave = async () => {
    if (editForm) {
      if (!editForm.Ticker.trim()) return alert("티커를 입력해주세요.");
      if (editForm.Quantity <= 0) return alert("수량은 1 이상이어야 합니다.");
      await updateVirtualAsset(editForm);
      setEditForm(null);
      setIsAdding(false);
    }
  };

  const handleDelete = async (ticker: string) => {
    if (window.confirm(`포트폴리오에서 ${ticker}를 삭제하시겠습니까? (거래 내역에 기록되지 않음)`)) {
      await updateVirtualAsset({ Ticker: ticker, Quantity: 0, AvgPrice: 0, PurchaseDate: '' });
    }
  };

  const handleAdd = () => {
    setIsAdding(true);
    setEditForm({ Ticker: '', Quantity: 0, AvgPrice: 0, PurchaseDate: new Date().toISOString().split('T')[0], Strategy: 'Virtual' });
  };

  const totalInvested = virtualPortfolio.reduce((sum, asset) => sum + ((asset.AvgPrice || 0) * (asset.Quantity || 0)), 0);
  const totalCurrentValue = virtualPortfolio.reduce((sum, asset) => sum + ((asset.CurrentPrice || 0) * (asset.Quantity || 0)), 0);
  const totalUnrealizedProfit = totalCurrentValue - totalInvested;

  return (
    <div className="portfolio-container" style={{ marginTop: '20px' }}>
      
      {/* 1. 성과 요약 (Performance Stats) */}
      <div className="perf-container" style={{ marginBottom: '30px' }}>
        <div className="perf-header">
          <h2>프워드 테스트 (가상 매매) 성과 🧪</h2>
          <div className="capital-input-group">
            <label>초기 투자금(₩):</label>
            <input type="number" value={initialCapital} onChange={e => setInitialCapital(Number(e.target.value) || 0)} step="1000000" />
            <button onClick={() => fetchVirtualPerformance(initialCapital)} className="calc-btn">조회</button>
          </div>
        </div>
        
        {virtualPerformanceData ? (
          <div className="metrics-grid">
            <div className="metric-card">
              <div className="metric-title">CAGR (연평균 수익률)</div>
              <div className={`metric-value ${virtualPerformanceData.total_metrics.cagr >= 0 ? 'positive' : 'negative'}`}>
                {virtualPerformanceData.total_metrics.cagr.toFixed(2)}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-title">MDD (최대 낙폭)</div>
              <div className="metric-value negative">
                -{virtualPerformanceData.total_metrics.mdd.toFixed(2)}%
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-title">총 누적 수익</div>
              <div className={`metric-value ${virtualPerformanceData.total_metrics.total_profit >= 0 ? 'positive' : 'negative'}`}>
                {virtualPerformanceData.total_metrics.total_profit > 0 ? '+' : ''}{virtualPerformanceData.total_metrics.total_profit.toLocaleString()}
              </div>
            </div>
            <div className="metric-card">
              <div className="metric-title">승률</div>
              <div className="metric-value neutral">{virtualPerformanceData.total_metrics.win_rate.toFixed(1)}%</div>
            </div>
          </div>
        ) : <p>성과 데이터 로딩 중...</p>}
      </div>

      {/* 2. 가상 포트폴리오 (Virtual Portfolio) */}
      <div className="portfolio-header">
        <h2>Virtual Portfolio</h2>
        <button className="add-btn" onClick={handleAdd} disabled={isAdding}>+ 수동 종목 편입</button>
      </div>

      <div className="portfolio-summary" style={{ marginBottom: '15px' }}>
        <span className="summary-item">총 가상 투자 금액: ${totalInvested.toLocaleString()}</span>
        <span className="summary-item">평가 손익: <span className={totalUnrealizedProfit >= 0 ? 'profit-text' : 'loss-text'}>${totalUnrealizedProfit.toLocaleString()}</span></span>
      </div>

      <div style={{ overflowX: 'auto', width: '100%' }}>
        <table className="portfolio-table">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Strategy</th>
              <th>Quantity</th>
              <th>Avg Price</th>
              <th>Current Price</th>
              <th>Purchase Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isAdding && editForm && (
              <tr>
                <td><input type="text" value={editForm.Ticker} onChange={e => setEditForm({ ...editForm, Ticker: e.target.value.toUpperCase() })} placeholder="AAPL" /></td>
                <td><input type="text" value={editForm.Strategy} onChange={e => setEditForm({ ...editForm, Strategy: e.target.value })} /></td>
                <td><input type="number" value={editForm.Quantity} onChange={e => setEditForm({ ...editForm, Quantity: parseInt(e.target.value) || 0 })} /></td>
                <td><input type="number" value={editForm.AvgPrice} onChange={e => setEditForm({ ...editForm, AvgPrice: parseFloat(e.target.value) || 0 })} /></td>
                <td>-</td>
                <td><input type="date" value={editForm.PurchaseDate} onChange={e => setEditForm({ ...editForm, PurchaseDate: e.target.value })} /></td>
                <td>
                  <button className="save-btn" onClick={handleSave}>Save</button>
                  <button className="cancel-btn" onClick={() => setIsAdding(false)}>Cancel</button>
                </td>
              </tr>
            )}
            
            {virtualPortfolio.length === 0 && !isAdding ? (
              <tr><td colSpan={7} className="no-data">가상 포트폴리오에 등록된 종목이 없습니다.</td></tr>
            ) : virtualPortfolio.map(asset => (
              <tr key={asset.Ticker}>
                <td className="ticker-col">{asset.Ticker}</td>
                <td><span className="strategy-badge">{asset.Strategy}</span></td>
                <td>{asset.Quantity}</td>
                <td>${(asset.AvgPrice || 0).toFixed(2)}</td>
                <td>${(asset.CurrentPrice || 0).toFixed(2)}</td>
                <td>{asset.PurchaseDate}</td>
                <td style={{ display: 'flex', gap: '4px' }}>
                  <button className="close-btn" onClick={() => handleCloseInit(asset)} style={{ padding: '4px 8px', backgroundColor: '#8b5cf6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>가상 매도(청산)</button>
                  <button className="delete-btn" onClick={() => handleDelete(asset.Ticker)} style={{ padding: '4px 8px' }}>삭제</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {closingAsset && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="modal-content" style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', width: '400px' }}>
            <h3>{closingAsset.Ticker} 가상 매도</h3>
            <div style={{ marginBottom: '12px' }}>
              <label>매도 가격 ($)</label>
              <input type="number" step="0.01" value={closeForm.sellPrice} onChange={(e) => setCloseForm({...closeForm, sellPrice: parseFloat(e.target.value) || 0})} style={{ width: '100%', padding: '8px' }} />
            </div>
            <div style={{ marginBottom: '12px' }}>
              <label>매도 수량 (보유: {closingAsset.Quantity})</label>
              <input type="number" value={closeForm.sellQuantity} onChange={(e) => setCloseForm({...closeForm, sellQuantity: parseInt(e.target.value) || 0})} style={{ width: '100%', padding: '8px' }} />
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '20px' }}>
              <button onClick={() => setClosingAsset(null)} style={{ padding: '8px 16px', border: '1px solid #ccc', background: 'white', borderRadius: '4px' }}>취소</button>
              <button onClick={submitClose} style={{ padding: '8px 16px', border: 'none', background: '#ef4444', color: 'white', borderRadius: '4px', fontWeight: 'bold' }}>청산 확정</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default VirtualTrading;
