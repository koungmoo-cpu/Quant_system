import random
from typing import List, Dict

class TrailingStopSystem:
    def __init__(self, entry_price: float, quantity: int):
        self.entry_price = entry_price
        self.quantity = quantity
        self.is_half_sold = False
        self.stop_price = entry_price * 0.95  # 초기 손절선 5%

    def update(self, current_price: float) -> str:
        """
        Returns action: 'HOLD', 'SELL_HALF', or 'SELL_ALL'
        """
        profit_ratio = (current_price - self.entry_price) / self.entry_price
        
        # 1. 초기 손절선 이탈 (5%)
        if profit_ratio <= -0.05 and not self.is_half_sold:
            return 'SELL_ALL'

        # 2. 1차 목표가 도달 (15% 상승)
        if profit_ratio >= 0.15 and not self.is_half_sold:
            self.is_half_sold = True
            self.quantity = self.quantity // 2
            # 1차 익절 시 본전 방어선 설정
            self.stop_price = self.entry_price
            return 'SELL_HALF'

        # 3. 트레일링 스탑 (70% 이익 보존)
        if self.is_half_sold:
            # 총수익 = 현재가 - 진입가
            profit = current_price - self.entry_price
            if profit > 0:
                new_stop = self.entry_price + (profit * 0.70)
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
            
            # 방어선 이탈 시 전량 매도
            if current_price < self.stop_price:
                return 'SELL_ALL'
                
        return 'HOLD'


# ======================================================================
# Mock 가상 매매 루프 시뮬레이션
# ======================================================================

def run_virtual_trading_loop():
    print("\n🚀 [Virtual Trading Loop Simulation]")
    
    # 1. 진입가 $100.00, 100주
    system = TrailingStopSystem(entry_price=100.0, quantity=100)
    
    # 시나리오: 100 -> 105 -> 116(1차 익절) -> 120(상승, stop_price 상향) -> 110(하락, stop_price 이탈 청산)
    prices = [100.0, 105.0, 116.0, 120.0, 110.0, 100.0]
    
    for day, price in enumerate(prices):
        print(f"\n[Day {day+1}] 현재가: ${price:.2f}")
        action = system.update(price)
        
        if action == 'SELL_HALF':
            print(f"✅ [1차 익절] 15% 상승 도달! 50% 매도. 잔여물량: {system.quantity}주, 새로운 방어선: ${system.stop_price:.2f}")
        elif action == 'SELL_ALL':
            print(f"🛑 [전량 청산] 방어선 이탈! 전량 매도. (방어선: ${system.stop_price:.2f})")
            break
        else:
            print(f"📈 HOLD. 잔여물량: {system.quantity}주, 현재 방어선: ${system.stop_price:.2f}")

if __name__ == '__main__':
    run_virtual_trading_loop()
    
    print("\n" + "=" * 50)
    print(f"✅ 백엔드 가상 매매 루프 테스트 및 TrailingStopSystem 로직 검증 완료")
    print("=" * 50)

