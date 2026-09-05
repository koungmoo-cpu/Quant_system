import React, { useState, useEffect } from 'react';
import { useStore, OwnedAsset } from '../store/useStore';
import './PortfolioTable.css'; 
import './PerformanceStats.css'; 

const VirtualTrading: React.FC = () => {
  const { 
    virtualPortfolio, 
    fetchVirtualPortfolio, 
    updateVirtualAsset, 
    closeVirtualAsset,
    virtualPerformanceData,
    fetchVirtualPerformance,
    virtualHistory,
    fetchVirtualHistory,
    minFactorScore,
    fetchRiskRules,
    updateRiskRules
  } = useStore();

  const [closingAsset, setClosingAsset] = useState<OwnedAsset | null>(null);
  const [closeForm, setCloseForm] = useState({ sellPrice: 0, sellQuantity: 0, exitReason: 'Trailing Stop' });
  
  const [isAdding, setIsAdding] = useState(false);
  const [editForm, setEditForm] = useState<OwnedAsset | null>(null);
  const [initialCapital, setInitialCapital] = useState<number>(10000000);

  const [currentPage, setCurrentPage] = useState(1);
  const [historyPage, setHistoryPage] = useState(1);
  const ITEMS_PER_PAGE = 15;

  useEffect(() => {
    fetchVirtualPortfolio();
    fetchVirtualPerformance(initialCapital);
    fetchVirtualHistory();
    fetchRiskRules();
  }, [fetchVirtualPortfolio, fetchVirtualPerformance, fetchVirtualHistory, initialCapital, fetchRiskRules]);

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
    fetchVirtualHistory();
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
    setEditForm({ Ticker: '', Quantity: 0, AvgPrice: 0, PurchaseDate: new Date().toISOString().split('T')[0], Strategy: 'Virtual', setup: '', factor_score: 0 });
  };

  const totalInvested = virtualPortfolio.reduce((sum, asset) => sum + ((asset.AvgPrice || 0) * (asset.Quantity || 0)), 0);
  const totalCurrentValue = virtualPortfolio.reduce((sum, asset) => sum + ((asset.CurrentPrice || 0) * (asset.Quantity || 0)), 0);
  const totalUnrealizedProfit = totalCurrentValue - totalInvested;

  const totalPages = Math.ceil(virtualPortfolio.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedPortfolio = virtualPortfolio.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const historyTotalPages = Math.ceil((virtualHistory || []).length / ITEMS_PER_PAGE);
  const historyStartIndex = (historyPage - 1) * ITEMS_PER_PAGE;
  const paginatedHistory = (virtualHistory || []).slice(historyStartIndex, historyStartIndex + ITEMS_PER_PAGE);

  return (
    <div className="portfolio-container" style={{ marginTop: '20px' }}>
      
      {/* 0. Quick Filter Bar */}
      <div className="quick-filter-bar" style={{ backgroundColor: '#f9fafb', padding: '16px', borderRadius: '8px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '20px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#1f2937' }}>⚙️ Quick Filter Settings</h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1 }}>
          <label style={{ fontWeight: 'bold', color: '#4b5563' }}>최소 진입 팩터 점수:</label>
          <input 
            type="range" 
            min="0" 
            max="20" 
            value={minFactorScore} 
            onChange={(e) => updateRiskRules(Number(e.target.value))}
            style={{ flex: 1, maxWidth: '300px' }}
          />
          <span style={{ backgroundColor: '#10b981', color: 'white', padding: '4px 12px', borderRadius: '16px', fontWeight: 'bold' }}>
            {minFactorScore} 점 이상 매수
          </span>
        </div>
      </div>
      
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

      <div style={{ overflowX: 'auto', width: '100%', marginBottom: '20px' }}>
        <table className="portfolio-table">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Setup/Strategy</th>
              <th>Quantity</th>
              <th>Avg Price</th>
              <th>Current Price</th>
              <th>1차 목표가</th>
              <th>방어선 (Stop Price)</th>
              <th>Buy Score</th>
              <th>SPY/QQQ (Entry)</th>
              <th>Purchase Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isAdding && editForm && (
              <tr>
                <td><input type="text" value={editForm.Ticker} onChange={e => setEditForm({ ...editForm, Ticker: e.target.value.toUpperCase() })} placeholder="AAPL" style={{width: '70px'}}/></td>
                <td><input type="text" value={editForm.setup || ''} onChange={e => setEditForm({ ...editForm, setup: e.target.value })} placeholder="VCP 등" style={{width: '90px'}}/></td>
                <td><input type="number" value={editForm.Quantity} onChange={e => setEditForm({ ...editForm, Quantity: parseInt(e.target.value) || 0 })} style={{width: '60px'}}/></td>
                <td><input type="number" value={editForm.AvgPrice} onChange={e => setEditForm({ ...editForm, AvgPrice: parseFloat(e.target.value) || 0 })} style={{width: '70px'}}/></td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td><input type="number" value={editForm.factor_score || 0} onChange={e => setEditForm({ ...editForm, factor_score: parseFloat(e.target.value) || 0 })} style={{width: '60px'}}/></td>
                <td>-</td>
                <td><input type="date" value={editForm.PurchaseDate} onChange={e => setEditForm({ ...editForm, PurchaseDate: e.target.value })} /></td>
                <td>
                  <button className="save-btn" onClick={handleSave}>Save</button>
                  <button className="cancel-btn" onClick={() => setIsAdding(false)}>Cancel</button>
                </td>
              </tr>
            )}
            
            {virtualPortfolio.length === 0 && !isAdding ? (
              <tr><td colSpan={9} className="no-data">가상 포트폴리오에 등록된 종목이 없습니다.</td></tr>
            ) : paginatedPortfolio.map(asset => (
              <tr key={asset.Ticker}>
                <td className="ticker-col">{asset.Ticker}</td>
                <td><span className="strategy-badge">{asset.setup || asset.Strategy}</span></td>
                <td>{asset.Quantity}</td>
                <td>${(asset.AvgPrice || 0).toFixed(2)}</td>
                <td>${(asset.CurrentPrice || 0).toFixed(2)}</td>
                <td style={{ color: '#10b981' }}>{asset.target_price ? `$${asset.target_price.toFixed(2)}` : '-'}</td>
                <td style={{ color: '#ef4444' }}>{asset.stop_price ? `$${asset.stop_price.toFixed(2)}` : '-'}</td>
                <td>{asset.factor_score || '-'}</td>
                <td style={{ fontSize: '0.8rem', color: '#666' }}>
                  {asset.spy_entry ? `S: ${asset.spy_entry.toFixed(1)}` : '-'} / {asset.qqq_entry ? `Q: ${asset.qqq_entry.toFixed(1)}` : '-'}
                </td>
                <td>{asset.PurchaseDate}</td>
                <td style={{ display: 'flex', gap: '4px' }}>
                  <button className="close-btn" onClick={() => handleCloseInit(asset)} style={{ padding: '4px 8px', backgroundColor: '#8b5cf6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>수동 매도(Close)</button>
                  <button className="delete-btn" onClick={() => handleDelete(asset.Ticker)} style={{ padding: '4px 8px' }}>삭제</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      
      {totalPages > 1 && (
        <div className="pagination" style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: '40px' }}>
          <button 
            disabled={currentPage === 1} 
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            style={{ padding: '6px 12px', border: '1px solid #ccc', borderRadius: '4px', background: currentPage === 1 ? '#f3f4f6' : 'white', cursor: currentPage === 1 ? 'not-allowed' : 'pointer' }}
          >
            이전
          </button>
          <span style={{ padding: '6px 12px' }}>{currentPage} / {totalPages}</span>
          <button 
            disabled={currentPage === totalPages} 
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            style={{ padding: '6px 12px', border: '1px solid #ccc', borderRadius: '4px', background: currentPage === totalPages ? '#f3f4f6' : 'white', cursor: currentPage === totalPages ? 'not-allowed' : 'pointer' }}
          >
            다음
          </button>
        </div>
      )}

      {/* 3. 거래 내역 (History) */}
      <div className="portfolio-header" style={{ marginTop: '20px' }}>
        <h2>Virtual Trade History (종료된 매매 내역)</h2>
      </div>

      <div style={{ overflowX: 'auto', width: '100%' }}>
        <table className="portfolio-table">
          <thead>
            <tr>
              <th>Ticker</th>
              <th>Setup</th>
              <th>Score</th>
              <th>Entry / Exit Price</th>
              <th>Profit Rate (%)</th>
              <th>SPY (Entry ➔ Exit)</th>
              <th>QQQ (Entry ➔ Exit)</th>
              <th>Dates</th>
              <th>Exit Reason</th>
            </tr>
          </thead>
          <tbody>
            {(virtualHistory || []).length === 0 ? (
              <tr><td colSpan={9} className="no-data">종료된 가상 거래 내역이 없습니다.</td></tr>
            ) : paginatedHistory.map((trade: any, idx: number) => {
              const spyChange = trade.spy_entry && trade.spy_exit ? ((trade.spy_exit - trade.spy_entry) / trade.spy_entry * 100).toFixed(2) : '-';
              const qqqChange = trade.qqq_entry && trade.qqq_exit ? ((trade.qqq_exit - trade.qqq_entry) / trade.qqq_entry * 100).toFixed(2) : '-';
              return (
              <tr key={`history-${trade.ticker}-${idx}`}>
                <td className="ticker-col">{trade.ticker}</td>
                <td><span className="strategy-badge">{trade.setup || trade.strategy || '-'}</span></td>
                <td>{trade.factor_score || '-'}</td>
                <td>${(trade.entry_price || 0).toFixed(2)} ➔ ${(trade.exit_price || 0).toFixed(2)}</td>
                <td className={(trade.profit_rate || 0) > 0 ? 'profit-text' : (trade.profit_rate || 0) < 0 ? 'loss-text' : ''}>
                  {(trade.profit_rate || 0) > 0 ? '+' : ''}{(trade.profit_rate || 0).toFixed(2)}%
                </td>
                <td style={{ fontSize: '0.85rem' }}>
                  {trade.spy_entry ? `${trade.spy_entry.toFixed(1)} ➔ ${trade.spy_exit?.toFixed(1) || '-'}` : '-'}
                  {spyChange !== '-' && <span style={{ marginLeft: '4px', color: parseFloat(spyChange) > 0 ? '#10b981' : '#ef4444' }}>({spyChange}%)</span>}
                </td>
                <td style={{ fontSize: '0.85rem' }}>
                  {trade.qqq_entry ? `${trade.qqq_entry.toFixed(1)} ➔ ${trade.qqq_exit?.toFixed(1) || '-'}` : '-'}
                  {qqqChange !== '-' && <span style={{ marginLeft: '4px', color: parseFloat(qqqChange) > 0 ? '#10b981' : '#ef4444' }}>({qqqChange}%)</span>}
                </td>
                <td style={{ fontSize: '0.85rem' }}>{trade.entry_date} ~ {trade.exit_date}</td>
                <td style={{ fontSize: '0.85rem' }}>{trade.exit_reason}</td>
              </tr>
            )})}
          </tbody>
        </table>
      </div>

      {historyTotalPages > 1 && (
        <div className="pagination" style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '20px' }}>
          <button 
            disabled={historyPage === 1} 
            onClick={() => setHistoryPage(p => Math.max(1, p - 1))}
            style={{ padding: '6px 12px', border: '1px solid #ccc', borderRadius: '4px', background: historyPage === 1 ? '#f3f4f6' : 'white', cursor: historyPage === 1 ? 'not-allowed' : 'pointer' }}
          >
            이전
          </button>
          <span style={{ padding: '6px 12px' }}>{historyPage} / {historyTotalPages}</span>
          <button 
            disabled={historyPage === historyTotalPages} 
            onClick={() => setHistoryPage(p => Math.min(historyTotalPages, p + 1))}
            style={{ padding: '6px 12px', border: '1px solid #ccc', borderRadius: '4px', background: historyPage === historyTotalPages ? '#f3f4f6' : 'white', cursor: historyPage === historyTotalPages ? 'not-allowed' : 'pointer' }}
          >
            다음
          </button>
        </div>
      )}

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
