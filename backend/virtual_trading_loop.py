import random
from typing import List, Dict
import yfinance as yf
from datetime import datetime, timedelta
import pytz

class TrailingStopSystem:
    def __init__(self, entry_price: float, quantity: int, take_profit_pct: float = 15.0, trailing_stop_pct: float = 70.0):
        self.entry_price = entry_price
        self.quantity = quantity
        self.take_profit_pct = take_profit_pct / 100.0
        self.trailing_stop_pct = trailing_stop_pct / 100.0
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

        # 2. 1차 목표가 도달
        if profit_ratio >= self.take_profit_pct and not self.is_half_sold:
            self.is_half_sold = True
            self.quantity = self.quantity // 2
            # 1차 익절 시 본전 방어선 설정
            self.stop_price = self.entry_price
            return 'SELL_HALF'

        # 3. 트레일링 스탑
        if self.is_half_sold:
            # 총수익 = 현재가 - 진입가
            profit = current_price - self.entry_price
            if profit > 0:
                new_stop = self.entry_price + (profit * self.trailing_stop_pct)
                if new_stop > self.stop_price:
                    self.stop_price = new_stop
            
            # 방어선 이탈 시 전량 매도
            if current_price < self.stop_price:
                return 'SELL_ALL'
                
        return 'HOLD'


# ======================================================================
# 실제 가상 매매 루프 실행 (Real Execution)
# ======================================================================

def execute_virtual_trading_cycle(db_connector):
    """
    백엔드 스케줄러에서 호출되어 가상 매매 엔진 1사이클을 수행합니다.
    1. Auto-Sell 평가 및 처리
    2. Auto-Buy 평가 및 처리
    """
    from backend.services.notifier import send_discord_alert
    
    print("\n" + "="*50)
    print("🚀 [Virtual Trading Engine Cycle Started]")
    
    db = db_connector
    
    # 1. Risk Rules 로드
    risk_rules = db.get_risk_rules()
    min_score = risk_rules.get('min_factor_score', 8)
    auto_buy_enabled = risk_rules.get('auto_buy_enabled', False)
    auto_sell_enabled = risk_rules.get('auto_sell_enabled', False)
    take_profit_pct = risk_rules.get('take_profit_pct', 15.0)
    trailing_stop_pct = risk_rules.get('trailing_stop_pct', 70.0)
    print(f"▶ [RISK RULES]: Min Score={min_score}, Auto-Buy={auto_buy_enabled}, Auto-Sell={auto_sell_enabled}")
    
    # 공통: 현재 KST 시각
    now_str = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d")
    
    # 2. Process Exits (Auto-Sell)
    portfolio = db.get_virtual_portfolio()
    active_items = []
    
    if auto_sell_enabled and portfolio:
        print("\n▶ [EXIT LOG] Assessing current holdings...")
        # yfinance를 사용하여 실시간 주가 일괄 조회
        tickers = [item.get('Ticker', item.get('ticker')) for item in portfolio if item.get('Ticker', item.get('ticker'))]
        current_prices = {}
        if tickers:
            try:
                # yf.download is efficient for multiple tickers
                data = yf.download(tickers, period="1d", progress=False)
                if not data.empty:
                    # Flatten multiindex if needed, or get Close
                    if 'Close' in data:
                        close_data = data['Close']
                        if len(tickers) == 1:
                            current_prices[tickers[0]] = float(close_data.iloc[-1])
                        else:
                            for ticker in tickers:
                                if ticker in close_data.columns:
                                    current_prices[ticker] = float(close_data[ticker].iloc[-1])
            except Exception as e:
                print(f"  - Error fetching prices via yfinance: {e}")

        # SPY, QQQ 조회 (Trade History 기록용)
        try:
            bench_data = yf.download(['SPY', 'QQQ'], period="1d", progress=False)
            spy_exit = float(bench_data['Close']['SPY'].iloc[-1]) if 'SPY' in bench_data['Close'] else 0.0
            qqq_exit = float(bench_data['Close']['QQQ'].iloc[-1]) if 'QQQ' in bench_data['Close'] else 0.0
        except Exception:
            spy_exit, qqq_exit = 0.0, 0.0

        for item in portfolio:
            ticker = item.get('Ticker', item.get('ticker'))
            if not ticker: continue
            
            entry_price = float(item.get('AvgPrice', 100))
            quantity = int(item.get('Quantity', 10))
            current_price = current_prices.get(ticker, entry_price) # 조회 실패시 진입가 유지
            
            system = TrailingStopSystem(entry_price=entry_price, quantity=quantity, take_profit_pct=take_profit_pct, trailing_stop_pct=trailing_stop_pct)
            # Restore state
            system.is_half_sold = item.get('is_half_sold', False)
            system.stop_price = float(item.get('stop_price', entry_price * 0.95))
            
            action = system.update(current_price)
            
            if action in ['SELL_ALL', 'SELL_HALF']:
                sell_qty = (quantity // 2) if action == 'SELL_HALF' else quantity
                reason = 'Take_Profit_50' if action == 'SELL_HALF' else ('Stop_Loss' if current_price < entry_price else 'Trailing_Stop')
                
                profit_loss = (current_price - entry_price) * sell_qty
                profit_rate = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                
                trade_data = {
                    "ticker": ticker,
                    "strategy": item.get('Strategy', 'Unknown'),
                    "setup": item.get('setup', ''),
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "profit_loss": profit_loss,
                    "profit_rate": profit_rate,
                    "quantity": sell_qty,
                    "entry_date": item.get('PurchaseDate', ''),
                    "exit_date": now_str,
                    "exit_reason": reason,
                    "factor_score": item.get('factor_score', 0),
                    "spy_entry": item.get('spy_entry', 0),
                    "qqq_entry": item.get('qqq_entry', 0),
                    "spy_exit": spy_exit,
                    "qqq_exit": qqq_exit
                }
                
                # 기록
                db.add_virtual_trade(trade_data)
                
                # 포트폴리오 업데이트
                remaining = quantity - sell_qty
                db.update_virtual_portfolio_item(
                    ticker=ticker,
                    quantity=remaining,
                    avgPrice=entry_price,
                    purchaseDate=item.get('PurchaseDate', ''),
                    strategy=item.get('Strategy', ''),
                    factor_score=item.get('factor_score', 0),
                    setup=item.get('setup', ''),
                    spy_entry=item.get('spy_entry', 0),
                    qqq_entry=item.get('qqq_entry', 0)
                )
                
                # DB에 TrailingStopSystem 상태 업데이트 (수량은 위에서 처리, 여기선 추가 필드 업데이트)
                doc_ref = db.db.collection('virtual_portfolio').document(ticker)
                doc_ref.set({
                    'is_half_sold': system.is_half_sold,
                    'stop_price': system.stop_price
                }, merge=True)
                
                if remaining > 0:
                    active_items.append(ticker)
                    print(f"  - ✅ {ticker} [SELL_HALF] 1차 익절 (잔여 {remaining}주)")
                    send_discord_alert(
                        title=f"💸 [가상 매매] 1차 익절: {ticker}",
                        description=f"목표가 15% 도달로 절반 매도 처리되었습니다.\n\n수익금: +${profit_loss:.2f} ({profit_rate:.2f}%)",
                        color=0x2ecc71
                    )
                else:
                    print(f"  - 🛑 {ticker} [{action}] 전략 청산 완료")
                    send_discord_alert(
                        title=f"🛑 [가상 매매] 전량 청산: {ticker}",
                        description=f"방어선 이탈로 전량 매도(청산) 처리되었습니다.\n\n수익/손실금: ${profit_loss:.2f} ({profit_rate:.2f}%)",
                        color=0xe74c3c if profit_loss < 0 else 0x2ecc71
                    )
            else:
                active_items.append(ticker)
                # 트레일링 스탑 상태 (stop_price 상승) 지속 업데이트
                doc_ref = db.db.collection('virtual_portfolio').document(ticker)
                doc_ref.set({
                    'stop_price': system.stop_price
                }, merge=True)
                
    else:
        # 매도 스킵 (그래도 active_items는 집계해야 빈 슬롯 계산 가능)
        for item in portfolio:
            t = item.get('Ticker', item.get('ticker'))
            if t and item.get('Quantity', 0) > 0:
                active_items.append(t)
    
    # 3. Process Entries (Auto-Buy)
    print("\n▶ [ENTRY LOG] Scanning for new setups...")
    max_slots = 100
    available_slots = max_slots - len(active_items)
    
    if not auto_buy_enabled:
        print("  - ⚠️ 자동매수가 비활성화되어 있어 신규 진입을 건너뜁니다.")
    elif available_slots > 0:
        setups = db.get_latest_detected_setups()
        if setups and 'items' in setups:
            last_scanned = setups.get('last_scanned_at', '')
            try:
                # ISO format parse
                scan_dt = datetime.fromisoformat(last_scanned.replace('Z', '+00:00'))
                is_recent = (datetime.now(scan_dt.tzinfo) - scan_dt) < timedelta(hours=48)
            except Exception:
                is_recent = True
                
            if not is_recent:
                print("  - ⚠️ 최근 스캔 데이터가 48시간 이상 지났습니다. (스킵)")
            else:
                candidates = setups['items']
                candidates = [c for c in candidates if c.get('score', 0) >= min_score and c.get('ticker') not in active_items]
                candidates.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                bought = candidates[:available_slots]
                
                if bought:
                    # SPY, QQQ 진입가 가져오기
                    try:
                        bench_data = yf.download(['SPY', 'QQQ'], period="1d", progress=False)
                        spy_entry = float(bench_data['Close']['SPY'].iloc[-1]) if 'SPY' in bench_data['Close'] else 0.0
                        qqq_entry = float(bench_data['Close']['QQQ'].iloc[-1]) if 'QQQ' in bench_data['Close'] else 0.0
                    except:
                        spy_entry, qqq_entry = 0.0, 0.0

                    for b in bought:
                        ticker = b.get('ticker')
                        price = b.get('current_price', 0)
                        qty = 10  # 10주 고정 (추후 고도화 가능)
                        
                        db.update_virtual_portfolio_item(
                            ticker=ticker,
                            quantity=qty,
                            avgPrice=price,
                            purchaseDate=now_str,
                            strategy=b.get('strategy', 'AI_Setup'),
                            factor_score=b.get('score', 0),
                            setup=b.get('ai_summary', ''),
                            spy_entry=spy_entry,
                            qqq_entry=qqq_entry
                        )
                        print(f"  - ✅ 신규 매수: {ticker} ({qty}주 @ ${price:.2f}, Score: {b.get('score', 0)})")
                        send_discord_alert(
                            title=f"🛒 [가상 매매] 신규 매수: {ticker}",
                            description=f"조건 부합으로 자동 편입되었습니다.\n\n수량: {qty}주\n진입가: ${price:.2f}\n전략: {b.get('strategy', 'AI_Setup')}",
                            color=0x3498db
                        )
                else:
                    print(f"  - 최소 점수({min_score}점)를 통과한 신규 진입 대상 종목이 없습니다.")
    else:
        print("  - 가용 슬롯이 0개입니다. (신규 진입 스킵)")
        
    print("="*50 + "\n")
