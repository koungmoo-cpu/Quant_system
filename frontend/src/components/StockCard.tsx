import React, { useState } from 'react';
import { StockItem, useStore } from '../store/useStore';
import './StockCard.css';

interface Props {
  stock: StockItem;
}

const StockCard: React.FC<Props> = ({ stock }) => {
  const [expanded, setExpanded] = useState(false);
  const [livePrice, setLivePrice] = useState<number | null>(null);
  const [briefingData, setBriefingData] = useState<StockItem | null>(null);
  const [isLoadingBriefing, setIsLoadingBriefing] = useState(false);

  const handleExpand = async () => {
    const newExpanded = !expanded;
    setExpanded(newExpanded);

    if (newExpanded && !briefingData) {
      const summaryStr = (stock.summary || []).join(' ');
      const needsBriefing = summaryStr.includes('대시보드 상단') || summaryStr.includes('스캐너 자동 탐지') || (stock.summary || []).length <= 2;
      
      if (needsBriefing) {
        setIsLoadingBriefing(true);
        try {
          const API_BASE = 'https://ai-stock-backend-108832568469.asia-northeast3.run.app';
          const res = await fetch(`${API_BASE}/api/analyze/${stock.ticker}`);
          if (res.ok) {
            const data = await res.json();
            setBriefingData(data);
          }
        } catch(e) {
          console.error(e);
        } finally {
          setIsLoadingBriefing(false);
        }
      }
    }
  };
  
  const displayStock = { ...stock, ...(briefingData || {}) };
  
  React.useEffect(() => {
    if (displayStock.currentPrice === 0 && !livePrice) {
      const fetchPrice = async () => {
        try {
          const API_BASE = 'https://ai-stock-backend-108832568469.asia-northeast3.run.app';
          const res = await fetch(`${API_BASE}/api/quote/${displayStock.ticker}`);
          const data = await res.json();
          if (data.price) {
            setLivePrice(data.price);
          }
        } catch (e) {
          console.error(e);
        }
      };
      fetchPrice();
    }
  }, [displayStock.ticker, displayStock.currentPrice, livePrice]);


  const { watchlist, toggleWatchlist, removeTicker } = useStore();
  const isStarred = watchlist.includes(displayStock.ticker);

  const getActionColor = (action: string) => {
    if (action === 'BUY') return '#10b981'; // Green
    if (action === 'SELL') return '#ef4444'; // Red
    return '#f59e0b'; // Orange
  };

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation(); // 아코디언이 열리는 것을 방지
    toggleWatchlist(displayStock.ticker);
  };

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation();
    removeTicker(displayStock.ticker);
  };

  // calculate D-Day
  let earningsBadge = null;
  if (displayStock.earningsDate) {
    try {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      const eDate = new Date(displayStock.earningsDate);
      eDate.setHours(0, 0, 0, 0);
      const diffTime = eDate.getTime() - today.getTime();
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays >= 0 && diffDays <= 60) {
        const dDayStr = diffDays === 0 ? "D-Day" : `D-${diffDays}`;
        earningsBadge = (
          <span style={{ marginLeft: '8px', fontSize: '0.75rem', padding: '2px 6px', backgroundColor: '#e0e7ff', color: '#4338ca', borderRadius: '4px', fontWeight: 'bold' }}>
            🗓️ Earning {dDayStr}
          </span>
        );
      }
    } catch (e) {
      // safely ignore
    }
  }

  return (
    <div className={`stock-card ${displayStock.action === 'BUY' ? 'highlight-buy' : ''} ${(displayStock.strategy.includes('Power Play') || (displayStock.score !== undefined && displayStock.score >= 15)) ? 'highlight-power-play' : ''}`}>
      <div className="stock-card-header" onClick={handleExpand}>
        
        {/* === 좌측/모바일 상단: 기본 정보 === */}
        <div className="stock-info">
          <div className="ticker-row">
            <span className="ticker">
              <span className="star-toggle" onClick={handleToggle}>
                {isStarred ? '⭐' : '☆'}
              </span>
              {' '}{displayStock.ticker}
              
              {displayStock.is_new === true ? (
                <span style={{ marginLeft: '8px', padding: '0.125rem 0.5rem', fontSize: '0.75rem', fontWeight: 700, borderRadius: '9999px', backgroundColor: 'rgba(244, 63, 94, 0.2)', color: '#f43f5e', border: '1px solid rgba(244, 63, 94, 0.3)', animation: 'pulse 2s infinite' }}>
                  🔥 NEW
                </span>
              ) : (
                <span style={{ marginLeft: '8px', padding: '0.125rem 0.5rem', fontSize: '0.75rem', fontWeight: 500, borderRadius: '9999px', backgroundColor: 'rgba(51, 65, 85, 0.5)', color: '#cbd5e1', border: '1px solid #475569' }}>
                  ⏳ {displayStock.streak_days || 2}일차
                </span>
              )}

              {displayStock.score !== undefined && displayStock.score > 0 && (
                <span style={{ marginLeft: '10px', fontSize: '0.85rem', padding: '2px 8px', backgroundColor: displayStock.score >= 15 ? '#fef08a' : '#f1f5f9', color: displayStock.score >= 15 ? '#854d0e' : '#475569', borderRadius: '12px', fontWeight: 'bold', boxShadow: displayStock.score >= 15 ? '0 0 8px rgba(250, 204, 21, 0.6)' : 'none' }}>
                  {displayStock.score >= 15 ? '🔥 ' : ''}🏆 {displayStock.score}/20
                </span>
              )}
            </span>
            <span className="action-badge mobile-only" style={{ backgroundColor: getActionColor(displayStock.action) }}>
              {displayStock.action}
            </span>
            <span className="remove-btn mobile-only" onClick={handleRemove} title="대시보드에서 삭제">🗑️</span>
          </div>
          <span className="strategy">
            {displayStock.name && <span className="company-name">{displayStock.name} • </span>}
            <span className="strategy-badge" style={(displayStock.strategy.includes('Power Play') || (displayStock.score !== undefined && displayStock.score >= 15)) ? { backgroundColor: '#fef3c7', color: '#b45309', fontWeight: 'bold' } : {}}>
              {(displayStock.strategy.includes('Power Play') || (displayStock.score !== undefined && displayStock.score >= 15)) ? '🚀 ' : ''}{displayStock.strategy}
            </span>
            {earningsBadge}
          </span>

          {/* 모바일 전용: 진입가/손절가/현재가 좌우 배치 */}
          <div className="mobile-price-row mobile-only">
            {displayStock.entryPivot ? (
              <div className="mobile-price-item">
                <span className="m-label">Entry</span>
                <span className="m-value text-blue">${(displayStock.entryPivot || 0).toFixed(2)}</span>
              </div>
            ) : (
              <div className="mobile-price-item">
                <span className="m-label">Entry</span>
                <span className="m-value">-</span>
              </div>
            )}
            <div className="mobile-price-item">
              <span className="m-label">Stop Loss</span>
              <span className="m-value text-red">${(displayStock.stopLoss || 0).toFixed(2)}</span>
            </div>
          </div>
          {displayStock.detected_at && (
            <div style={{ fontSize: '0.75rem', color: '#6b7280', marginTop: '6px' }} className="mobile-only">
              🕒 포착 시각: {displayStock.detected_at.split(' ')[1] || displayStock.detected_at} (당시 주가: ${displayStock.detected_price?.toFixed(2)})
            </div>
          )}
          <div className="mobile-expand mobile-only">
            <span>{expanded ? '▲ 접기' : '▼ AI 브리핑 및 주문서 보기'}</span>
          </div>
        </div>

        {/* === 우측/PC 전용: 액션 및 가격 === */}
        <div className="stock-action desktop-only">
          <span className="action-badge" style={{ backgroundColor: getActionColor(displayStock.action) }}>
            {displayStock.action}
          </span>
          {displayStock.entryPivot && (
            <span className="entry-pivot" style={{ fontSize: '0.9rem', color: '#6b7280', marginRight: '8px' }}>
              Entry: ${(displayStock.entryPivot || 0).toFixed(2)}
            </span>
          )}
          {displayStock.detected_at && (
             <span style={{ fontSize: '0.8rem', color: '#9ca3af', marginRight: '12px' }}>
               🕒 {displayStock.detected_at.split(' ')[1] || displayStock.detected_at} (포착가: ${displayStock.detected_price?.toFixed(2)})
             </span>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', justifyContent: 'center' }}>
            <span className="price">${(displayStock.currentPrice || livePrice || 0).toFixed(2)}</span>
            {displayStock.change_pct !== undefined && (
              <span style={{ fontSize: '0.8rem', color: displayStock.change_pct >= 0 ? '#ef4444' : '#3b82f6', fontWeight: 'bold' }}>
                {displayStock.change_pct > 0 ? '+' : ''}{displayStock.change_pct}%
              </span>
            )}
          </div>
          <span className="expand-icon">{expanded ? '▲' : '▼'}</span>
          <span className="remove-btn" onClick={handleRemove} title="대시보드에서 삭제">🗑️</span>
        </div>
      </div>
      
      {expanded && (
        <div className="stock-card-details">
          <div className="ai-briefing">
            <h4>🤖 Gemini AI Briefing</h4>
            {isLoadingBriefing ? (
              <div style={{ padding: '20px', textAlign: 'center', color: '#64748b' }}>
                <div className="loading-spinner" style={{ margin: '0 auto 10px auto', width: '24px', height: '24px', border: '3px solid #cbd5e1', borderTop: '3px solid #3b82f6', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
                AI 심층 분석을 가져오는 중입니다...
              </div>
            ) : (
              <ul>
                {displayStock.summary.map((line, idx) => (
                  <li key={idx}>{line}</li>
                ))}
              </ul>
            )}
          </div>

          {!isLoadingBriefing && displayStock.action === 'BUY' && displayStock.entryPivot && (
            <div className="order-ticket" style={{ marginTop: '16px', marginBottom: '16px', padding: '16px', backgroundColor: '#f8fafc', borderRadius: '8px', borderLeft: '4px solid #3b82f6', boxShadow: '0 1px 3px rgba(0,0,0,0.05)' }}>
              <h4 style={{ margin: '0 0 12px 0', color: '#1e293b', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                🤖 자동감시주문 셋팅 가이드
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.95rem', color: '#334155' }}>
                <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '4px' }}>
                  <span>🔵 신규 매수 조건: 주가가</span>
                  <strong style={{ backgroundColor: '#dbeafe', color: '#1d4ed8', padding: '2px 6px', borderRadius: '4px', fontSize: '1.05rem', margin: '0 4px' }}>
                    ${(displayStock.entryPivot || 0).toFixed(2)}
                  </strong>
                  <span>이상으로 상승(돌파)할 때 ➔ <b>시장가 매수</b></span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: '4px' }}>
                  <span>🔴 리스크 관리(손절): 매수 후, 주가가</span>
                  <strong style={{ backgroundColor: '#fee2e2', color: '#b91c1c', padding: '2px 6px', borderRadius: '4px', fontSize: '1.05rem', margin: '0 4px' }}>
                    ${(displayStock.stopLoss || 0).toFixed(2)}
                  </strong>
                  <span>이하로 하락(이탈)할 때 ➔ <b>시장가 전량 매도</b></span>
                </div>
              </div>
            </div>
          )}

          {!isLoadingBriefing && (
            <div className="price-targets">
              <div className="target">
                <span className="label">Target Price</span>
                <span className="value success">${(displayStock.targetPrice || 0).toFixed(2)}</span>
              </div>
              <div className="target">
                <span className="label">Stop Loss</span>
                <span className="value danger">${(displayStock.stopLoss || 0).toFixed(2)}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default StockCard;
