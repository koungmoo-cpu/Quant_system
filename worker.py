import yfinance as yf
import pandas as pd
import numpy as np
import requests

def get_sp500_tickers():
    """
    위키피디아에서 S&P 500 종목 리스트를 가져옵니다.
    """
    print("S&P 500 종목 리스트를 가져오는 중...")
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    from io import StringIO
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
    response = requests.get(url, headers=headers)
    tables = pd.read_html(StringIO(response.text))
    df = tables[0]
    tickers = df['Symbol'].tolist()
    
    # 야후 파이낸스 티커 형식으로 변환 (예: BRK.B -> BRK-B)
    tickers = [ticker.replace('.', '-') for ticker in tickers]
    return tickers

def fetch_data_and_filter(tickers):
    """
    yfinance를 사용해 주가 데이터를 가져오고 1차 필터링 로직을 수행합니다.
    - 최근 20일 평균 거래대금 $15M 이상
    - 최근 20일 일일 변동폭(ADR) 평균 3.5% 이상
    """
    print(f"총 {len(tickers)}개 종목의 최근 1달 데이터를 다운로드합니다...")
    
    # yfinance를 사용하여 여러 종목 데이터를 한 번에 다운로드
    # 최근 1개월(약 21 거래일) 데이터 가져오기
    data = yf.download(tickers, period="1mo", group_by="ticker", threads=True, progress=False)
    
    passed_tickers = []
    
    for ticker in tickers:
        try:
            # 해당 티커의 데이터가 존재하는지 확인
            if ticker in data and not data[ticker].empty:
                df = data[ticker].copy()
            elif isinstance(data.columns, pd.MultiIndex) and ticker in data.columns.levels[0]:
                df = data[ticker].copy()
            else:
                continue
                
            # 데이터가 20일 이상 충분한지 확인
            if len(df) < 20:
                continue
                
            # 최근 20일 데이터로 자르기
            df = df.tail(20)
            
            # 평균 거래대금(Dollar Volume) 계산 = Close * Volume
            df['DollarVolume'] = df['Close'] * df['Volume']
            avg_dollar_volume = df['DollarVolume'].mean()
            
            # 일일 변동폭 (ADR) 계산 = (High / Low - 1) * 100
            df['ADR'] = (df['High'] / df['Low'] - 1) * 100
            avg_adr = df['ADR'].mean()
            
            # 필터링 조건
            if avg_dollar_volume >= 15_000_000 and avg_adr >= 3.5:
                passed_tickers.append({
                    'ticker': ticker,
                    'avg_dollar_volume': float(avg_dollar_volume),
                    'avg_adr': float(avg_adr)
                })
        except Exception as e:
            # 일부 종목에서 데이터 누락 등의 에러가 발생할 수 있으므로 무시
            continue
            
    return passed_tickers

from backend.services.notifier import send_discord_alert
from scanner import master_strategy_analyzer, get_gemini_master_signal
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()

def run_scan():
    print("--- Phase 1: 로컬 Worker 1단계 스크리닝 시작 ---")
    tickers = get_sp500_tickers()
    
    filtered_stocks = fetch_data_and_filter(tickers)
    
    print("\n--- 1차 필터링 결과 ---")
    print(f"조건 통과 종목 수: {len(filtered_stocks)} / {len(tickers)}")
    
    print("\n--- Phase 2: 2단계 정밀 분석 및 Scoring 시작 ---")
    passed_tickers_list = [stock['ticker'] for stock in filtered_stocks]
    
    final_results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ticker = {executor.submit(master_strategy_analyzer, ticker): ticker for ticker in passed_tickers_list}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_ticker)):
            result = future.result()
            final_results.append(result)
            if (i+1) % 10 == 0:
                print(f"진행 상황: {i+1} / {len(passed_tickers_list)}")
                
    # 점수(score) 높은 순으로 정렬
    final_results.sort(key=lambda x: x.get('score', 0), reverse=True)
    
    print("\n--- 2차 정밀 분석 결과 (Top 20) ---")
    
    setup_fields = []
    
    for i, res in enumerate(final_results[:20]):
        score = res.get('score', 0)
        strategy = res.get('strategy', 'None')
        details = res.get('details', [])
        is_setup = "No Setup" not in strategy and "Data" not in strategy
        
        print(f"{i+1:02d}. {res['ticker']:<5} | Score: {score:02d} | Strategy: {strategy}")
        if is_setup:
            print(f"    -> Entry Pivot: {res.get('entry_pivot')}, Stop Loss: {res.get('stop_loss')}")
            for d in details:
                print(f"    -> {d}")
                
            # Add to discord embed fields if it's a good setup (e.g. score >= 4)
            if score >= 4 and len(setup_fields) < 10:
                print(f"    -> [AI 분석 중...]")
                ai_summary = get_gemini_master_signal(res)
                
                setup_fields.append({
                    "name": f"{res['ticker']} (Score: {score})",
                    "value": f"**전략**: {strategy}\n**진입가**: ${res.get('entry_pivot')} | **손절가**: ${res.get('stop_loss')}\n\n**🤖 AI 분석**\n{ai_summary}",
                    "inline": False
                })
                
    print("\n--- Phase 3: 데이터베이스 연동 및 저장 시작 ---")
    try:
        from db_connector import db
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.save_scan_results(final_results, timestamp)
        print("결과가 데이터베이스에 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"DB 저장 중 에러 발생: {e}")
        
    # Send Discord Alert if setups found
    if setup_fields:
        title = "📈 AI Quant 스캐너: 신규 셋업 포착!"
        desc = f"조건에 부합하는 주요 셋업 {len(setup_fields)}개가 포착되었습니다."
        send_discord_alert(title, desc, color=0x00ff00, fields=setup_fields)
        print("디스코드 알림이 전송되었습니다.")

if __name__ == "__main__":
    run_scan()
