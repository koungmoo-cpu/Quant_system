import React, { useState, useEffect } from 'react';
import { useStore, OwnedAsset } from '../store/useStore';
import './PortfolioTable.css';

const PortfolioTable: React.FC = () => {
  const { ownedAssets, fetchOwnedAssets, updateOwnedAsset, fetchPerformanceData } = useStore();
  const [closingAsset, setClosingAsset] = useState<OwnedAsset | null>(null);
  const [closeForm, setCloseForm] = useState({ sellPrice: 0, sellQuantity: 0, exitReason: '10MA 이탈 (Trailing Stop)' });

  const handleCloseInit = (asset: OwnedAsset) => {
    setClosingAsset(asset);
    setCloseForm({ sellPrice: asset.CurrentPrice || asset.AvgPrice || 0, sellQuantity: asset.Quantity, exitReason: '10MA 이탈 (Trailing Stop)' });
  };

  const submitClose = async () => {
    if (!closingAsset) return;
    if (closeForm.sellQuantity <= 0 || closeForm.sellQuantity > closingAsset.Quantity) {
      alert(`매도 수량은 1부터 ${closingAsset.Quantity} 사이여야 합니다.`);
      return;
    }
    try {
      const API_BASE = 'https://ai-stock-backend-108832568469.asia-northeast3.run.app';
      const res = await fetch(`${API_BASE}/api/portfolio/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: closingAsset.Ticker,
          sell_price: closeForm.sellPrice,
          sell_quantity: closeForm.sellQuantity,
          exit_reason: closeForm.exitReason,
          strategy: closingAsset.Strategy || 'Manual'
        })
      });
      if (res.ok) {
        setClosingAsset(null);
        await fetchOwnedAssets();
        // optionally refresh performanceData (pass initial capital if we had it, but default is fine)
        await fetchPerformanceData(10000000); 
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail || 'Failed to close position'}`);
      }
    } catch(e) {
      console.error(e);
      alert('Network error');
    }
  };

  const [editingTicker, setEditingTicker] = useState<string | null>(null);
  const [editForm, setEditForm] = useState<OwnedAsset | null>(null);
  const [isAdding, setIsAdding] = useState(false);

  useEffect(() => {
    fetchOwnedAssets();
  }, [fetchOwnedAssets]);

  const handleEdit = (asset: OwnedAsset) => {
    setEditingTicker(asset.Ticker);
    setEditForm({ ...asset });
  };

  const handleSave = async () => {
    if (editForm) {
      if (!editForm.Ticker.trim()) {
        alert("티커를 입력해주세요.");
        return;
      }
      if (editForm.Quantity <= 0) {
        alert("수량은 1 이상이어야 합니다.");
        return;
      }
      await updateOwnedAsset(editForm);
      setEditingTicker(null);
      setEditForm(null);
      setIsAdding(false);
    }
  };

  const handleDelete = async (ticker: string) => {
    if (window.confirm(`Are you sure you want to delete ${ticker} from your portfolio?`)) {
      await updateOwnedAsset({ Ticker: ticker, Quantity: 0, AvgPrice: 0, PurchaseDate: '' });
    }
  };

  const handleAdd = () => {
    setIsAdding(true);
    setEditForm({ Ticker: '', Quantity: 0, AvgPrice: 0, PurchaseDate: new Date().toISOString().split('T')[0] });
  };


  const handleExport = () => {
    window.open('https://ai-stock-backend-108832568469.asia-northeast3.run.app/api/portfolio/export', '_blank');
  };

  const totalInvested = ownedAssets.reduce((sum, asset) => sum + ((asset.AvgPrice || 0) * (asset.Quantity || 0)), 0);
  const totalCurrentValue = ownedAssets.reduce((sum, asset) => sum + ((asset.CurrentPrice || 0) * (asset.Quantity || 0)), 0);
  const totalUnrealizedProfit = totalCurrentValue - totalInvested;
  const totalReturnRate = totalInvested > 0 ? (totalUnrealizedProfit / totalInvested) * 100 : 0;

  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 15;
  const totalPages = Math.ceil(ownedAssets.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedAssets = ownedAssets.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  return (
    <div className="portfolio-container">
      {closingAsset && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1000 }}>
          <div className="modal-content" style={{ backgroundColor: 'white', padding: '24px', borderRadius: '8px', width: '400px', maxWidth: '90%' }}>
            <h3 style={{ marginTop: 0 }}>{closingAsset.Ticker} 포지션 청산 (매도)</h3>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', marginBottom: '4px' }}>매도 가격 ($)</label>
              <input type="number" step="0.01" value={closeForm.sellPrice} onChange={(e) => setCloseForm({...closeForm, sellPrice: parseFloat(e.target.value) || 0})} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
            </div>
            <div style={{ marginBottom: '12px' }}>
              <label style={{ display: 'block', marginBottom: '4px' }}>매도 수량 (보유: {closingAsset.Quantity})</label>
              <input type="number" value={closeForm.sellQuantity} onChange={(e) => setCloseForm({...closeForm, sellQuantity: parseInt(e.target.value) || 0})} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }} />
            </div>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '4px' }}>청산 사유</label>
              <select value={closeForm.exitReason} onChange={(e) => setCloseForm({...closeForm, exitReason: e.target.value})} style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}>
                <option value="10MA 이탈 (Trailing Stop)">10MA 이탈 (Trailing Stop)</option>
                <option value="20MA 이탈 (비중 축소/손절)">20MA 이탈 (비중 축소/손절)</option>
                <option value="목표가 달성 (익절)">목표가 달성 (익절)</option>
                <option value="기타 사유">기타 사유</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button onClick={() => setClosingAsset(null)} style={{ padding: '8px 16px', border: '1px solid #ccc', background: 'white', borderRadius: '4px', cursor: 'pointer' }}>취소</button>
              <button onClick={submitClose} style={{ padding: '8px 16px', border: 'none', background: '#ef4444', color: 'white', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>청산 확정</button>
            </div>
          </div>
        </div>
      )}

      <div className="portfolio-header">
        <h2>My Portfolio 💼</h2>
        <div style={{display: 'flex', gap: '10px'}}>
          <button className="export-btn" onClick={handleExport} style={{background: '#10b981', color: 'white', border: 'none', padding: '8px 16px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}>⬇️ 엑셀(CSV) 다운로드</button>
          <button className="add-btn" onClick={handleAdd} disabled={isAdding}>+ Add Asset</button>
        </div>
      </div>

      <div className="portfolio-summary">
        <div className="summary-item">
          <span className="summary-label">총 투자 금액:</span>
          <span className="summary-value">${totalInvested.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">총 평가 금액:</span>
          <span className="summary-value">${totalCurrentValue.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">총 평가 손익:</span>
          <span className={`summary-value ${totalUnrealizedProfit > 0 ? 'profit-text' : totalUnrealizedProfit < 0 ? 'loss-text' : ''}`}>
            {totalUnrealizedProfit > 0 ? '+$' : totalUnrealizedProfit < 0 ? '-$' : '$'}{Math.abs(totalUnrealizedProfit).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
            {' '}({totalReturnRate > 0 ? '+' : ''}{totalReturnRate.toFixed(2)}%)
          </span>
        </div>
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
              <th>Trailing Stop (10MA)</th>
              <th>Risk Guide (20MA)</th>
              <th>Return (%)</th>
              <th>Total Invested</th>
              <th>Profit/Loss</th>
              <th>Purchase Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isAdding && editForm && (
              <tr>
                <td>
                  <input 
                    type="text" 
                    value={editForm.Ticker} 
                    onChange={e => setEditForm({ ...editForm, Ticker: e.target.value.toUpperCase() })} 
                    placeholder="e.g. AAPL"
                  />
                </td>
                <td>
                  <select 
                    value={editForm.Strategy || 'Manual'} 
                    onChange={e => setEditForm({ ...editForm, Strategy: e.target.value })} 
                  >
                    <option value="Manual">Manual</option>
                    <option value="Breakout">Breakout</option>
                    <option value="Power Play">Power Play</option>
                    <option value="Episodic Pivot">Episodic Pivot</option>
                    <option value="Pullback">Pullback</option>
                    <option value="Reversal">Reversal</option>
                    <option value="Trend Following">Trend Following</option>
                  </select>
                </td>
                <td>
                  <input 
                    type="number" 
                    value={editForm.Quantity} 
                    onChange={e => setEditForm({ ...editForm, Quantity: parseInt(e.target.value) || 0 })} 
                  />
                </td>
                <td>
                  <input 
                    type="number" 
                    value={editForm.AvgPrice} 
                    onChange={e => setEditForm({ ...editForm, AvgPrice: parseFloat(e.target.value) || 0 })} 
                  />
                </td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>-</td>
                <td>
                  <input 
                    type="date" 
                    value={editForm.PurchaseDate} 
                    onChange={e => setEditForm({ ...editForm, PurchaseDate: e.target.value })} 
                  />
                </td>
                <td>
                  <button className="save-btn" onClick={handleSave}>Save</button>
                  <button className="cancel-btn" onClick={() => setIsAdding(false)}>Cancel</button>
                </td>
              </tr>
            )}

            {ownedAssets.length === 0 && !isAdding ? (
              <tr>
                <td colSpan={10} className="no-data">No assets in portfolio yet.</td>
              </tr>
            ) : (
              paginatedAssets.map((asset, idx) => {
                const currentPrice = asset.CurrentPrice || 0;
                const avgPrice = asset.AvgPrice || 0;
                const quantity = asset.Quantity || 0;
                const totalInvested = avgPrice * quantity;
                const unrealizedProfit = currentPrice > 0 ? (currentPrice - avgPrice) * quantity : 0;
                const returnRate = avgPrice > 0 && currentPrice > 0 ? ((currentPrice - avgPrice) / avgPrice) * 100 : 0;

                return (
                <tr key={asset.Ticker || `empty-${idx}`}>
                  {editingTicker === asset.Ticker && editForm ? (
                    <>
                      <td>{asset.Ticker}</td>
                      <td>
                        <select 
                          value={editForm.Strategy || 'Manual'} 
                          onChange={e => setEditForm({ ...editForm, Strategy: e.target.value })} 
                        >
                          <option value="Manual">Manual</option>
                          <option value="Breakout">Breakout</option>
                          <option value="Power Play">Power Play</option>
                          <option value="Episodic Pivot">Episodic Pivot</option>
                          <option value="Pullback">Pullback</option>
                          <option value="Reversal">Reversal</option>
                          <option value="Trend Following">Trend Following</option>
                        </select>
                      </td>
                      <td>
                        <input 
                          type="number" 
                          value={editForm.Quantity} 
                          onChange={e => setEditForm({ ...editForm, Quantity: parseInt(e.target.value) || 0 })} 
                        />
                      </td>
                      <td>
                        <input 
                          type="number" 
                          value={editForm.AvgPrice} 
                          onChange={e => setEditForm({ ...editForm, AvgPrice: parseFloat(e.target.value) || 0 })} 
                        />
                      </td>
                      <td>${currentPrice.toFixed(2)}</td>
                      <td>-</td>
                      <td>-</td>
                      <td>-</td>
                      <td>-</td>
                      <td>
                        <input 
                          type="date" 
                          value={editForm.PurchaseDate} 
                          onChange={e => setEditForm({ ...editForm, PurchaseDate: e.target.value })} 
                        />
                      </td>
                      <td>
                        <button className="save-btn" onClick={handleSave}>Save</button>
                        <button className="cancel-btn" onClick={() => setEditingTicker(null)}>Cancel</button>
                      </td>
                    </>
                  ) : (
                    <>
                      <td className="ticker-col">{asset.Ticker}</td>
                      <td>
                        <span className="strategy-badge" style={{ fontSize: '0.75rem', padding: '2px 6px' }}>
                          {asset.Strategy || 'Manual'}
                        </span>
                      </td>
                      <td>{asset.Quantity}</td>
                      <td>${avgPrice.toFixed(2)}</td>
                      <td>${currentPrice.toFixed(2)}</td>
                      <td style={{ 
                          fontWeight: 'bold', 
                          color: (asset.trailingStop && currentPrice < asset.trailingStop) ? '#ef4444' : '#10b981',
                          backgroundColor: (asset.trailingStop && currentPrice < asset.trailingStop) ? '#fee2e2' : 'transparent',
                          padding: '4px',
                          borderRadius: '4px'
                        }}>
                        {asset.trailingStop ? `$${asset.trailingStop.toFixed(2)}` : '-'}
                        {asset.trailingStop && currentPrice < asset.trailingStop && ' 🚨이탈'}
                      </td>
                      <td style={{ fontSize: '0.85rem', color: '#4b5563' }}>
                        {asset.ma20 ? (currentPrice < asset.ma20 ? (
                           <span style={{color: '#ef4444', fontWeight: 'bold'}}>20MA 이탈 (비중 축소)</span>
                        ) : (
                           <span style={{color: '#10b981', fontWeight: 'bold'}}>안정적 (20MA 지지)</span>
                        )) : '-'}
                      </td>
                      <td className={returnRate > 0 ? 'profit-text' : returnRate < 0 ? 'loss-text' : ''}>
                        {returnRate > 0 ? '+' : ''}{returnRate.toFixed(2)}%
                      </td>
                      <td>${totalInvested.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}</td>
                      <td className={unrealizedProfit > 0 ? 'profit-text' : unrealizedProfit < 0 ? 'loss-text' : ''}>
                        {unrealizedProfit > 0 ? '+$' : unrealizedProfit < 0 ? '-$' : '$'}{Math.abs(unrealizedProfit).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                      </td>
                      <td>{asset.PurchaseDate}</td>
                      <td style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
                        <button className="edit-btn" onClick={() => handleEdit(asset)} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>Edit</button>
                        <button className="delete-btn" onClick={() => handleDelete(asset.Ticker)} style={{ padding: '4px 8px', fontSize: '0.8rem' }}>Delete</button>
                        <button className="close-btn" onClick={() => handleCloseInit(asset)} style={{ padding: '4px 8px', fontSize: '0.8rem', backgroundColor: '#8b5cf6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}>매도/청산</button>
                      </td>
                    </>
                  )}
                </tr>
              )})
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="pagination" style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '20px' }}>
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
    </div>
  );
};

export default PortfolioTable;
