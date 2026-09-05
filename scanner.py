import yfinance as yf
import pandas as pd
import json
import sys
import os

# backend 디렉토리를 path에 추가하여 config.py를 불러올 수 있게 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from config import settings
except ImportError:
    class MockSettings:
        google_genai_api_key = os.environ.get("GOOGLE_GENAI_API_KEY", "")
    settings = MockSettings()

def is_momentum_growth_stock(df: pd.DataFrame) -> tuple[bool, str]:
    """
    사전 변동성/유동성 필터 (Pre-filter)
    무거운 안정주나 호가창이 얇은 잡주를 걸러냅니다.
    반환값: (통과여부, 탈락사유문자열)
    """
    if len(df) < 20:
        return False, "데이터 부족 (20일 미만)"
        
    # 1. ADR 필터: 최근 20일 일일 변동폭 평균 >= 3.5%
    adr_20 = ((df['High'] / df['Low']) - 1).tail(20).mean() * 100
    
    # 2. 유동성 필터: 최근 20일 평균 거래대금 >= $15,000,000
    dollar_vol_20 = (df['Close'] * df['Volume']).tail(20).mean()
    
    if adr_20 < 3.5:
        return False, f"ADR 필터 미달 (현재 {adr_20:.1f}%, 기준 3.5%) - 무거운 주식"
    if dollar_vol_20 < 15000000:
        return False, f"유동성 필터 미달 (현재 ${dollar_vol_20/1000000:.1f}M, 기준 $15M) - 호가창 얇음"
        
    return True, "통과"

def master_strategy_analyzer(ticker: str):
    """
    주어진 티커의 데이터를 분석하여 5가지 전략 중 하나로 분류하는 라우터
    """
    df = yf.download(ticker, period="1y", progress=False)
    
    if df.empty:
        return {'ticker': ticker, 'score': 0, 'strategy': 'Data Error', 'stop_loss': None, 'entry_pivot': None, 'details': ['데이터 오류']}
    
    # yfinance 최신 버전의 MultiIndex 컬럼 평탄화
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
        
    # [Pre-filter] 변동성/유동성 필터 적용 (무거운 안정주, 잡주 제외)
    is_valid_stock, filter_reason = is_momentum_growth_stock(df)
    if not is_valid_stock:
        return {
            'ticker': ticker, 
            'score': 0,
            'strategy': 'No Setup (Low Volatility/Stable)', 
            'stop_loss': None, 
            'entry_pivot': None, 
            'details': [f"[사전 필터 탈락] {filter_reason}"]
        }

    score = calculate_momentum_score(df)

    # 1. 이동평균선(10, 20, 50, 150, 200) 및 최근 데이터 계산
    df['SMA10'] = df['Close'].rolling(window=10).mean()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA150'] = df['Close'].rolling(window=150).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    df['AvgVol20'] = df['Volume'].rolling(window=20).mean()
    
    # 최근 3일, 20일, 40일(약 8주) 최고/최저가
    df['High3'] = df['High'].rolling(window=3).max()
    df['High20'] = df['High'].rolling(window=20).max()
    df['High40'] = df['High'].rolling(window=40).max()
    df['Low40'] = df['Low'].rolling(window=40).min()
    df['Low20'] = df['Low'].rolling(window=20).min()
    
    # 갭상승 계산 및 당일 진입 기준을 위한 전일 데이터
    df['PrevClose'] = df['Close'].shift(1)
    df['PrevHigh'] = df['High'].shift(1)
    
    # 데이터가 200일 미만이면 SMA200 계산 불가
    df_valid = df.dropna()
    if len(df_valid) < 1:
        return {'ticker': ticker, 'score': score, 'strategy': 'Not Enough Data (200d)', 'stop_loss': None, 'entry_pivot': None}
        

    latest = df_valid.iloc[-1]
    
    # Get intraday real-time price using fast_info
    try:
        t_obj = yf.Ticker(ticker)
        fast_price = t_obj.fast_info.get('lastPrice', None)
        if fast_price is not None and fast_price > 0:
            C_price = float(fast_price)
        else:
            C_price = float(latest['Close'])
    except Exception:
        C_price = float(latest['Close'])
        
    ret_5d = round(((C_price - float(df_valid.iloc[-5]['Close'])) / float(df_valid.iloc[-5]['Close'])) * 100, 2) if len(df_valid) >= 5 else 0
    ret_10d = round(((C_price - float(df_valid.iloc[-10]['Close'])) / float(df_valid.iloc[-10]['Close'])) * 100, 2) if len(df_valid) >= 10 else 0
    ret_20d = round(((C_price - float(df_valid.iloc[-20]['Close'])) / float(df_valid.iloc[-20]['Close'])) * 100, 2) if len(df_valid) >= 20 else 0

    # 숫자 값들 추출 (pandas 2.0+ Series 처리를 위해 float로 변환)
    C = C_price
    O = float(latest['Open'])
    L = float(latest['Low'])
    V = float(latest['Volume'])
    PC = float(latest['PrevClose'])
    
    sma10 = float(latest['SMA10'])
    sma20 = float(latest['SMA20'])
    sma50 = float(latest['SMA50'])
    sma150 = float(latest['SMA150'])
    sma200 = float(latest['SMA200'])
    
    avg_vol20 = float(latest['AvgVol20'])
    high3 = float(latest['High3'])
    high20 = float(latest['High20'])
    high40 = float(latest['High40'])
    low40 = float(latest['Low40'])
    low20 = float(latest['Low20'])
    prev_high = float(latest['PrevHigh'])

    # === 우선순위 기반 전략 판별 로직 ===
    details = []

    # 1순위: [Qullamaggie - EP] 당일 5% 이상 갭상승 & 거래량 300% 폭발
    gap_up = (O / PC) >= 1.05
    vol_surge = (V / avg_vol20) >= 3.0 if avg_vol20 > 0 else False
    details.append(f"[EP] 갭상승({'O' if gap_up else 'X'}), 거래량폭발({'O' if vol_surge else 'X'})")
    if gap_up and vol_surge:
        ep_entry = O if O > prev_high else prev_high
        return {'ticker': ticker, 'score': score, 'strategy': 'Qullamaggie - EP', 'stop_loss': round(L, 2), 'entry_pivot': round(ep_entry, 2), 'details': details, 'ret_5d': ret_5d, 'ret_10d': ret_10d, 'ret_20d': ret_20d, 'currentPrice': round(C_price, 2)}
        
    # 2순위: [Minervini - Power Play] 8주 저점 대비 100% 상승 & 현재가 고점 대비 -20% 이내 횡보 & 단기 이평선(10, 20) 위
    up_100 = (high40 / low40) >= 2.0 if low40 > 0 else False
    consolidation = C >= (high40 * 0.8)
    above_short_mas = (C > sma10) and (C > sma20)
    details.append(f"[PowerPlay] 100%급등({'O' if up_100 else 'X'}), 20%내수렴({'O' if consolidation else 'X'}), 10/20일선위({'O' if above_short_mas else 'X'})")
    if up_100 and consolidation and above_short_mas:
        power_play_stop = max(sma10, C * 0.95)
        return {'ticker': ticker, 'score': score, 'strategy': 'Minervini - Power Play', 'stop_loss': round(power_play_stop, 2), 'entry_pivot': round(high3, 2), 'details': details, 'ret_5d': ret_5d, 'ret_10d': ret_10d, 'ret_20d': ret_20d, 'currentPrice': round(C_price, 2)}
        
    # 3순위: [Qullamaggie - Breakout] 10/20일선 위 & 20일 고점 대비 -5% 이내 바짝 수렴
    above_mas = (C > sma10) and (C > sma20)
    tight_near_high = C >= (high20 * 0.95)
    details.append(f"[Breakout] 10/20일선 위({'O' if above_mas else 'X'}), 20일고점부근 수렴({'O' if tight_near_high else 'X'})")
    if above_mas and tight_near_high:
        return {'ticker': ticker, 'score': score, 'strategy': 'Qullamaggie - Breakout', 'stop_loss': round(sma20, 2), 'entry_pivot': round(high3, 2), 'details': details, 'ret_5d': ret_5d, 'ret_10d': ret_10d, 'ret_20d': ret_20d, 'currentPrice': round(C_price, 2)}
        
    # 4순위: [Minervini - Pullback Bounce] 150/200일선 정배열 & 주가가 50일선 첫 터치(±2% 이내)
    trend_template = (sma150 > sma200) and (C > sma200)
    touch_50 = abs(C - sma50) / sma50 <= 0.02
    details.append(f"[Pullback] 정배열({'O' if trend_template else 'X'}), 50일선 터치({'O' if touch_50 else 'X'})")
    if trend_template and touch_50:
        return {'ticker': ticker, 'score': score, 'strategy': 'Minervini - Pullback Bounce', 'stop_loss': round(sma50 * 0.98, 2), 'entry_pivot': round(sma50, 2), 'details': details, 'ret_5d': ret_5d, 'ret_10d': ret_10d, 'ret_20d': ret_20d, 'currentPrice': round(C_price, 2)}
        
    # 5순위: [Minervini - VCP] 200일선 위 & 3주 이상 변동성 축소(고저폭 15% 이내로 가정) & 거래량 마름
    vcp_tight = (high20 - low20) / low20 <= 0.15 if low20 > 0 else False
    vol_dry = V < avg_vol20
    c_above_200 = C > sma200
    details.append(f"[VCP] 200일선 위({'O' if c_above_200 else 'X'}), 변동성축소({'O' if vcp_tight else 'X'}), 거래량마름({'O' if vol_dry else 'X'})")
    if c_above_200 and vcp_tight and vol_dry:
        return {'ticker': ticker, 'score': score, 'strategy': 'Minervini - VCP', 'stop_loss': round(C * 0.95, 2), 'entry_pivot': round(high3, 2), 'details': details, 'ret_5d': ret_5d, 'ret_10d': ret_10d, 'ret_20d': ret_20d, 'currentPrice': round(C_price, 2)}
        
    # 5가지 모두 실패
    return {'ticker': ticker, 'score': score, 'strategy': 'No Setup (관망)', 'stop_loss': None, 'entry_pivot': None, 'details': details}

def get_gemini_master_signal(analyzed_data: dict) -> str:
    from google import genai
    from google.genai import types
    
    api_key = settings.google_genai_api_key
    if not api_key:
        return "[AI_Fallback] " + ", ".join(analyzed_data.get('details', []))
        
    client = genai.Client(api_key=api_key)
    
    prompt = f"당신은 퀀트 트레이딩 AI입니다. 파이썬이 분류한 셋업 데이터({json.dumps(analyzed_data, ensure_ascii=False)})를 바탕으로, 해당 전략의 원칙에 맞추어 '매수하십시오(BUY)' 또는 '관망하십시오(WAIT)'라는 명확한 지시와 함께 목표가/손절가를 3줄 이내로 브리핑해 주세요."
    
    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2)
        )
        return response.text
    except Exception as e:
        return f"AI API Error: {str(e)}"

import concurrent.futures

def get_index_tickers():
    """
    S&P 500, Nasdaq 100, 다우 30 티커를 위키피디아에서 스크래핑하여 중복을 제거한 리스트 반환
    """
    try:
        # html5lib 또는 lxml 필요할 수 있으나 pandas 기본 리더 사용
        sp500 = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]['Symbol'].tolist()
        ndx = pd.read_html('https://en.wikipedia.org/wiki/Nasdaq-100')[4]['Ticker'].tolist()
        dji = pd.read_html('https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average')[1]['Symbol'].tolist()
        
        all_tickers = set(sp500 + ndx + dji)
        clean_tickers = [t.replace('.', '-') for t in all_tickers]
        return list(clean_tickers)
    except Exception as e:
        print(f"Error fetching index tickers: {e}")
        return ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL"]

def fetch_single_ticker_1mo(ticker):
    """ThreadPoolExecutor에서 사용하기 위한 단일 티커 1개월 데이터 수집 함수"""
    try:
        df = yf.download(ticker, period="1mo", progress=False, threads=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()
        if len(df) >= 10:
            return ticker, df
        return ticker, None
    except Exception:
        return ticker, None

def fast_pre_filter(tickers):
    """
    1차 깔때기 필터 (속도 최적화):
    ThreadPoolExecutor를 사용해 최근 1개월 데이터만 병렬 수집 후,
    최근 20일 평균 거래대금 1,500만 달러 이상 & ADR 3.5% 이상인 종목만 필터링.
    """
    valid_tickers = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ticker = {executor.submit(fetch_single_ticker_1mo, t): t for t in tickers}
        for future in concurrent.futures.as_completed(future_to_ticker):
            ticker, df = future.result()
            if df is not None:
                try:
                    adr_20 = ((df['High'] / df['Low']) - 1).tail(20).mean() * 100
                    dollar_vol_20 = (df['Close'] * df['Volume']).tail(20).mean()
                    
                    if adr_20 >= 3.5 and dollar_vol_20 >= 15000000:
                        valid_tickers.append(ticker)
                except Exception:
                    pass
                    
    return valid_tickers

def calculate_momentum_score(df: pd.DataFrame) -> int:
    """
    20점 만점 팩터 스코어링 엔진 (Phase 3)
    1. 상대강도 (5점)
    2. 수급 강도 (5점)
    3. 50일선 이격도 (5점)
    4. 변동성 축소 (5점)
    """
    score = 0
    
    if len(df) < 120:  # 최소 6개월 데이터 필요
        return score
        
    try:
        latest = df.iloc[-1]
        C = float(latest['Close'])
        V = float(latest['Volume'])
        
        # 1. 상대강도 (Relative Strength)
        high52 = float(df['High'].tail(252).max()) if len(df) >= 252 else float(df['High'].max())
        momentum_6m = C / float(df['Close'].iloc[-120]) if len(df) >= 120 else 1.0
        
        if C >= high52 * 0.95: score += 3
        elif C >= high52 * 0.85: score += 1
        
        if momentum_6m >= 1.5: score += 2
        elif momentum_6m >= 1.2: score += 1
        
        # 2. 수급 강도 (Volume/Supply)
        avg_vol20 = float(df['Volume'].tail(20).mean())
        if V >= avg_vol20 * 2.0: score += 3
        elif V >= avg_vol20 * 1.5: score += 1
        
        recent_20 = df.tail(20)
        up_vol = recent_20[recent_20['Close'] > recent_20['Open']]['Volume'].sum()
        down_vol = recent_20[recent_20['Close'] < recent_20['Open']]['Volume'].sum()
        if up_vol > down_vol * 1.5: score += 2
        elif up_vol > down_vol: score += 1
        
        # 3. 50일선 이격도 (50MA Separation)
        sma50 = float(df['Close'].rolling(50).mean().iloc[-1])
        gap_50 = (C - sma50) / sma50
        if 0 < gap_50 <= 0.05: score += 5
        elif 0.05 < gap_50 <= 0.15: score += 3
        elif gap_50 > 0.15: score += 1
        
        # 4. 변동성 축소 (VCP Tightness)
        high15 = float(recent_20['High'].tail(15).max())
        low15 = float(recent_20['Low'].tail(15).min())
        tightness = (high15 - low15) / low15
        if tightness <= 0.10: score += 5
        elif tightness <= 0.15: score += 3
        elif tightness <= 0.20: score += 1
        
    except Exception as e:
        print(f"Error calculating score: {e}")
        
    return min(score, 20)

