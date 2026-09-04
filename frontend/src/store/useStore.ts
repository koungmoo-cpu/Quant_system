import { create } from 'zustand'

export interface StockItem {
  ticker: string;
  name?: string;
  strategy: string;
  action: 'BUY' | 'WAIT' | 'SELL';
  summary: string[];
  stopLoss: number;
  targetPrice: number;
  currentPrice: number;
  entryPivot?: number;
  score?: number;
  detected_at?: string;
  detected_price?: number;
  earningsDate?: string | null;
  is_new?: boolean;
  streak_days?: number;
  change_pct?: number;
}

export interface MarketStatus {
  status: 'Green' | 'Yellow' | 'Red' | string;
  recommended_exposure: number;
  last_updated: string;
}

export interface SectorItem {
  ticker: string;
  name: string;
  return_pct: number;
  current: number;
}

export interface OwnedAsset {
  Ticker: string;
  Quantity: number;
  AvgPrice: number;
  PurchaseDate: string;
  CurrentPrice?: number;
  trailingStop?: number;
  ma20?: number;
  Strategy?: string;
}

export interface PerformanceMetrics {
  total_trades: number;
  total_profit: number;
  win_rate: number;
  risk_reward_ratio: number;
  profit_factor: number;
  max_consecutive_losses: number;
  mdd: number;
  cagr: number;
  initial_capital: number;
}

export interface StrategyMetrics {
  [strategy: string]: {
    total_trades: number;
    total_profit: number;
    win_rate: number;
    risk_reward_ratio: number;
  };
}

export interface PerformanceData {
  total_metrics: PerformanceMetrics;
  strategy_metrics: StrategyMetrics;
}

interface TradingState {
  portfolio: StockItem[];
  setPortfolio: (portfolio: StockItem[]) => void;
  filter: 'ALL' | 'QULLAMAGGIE' | 'MINERVINI' | 'FAVORITES' | 'PORTFOLIO' | 'PERFORMANCE' | 'DETECTED';
  setFilter: (filter: 'ALL' | 'QULLAMAGGIE' | 'MINERVINI' | 'FAVORITES' | 'PORTFOLIO' | 'PERFORMANCE' | 'DETECTED') => void;
  currentPage: number;
  setCurrentPage: (page: number) => void;
  
  searchQuery: string;
  analyzedResult: StockItem | null;
  setAnalyzedResult: (item: StockItem | null) => void;
  setSearchQuery: (query: string) => void;

  watchlist: string[];
  fetchWatchlist: () => Promise<void>;
  toggleWatchlist: (ticker: string) => Promise<void>;
  
  isAnalyzing: boolean;
  analyzeTicker: (ticker: string) => Promise<void>;
  analyzeTickerFast: (ticker: string) => Promise<void>;
  
  isScanning: boolean;
  runGlobalScan: () => Promise<void>;
  
  removeTicker: (ticker: string) => void;
  bulkRemoveWatchlist: (tickers: string[]) => Promise<void>;
  
  ownedAssets: OwnedAsset[];
  fetchOwnedAssets: () => Promise<void>;
  updateOwnedAsset: (asset: OwnedAsset) => Promise<void>;

  marketStatus: MarketStatus | null;
  fetchMarketStatus: () => Promise<void>;
  sectorData: SectorItem[];
  fetchSectorData: () => Promise<void>;

  performanceData: PerformanceData | null;
  fetchPerformanceData: (initialCapital: number) => Promise<void>;
  

  scanTimestamp: string | null;
  detectedSetups: any | null;
  fetchDetectedSetups: () => Promise<void>;
  fetchLatestScan: () => Promise<void>;
  
  initializeFavorites: () => Promise<void>;

  virtualPortfolio: OwnedAsset[];
  fetchVirtualPortfolio: () => Promise<void>;
  updateVirtualAsset: (asset: OwnedAsset) => Promise<void>;
  closeVirtualAsset: (ticker: string, sellPrice: number, sellQuantity: number, exitReason: string, strategy: string) => Promise<void>;
  virtualPerformanceData: PerformanceData | null;
  fetchVirtualPerformance: (initialCapital: number) => Promise<void>;
}

let API_BASE = 'https://ai-stock-backend-108832568469.asia-northeast3.run.app';
if (API_BASE.includes('api.example.com')) {
  API_BASE = 'https://ai-stock-backend-108832568469.asia-northeast3.run.app';
}

export const useStore = create<TradingState>((set, get) => ({
  portfolio: [],
  setPortfolio: (portfolio) => set({ portfolio }),
  filter: 'DETECTED',
  setFilter: (filter) => set({ filter, currentPage: 1 }),
  currentPage: 1,
  setCurrentPage: (page) => set({ currentPage: page }),
  
  searchQuery: '',
  analyzedResult: null,
  setAnalyzedResult: (item) => set({ analyzedResult: item }),
  setSearchQuery: (query) => set({ searchQuery: query, currentPage: 1 }),

  watchlist: [],
  fetchWatchlist: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/watchlist/full`);
      const data = await res.json();
      if (data.watchlist && Array.isArray(data.watchlist)) {
        const tickers = data.watchlist.map((item: any) => item.Ticker || item.ticker);
        set({ watchlist: tickers });

        const currentPortfolio = get().portfolio;
        const newPortfolio = [...currentPortfolio];
        
        data.watchlist.forEach((item: any) => {
           const t = item.Ticker || item.ticker;
           const cName = item['Company Name'] || item.name || t;
           const existingIndex = newPortfolio.findIndex(p => p.ticker === t);
           
           const parsedItem = {
             ticker: t,
             name: cName,
             action: item.action || item.signal || 'WAIT',
             strategy: item.strategy || '관심종목 (수동 추가)',
             summary: [item.ai_summary || '수동 추가된 관심종목입니다.'],
             targetPrice: item.targetPrice || item.target_price || 0,
             stopLoss: item.stopLoss || item.stop_loss || 0,
             currentPrice: item.currentPrice || item.current_price || 0,
             change_pct: item.change_pct || 0,
             score: item.score || 0,
             entryPivot: item.entryPivot || item.entry_pivot,
             detected_at: item.detected_at,
             detected_price: item.detected_price,
             is_new: item.is_new,
             streak_days: item.streak_days
           };

           if (existingIndex >= 0) {
              newPortfolio[existingIndex] = { ...newPortfolio[existingIndex], ...parsedItem, summary: newPortfolio[existingIndex].summary.length > 1 ? newPortfolio[existingIndex].summary : parsedItem.summary };
           } else {
              newPortfolio.push(parsedItem);
           }
        });
        set({ portfolio: newPortfolio, scanTimestamp: data.last_scanned_at || get().scanTimestamp });
      }
    } catch (e) {
      console.error("Failed to fetch watchlist:", e);
    }
  },
  toggleWatchlist: async (ticker: string) => {
    try {
      // Optimistic update for fast UI response
      const currentList = get().watchlist;
      const isStarred = currentList.includes(ticker);
      set({ 
        watchlist: isStarred 
          ? currentList.filter(t => t !== ticker) 
          : [...currentList, ticker] 
      });
      
      await fetch(`${API_BASE}/api/watchlist/toggle`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ticker })
      });
      
    } catch (e) {
      console.error("Failed to toggle watchlist:", e);
    }
  },
  
  isAnalyzing: false,
  analyzeTicker: async (ticker: string) => {
    if (!ticker) return;
    set({ isAnalyzing: true });
    try {
      const res = await fetch(`${API_BASE}/api/analyze/${ticker.toUpperCase()}`);
      if (!res.ok) {
        alert(`Failed to fetch data for ${ticker}. Ensure the ticker is valid.`);
        set({ isAnalyzing: false });
        return;
      }
      const data: StockItem = await res.json();
      
      const currentPortfolio = get().portfolio;
      const existsIdx = currentPortfolio.findIndex(p => p.ticker === data.ticker);
      let newPortfolio = [...currentPortfolio];
      
      if (existsIdx >= 0) {
        const oldName = currentPortfolio[existsIdx].name;
        if (oldName && oldName !== data.ticker && (!data.name || data.name === data.ticker)) {
            data.name = oldName;
        }
        newPortfolio[existsIdx] = data;
      } else {
        newPortfolio = [data, ...newPortfolio];
      }
      
      // 스코어 내림차순 정렬
      newPortfolio.sort((a, b) => (b.score || 0) - (a.score || 0));
      set({ portfolio: newPortfolio, filter: 'ALL', searchQuery: '' });
      
    } catch (e: any) {
      console.error("Error analyzing ticker:", e);
      // Check if it's a network error
      if (e.name === 'TypeError' && e.message.includes('fetch')) {
        alert('백엔드 서버에 연결할 수 없습니다. 백엔드 서버(FastAPI)가 실행 중인지 확인해주세요.');
      } else {
        alert('분석 중 오류가 발생했습니다. 존재하지 않는 티커이거나 서버 오류일 수 있습니다.');
      }
    } finally {
      set({ isAnalyzing: false });
    }
  },
  analyzeTickerFast: async (ticker: string) => {
    if (!ticker) return;
    set({ isAnalyzing: true });
    try {
      const res = await fetch(`${API_BASE}/api/analyze-fast/${ticker.toUpperCase()}`);
      if (!res.ok) {
        alert(`Failed to fetch data for ${ticker}. Ensure the ticker is valid.`);
        set({ isAnalyzing: false });
        return;
      }
      const data: StockItem = await res.json();
      
      const currentPortfolio = get().portfolio;
      const existsIdx = currentPortfolio.findIndex(p => p.ticker === data.ticker);
      let newPortfolio = [...currentPortfolio];
      
      if (existsIdx >= 0) {
        const oldName = currentPortfolio[existsIdx].name;
        if (oldName && oldName !== data.ticker && (!data.name || data.name === data.ticker)) {
            data.name = oldName;
        }
        newPortfolio[existsIdx] = data;
      } else {
        newPortfolio = [data, ...newPortfolio];
      }
      
      newPortfolio.sort((a, b) => (b.score || 0) - (a.score || 0));
      set({ portfolio: newPortfolio, filter: 'ALL', searchQuery: '' });
      
    } catch (e: any) {
      console.error("Error analyzing ticker fast:", e);
      if (e.name === 'TypeError' && e.message.includes('fetch')) {
        alert('백엔드 서버에 연결할 수 없습니다. 백엔드 서버(FastAPI)가 실행 중인지 확인해주세요.');
      } else {
        alert('분석 중 오류가 발생했습니다. 존재하지 않는 티커이거나 서버 오류일 수 있습니다.');
      }
    } finally {
      set({ isAnalyzing: false });
    }
  },

  isScanning: false,
  runGlobalScan: async () => {
    set({ isScanning: true });
    try {
      const res = await fetch(`${API_BASE}/api/watchlist/scan-fast`);
      if (!res.ok) {
        alert('관심종목 스캔 중 오류가 발생했습니다.');
        set({ isScanning: false });
        return;
      }
      const data = await res.json();
      if (data.results && data.results.length > 0) {
        // 기존 포트폴리오(검색된 항목)와 합치되 티커 중복 방지
        const currentPortfolio = get().portfolio;
        const newMap = new Map();
        currentPortfolio.forEach(p => newMap.set(p.ticker, p));
        data.results.forEach((p: StockItem) => {
           const existing = newMap.get(p.ticker);
           if (existing && existing.name && existing.name !== p.ticker && (!p.name || p.name === p.ticker)) {
               p.name = existing.name;
           }
           newMap.set(p.ticker, { ...existing, ...p });
        });
        
        const merged = Array.from(newMap.values());
        merged.sort((a, b) => (b.score || 0) - (a.score || 0));
        
        set({ portfolio: merged, filter: 'ALL', searchQuery: '', scanTimestamp: data.timestamp || get().scanTimestamp });
      } else {
        alert("관심종목 스캔을 완료했으나 결과가 없습니다.");
      }
    } catch (e) {
      console.error("Error running watchlist scan:", e);
      alert('스캐너 실행 중 오류가 발생했습니다.');
    } finally {
      set({ isScanning: false });
    }
  },
  
  bulkRemoveWatchlist: async (tickers: string[]) => {
    try {
      const res = await fetch(`${API_BASE}/api/watchlist/bulk-remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tickers })
      });
      const data = await res.json();
      if (data.watchlist) {
        set({ watchlist: data.watchlist });
      }
    } catch (e) {
      console.error("bulkRemoveWatchlist failed", e);
    }
  },

  removeTicker: (ticker: string) => {
    set((state) => ({
      portfolio: state.portfolio.filter(p => p.ticker !== ticker)
    }));
  },
  
  ownedAssets: [],
  fetchOwnedAssets: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/portfolio`);
      if (res.ok) {
        const data = await res.json();
        // Handle case where user's google sheet headers might be lowercase or Korean
        const mappedAssets = (data.portfolio || []).map((a: any) => ({
          Ticker: String(a.Ticker || a.ticker || a['종목명'] || a['종목'] || ''),
          Quantity: Number(a.Quantity || a.quantity || a['수량'] || 0),
          AvgPrice: Number(a.AvgPrice || a.avgPrice || a['Avg Price'] || a['매수가'] || a['평균단가'] || 0),
          PurchaseDate: String(a.PurchaseDate || a.purchaseDate || a['Purchase Date'] || a['매수일'] || ''),
          Strategy: String(a.Strategy || a.strategy || 'Manual'),
          CurrentPrice: Number(a.CurrentPrice || 0),
          trailingStop: Number(a.trailingStop || 0),
          ma20: Number(a.ma20 || 0)
        }));
        const validAssets = mappedAssets.filter((a: OwnedAsset) => a.Ticker && a.Ticker.trim() !== '');
        set({ ownedAssets: validAssets });
      }
    } catch (e) {
      console.error("Failed to fetch owned assets:", e);
    }
  },
  
  updateOwnedAsset: async (asset: OwnedAsset) => {
    try {
      const res = await fetch(`${API_BASE}/api/portfolio/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: asset.Ticker,
          quantity: asset.Quantity,
          avgPrice: asset.AvgPrice,
          purchaseDate: asset.PurchaseDate,
          strategy: asset.Strategy
        })
      });
      if (res.ok) {
        // Refresh after update
        get().fetchOwnedAssets();
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(`저장 실패: ${errData.detail || "Google Sheets 연동을 다시 확인해주세요."}`);
      }
    } catch (e) {
      console.error("Failed to update owned asset:", e);
    }
  },
  
  marketStatus: null,
  fetchMarketStatus: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/market/status`);
      if (res.ok) {
        const data = await res.json();
        set({ marketStatus: data });
      }
    } catch (e) {
      console.error('Failed to fetch market status:', e);
    }
  },
  sectorData: [],
  fetchSectorData: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/market/sectors`);
      if (res.ok) {
        const data = await res.json();
        if (data.sectors) {
          set({ sectorData: data.sectors });
        }
      }
    } catch (e) {
      console.error("Failed to fetch sector data:", e);
    }
  },

  performanceData: null,
  fetchPerformanceData: async (initialCapital: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/performance?initial_capital=${initialCapital}`);
      if (res.ok) {
        const data = await res.json();
        set({ performanceData: data });
      }
    } catch (e) {
      console.error("Failed to fetch performance data:", e);
    }
  },
  

  scanTimestamp: null,
  detectedSetups: null,
  fetchDetectedSetups: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/scan/detected`);
      const data = await res.json();
      if (data && data.last_scanned_at) {
        set({ detectedSetups: data });
      }
    } catch (e) {
      console.error(e);
    }
  },
  fetchLatestScan: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/scan/latest`);
      const data = await res.json();
      if (data.results && data.results.length > 0) {
        set({ scanTimestamp: data.timestamp });
        
        const currentPortfolio = get().portfolio;
        const newMap = new Map();
        currentPortfolio.forEach(p => newMap.set(p.ticker, p));
        data.results.forEach((p: any) => {
           const existing = newMap.get(p.ticker);
           if (existing && existing.name && existing.name !== p.ticker && (!p.name || p.name === p.ticker)) {
               p.name = existing.name;
           }
           newMap.set(p.ticker, p);
        });
        
        const merged = Array.from(newMap.values());
        merged.sort((a, b) => {
            if (a.action === 'BUY' && b.action !== 'BUY') return -1;
            if (a.action !== 'BUY' && b.action === 'BUY') return 1;
            return (b.score || 0) - (a.score || 0);
        });
        set({ portfolio: merged });
      }
    } catch (e) {
      console.error("Failed to fetch latest scan:", e);
    }
  },

  initializeFavorites: async () => {
    // 1. Fetch watchlist from backend (creates dummy items)
    await get().fetchWatchlist();
    // 2. Fetch the latest cached scan results and merge them
    await get().fetchLatestScan();
  },

  virtualPortfolio: [],
  fetchVirtualPortfolio: async () => {
    try {
      const res = await fetch(`${API_BASE}/api/virtual/portfolio`);
      if (res.ok) {
        const data = await res.json();
        const mappedAssets = (data || []).map((a: any) => ({
          Ticker: String(a.Ticker || ''),
          Quantity: Number(a.Quantity || 0),
          AvgPrice: Number(a.AvgPrice || 0),
          PurchaseDate: String(a.PurchaseDate || ''),
          Strategy: String(a.Strategy || 'Manual'),
          CurrentPrice: Number(a.CurrentPrice || 0),
          trailingStop: Number(a.trailingStop || 0),
          ma20: Number(a.ma20 || 0)
        }));
        const validAssets = mappedAssets.filter((a: OwnedAsset) => a.Ticker && a.Ticker.trim() !== '');
        set({ virtualPortfolio: validAssets });
      }
    } catch (e) {
      console.error("Failed to fetch virtual portfolio:", e);
    }
  },
  
  updateVirtualAsset: async (asset: OwnedAsset) => {
    try {
      const res = await fetch(`${API_BASE}/api/virtual/portfolio/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker: asset.Ticker,
          quantity: asset.Quantity,
          avgPrice: asset.AvgPrice,
          purchaseDate: asset.PurchaseDate,
          strategy: asset.Strategy
        })
      });
      if (res.ok) {
        get().fetchVirtualPortfolio();
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(`저장 실패: ${errData.detail || "오류가 발생했습니다."}`);
      }
    } catch (e) {
      console.error("Failed to update virtual asset:", e);
    }
  },

  closeVirtualAsset: async (ticker: string, sellPrice: number, sellQuantity: number, exitReason: string, strategy: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/virtual/portfolio/close`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticker,
          sell_price: sellPrice,
          sell_quantity: sellQuantity,
          exit_reason: exitReason,
          strategy
        })
      });
      if (res.ok) {
        await get().fetchVirtualPortfolio();
      } else {
        const error = await res.json();
        alert(`Error: ${error.detail || 'Failed to close position'}`);
      }
    } catch(e) {
      console.error(e);
      alert('Network error');
    }
  },

  virtualPerformanceData: null,
  fetchVirtualPerformance: async (initialCapital: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/virtual/performance?initial_capital=${initialCapital}`);
      if (res.ok) {
        const data = await res.json();
        set({ virtualPerformanceData: data });
      }
    } catch (e) {
      console.error("Failed to fetch virtual performance data:", e);
    }
  }
}))
