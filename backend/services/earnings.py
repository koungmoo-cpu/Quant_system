import yfinance as yf
from datetime import datetime

def get_earnings_date(ticker_str: str):
    try:
        t = yf.Ticker(ticker_str)
        cal = t.calendar
        if cal is not None:
            if isinstance(cal, dict) and 'Earnings Date' in cal:
                dates = cal['Earnings Date']
                if dates and len(dates) > 0:
                    return dates[0].strftime('%Y-%m-%d')
            elif hasattr(cal, 'empty') and not cal.empty:
                # In yfinance >= 0.2.x, calendar is a DataFrame or dict
                pass
    except Exception:
        pass
    return None
