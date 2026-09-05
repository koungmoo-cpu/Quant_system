import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.db_connector import DBConnector
from backend.virtual_trading_loop import TrailingStopSystem
import random

def run_test():
    db = DBConnector()
    print("\n" + "="*50)
    print("🚀 [Virtual Trading Engine Test]")
    print("="*50)
    
    # 1. Market Status Fetch
    try:
        status_docs = list(db.db.collection('market_status').order_by('timestamp', direction='DESCENDING').limit(1).stream())
        market_status = status_docs[0].to_dict().get('status', 'Unknown') if status_docs else "Yellow"
    except Exception:
        market_status = "Yellow"
        
    print(f"\n▶ [MARKET STATUS]: {market_status}")
    
    # 2. Risk Rules
    risk_rules = db.get_risk_rules()
    min_score = risk_rules.get('min_factor_score', 8)
    auto_buy_enabled = risk_rules.get('auto_buy_enabled', False)
    auto_sell_enabled = risk_rules.get('auto_sell_enabled', False)
    take_profit_pct = risk_rules.get('take_profit_pct', 15.0)
    trailing_stop_pct = risk_rules.get('trailing_stop_pct', 70.0)
    print(f"▶ [RISK RULES]: Min Score={min_score}, Auto-Buy={auto_buy_enabled}, Auto-Sell={auto_sell_enabled}")
    print(f"  - Take Profit: {take_profit_pct}%, Trailing Stop: {trailing_stop_pct}%")
    
    # 3. Process Exits (Trailing Stop)
    print("\n▶ [EXIT LOG] Assessing current holdings...")
    portfolio = db.get_virtual_portfolio()
    
    sold_items = []
    active_items = []
    
    for item in portfolio:
        ticker = item.get('Ticker', item.get('ticker'))
        if not ticker: continue
        
        # Mock price movement for testing
        entry = float(item.get('AvgPrice', 100))
        qty = int(item.get('Quantity', 10))
        # Random price movement -10% to +20%
        mock_current_price = entry * (1 + random.uniform(-0.10, 0.20))
        
        if not auto_sell_enabled:
            active_items.append(ticker)
            continue
            
        system = TrailingStopSystem(entry_price=entry, quantity=qty, take_profit_pct=take_profit_pct, trailing_stop_pct=trailing_stop_pct)
        # Restore state if exists
        system.is_half_sold = item.get('is_half_sold', False)
        system.stop_price = float(item.get('stop_price', entry * 0.95))
        
        action = system.update(mock_current_price)
        
        if action == 'SELL_ALL':
            reason = 'Stop_Loss' if mock_current_price < entry else 'Trailing_Stop'
            sold_items.append(f"{ticker} (청산 사유: {reason}, 수익률: {((mock_current_price-entry)/entry)*100:.2f}%)")
        elif action == 'SELL_HALF':
            sold_items.append(f"{ticker} (청산 사유: Take_Profit_50, 수익률: 15% 이상 도달)")
            active_items.append(ticker)
        else:
            active_items.append(ticker)
            
    if not sold_items:
        print("  - 방금 청산된 종목이 없습니다.")
    else:
        for sold in sold_items:
            print(f"  - 🛑 {sold}")
            
    # 4. Process Entries
    print("\n▶ [ENTRY LOG] Scanning for new setups...")
    max_slots = 100
    available_slots = max_slots - len(active_items)
    print(f"  - 현재 가용 슬롯: {available_slots} / {max_slots}")
    
    if not auto_buy_enabled:
        print("  - ⚠️ 자동매수가 비활성화되어 있어 신규 진입을 건너뜁니다.")
    elif available_slots > 0:
        from datetime import datetime, timedelta
        # Fetch detected setups
        setups = db.get_latest_detected_setups()
        if setups and 'items' in setups:
            last_scanned = setups.get('last_scanned_at', '')
            try:
                # ISO format parse (approx)
                scan_dt = datetime.fromisoformat(last_scanned.replace('Z', '+00:00'))
                is_recent = (datetime.now(scan_dt.tzinfo) - scan_dt) < timedelta(hours=48)
            except Exception:
                is_recent = True # fallback
                
            if not is_recent:
                print(f"  - ⚠️ 최근 스캔 데이터가 48시간 이상 지났습니다. (새로운 종목 아님, 스킵)")
            else:
                candidates = setups['items']
                # Filter by min_score
                candidates = [c for c in candidates if c.get('score', 0) >= min_score and c.get('ticker') not in active_items]
                candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                bought = candidates[:available_slots]
                if bought:
                    for b in bought:
                        print(f"  - ✅ 신규 매수: {b.get('ticker')} (Score: {b.get('score', 0)}, Price: ${b.get('current_price', 100):.2f})")
                else:
                    print(f"  - 최소 점수({min_score}점)를 통과한 신규 진입 대상 종목이 없습니다.")
        else:
            print("  - 최근 포착된 셋업이 없습니다.")
            
    print("\n" + "="*50)
    print("✅ 가상 매매 루프 시뮬레이션 완료")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_test()
