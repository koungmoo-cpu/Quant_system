import requests

def call_gemma4():
    url = "http://localhost:11434/api/generate"
    prompt = """
(수정 지시 - Strike 1) 
네가 작성한 SQLite3 변환 스크립트에서 `virtual_portfolio` 테이블에 PM이 지시했던 **'factor_score(팩터 점수)'**와 **'strategy_type(셋업 종류)'** 필드가 누락되었어! 

다시 작성해서, 반드시 `virtual_portfolio` 테이블에 두 필드를 포함시키고, 스크립트 실행 시 "✅ 가상 매매 DB 마이그레이션 완료 (virtual_portfolio, virtual_trade_history, virtual_daily_logs 테이블 생성 성공)" 메시지가 출력되도록 수정해.
오직 파이썬 코드 블록으로만 대답해.
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
