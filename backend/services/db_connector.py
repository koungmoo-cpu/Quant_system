import json
from datetime import datetime
import pytz
from typing import List, Dict, Any, Tuple, Optional
from google.cloud import firestore

class DBConnector:
    def __init__(self):
        try:
            self.db = firestore.Client(project="ai-stock-506110")
        except Exception as e:
            print(f"Warning: Firestore init failed (expected in local sandbox without ADC): {e}")
            self.db = None
            
    def get_risk_rules(self) -> dict:
        default_rules = {
            "min_factor_score": 8,
            "auto_buy_enabled": False,
            "auto_sell_enabled": False,
            "take_profit_pct": 15.0,
            "trailing_stop_pct": 70.0
        }
        if not self.db: return default_rules
        try:
            doc = self.db.collection('settings').document('risk_rules').get()
            if doc.exists:
                data = doc.to_dict()
                return {**default_rules, **data}
            return default_rules
        except Exception as e:
            print(f"Error fetching risk_rules: {e}")
            return default_rules

    def update_risk_rules(self, risk_rules: dict) -> bool:
        if not self.db: return False
        try:
            self.db.collection('settings').document('risk_rules').set(risk_rules, merge=True)
            return True
        except Exception as e:
            print(f"Error updating risk_rules: {e}")
            return False
            
    def get_universe_tickers(self) -> List[str]:
        if not self.db: return []
        docs = self.db.collection('universe').stream()
        return [doc.id for doc in docs]

    def get_universe(self) -> List[Dict[str, Any]]:
        if not self.db: return []
        docs = self.db.collection('universe').stream()
        return [doc.to_dict() for doc in docs]
        
    def add_to_universe(self, ticker: str, company_name: str) -> None:
        if not self.db: return
        self.db.collection('universe').document(ticker).set({
            "ticker": ticker,
            "name": company_name
        }, merge=True)

    
    def bulk_remove_favorites(self, tickers_to_remove: List[str]) -> List[str]:
        if not self.db: return []
        doc_ref = self.db.collection('settings').document('favorites')
        doc = doc_ref.get()
        current = []
        if doc.exists:
            current = doc.to_dict().get("tickers", [])
            
        updated = [t for t in current if t not in tickers_to_remove]
        doc_ref.set({"tickers": updated})
        return updated

    def get_favorites(self) -> List[str]:
        if not self.db: return []
        doc_ref = self.db.collection('settings').document('favorites')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict().get("tickers", [])
        return []
        
    def toggle_favorite(self, ticker: str) -> bool:
        if not self.db: return False
        doc_ref = self.db.collection('settings').document('favorites')
        doc = doc_ref.get()
        tickers = doc.to_dict().get("tickers", []) if doc.exists else []
        
        if ticker in tickers:
            tickers.remove(ticker)
            added = False
        else:
            tickers.append(ticker)
            added = True
            
        doc_ref.set({"tickers": tickers}, merge=True)
        return added

    def save_scan_results(self, results: List[Dict[str, Any]], timestamp: str):
        if not self.db: return
        batch = self.db.batch()
        
        # 1. Update latest
        doc_ref = self.db.collection('scan_results').document('latest')
        batch.set(doc_ref, {
            "timestamp": timestamp,
            "results": results
        })
        
        # 2. Add to scan_history using batch (individual documents in subcollection)
        safe_id = timestamp.replace(" ", "_").replace(":", "-").replace("/", "-")
        hist_doc_ref = self.db.collection('scan_history').document(safe_id)
        batch.set(hist_doc_ref, {"timestamp": timestamp}) # parent doc
        
        for r in results:
            ticker = r.get("ticker", "UNKNOWN")
            item_ref = hist_doc_ref.collection('results').document(ticker)
            batch.set(item_ref, r)
            
        batch.commit()

    def get_latest_scan_results(self) -> Dict[str, Any]:
        if not self.db: return {"timestamp": None, "results": []}
        doc_ref = self.db.collection('scan_results').document('latest')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return {"timestamp": None, "results": []}
        
    def get_trade_history(self) -> List[Dict[str, Any]]:
        if not self.db: return []
        docs = self.db.collection('trades').stream()
        return [doc.to_dict() for doc in docs]

    def add_trade(self, trade_data: Dict[str, Any]) -> None:
        if not self.db: return
        
        # Ensure schema fields exist for performance.py
        validated_trade = {
            "strategy": trade_data.get("strategy", trade_data.get("적용전략", "")),
            "entry_price": float(trade_data.get("entry_price", trade_data.get("매수가", 0))),
            "exit_price": float(trade_data.get("exit_price", trade_data.get("매도가", 0))),
            "profit_loss": float(trade_data.get("profit_loss", trade_data.get("실현손익", 0))),
            "profit_rate": float(trade_data.get("profit_rate", trade_data.get("수익률(%)", 0))),
            "quantity": int(trade_data.get("quantity", trade_data.get("수량", 0))),
            "entry_date": trade_data.get("entry_date", trade_data.get("매수일", "")),
                        "exit_date": trade_data.get("exit_date", trade_data.get("매도일", "")),
            "exit_reason": trade_data.get("exit_reason", trade_data.get("청산사유", "")),
            "strategy_type": trade_data.get("strategy_type", trade_data.get("strategy", "")),
            "market_status": trade_data.get("market_status", "Unknown"),
            "adr_pct": float(trade_data.get("adr_pct", 0)),
            "volume_surge_ratio": float(trade_data.get("volume_surge_ratio", 0)),
            "factor_score": int(trade_data.get("factor_score", trade_data.get("score", 0)))
        }
        
        # Add any other additional fields
        for k, v in trade_data.items():
            if k not in validated_trade and k not in ["적용전략", "매수가", "매도가", "실현손익", "수익률(%)", "수량", "매수일", "매도일", "청산사유"]:
                validated_trade[k] = v
                
        self.db.collection('trades').add(validated_trade)

    def get_portfolio(self) -> List[Dict[str, Any]]:
        if not self.db: return []
        docs = self.db.collection('portfolio').stream()
        return [doc.to_dict() for doc in docs]

    def update_portfolio(self, portfolio_data: List[Dict[str, Any]]) -> None:
        if not self.db: return
        batch = self.db.batch()
        docs = self.db.collection('portfolio').stream()
        for doc in docs:
            batch.delete(doc.reference)
            
        for idx, item in enumerate(portfolio_data):
            doc_ref = self.db.collection('portfolio').document(str(idx))
            batch.set(doc_ref, item)
            
        batch.commit()


    def update_portfolio_item(self, ticker: str, quantity: int, avgPrice: float, purchaseDate: str, strategy: Optional[str] = None) -> str:
        if not self.db: return "error: no db"
        try:
            doc_ref = self.db.collection('portfolio').document(ticker)
            if quantity > 0:
                data = {
                    "Ticker": ticker,
                    "Quantity": quantity,
                    "AvgPrice": avgPrice,
                    "PurchaseDate": purchaseDate
                }
                if strategy:
                    data["Strategy"] = strategy
                doc_ref.set(data, merge=True)
            else:
                doc_ref.delete()
            return "success"
        except Exception as e:
            return str(e)

    def get_market_status(self) -> Dict[str, Any]:
        if not self.db: return {}
        doc_ref = self.db.collection('settings').document('market_trend')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return {"status": "Yellow", "recommended_exposure": 50, "last_updated": ""}

    def update_market_status(self, status: str, exposure: int, timestamp: str) -> None:
        if not self.db: return
        self.db.collection('settings').document('market_trend').set({
            "status": status,
            "recommended_exposure": exposure,
            "last_updated": timestamp
        }, merge=True)

    def get_risk_rules(self) -> Dict[str, Any]:
        if not self.db: return {}
        doc_ref = self.db.collection('settings').document('risk_rules')
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return {
            "initial_capital": 10000000,
            "risk_per_trade_pct": 1.0,
            "stop_loss_pct": 5.0,
            "trailing_ma": 10
        }

    def update_risk_rules(self, rules: Dict[str, Any]) -> None:
        if not self.db: return
        self.db.collection('settings').document('risk_rules').set(rules, merge=True)


    def save_detected_setups(self, data: Dict[str, Any]) -> None:
        if not self.db: return
        batch = self.db.batch()
        
        # 1. Update latest
        doc_ref = self.db.collection('scan_results').document('latest_setups')
        batch.set(doc_ref, data)
        
        # 2. Add to history
        timestamp = data.get("last_scanned_at", "unknown")
        safe_id = timestamp.replace(" ", "_").replace(":", "-").replace("/", "-")
        hist_doc_ref = self.db.collection('scan_history_setups').document(safe_id)
        batch.set(hist_doc_ref, data)
        
        batch.commit()

    def get_latest_detected_setups(self) -> Dict[str, Any]:
        if not self.db: return {"last_scanned_at": "", "total_scanned": 0, "detected_count": 0, "items": []}
        doc_ref = self.db.collection('scan_results').document('latest_setups')
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            # Map names if missing or same as ticker
            try:
                universe_docs = self.db.collection('universe').stream()
                ticker_name_map = {u.id: u.to_dict().get('name', u.id) for u in universe_docs}
                for item in data.get("items", []):
                    ticker = item.get("ticker", "")
                    if ticker in ticker_name_map:
                        item["name"] = ticker_name_map[ticker]
            except Exception as e:
                print(f"Error mapping names: {e}")
            return data
        return {"last_scanned_at": "", "total_scanned": 0, "detected_count": 0, "items": []}

    # ==========================================
    # Virtual Forward Trading (Paper Trading)
    # ==========================================
    def get_virtual_portfolio(self) -> List[Dict[str, Any]]:
        if not self.db: return []
        docs = self.db.collection('virtual_portfolio').stream()
        return [doc.to_dict() for doc in docs]

    def update_virtual_portfolio_item(
        self, 
        ticker: str, 
        quantity: int, 
        avgPrice: float, 
        purchaseDate: str, 
        strategy: Optional[str] = None, 
        factor_score: float = 0,
        setup: str = "",
        spy_entry: float = 0,
        qqq_entry: float = 0,
        is_half_sold: bool = False,
        stop_price: float = 0.0,
        target_price: float = 0.0
    ) -> str:
        if not self.db: return "error: no db"
        try:
            doc_ref = self.db.collection('virtual_portfolio').document(ticker)
            if quantity > 0:
                data = {
                    "Ticker": ticker,
                    "Quantity": quantity,
                    "AvgPrice": avgPrice,
                    "PurchaseDate": purchaseDate,
                    "factor_score": factor_score,
                    "setup": setup,
                    "spy_entry": spy_entry,
                    "qqq_entry": qqq_entry,
                    "is_half_sold": is_half_sold,
                    "stop_price": stop_price,
                    "target_price": target_price
                }
                if strategy:
                    data["Strategy"] = strategy
                doc_ref.set(data, merge=True)
            else:
                doc_ref.delete()
            return "success"
        except Exception as e:
            return str(e)

    def add_virtual_trade(self, trade_data: Dict[str, Any]) -> None:
        if not self.db: return
        validated_trade = {
            "strategy": trade_data.get("strategy", ""),
            "setup": trade_data.get("setup", ""),
            "entry_price": float(trade_data.get("entry_price", 0)),
            "exit_price": float(trade_data.get("exit_price", 0)),
            "profit_loss": float(trade_data.get("profit_loss", 0)),
            "profit_rate": float(trade_data.get("profit_rate", 0)),
            "quantity": int(trade_data.get("quantity", 0)),
            "entry_date": trade_data.get("entry_date", ""),
            "exit_date": trade_data.get("exit_date", ""),
            "exit_reason": trade_data.get("exit_reason", ""),
            "factor_score": float(trade_data.get("factor_score", 0)),
            "spy_entry": float(trade_data.get("spy_entry", 0)),
            "qqq_entry": float(trade_data.get("qqq_entry", 0)),
            "spy_exit": float(trade_data.get("spy_exit", 0)),
            "qqq_exit": float(trade_data.get("qqq_exit", 0))
        }
        self.db.collection('virtual_trade_history').add(validated_trade)

    def get_virtual_trade_history(self) -> List[Dict[str, Any]]:
        if not self.db: return []
        docs = self.db.collection('virtual_trade_history').stream()
        return [doc.to_dict() for doc in docs]

db = DBConnector()

