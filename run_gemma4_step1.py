import requests

def call_gemma4():
    url = "http://localhost:11434/api/generate"
    prompt = """
너는 미국 주식 AI 트레이딩 시스템의 '포워드 테스팅(전진 가상 매매) 시스템' 구축을 담당하는 코딩 에이전트야.
다음은 너의 PM(안티그래비티)이 너에게 내리는 지시사항이야:

[지시사항]
Supabase에 가상 매매 전용 테이블 3개(`virtual_portfolio`, `virtual_trade_history`, `virtual_daily_logs`)를 생성하는 SQL 쿼리를 작성해. 
포트폴리오에는 팩터 점수(factor_score)와 셋업 종류(strategy_type) 필드를 반드시 포함해.

위 지시사항에 맞는 SQL 스크립트를 작성해서 코드 블록으로만 응답해. 부연 설명은 하지 마.
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
