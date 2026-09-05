import requests

def call_gemma4():
    url = "http://localhost:11434/api/generate"
    prompt = """
방금 네가 작성한 Supabase용 SQL을 로컬에서 검증하기 위해, SQLite3 문법으로 변환하여 `virtual_trading_schema.db`에 테이블을 생성하는 파이썬 스크립트를 작성해줘. 
스크립트를 실행하면 "✅ 가상 매매 DB 마이그레이션 완료 (virtual_portfolio, virtual_trade_history, virtual_daily_logs 테이블 생성 성공)" 이라는 완료 메시지가 출력되도록 해.
결과는 파이썬 코드 블록으로만 대답해.
"""
    payload = {
        "model": "gemma4",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print(response.json().get("response", ""))
    except Exception as e:
        print(f"Error calling Gemma4: {e}")

call_gemma4()
