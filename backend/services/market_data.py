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
