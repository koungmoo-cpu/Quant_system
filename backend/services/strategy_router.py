import pandas as pd
from typing import Dict, Optional, Tuple

class StrategyRouter:
    def __init__(self):
        pass
        
    def evaluate(self, ticker: str, data: pd.DataFrame) -> Tuple[Optional[str], Optional[Dict]]:
        """
        if-elif waterfall model for technical strategies.
        Returns a tuple of (strategy_name, context_data) if it passes the filter, else (None, None).
        Priority:
        1. Qullamaggie EP (Episodic Pivot)
        2. Minervini Power Play
        3. Breakout Setup
        """
        if data is None or data.empty:
            return None, None

        # 1순위: 쿨라매기 EP (Episodic Pivot)
        if self._is_qullamaggie_ep(data):
            return "Qullamaggie EP", {"setup": "Episodic Pivot", "catalyst": "Earnings/News expected"}
            
        # 2순위: 미너비니 Power Play (High Tight Flag)
        elif self._is_minervini_power_play(data):
            return "Minervini Power Play", {"setup": "Power Play", "momentum": "Strong accumulation"}
            
        # 3순위: 돌파 셋업 (Breakout Setup)
        elif self._is_breakout_setup(data):
            return "Breakout Setup", {"setup": "Standard Breakout", "volume": "Expanding"}
            
        return None, None
        
    def _is_qullamaggie_ep(self, data: pd.DataFrame) -> bool:
        # TODO: Implement actual Episodic Pivot logic 
        # (e.g., massive gap up, volume > 3x average, closing near highs)
        return False
        
    def _is_minervini_power_play(self, data: pd.DataFrame) -> bool:
        # TODO: Implement actual Power Play logic
        # (e.g., up 100% in 8 weeks, consolidating tightly with volatility contraction)
        return False
        
    def _is_breakout_setup(self, data: pd.DataFrame) -> bool:
        # TODO: Implement Standard Breakout logic
        # (e.g., crossing major resistance or moving average on high volume)
        return False
