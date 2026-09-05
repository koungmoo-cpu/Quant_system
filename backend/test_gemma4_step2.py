import requests

def call_gemma4():
    url = "http://localhost:11434/api/generate"
    prompt = """
너는 미국 주식 AI 트레이딩 시스템의 '포워드 테스팅(전진 가상 매매) 시스템' 구축을 담당하는 코딩 에이전트야.
다음은 너의 PM(안티그래비티)이 너에게 내리는 두 번째 지시사항이야:

[지시사항]
파이썬으로 매일 100개의 포트폴리오 슬롯을 운용하는 가상 매매 반복문(Loop) 스크립트(`virtual_trading_loop.py`)의 뼈대를 만들어. 
다음 조건들을 스크립트에 반드시 포함시켜야 해:
1. DB 연결 없이 실행 가능하도록 메모리 기반 Mock 데이터 구조(리스트/딕셔너리)를 사용해서 동작하게 만들 것. (통과 검증용)
2. 루프를 실행하면 빈 슬롯에 "스캐너 총점 8점 이상 종목을 채웠습니다" 라는 시뮬레이션 처리를 하고, 100개의 슬롯이 유지되는지 확인.
3. 보유 중인 종목에 대해 가상의 "당일 종가"와 "수익률"을 계산하여 `virtual_daily_logs` 처럼 로깅하는 기능.
4. 스크립트 맨 아래에 `if __name__ == '__main__':`을 통해 실행했을 때, "✅ 100개 슬롯 로딩 및 데일리 로깅 엔진 동작 확인 완료"라는 완료 메시지와 함께 슬롯 100개가 채워졌다는 결과가 터미널에 명확히 출력되도록 작성해.

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
