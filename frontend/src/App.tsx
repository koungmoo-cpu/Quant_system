import React, { useState, useEffect } from 'react'
import { useStore } from './store/useStore'
import StockCard from './components/StockCard'
import SectorHeatmap from './components/SectorHeatmap'
import TradingPlaybook from './components/TradingPlaybook'
import PortfolioTable from './components/PortfolioTable'
import PerformanceStats from './components/PerformanceStats'
import VirtualTrading from './components/VirtualTrading'
import './App.css'

function App() {
  const { 
    portfolio, 
    fetchWatchlist, 
    searchQuery, 
    setSearchQuery, 
    watchlist, 
    isAnalyzing,
    analyzeTickerFast,
    initializeFavorites, 
    fetchOwnedAssets, 
    isScanning, 
    runGlobalScan, 
    scanTimestamp, 
    detectedSetups, 
    fetchDetectedSetups,
    marketStatus,
    fetchMarketStatus,
    bulkRemoveWatchlist,
    analyzedResult,
    setAnalyzedResult
  } = useStore()
  
  const [isPlaybookOpen, setIsPlaybookOpen] = useState(false);
  const [mainView, setMainView] = useState<'SCANNER' | 'MY_SPACE'>('SCANNER');
  const [mySpaceTab, setMySpaceTab] = useState<'WATCHLIST' | 'PORTFOLIO' | 'STATISTICS' | 'VIRTUAL'>('WATCHLIST');

  // Pagination for Watchlist tab
  const [currentPage, setCurrentPage] = useState(1);
  const ITEMS_PER_PAGE = 11;
  const [selectedWatchlistItems, setSelectedWatchlistItems] = useState<Set<string>>(new Set());

  const handleAnalyze = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      analyzeTickerFast(searchQuery.trim());
    }
  };

  useEffect(() => {
    fetchWatchlist();
    initializeFavorites();
    fetchOwnedAssets();
    fetchDetectedSetups();
    fetchMarketStatus();
  }, [fetchWatchlist, initializeFavorites, fetchOwnedAssets, fetchDetectedSetups, fetchMarketStatus]);

  // Merge detected setups with portfolio BUY setups
  const scannerList = React.useMemo(() => {
    const map = new Map<string, any>();
    if (portfolio) {
      portfolio.filter(p => p.action === 'BUY' && (p.score || 0) >= 15).forEach(p => map.set(p.ticker, p));
    }
    if (detectedSetups && detectedSetups.items) {
      detectedSetups.items.forEach((p: any) => {
        const mapped = {
          ticker: p.ticker,
          name: p.name || p.ticker,
          strategy: p.strategy,
          action: p.signal || 'BUY',
          summary: p.ai_summary ? p.ai_summary.split('\n') : [],
          stopLoss: p.stop_loss || 0,
          targetPrice: p.entry_pivot ? p.entry_pivot * 1.15 : 0,
          currentPrice: p.current_price || p.detected_price || 0,
          entryPivot: p.entry_pivot,
          score: p.score,
          detected_at: p.detected_at,
          detected_price: p.detected_price,
          is_new: p.is_new,
          streak_days: p.streak_days
        };
        map.set(p.ticker, mapped);
      });
    }
    const merged = Array.from(map.values());
    merged.sort((a, b) => (b.score || 0) - (a.score || 0));
    
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const exactMatch = portfolio.find(p => p.ticker.toLowerCase() === q);
      const filtered = merged.filter(m => m.ticker.toLowerCase().includes(q) || m.name?.toLowerCase().includes(q));
      if (exactMatch && !filtered.find(f => f.ticker === exactMatch.ticker)) {
         filtered.unshift(exactMatch);
      }
      return filtered;
    }
    return merged;
  }, [portfolio, detectedSetups, searchQuery]);

  // Watchlist items
  const watchlistPortfolio = React.useMemo(() => {
    let filtered = portfolio.filter(p => watchlist.includes(p.ticker));
    filtered.sort((a, b) => {
      if (a.action === 'BUY' && b.action !== 'BUY') return -1;
      if (a.action !== 'BUY' && b.action === 'BUY') return 1;
      return (b.score || 0) - (a.score || 0);
    });
    return filtered;
  }, [portfolio, watchlist]);

  const totalPages = Math.ceil(watchlistPortfolio.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedWatchlist = watchlistPortfolio.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.checked) {
       const newSet = new Set(selectedWatchlistItems);
       paginatedWatchlist.forEach(stock => newSet.add(stock.ticker));
       setSelectedWatchlistItems(newSet);
    } else {
       const newSet = new Set(selectedWatchlistItems);
       paginatedWatchlist.forEach(stock => newSet.delete(stock.ticker));
       setSelectedWatchlistItems(newSet);
    }
  };

  const handleSelectItem = (ticker: string, checked: boolean) => {
    const newSet = new Set(selectedWatchlistItems);
    if (checked) newSet.add(ticker);
    else newSet.delete(ticker);
    setSelectedWatchlistItems(newSet);
  };

  const handleBulkRemove = async () => {
    const tickers = Array.from(selectedWatchlistItems);
    if (tickers.length > 0) {
      if (window.confirm(`선택한 ${tickers.length}개 종목을 즐겨찾기에서 제거하시겠습니까?`)) {
        await bulkRemoveWatchlist(tickers);
        setSelectedWatchlistItems(new Set());
      }
    }
  };

  return (
    <div className="app-container" style={{ paddingBottom: '80px' }}>
      <header className="header" style={{ position: 'relative', marginBottom: '16px' }}>
        <h1>AI Stock Trading Dashboard</h1>
        <p>Minervini & Qullamaggie AI Agent</p>
        <button 
          className="help-icon-btn" 
          onClick={() => setIsPlaybookOpen(true)}
          title="실전 매매 매뉴얼 보기"
          style={{ position: 'absolute', top: '10px', right: '10px', background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer' }}
        >
          ❓
        </button>
      </header>
      
      <TradingPlaybook isOpen={isPlaybookOpen} onClose={() => setIsPlaybookOpen(false)} />

      <div className="main-nav-segmented">
        <button 
          className={mainView === 'SCANNER' ? 'active' : ''}
          onClick={() => setMainView('SCANNER')}
        >
          🔍 시장 스캐너
        </button>
        <button 
          className={mainView === 'MY_SPACE' ? 'active' : ''}
          onClick={() => setMainView('MY_SPACE')}
        >
          💼 마이 스페이스
        </button>
      </div>

      {mainView === 'SCANNER' ? (
        <div className="scanner-view">
          {marketStatus && (
             <div className={`market-status-banner status-${(marketStatus.status || '').toLowerCase()}`}>
               <div className="status-indicator"></div>
               <div>
                 <h3>Market Status: {marketStatus.status}</h3>
                 <p>Recommended Exposure: <strong>{marketStatus.recommended_exposure}%</strong></p>
               </div>
             </div>
          )}

          <SectorHeatmap />

          <div className="search-bar-container">
            <form onSubmit={handleAnalyze} className="search-form">
              <input 
                type="text" 
                placeholder="티커 검색 (예: TSLA) 후 Enter로 빠른 스캔" 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                disabled={isAnalyzing || isScanning}
              />
              <button type="submit" disabled={isAnalyzing || isScanning} className="analyze-btn" style={{ backgroundColor: '#10b981' }}>
                {isAnalyzing ? '분석 중...' : '🔍 종목 스캔'}
              </button>
            </form>
            
          </div>
          

          {analyzedResult && (
            <div className="analyzed-result-container" style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ backgroundColor: '#fef08a', color: '#854d0e', padding: '6px 12px', borderRadius: '16px', fontSize: '0.9rem', fontWeight: 'bold' }}>
                  🔍 개별 종목 분석 결과
                </span>
                <button 
                  onClick={() => setAnalyzedResult(null)} 
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1rem' }}
                >
                  ✕ 닫기
                </button>
              </div>
              <StockCard stock={analyzedResult} />
            </div>
          )}

          <div className="detected-container">
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <span style={{ backgroundColor: '#e0e7ff', color: '#4338ca', padding: '6px 12px', borderRadius: '16px', fontSize: '0.9rem', fontWeight: 'bold' }}>
                🎯 S&P 500 포착 종목 (최근 완료: {detectedSetups?.last_scanned_at || scanTimestamp || '이력 없음'})
              </span>
            </div>
            
            <div className="stock-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {scannerList.length > 0 ? (
                scannerList.map((item: any, idx: number) => (
                  <StockCard key={`scanner-${item.ticker}-${idx}`} stock={item} />
                ))
              ) : (
                <div className="no-data">조건을 통과한 매수 셋업이 없습니다.</div>
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="my-space-view">
          <div className="tabs" style={{ justifyContent: 'center' }}>
            <button className={mySpaceTab === 'WATCHLIST' ? 'active' : ''} onClick={() => setMySpaceTab('WATCHLIST')}>⭐ 즐겨찾기</button>
            <button className={mySpaceTab === 'PORTFOLIO' ? 'active' : ''} onClick={() => setMySpaceTab('PORTFOLIO')}>💼 실전 포트폴리오</button>
            <button className={mySpaceTab === 'VIRTUAL' ? 'active' : ''} onClick={() => setMySpaceTab('VIRTUAL')}>🧪 가상 매매 (프워드)</button>
            <button className={mySpaceTab === 'STATISTICS' ? 'active' : ''} onClick={() => setMySpaceTab('STATISTICS')}>📈 성과 요약</button>
          </div>

          {mySpaceTab === 'WATCHLIST' && (
             <>
               <div style={{ textAlign: 'center', marginBottom: '16px' }}>
                 <button 
                   onClick={runGlobalScan} 
                   disabled={isScanning || isAnalyzing}
                   className="scan-btn"
                   style={{ marginBottom: '12px' }}
                 >
                   {isScanning ? '⏳ 관심종목 스캔 중...' : '🔍 관심종목 전체 스캔'}
                 </button>
                 <div style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
                   🕒 전체 스캔 업데이트: {scanTimestamp || '이력 없음'}
                 </div>
               </div>
               <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', padding: '0 8px' }}>
                 <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 'bold' }}>
                   <input 
                     type="checkbox" 
                     style={{ transform: 'scale(1.3)', cursor: 'pointer' }}
                     checked={paginatedWatchlist.length > 0 && paginatedWatchlist.every(s => selectedWatchlistItems.has(s.ticker))}
                     onChange={handleSelectAll}
                   />
                   현재 페이지 전체 선택
                 </label>
                 {selectedWatchlistItems.size > 0 && (
                   <button 
                     style={{ backgroundColor: '#ef4444', color: 'white', border: 'none', padding: '6px 16px', borderRadius: '8px', fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 2px 4px rgba(239,68,68,0.2)' }}
                     onClick={handleBulkRemove}
                   >
                     선택 항목 제거 ({selectedWatchlistItems.size}개) 🗑️
                   </button>
                 )}
               </div>
               <div className="stock-list">
                  {paginatedWatchlist.length > 0 ? (
                    paginatedWatchlist.map(stock => (
                      <div key={stock.ticker} style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                        <div style={{ paddingTop: '22px', paddingLeft: '4px' }}>
                          <input 
                            type="checkbox" 
                            style={{ transform: 'scale(1.4)', cursor: 'pointer' }}
                            checked={selectedWatchlistItems.has(stock.ticker)}
                            onChange={(e) => handleSelectItem(stock.ticker, e.target.checked)}
                          />
                        </div>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <StockCard stock={stock} />
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="no-data">즐겨찾기에 등록된 종목이 없습니다. 스캐너에서 ⭐ 버튼을 눌러 추가해보세요.</div>
                  )}
               </div>
               {totalPages > 1 && (
                  <div className="pagination">
                    <button 
                      disabled={currentPage === 1} 
                      onClick={() => setCurrentPage(currentPage - 1)}
                      className="page-btn"
                    >
                      Previous
                    </button>
                    <span className="page-info">Page {currentPage} of {totalPages}</span>
                    <button 
                      disabled={currentPage === totalPages} 
                      onClick={() => setCurrentPage(currentPage + 1)}
                      className="page-btn"
                    >
                      Next
                    </button>
                  </div>
                )}
             </>
          )}

          {mySpaceTab === 'PORTFOLIO' && (
             <PortfolioTable />
          )}

          {mySpaceTab === 'STATISTICS' && (
             <PerformanceStats />
          )}

          {mySpaceTab === 'VIRTUAL' && (
             <VirtualTrading />
          )}
        </div>
      )}
      
      <div className="mobile-bottom-nav">
        <button 
          className={mainView === 'SCANNER' ? 'active' : ''}
          onClick={() => setMainView('SCANNER')}
        >
          <span style={{fontSize: '1.2rem'}}>🔍</span>
          <span>스캐너</span>
        </button>
        <button 
          className={mainView === 'MY_SPACE' ? 'active' : ''}
          onClick={() => setMainView('MY_SPACE')}
        >
          <span style={{fontSize: '1.2rem'}}>💼</span>
          <span>마이스페이스</span>
        </button>
      </div>
    </div>
  )
}

export default App
