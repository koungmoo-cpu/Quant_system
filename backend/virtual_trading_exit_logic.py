import time
import random
from collections import deque

# =================================================================
# Mock Environment Setup (Previous steps maintained)
# =================================================================

class Stock:
    def __init__(self, ticker, initial_price, strategy_type, mock_days=100):
        self.ticker = ticker
        self.price = initial_price
        self.strategy_type = strategy_type
        self.price_history = deque([initial_price] * mock_days, maxlen=mock_days)
        self.entry_price = initial_price
        self.position_size = 1000 
        self.days = 0

    def update_price(self, new_price):
        self.price_history.append(new_price)
        self.days += 1

    def get_mock_support_level(self):
        if len(self.price_history) < 10:
            return self.price_history[-1] * 0.95
        ten_day_avg = sum(list(self.price_history)[-10:]) / 10
        return ten_day_avg

    def get_mock_support_level_20(self):
        if len(self.price_history) < 20:
            return self.price_history[-1] * 0.95
        twenty_day_avg = sum(list(self.price_history)[-20:]) / 20
        return twenty_day_avg

class Trade:
    def __init__(self, stock, initial_price):
        self.stock = stock
        self.initial_price = initial_price
        self.current_profit = 0
        self.is_open = True
        self.position_size = 1000

virtual_trade_history = []

# =================================================================
# Exit Condition Logic (New Function Implementation)
# =================================================================

def evaluate_exit_condition(trade: Trade, current_price: float, current_day: int) -> tuple[bool, float, str]:
    stock = trade.stock
    initial_price = trade.initial_price
    position_size = trade.position_size
    
    profit_ratio = (current_price - initial_price) / initial_price
    
    # 1. STOP_LOSS
    if profit_ratio <= -0.05:
        exit_reason = 'STOP_LOSS'
        print(f"\n⚠️ [🛑 EXIT] {stock.ticker}: 공통 손절(-5%) 도달. 전량 청산.")
        virtual_trade_history.append({
            'stock': stock,
            'exit_reason': exit_reason,
            'final_profit_ratio': profit_ratio,
            'exit_price': current_price,
            'initial_price': initial_price,
            'volume_exit': position_size,
            'action_type': 'FULL_SELL'
        })
        trade.position_size = 0
        return True, current_price, exit_reason

    if stock.strategy_type == 'EP':
        exit_target = 0.15
        mock_support = stock.get_mock_support_level()
        
        if current_price < mock_support and 'TAKE_PROFIT_50' in [h['exit_reason'] for h in virtual_trade_history if h['stock'].ticker == stock.ticker]:
            exit_reason = 'TRAILING_STOP'
            print(f"\n⚠️ [🛑 EXIT] {stock.ticker} (EP): 10일선 하향 이탈 ({mock_support:.2f} < {current_price:.2f}). 트레일링 스탑 발동.")
            virtual_trade_history.append({
                'stock': stock,
                'exit_reason': exit_reason,
                'final_profit_ratio': profit_ratio,
                'exit_price': current_price,
                'initial_price': initial_price,
                'volume_exit': trade.position_size,
                'action_type': 'FULL_SELL'
            })
            trade.position_size = 0
            return True, current_price, exit_reason
            
    elif stock.strategy_type == 'VCP':
        exit_target = 0.20
        mock_support = stock.get_mock_support_level_20()

        if current_price < mock_support and 'TAKE_PROFIT_50' in [h['exit_reason'] for h in virtual_trade_history if h['stock'].ticker == stock.ticker]:
            exit_reason = 'TRAILING_STOP'
            print(f"\n⚠️ [🛑 EXIT] {stock.ticker} (VCP): 20일선 하향 이탈 ({mock_support:.2f} < {current_price:.2f}). 트레일링 스탑 발동.")
            virtual_trade_history.append({
                'stock': stock,
                'exit_reason': exit_reason,
                'final_profit_ratio': profit_ratio,
                'exit_price': current_price,
                'initial_price': initial_price,
                'volume_exit': trade.position_size,
                'action_type': 'FULL_SELL'
            })
            trade.position_size = 0
            return True, current_price, exit_reason

    if stock.strategy_type == 'EP' and profit_ratio >= 0.15 and 'TAKE_PROFIT_50' not in [h['exit_reason'] for h in virtual_trade_history if h['stock'].ticker == stock.ticker]:
        print(f"💰 [✅ EXIT] {stock.ticker} (EP): 15% 익절 도달. 50% 매도 기록.")
        virtual_trade_history.append({
            'stock': stock,
            'exit_reason': 'TAKE_PROFIT_50',
            'final_profit_ratio': profit_ratio,
            'exit_price': current_price,
            'initial_price': initial_price,
            'volume_exit': position_size * 0.5,
            'action_type': 'PARTIAL_SELL'
        })
        trade.position_size *= 0.5
        
    elif stock.strategy_type == 'VCP' and profit_ratio >= 0.20 and 'TAKE_PROFIT_50' not in [h['exit_reason'] for h in virtual_trade_history if h['stock'].ticker == stock.ticker]:
        print(f"💰 [✅ EXIT] {stock.ticker} (VCP): 20% 익절 도달. 50% 매도 기록.")
        virtual_trade_history.append({
            'stock': stock,
            'exit_reason': 'TAKE_PROFIT_50',
            'final_profit_ratio': profit_ratio,
            'exit_price': current_price,
            'initial_price': initial_price,
            'volume_exit': position_size * 0.5,
            'action_type': 'PARTIAL_SELL'
        })
        trade.position_size *= 0.5
        
    return False, current_price, 'NONE'

def run_virtual_trading(trade: Trade, num_steps: int, price_simulation_func):
    print("-" * 50)
    print(f"▶️ {trade.stock.ticker} ({trade.stock.strategy_type}) 시뮬레이션 시작 (총 {num_steps}일)")
    print("-" * 50)
    
    for day in range(1, num_steps + 1):
        current_price = price_simulation_func(day)
        trade.stock.update_price(current_price)
        
        exit_triggered, _, _ = evaluate_exit_condition(trade, current_price, day)
        
        if exit_triggered:
            print(f"\n--- 📈 시뮬레이션 종료 (Day {day}): {trade.stock.ticker} 청산 완료 ---")
            break
        
        if day % 10 == 0:
            profit = (current_price / trade.initial_price) - 1
            print(f"Day {day:03d} | Price: {current_price:.2f} | Profit: {profit*100:6.2f}% | Position: {trade.position_size:.0f}")
        

if __name__ == '__main__':
    print("===================================================")
    print("📊 포워드 테스팅 시스템: 청산 로직 검증 시작")
    print("===================================================\n")

    stock_ep_loss = Stock("ABC_EP", 100.0, 'EP')
    trade_ep_loss = Trade(stock_ep_loss, 100.0)

    def simulate_ep_loss(day):
        if day < 20:
            return 100.0 - (day * 0.15) 
        elif day < 40:
            return 94.0 - ((day - 20) * 0.02) 
        else:
            return 93.0 
    
    run_virtual_trading(trade_ep_loss, num_steps=50, price_simulation_func=simulate_ep_loss)

    stock_ep_profit = Stock("XYZ_EP", 50.0, 'EP')
    trade_ep_profit = Trade(stock_ep_profit, 50.0)

    def simulate_ep_profit(day):
        if day < 30:
            return 50.0 + (day * 0.3)
        else:
            return 58.0

    run_virtual_trading(trade_ep_profit, num_steps=50, price_simulation_func=simulate_ep_profit)

    stock_vcp_profit = Stock("MIN_VCP", 200.0, 'VCP')
    trade_vcp_profit = Trade(stock_vcp_profit, 200.0)

    def simulate_vcp_profit(day):
        if day < 40:
            return 200.0 + (day * 1.5)
        else:
            return 242.0
            
    run_virtual_trading(trade_vcp_profit, num_steps=50, price_simulation_func=simulate_vcp_profit)

    print("\n" + "="*70)
    print("✅ 청산 로직 검증 완료: virtual_trade_history에 기록된 청산 이벤트 목록:")
    print("="*70)

    for i, history in enumerate(virtual_trade_history):
        print(f"[{i+1}] 종목: {history['stock'].ticker} ({history['stock'].strategy_type})")
        print(f"    -> 청산 사유: {history['exit_reason']}")
        if history['exit_reason'] == 'TAKE_PROFIT_50':
             print(f"    -> 이벤트: 50% 부분 익절 발생. 최종 수익률: {history['final_profit_ratio']*100:.2f}%")
        else:
             print(f"    -> 최종 수익률: {history['final_profit_ratio']*100:.2f}%")
        print("-" * 20)
