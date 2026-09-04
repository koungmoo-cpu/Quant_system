import yfinance as yf
import time
from typing import List, Dict
import pandas as pd

class MarketDataFetcher:
    def __init__(self, batch_size: int = 20, delay_seconds: float = 2.0):
        self.batch_size = batch_size
        self.delay_seconds = delay_seconds

    def _chunk_tickers(self, tickers: List[str]):
        """Yield successive batch_size chunks from tickers."""
        for i in range(0, len(tickers), self.batch_size):
            yield tickers[i:i + self.batch_size]

    def fetch_data(self, tickers: List[str], period: str = "6mo", interval: str = "1d") -> Dict[str, pd.DataFrame]:
        """
        Fetch data for a list of tickers in chunks to avoid API overload and IP bans.
        Strictly batches requests into sizes of self.batch_size (default: 20).
        """
        all_data = {}
        chunks = list(self._chunk_tickers(tickers))
        
        for idx, chunk in enumerate(chunks):
            print(f"Fetching batch {idx + 1}/{len(chunks)}: {chunk}")
            
            try:
                if len(chunk) == 1:
                    batch_data = yf.download(
                        tickers=chunk[0], 
                        period=period, 
                        interval=interval, 
                        threads=False
                    )
                    ticker = chunk[0]
                    if not batch_data.empty:
                        all_data[ticker] = batch_data
                else:
                    batch_data = yf.download(
                        tickers=" ".join(chunk), 
                        period=period, 
                        interval=interval, 
                        group_by='ticker', 
                        threads=False
                    )
                    for ticker in chunk:
                        if isinstance(batch_data.columns, pd.MultiIndex):
                            if ticker in batch_data.columns.levels[0]:
                                ticker_data = batch_data[ticker].dropna(how='all')
                                if not ticker_data.empty:
                                    all_data[ticker] = ticker_data
                        else:
                            # Fallback if somehow not multi-index
                            pass
                                
            except Exception as e:
                print(f"Error fetching data for chunk {chunk}: {e}")
                
            # Sleep between batches to prevent rate limiting
            if idx < len(chunks) - 1:
                print(f"Waiting {self.delay_seconds} seconds before next batch...")
                time.sleep(self.delay_seconds)
                
        return all_data

    def evaluate_market_trend(self) -> tuple[str, int]:
        try:
            # QQQ (Nasdaq 100) trend evaluation
            qqq = yf.download("QQQ", period="1y", interval="1d", progress=False)
            if qqq.empty:
                return "Yellow", 50
                
            qqq['20MA'] = qqq['Close'].rolling(window=20).mean()
            qqq['50MA'] = qqq['Close'].rolling(window=50).mean()
            
            # handle pandas Series/DataFrame access
            last_close = float(qqq['Close'].iloc[-1].item() if hasattr(qqq['Close'].iloc[-1], 'item') else qqq['Close'].iloc[-1])
            ma20 = float(qqq['20MA'].iloc[-1].item() if hasattr(qqq['20MA'].iloc[-1], 'item') else qqq['20MA'].iloc[-1])
            ma50 = float(qqq['50MA'].iloc[-1].item() if hasattr(qqq['50MA'].iloc[-1], 'item') else qqq['50MA'].iloc[-1])
            
            if last_close > ma20 and last_close > ma50:
                status = "Green"
                exposure = 100
            elif last_close > ma50:
                status = "Yellow"
                exposure = 50
            else:
                status = "Red"
                exposure = 25
                
            return status, exposure
        except Exception as e:
            print(f"Market trend evaluation failed: {e}")
            return "Yellow", 50

    def get_historical_prices(self, date_str: str, tickers: List[str] = ["SPY", "QQQ"]) -> Dict[str, float]:
        """
        특정 날짜(또는 그 이전 가장 가까운 거래일)의 종가를 가져옵니다.
        """
        try:
            # 날짜를 파싱하고 휴일/주말을 고려하여 해당일 포함 이전 7일치의 데이터를 가져옴
            target_date = pd.to_datetime(date_str)
            start_date = (target_date - pd.Timedelta(days=7)).strftime('%Y-%m-%d')
            # end_date는 target_date + 1일 (yf는 end date를 포함하지 않음)
            end_date = (target_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
            
            data = yf.download(tickers, start=start_date, end=end_date, progress=False)
            if data.empty:
                return {t: 0.0 for t in tickers}
            
            result = {}
            for ticker in tickers:
                if len(tickers) == 1:
                    close_series = data['Close'].dropna()
                else:
                    if 'Close' in data.columns and ticker in data['Close'].columns:
                        close_series = data['Close'][ticker].dropna()
                    else:
                        close_series = pd.Series(dtype=float)
                
                if not close_series.empty:
                    # 가장 마지막 날짜(target_date에 가장 가까운 이전 거래일)의 종가 반환
                    val = close_series.iloc[-1]
                    result[ticker] = float(val.item() if hasattr(val, 'item') else val)
                else:
                    result[ticker] = 0.0
            return result
        except Exception as e:
            print(f"Failed to fetch historical prices for {date_str}: {e}")
            return {t: 0.0 for t in tickers}
