import requests

def call_gemma4():
    url = "http://localhost:11434/api/generate"
    prompt = """
너는 미국 주식 AI 트레이딩 시스템의 '포워드 테스팅(전진 가상 매매) 시스템' 구축을 담당하는 코딩 에이전트야.
다음은 너의 PM(안티그래비티)이 너에게 내리는 마지막 네 번째 지시사항이야:

[지시사항]
이전 단계들에서 생성된 `virtual_trade_history` 리스트(청산이 완료된 딕셔너리 리스트)를 바탕으로, 가상 매매 성과를 통계 내는 함수 `calculate_performance_stats(history)`를 파이썬으로 작성해.
다음 조건들을 스크립트에 반드시 포함시켜야 해:
1. 전체 승률 (총 거래 건수 중 최종 수익률이 0보다 큰 거래의 비율)과 전체 평균 수익률.
2. 진입 전략(`strategy_type`: 'EP', 'VCP')별 평균 수익률 및 승률.
3. 맨 아래 `if __name__ == '__main__':` 블록에서 가상의 Mock 데이터 (EP와 VCP 전략이 섞여 있고, 수익 및 손실 건이 포함된 총 10개 정도의 딕셔너리를 포함하는 `virtual_trade_history` 리스트)를 강제로 생성해.
4. 해당 Mock 데이터를 `calculate_performance_stats(history)` 함수에 넣고 실행한 뒤, 터미널에 통계 결과를 깔끔하게 출력하고 마지막에 "✅ 성과 분석 통계 엔진 동작 확인 완료" 메시지를 명확히 출력해.

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
