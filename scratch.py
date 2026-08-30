from backend.services.performance import PerformanceEngine
from backend.services.db_connector import db
engine = PerformanceEngine()
trades = db.get_trade_history()
metrics = engine.calculate_account_metrics(trades, 10000000)
print(metrics)
import pandas as pd
print("RAW TRADES")
for t in trades:
    print(t.get("매수일"), t.get("매도일"))
