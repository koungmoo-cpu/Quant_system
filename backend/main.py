from services.db_connector import db
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from config import settings
from services.market_data import MarketDataFetcher
from services.strategy_router import StrategyRouter
from services.performance import PerformanceEngine

app = FastAPI(title=settings.app_name)
market_fetcher = MarketDataFetcher(batch_size=20, delay_seconds=0.5)
strategy_router = StrategyRouter()
performance_engine = PerformanceEngine()

# CORS setup for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BulkRemoveReq(BaseModel):
    tickers: list[str]

class ToggleRequest(BaseModel):
    ticker: str

@app.get("/")
async def root():
    return {"message": f"Welcome to the {settings.app_name} API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/api/watchlist")
def get_watchlist():
    tickers = db.get_favorites()
    return {"watchlist": tickers}


@app.get("/api/watchlist/scan")
def scan_watchlist():
    from services.scanner import fast_pre_filter, master_strategy_analyzer
    from datetime import datetime
    import pytz
    
    try:
        tickers = db.get_favorites()
        if not tickers:
            return {"results": []}
            
        results = []
        for t in tickers:
            setup_data = master_strategy_analyzer(t)
            strategy_name = setup_data.get('strategy', 'No Setup (관망)')
            
            stop_loss = setup_data.get('stop_loss') or 0.0
            entry_pivot = setup_data.get('entry_pivot')
            
            results.append({
                "ticker": t,
                "name": t,
                "strategy": strategy_name,
                "action": "BUY" if 'No Setup' not in strategy_name and strategy_name != 'Data Error' else "WAIT",
                "summary": [f"✅ 분석 완료: {setup_data.get('details', [])[-1] if setup_data.get('details') else ''}"],
                "stopLoss": round(stop_loss, 2),
                "targetPrice": round(entry_pivot * 1.15 if entry_pivot else 0, 2),
                "currentPrice": setup_data.get("currentPrice", 0.0),
                "entryPivot": round(entry_pivot, 2) if entry_pivot else None,
                "score": setup_data.get('score', 0),
                "earningsDate": get_earnings_date(t),
                "ret_5d": setup_data.get('ret_5d', 0),
                "ret_10d": setup_data.get('ret_10d', 0),
                "ret_20d": setup_data.get('ret_20d', 0)
            })
            
        results.sort(key=lambda x: x['score'], reverse=True)
        
        now_str = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S")
        return {"results": results, "timestamp": now_str}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"results": [], "error": str(e)}

@app.get("/api/watchlist/full")
def get_watchlist_full():
    import yfinance as yf
    tickers = db.get_favorites()
    if not tickers:
        return {"watchlist": []}
    
    # 1. Fetch cached data from latest_setups
    latest_data = db.get_latest_detected_setups()
    cached_items = {item["ticker"]: item for item in latest_data.get("items", [])}
    
    # 2. Process each ticker
    results = []
    for ticker in tickers:
        if ticker in cached_items:
            base_item = dict(cached_items[ticker])
            # Ensure action and currentPrice match what StockCard expects
            if "action" not in base_item:
                base_item["action"] = base_item.get("signal", "WAIT")
            if "currentPrice" not in base_item:
                base_item["currentPrice"] = base_item.get("current_price", 0.0)
            if "targetPrice" not in base_item:
                base_item["targetPrice"] = base_item.get("entry_pivot", 0.0) * 1.20 if base_item.get("entry_pivot") else 0.0
        else:
            base_item = {
                "ticker": ticker,
                "name": ticker,
                "action": "WAIT",
                "currentPrice": 0.0,
                "current_price": 0.0,
                "change_pct": 0.0,
                "targetPrice": 0.0,
                "stopLoss": 0.0,
                "stop_loss": 0.0,
                "score": 0,
                "strategy": "관심종목 (수동 추가)",
                "ai_summary": "수동 추가된 관심종목입니다."
            }
        
        # Fallback / Fill missing with yfinance fast_info
        if base_item.get("current_price", 0.0) == 0.0 or "change_pct" not in base_item:
            try:
                t_obj = yf.Ticker(ticker)
                info = t_obj.fast_info
                cp = info.last_price
                prev_close = info.previous_close
                change = ((cp - prev_close) / prev_close * 100) if prev_close else 0.0
                
                if base_item.get("current_price", 0.0) == 0.0:
                    base_item["current_price"] = round(cp, 2)
                    base_item["currentPrice"] = round(cp, 2)
                    base_item["targetPrice"] = round(cp * 1.20, 2)
                    base_item["stop_loss"] = round(cp * 0.95, 2)
                    base_item["stopLoss"] = round(cp * 0.95, 2)
                    
                base_item["change_pct"] = round(change, 2)
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")
                
        results.append(base_item)
        
    return {"watchlist": results, "last_scanned_at": latest_data.get("last_scanned_at")}


@app.post("/api/watchlist/bulk-remove")
async def bulk_remove_watchlist(req: BulkRemoveReq):
    updated = db.bulk_remove_favorites(req.tickers)
    return {"watchlist": updated}

@app.post("/api/watchlist/toggle")
async def toggle_watchlist(req: ToggleRequest):
    added = db.toggle_favorite(req.ticker)
    return {"ticker": req.ticker, "added": added}


@app.get("/api/quote/{ticker}")
def get_quote(ticker: str):
    import yfinance as yf
    try:
        t = yf.Ticker(ticker)
        # fast_info is much faster than info
        price = t.fast_info.last_price
        return {"ticker": ticker, "price": round(price, 2)}
    except Exception as e:
        print(f"Error fetching quote for {ticker}: {e}")
        return {"ticker": ticker, "price": 0.0}

from services.scanner import master_strategy_analyzer, get_index_tickers, fast_pre_filter
import json
from google import genai
from google.genai import types


@app.get("/api/scan/latest")
async def get_latest_scan():
    try:
        data = db.get_latest_scan_results()
        return data
    except Exception as e:
        print(f"Error fetching latest scan: {e}")
        return {"timestamp": None, "results": []}

@app.get("/api/scan/universe")
def scan_universe():
    try:
        # 1. 전체 유니버스 스캔
        all_tickers = db.get_universe_tickers()
        
        # 2. 1차 깔때기 (1개월 데이터, 멀티스레딩)
        valid_tickers = fast_pre_filter(all_tickers)
        
        # 3. 2차 정밀 분석 및 스코어링
        results = []
        for t in valid_tickers:
            setup_data = master_strategy_analyzer(t)
            strategy_name = setup_data.get('strategy', 'No Setup (관망)')
            
            # BUY 셋업이 발생한 종목만 필터링
            if 'No Setup' not in strategy_name and strategy_name != 'Data Error' and 'Not Enough Data' not in strategy_name:
                stop_loss = setup_data.get('stop_loss') or 0.0
                entry_pivot = setup_data.get('entry_pivot')
                
                # Gemini 호출을 50개 종목에 전부 하면 Rate Limit 위험이 있으므로
                # 스캐너에서는 AI 요약 단계를 생략하고 기본 메시지로 대체하거나 점수만 반환합니다.
                results.append({
                    "ticker": t,
                    "name": t,
                    "strategy": strategy_name,
                    "action": "BUY",
                    "summary": [f"✅ 조건 통과: {setup_data.get('details', [])[-1] if setup_data.get('details') else ''}", "스캐너 자동 탐지 종목"],
                    "stopLoss": round(stop_loss, 2),
                    "targetPrice": round(entry_pivot * 1.15 if entry_pivot else 0, 2),
                    "currentPrice": setup_data.get("currentPrice", 0.0),
                    "entryPivot": round(entry_pivot, 2) if entry_pivot else None,
                                        "entryPivot": round(entry_pivot, 2) if entry_pivot else None,
                    "score": setup_data.get('score', 0),
                    "earningsDate": get_earnings_date(t),
                    "ret_5d": setup_data.get('ret_5d', 0),
                    "ret_10d": setup_data.get('ret_10d', 0),
                    "ret_20d": setup_data.get('ret_20d', 0)
                })
                
        # 점수 내림차순 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ai-catalyst-insight/{ticker}")
def get_ai_catalyst_insight(ticker: str):
    ticker = ticker.upper()
    api_key = settings.google_genai_api_key
    if not api_key:
        return {"summary": ["API Key가 설정되지 않아 AI 분석을 건너뜁니다."]}
        
    try:
        client = genai.Client(api_key=api_key)
        prompt = f"""
당신은 월스트리트의 엘리트 퀀트 애널리스트입니다. 
주식 {ticker}에 대한 최신 뉴스, 테마, 실적(Earnings) 이슈, 거시경제적 촉매제(Catalyst)를 바탕으로,
이 주식이 왜 현재 시장의 주목을 받고 있거나 급등/급락하고 있는지 스토리 위주로 3~4줄로 요약해주세요.

주의사항: 
- 차트 셋업이나 매수가/손절가 같은 기술적 분석 수치는 절대 언급하지 마세요. (이미 시스템이 계산했습니다)
- 오직 뉴스, 펀더멘털, 테마, 호재/악재 등 '왜(Why)'에만 집중하세요.
- 답변은 마크다운 불릿 포인트(- ) 형태로만 작성해주세요.
"""
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.4
            )
        )
        
        lines = response.text.strip().split('\n')
        clean_lines = [line.strip().lstrip('-').strip() for line in lines if line.strip()]
        
        return {"summary": clean_lines}
    except Exception as e:
        print(f"AI Error for {ticker}: {e}")
        return {"summary": ["AI 분석 중 오류가 발생했습니다.", str(e)]}
        
    # 3. 적합한 셋업이면 Gemini AI로 최종 브리핑 및 액션 결정 (JSON 포맷 강제)
    action = "WAIT"
    summary_lines = ["AI 분석 대기 중..."]
    target_price = current_price * 1.15
    
    api_key = settings.google_genai_api_key
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
당신은 퀀트 트레이딩 AI입니다. 파이썬이 통과시킨 다음 셋업을 최종 분석하세요.
티커: {ticker}
매칭된 전략: {strategy_name}
현재가: {current_price}
제안된 손절가: {stop_loss}
제안된 진입가: {entry_pivot}

이 전략의 핵심 원칙에 맞추어 명확한 지시를 내리세요.
반드시 아래 JSON 형식으로만 응답하세요:
{{
    "action": "BUY" 또는 "WAIT",
    "summary": "첫 번째 줄 이유.\\n두 번째 줄 이유.\\n세 번째 줄 이유.",
    "target_price": 목표가(숫자로만)
}}
"""
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json", 
                    temperature=0.2
                )
            )
            
            # JSON 파싱 전 마크다운 찌꺼기 제거
            clean_text = response.text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
                
            result = json.loads(clean_text.strip())
            action = result.get("action", "BUY").upper()
            
            # AI 요약 결과 맨 위에 통과한 조건식(O/X)을 추가
            ai_summary = result.get("summary", "").split("\n")
            matched_detail = setup_data.get('details', [])[-1] if setup_data.get('details') else ""
            summary_lines = [f"✅ 조건 통과: {matched_detail}"] + ai_summary
            
            target_price = float(result.get("target_price", current_price * 1.15))
        except Exception as e:
            print(f"AI Error for {ticker}: {e}")
            summary_lines = ["AI 브리핑 생성 중 오류가 발생했습니다.", str(e)]
    else:
        summary_lines = ["API Key가 설정되지 않아 AI 분석을 건너뜁니다."]

    universe_list = db.get_universe()
    ticker_name_map = {u["ticker"]: u.get("name", u["ticker"]) for u in universe_list if "ticker" in u}
    return {
        "ticker": ticker,
        "name": ticker_name_map.get(ticker, ticker),
        "strategy": strategy_name,
        "action": action,
        "summary": summary_lines,
        "stopLoss": round(stop_loss, 2),
        "targetPrice": round(target_price, 2),
        "currentPrice": round(current_price, 2),
        "entryPivot": round(entry_pivot, 2) if entry_pivot else None,
                "entryPivot": round(entry_pivot, 2) if entry_pivot else None,
        "score": setup_data.get('score', 0),
        "earningsDate": get_earnings_date(ticker),
        "ret_5d": setup_data.get('ret_5d', 0),
        "ret_10d": setup_data.get('ret_10d', 0),
        "ret_20d": setup_data.get('ret_20d', 0)
    }


@app.get("/api/analyze-fast/{ticker}")
def analyze_ticker_fast(ticker: str):
    ticker = ticker.upper()
    
    setup_data = master_strategy_analyzer(ticker)
    strategy_name = setup_data.get('strategy', 'No Setup (관망)')
    
    try:
        t_data = market_fetcher.fetch_data([ticker])
        if ticker in t_data and not t_data[ticker].empty:
            df = t_data[ticker]
            try:
                current_price = float(df['Close'].iloc[-1])
            except TypeError:
                current_price = float(df['Close'].iloc[-1].iloc[0])
        else:
            current_price = 0.0
    except Exception:
        current_price = 0.0
        
    stop_loss = setup_data.get('stop_loss') or (current_price * 0.95)
    entry_pivot = setup_data.get('entry_pivot')
    
    if 'No Setup' in strategy_name or strategy_name == 'Data Error':
        action = "WAIT"
        details_list = setup_data.get('details', [])
        summary_lines = []
        if 'Low Volatility/Stable' in strategy_name:
            summary_lines.append("⚠️ 사전 변동성/유동성 필터 미달")
        else:
            summary_lines.append("⚠️ 모든 매매 셋업 조건 미달")
        summary_lines.extend(details_list)
    else:
        action = "BUY"
        matched_detail = setup_data.get('details', [])[-1] if setup_data.get('details') else ""
        summary_lines = [f"✅ 조건 통과: {matched_detail}", "⚡ AI 요약 없는 빠른 퀀트 분석 결과입니다."]
        
    universe_list = db.get_universe()
    ticker_name_map = {u["ticker"]: u.get("name", u["ticker"]) for u in universe_list if "ticker" in u}
    
    return {
        "ticker": ticker,
        "name": ticker_name_map.get(ticker, ticker),
        "strategy": strategy_name,
        "action": action,
        "summary": summary_lines,
        "stopLoss": round(stop_loss, 2),
        "targetPrice": round(current_price * 1.15, 2),
        "currentPrice": round(current_price, 2),
        "entryPivot": round(entry_pivot, 2) if entry_pivot else None,
        "score": setup_data.get('score', 0),
        "ret_5d": setup_data.get('ret_5d', 0),
        "ret_10d": setup_data.get('ret_10d', 0),
        "ret_20d": setup_data.get('ret_20d', 0)
    }

class PortfolioItemReq(BaseModel):
    ticker: str
    quantity: int
    avgPrice: float
    purchaseDate: str
    strategy: Optional[str] = None

import yfinance as yf
from datetime import datetime

def get_earnings_date(ticker_str: str):
    try:
        t = yf.Ticker(ticker_str)
        cal = t.calendar
        if cal is not None:
            if isinstance(cal, dict) and "Earnings Date" in cal:
                dates = cal["Earnings Date"]
                if dates and len(dates) > 0:
                    return dates[0].strftime("%Y-%m-%d")
            elif hasattr(cal, "empty") and not cal.empty:
                return cal.iloc[0, 0].strftime("%Y-%m-%d")
    except Exception:
        pass
    return None

@app.get("/api/portfolio")
async def get_portfolio():
    items = db.get_portfolio()
    
    tickers = []
    for item in items:
        t = item.get("Ticker", item.get("ticker", item.get("종목명", "")))
        if t and str(t).strip() and t not in tickers:
            tickers.append(str(t).strip())
            
    if tickers:
        try:
            # 10일 이동평균선(Trailing Stop) 계산을 위해 1달치(약 22거래일) 데이터를 가져옵니다.
            data = yf.download(tickers, period="1mo", progress=False)
            if not data.empty and "Close" in data:
                close_data = data["Close"]
                for item in items:
                    t = str(item.get("Ticker", item.get("ticker", item.get("종목명", "")))).strip()
                    if t:
                        try:
                            if len(tickers) == 1:
                                series = close_data
                                if isinstance(series, pd.DataFrame):
                                    series = series.iloc[:, 0]
                            else:
                                series = close_data[t]
                                
                            series = series.dropna()
                            if len(series) > 0:
                                current_price = float(series.iloc[-1])
                                sma10 = float(series.tail(10).mean())
                                sma20 = float(series.tail(20).mean()) if len(series) >= 20 else sma10
                            else:
                                current_price = 0.0
                                sma10 = 0.0
                                sma20 = 0.0
                                
                            item["CurrentPrice"] = round(current_price, 2)
                            item["trailingStop"] = round(sma10, 2)
                            item["ma20"] = round(sma20, 2)
                        except Exception as e:
                            print(f"Error calculating for {t}: {e}")
                            item["CurrentPrice"] = 0.0
                            item["trailingStop"] = 0.0
                            item["ma20"] = 0.0
        except Exception as e:
            print(f"Error fetching portfolio current prices: {e}")
            
    return {"portfolio": items}

class PortfolioCloseReq(BaseModel):
    ticker: str
    sell_price: float
    sell_quantity: int
    exit_reason: str
    strategy: str

@app.post("/api/portfolio/close")
async def close_portfolio(req: PortfolioCloseReq):
    try:
        # Get portfolio items to find the doc id and old data
        items = db.db.collection('portfolio').stream()
        target_doc = None
        item_data = None
        for doc in items:
            data = doc.to_dict()
            t = data.get("Ticker", data.get("ticker", data.get("종목명", "")))
            if t == req.ticker:
                target_doc = doc
                item_data = data
                break
                
        if not target_doc:
            raise HTTPException(status_code=404, detail="Portfolio item not found")
            
        buy_price = float(item_data.get("Avg Price", item_data.get("AvgPrice", item_data.get("buy_price", 0))))
        buy_quantity = int(item_data.get("Quantity", item_data.get("quantity", item_data.get("buy_quantity", 0))))
        buy_date = item_data.get("Purchase Date", item_data.get("PurchaseDate", item_data.get("buy_date", "")))
        strategy = req.strategy or item_data.get("Strategy", item_data.get("strategy", "Manual"))
        
        if req.sell_quantity > buy_quantity:
            raise HTTPException(status_code=400, detail="Sell quantity exceeds owned quantity")
            
        profit_loss = (req.sell_price - buy_price) * req.sell_quantity
        profit_rate = ((req.sell_price / buy_price) - 1) * 100 if buy_price > 0 else 0
        
        import datetime
        sell_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Add to trades
        trade_data = {
            "ticker": req.ticker,
            "strategy": strategy,
            "buy_date": buy_date,
            "sell_date": sell_date,
            "buy_price": buy_price,
            "sell_price": req.sell_price,
            "quantity": req.sell_quantity,
            "profit_loss": round(profit_loss, 2),
            "profit_rate": round(profit_rate, 2),
            "exit_reason": req.exit_reason,
            "market_status": "Unknown", # Can be updated if needed
            "factor_score": 0
        }
        db.add_trade(trade_data)
        
        # Update or delete portfolio item
        remaining_quantity = buy_quantity - req.sell_quantity
        if remaining_quantity <= 0:
            target_doc.reference.delete()
        else:
            target_doc.reference.update({
                "Quantity": remaining_quantity
            })
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/portfolio/update")
async def update_portfolio(req: PortfolioItemReq):
    result = db.update_portfolio_item(req.ticker, req.quantity, req.avgPrice, req.purchaseDate, getattr(req, 'strategy', None))
    if result != "success":
        raise HTTPException(status_code=500, detail=result)
    return {"status": "success"}

@app.get("/api/performance")
async def get_performance(initial_capital: float = None):
    trade_data = db.get_trade_history()
    
    if initial_capital is None:
        rules = db.get_risk_rules()
        initial_capital = rules.get("initial_capital", 10000000.0)
        
    metrics = performance_engine.calculate_account_metrics(trade_data, initial_capital)
    return metrics

@app.get("/api/market/sectors")
async def get_sectors():
    # S&P 500 주요 11개 섹터 ETF
    sectors = {
        "XLK": "Technology",
        "XLV": "Health Care",
        "XLF": "Financials",
        "XLY": "Consumer Discretionary",
        "XLC": "Communication Services",
        "XLI": "Industrials",
        "XLP": "Consumer Staples",
        "XLE": "Energy",
        "XLU": "Utilities",
        "XLRE": "Real Estate",
        "XLB": "Materials"
    }
    try:
        tickers = list(sectors.keys())
        data = yf.download(tickers, period="5d", progress=False)
        results = []
        if not data.empty and "Close" in data:
            close_data = data["Close"]
            for ticker, name in sectors.items():
                if ticker in close_data:
                    series = close_data[ticker].dropna()
                    if len(series) >= 2:
                        current = float(series.iloc[-1])
                        prev = float(series.iloc[0])
                        return_pct = ((current - prev) / prev) * 100
                        results.append({
                            "ticker": ticker,
                            "name": name,
                            "return_pct": round(return_pct, 2),
                            "current": round(current, 2)
                        })
        # 정렬
        results.sort(key=lambda x: x["return_pct"], reverse=True)
        return {"sectors": results}
    except Exception as e:
        print(f"Error fetching sectors: {e}")
        return {"sectors": []}

@app.get("/api/cron/daily-scan")
async def cron_daily_scan():
    try:
        # Update market trend
        from services.market_data import MarketDataFetcher
        from datetime import datetime
        import pytz
        
        md_fetcher = MarketDataFetcher()
        status, exposure = md_fetcher.evaluate_market_trend()
        now_str = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S")
        db.update_market_status(status, exposure, now_str)

        # scan_universe 로직 재사용
        scan_res = scan_universe()
        results = scan_res.get("results", [])
        
        # BUY 셋업 종목 필터링
        buy_list = [r for r in results if r["action"] == "BUY" and r["score"] >= 15]
        
        if buy_list:
            description = f"오늘의 최상위(15점 이상) BUY 셋업 종목이 {len(buy_list)}개 발견되었습니다."
            fields = []
            for item in buy_list[:10]: # 최대 10개만
                fields.append({
                    "name": f"🚀 {item['ticker']} (Score: {item['score']}/20)",
                    "value": f"전략: {item['strategy']}\n진입가: ${item['entryPivot']}\n손절가: ${item['stopLoss']}",
                    "inline": False
                })
            
        return {"status": "success", "found": len(buy_list)}
    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cron/intraday-scan")
async def cron_intraday_scan():
    try:
        from datetime import datetime
        import pytz
        import yfinance as yf
                
        # 1. Fetch portfolio
        res_portfolio = await get_portfolio()
        portfolio = res_portfolio.get("portfolio", [])
        
        # 2. Fetch latest_setups and scan_results/latest
        setup_data = db.get_latest_detected_setups()
        setups = setup_data.get("items", []) if setup_data else []
        
        latest_scan_data = db.get_latest_scan_results()
        latest_results = latest_scan_data.get("results", []) if latest_scan_data else []
        
        # Create a unified set of tickers
        all_tickers = set()
        for item in portfolio:
            t = item.get("Ticker", item.get("ticker"))
            if t: all_tickers.add(t)
            
        for item in setups:
            t = item.get("ticker", item.get("Ticker"))
            if t: all_tickers.add(t)
            
        for item in latest_results:
            t = item.get("ticker", item.get("Ticker"))
            if t: all_tickers.add(t)
            
        all_tickers = list(all_tickers)
        if not all_tickers:
            return {"status": "no tickers"}
            
        # 3. Fetch fast_info in a loop
        price_map = {}
        for t in all_tickers:
            try:
                t_obj = yf.Ticker(t)
                price = t_obj.fast_info.get("lastPrice")
                if price and price > 0:
                    price_map[t] = price
            except Exception:
                continue
                
        alerts_sent = 0
        fields = []
        
        # 4. Check Portfolio for Stop Loss & 20MA
        for item in portfolio:
            t = item.get("Ticker", item.get("ticker"))
            if t not in price_map: continue
            
            current_price = price_map[t]
            trailing_stop = float(item.get("trailingStop", 0)) if item.get("trailingStop") else 0
            ma20 = float(item.get("ma20", 0)) if item.get("ma20") else 0
            
            # Check 10MA trailing stop
            if trailing_stop > 0 and current_price < trailing_stop:
                fields.append({
                    "name": f"🚨 [보유종목] {t} 손절가(10MA) 이탈!",
                    "value": f"현재가: **${current_price:.2f}** < 10MA: ${trailing_stop:.2f}\n(포트폴리오 비중 축소 또는 전량 매도 고려)",
                    "inline": False
                })
            # Check 20MA
            elif ma20 > 0 and current_price < ma20:
                fields.append({
                    "name": f"⚠️ [보유종목] {t} 20MA 이탈 경고!",
                    "value": f"현재가: **${current_price:.2f}** < 20MA: ${ma20:.2f}",
                    "inline": False
                })
                
        # 5. Check Setups for Entry Breakout & update prices
        for item in setups:
            t = item.get("ticker", item.get("Ticker"))
            if t in price_map:
                current_price = price_map[t]
                item["currentPrice"] = current_price
                
                entry_pivot = float(item.get("entry_pivot", 0)) if item.get("entry_pivot") else 0
                if entry_pivot > 0 and current_price >= entry_pivot:
                    fields.append({
                        "name": f"🚀 [신규포착] {t} 진입가 돌파!",
                        "value": f"현재가: **${current_price:.2f}** >= 진입가: ${entry_pivot:.2f}\n전략: {item.get('strategy', 'N/A')}",
                        "inline": False
                    })
                    
        # Update latest_results prices
        for item in latest_results:
            t = item.get("ticker", item.get("Ticker"))
            if t in price_map:
                item["currentPrice"] = price_map[t]
                if "current_price" in item:
                    item["current_price"] = price_map[t]
            
        # 6. Send Discord alert if any fields
        if fields:
            # Batch them into 25 fields per embed limit
            chunked_fields = [fields[i:i+25] for i in range(0, len(fields), 25)]
            for chunk in chunked_fields:
                alerts_sent += len(chunk)
                
        # 7. Update Firestore latest_setups and scan_results/latest with new prices
        now_str = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S")
        
        # update latest_setups
        if setup_data:
            setup_data["items"] = setups
            setup_data["last_scanned_at"] = now_str
            db.save_detected_setups(setup_data)
            
        # update scan_results/latest
        if latest_results:
            db.save_scan_results(latest_results, now_str)
        
        return {
            "status": "success", 
            "prices_fetched": len(price_map), 
            "alerts_sent": alerts_sent,
            "timestamp": now_str
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/cron/risk-check")
async def cron_risk_check():
    try:
        res = await get_portfolio()
        portfolio = res.get("portfolio", [])
        
        triggered = []
        for item in portfolio:
            ticker = item.get("Ticker")
            current = float(item.get("CurrentPrice", 0))
            stop = float(item.get("trailingStop", 0))
            
            if current > 0 and stop > 0 and current < stop:
                triggered.append(item)
                
        if triggered:
            fields = []
            for item in triggered:
                fields.append({
                    "name": f"🚨 {item['Ticker']} 손절가 이탈!",
                    "value": f"현재가: ${item['CurrentPrice']} < 손절가(10MA): ${item['trailingStop']}",
                    "inline": False
                })

            
        return {"status": "success", "triggered": len(triggered)}
    except Exception as e:
        print(f"Risk check failed: {e}")
        return {"status": "error", "message": str(e)}



class SeedDataReq(BaseModel):
    items: List[Dict[str, Any]]

@app.post("/api/admin/seed-universe")
async def seed_universe(req: SeedDataReq):
    try:
        from services.db_connector import db
        count = 0
        tickers = []
        for item in req.items:
            ticker = item.get("Ticker", item.get("ticker"))
            name = item.get("Company Name", item.get("name", ticker))
            if ticker:
                db.add_to_universe(ticker, name)
                tickers.append(ticker)
                count += 1
                
        doc_ref = db.db.collection('settings').document('favorites')
        doc_ref.set({"tickers": tickers}, merge=True)
        return {"status": "success", "message": f"Seeded {count} items"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/admin/debug-db")
async def debug_db():
    from services.db_connector import db
    return {"db_is_none": db.db is None}

@app.get("/api/admin/debug-db-error")
async def debug_db_error():
    try:
        from google.cloud import firestore
        db = firestore.Client(project="ai-stock-506110")
        return {"status": "ok", "project": db.project}
    except Exception as e:
        import traceback
        return {"status": "error", "traceback": traceback.format_exc()}

class SeedPortfolioReq(BaseModel):
    portfolio: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]

@app.post("/api/admin/seed-portfolio")
async def seed_portfolio(req: SeedPortfolioReq):
    try:
        from services.db_connector import db
        # Set portfolio
        db.update_portfolio(req.portfolio)
        
        # Set trades
        for trade in req.trades:
            db.add_trade(trade)
            
        return {"status": "success", "portfolio": len(req.portfolio), "trades": len(req.trades)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/portfolio/export")
async def export_portfolio():
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse
    
    data = db.get_portfolio()
    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False, encoding='utf-8-sig')
    stream.seek(0)
    
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=portfolio.csv"}
    )

@app.get("/api/trades/export")
async def export_trades():
    import io
    import pandas as pd
    from fastapi.responses import StreamingResponse
    
    data = db.get_trade_history()
    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False, encoding='utf-8-sig')
    stream.seek(0)
    
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=trades.csv"}
    )

class RiskRulesReq(BaseModel):
    initial_capital: float
    risk_per_trade_pct: float
    stop_loss_pct: float
    trailing_ma: int

@app.get("/api/settings/risk-rules")
async def get_risk_rules():
    return db.get_risk_rules()

@app.post("/api/settings/risk-rules")
async def update_risk_rules(req: RiskRulesReq):
    db.update_risk_rules({
        "initial_capital": req.initial_capital,
        "risk_per_trade_pct": req.risk_per_trade_pct,
        "stop_loss_pct": req.stop_loss_pct,
        "trailing_ma": req.trailing_ma
    })
    return {"status": "success"}

@app.get("/api/market/status")
async def get_market_status():
    return db.get_market_status()

@app.get("/api/cron/scan-sp500")
def cron_scan_sp500():
    try:
        from datetime import datetime
        import pytz
        now_str = datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d %H:%M:%S")
        
        # 전체 유니버스 스캔 로직 재사용
        scan_res = scan_universe()
        all_results = scan_res.get("results", [])
        total_scanned = len(db.get_universe_tickers()) # 대략적인 수치
        
        # 필터링: BUY 시그널이 발생한 종목만
        universe_list = db.get_universe()
        ticker_name_map = {u["ticker"]: u.get("name", u["ticker"]) for u in universe_list if "ticker" in u}
        
        detected_items = []
        for r in all_results:
            if r.get("action") == "BUY":
                # Schema mapping
                ticker = r.get("ticker", "")
                item = {
                    "ticker": ticker,
                    "name": ticker_name_map.get(ticker, ticker),
                    "strategy": r.get("strategy", ""),
                    "signal": "BUY",
                    "detected_at": now_str,
                    "detected_price": round(float(r.get("currentPrice", 0)), 2),
                    "current_price": round(float(r.get("currentPrice", 0)), 2),
                    "entry_pivot": round(float(r.get("entryPivot", 0) or 0), 2),
                    "stop_loss": round(float(r.get("stopLoss", 0) or 0), 2),
                    "score": int(r.get("score", 0)),
                    "ai_summary": " ".join(r.get("summary", []))
                }
                detected_items.append(item)
                
        # 1. Update all_results using scan_results/latest (scan_history snapshot)
        prev_scan_data = db.get_latest_scan_results()
        prev_scan_items = {item.get("ticker"): item for item in prev_scan_data.get("results", []) if item.get("ticker")}
        
        for item in all_results:
            ticker = item["ticker"]
            if ticker in prev_scan_items:
                item["is_new"] = False
                item["streak_days"] = int(prev_scan_items[ticker].get("streak_days", 1)) + 1
            else:
                item["is_new"] = True
                item["streak_days"] = 1
                
        # 2. Update detected_items using latest_setups (for setups UI)
        prev_data = db.get_latest_detected_setups()
        prev_items = {item["ticker"]: item for item in prev_data.get("items", [])}
        
        for item in detected_items:
            ticker = item["ticker"]
            if ticker in prev_items:
                item["is_new"] = False
                item["streak_days"] = int(prev_items[ticker].get("streak_days", 1)) + 1
                item["detected_at"] = prev_items[ticker].get("detected_at", item["detected_at"])
                item["detected_price"] = float(prev_items[ticker].get("detected_price", item["detected_price"]))
            else:
                item["is_new"] = True
                item["streak_days"] = 1

        # 높은 점수 순으로 정렬
        detected_items.sort(key=lambda x: x["score"], reverse=True)
                
        schema_data = {
            "last_scanned_at": now_str,
            "total_scanned": total_scanned,
            "detected_count": len(detected_items),
            "items": detected_items
        }
        
        # Firestore에 덮어쓰기 및 히스토리 저장
        db.save_detected_setups(schema_data)
        
        # scan_results/latest (및 scan_history) 에도 전체 결과 저장
        db.save_scan_results(all_results, now_str)
        
        return {"status": "success", "data": schema_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/scan/detected")
async def get_scan_detected():
    data = db.get_latest_detected_setups()
    return data

# ==========================================
# Virtual Trading Endpoints
# ==========================================
@app.get("/api/virtual/portfolio")
async def get_virtual_portfolio():
    return db.get_virtual_portfolio()

class VirtualPortfolioUpdateReq(BaseModel):
    ticker: str
    quantity: int
    avgPrice: float
    purchaseDate: str
    strategy: Optional[str] = None
    factor_score: Optional[float] = 0.0
    setup: Optional[str] = ""

@app.post("/api/virtual/portfolio/update")
async def update_virtual_portfolio(req: VirtualPortfolioUpdateReq):
    prices = market_fetcher.get_historical_prices(req.purchaseDate)
    spy_entry = prices.get("SPY", 0.0)
    qqq_entry = prices.get("QQQ", 0.0)

    result = db.update_virtual_portfolio_item(
        req.ticker, req.quantity, req.avgPrice, req.purchaseDate, 
        req.strategy, req.factor_score, req.setup, spy_entry, qqq_entry
    )
    if result == "success":
        return {"status": "success"}
    raise HTTPException(status_code=500, detail=result)

class VirtualCloseReq(BaseModel):
    ticker: str
    sell_price: float
    sell_quantity: int
    exit_reason: str
    strategy: str

@app.post("/api/virtual/portfolio/close")
async def close_virtual_position(req: VirtualCloseReq):
    from datetime import datetime
    import pytz
    
    portfolio = db.get_virtual_portfolio()
    asset = next((item for item in portfolio if item.get("Ticker") == req.ticker), None)
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found in virtual portfolio")
    
    current_quantity = asset.get("Quantity", 0)
    if req.sell_quantity > current_quantity:
        raise HTTPException(status_code=400, detail="Cannot sell more than owned")
        
    avg_price = asset.get("AvgPrice", 0)
    profit_loss = (req.sell_price - avg_price) * req.sell_quantity
    profit_rate = ((req.sell_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
    
    now_str = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d")
    prices = market_fetcher.get_historical_prices(now_str)
    spy_exit = prices.get("SPY", 0.0)
    qqq_exit = prices.get("QQQ", 0.0)
    
    trade_data = {
        "ticker": req.ticker,
        "strategy": req.strategy,
        "setup": asset.get("setup", ""),
        "entry_price": avg_price,
        "exit_price": req.sell_price,
        "profit_loss": profit_loss,
        "profit_rate": profit_rate,
        "quantity": req.sell_quantity,
        "entry_date": asset.get("PurchaseDate", ""),
        "exit_date": now_str,
        "exit_reason": req.exit_reason,
        "factor_score": asset.get("factor_score", 0),
        "spy_entry": asset.get("spy_entry", 0),
        "qqq_entry": asset.get("qqq_entry", 0),
        "spy_exit": spy_exit,
        "qqq_exit": qqq_exit
    }
    
    db.add_virtual_trade(trade_data)
    
    remaining = current_quantity - req.sell_quantity
    db.update_virtual_portfolio_item(
        req.ticker, 
        remaining, 
        avg_price, 
        asset.get("PurchaseDate", ""),
        asset.get("Strategy"),
        asset.get("factor_score", 0),
        asset.get("setup", ""),
        asset.get("spy_entry", 0),
        asset.get("qqq_entry", 0)
    )
    
    return {"status": "success", "message": f"Sold {req.sell_quantity} of {req.ticker} virtually"}

@app.get("/api/virtual/performance")
async def get_virtual_performance(initial_capital: float = 10000000):
    trades = db.get_virtual_trade_history()
    stats = performance_engine.calculate_account_metrics(trades, initial_capital)
    return stats

@app.get("/api/virtual/history")
async def get_virtual_history():
    return db.get_virtual_trade_history()

