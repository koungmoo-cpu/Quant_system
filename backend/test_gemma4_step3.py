import requests

def call_gemma4():
    url = "http://localhost:11434/api/generate"
    prompt = """
너는 미국 주식 AI 트레이딩 시스템의 '포워드 테스팅(전진 가상 매매) 시스템' 구축을 담당하는 코딩 에이전트야.
다음은 너의 PM(안티그래비티)이 너에게 내리는 세 번째 지시사항이야:

[지시사항]
이전 단계에서 만든 `virtual_trading_loop.py`에 청산(Exit) 로직 함수 `evaluate_exit_condition(slot)`을 추가해.
청산 로직은 진입 전략(strategy_type)에 따라 다르게 적용해야 해:
1. 'EP' (쿨라매기 EP): 15% 수익 도달 시 50% 익절(매도)하고, 이후 10일선(mock price를 10일선으로 가정) 하향 이탈 시 트레일링 스탑으로 전량 매도.
2. 'VCP' (미너비니 VCP): 20% 수익 도달 시 50% 익절(매도)하고, 이후 20일선(mock price를 20일선으로 가정) 하향 이탈 시 트레일링 스탑으로 전량 매도.
3. [공통]: 고점 대비가 아닌 진입가 대비 -5% 하락 시에는 무조건 즉각 전량 손절.
4. 매도(청산)가 발생하면 `virtual_trade_history` 리스트(메모리 기반 Mock)에 딕셔너리 형태로 데이터를 추가해. 정확한 청산 사유(`exit_reason` 예: 'STOP_LOSS', 'TAKE_PROFIT_50', 'TRAILING_STOP')와 최종 수익률이 포함되어야 해.
5. 코드 맨 아래에 `if __name__ == '__main__':` 블록에서 'EP' 전략 종목 1개와 'VCP' 전략 종목 1개를 강제로 수익률 -6%(손절), 16%(EP 익절), 21%(VCP 익절) 상황으로 각각 시뮬레이션하고, `virtual_trade_history`에 정확한 청산 사유가 Insert된 결과를 "✅ 청산 로직 검증 완료" 메시지와 함께 출력해.

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
