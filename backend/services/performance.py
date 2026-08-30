import pandas as pd
import numpy as np
from typing import List, Dict, Any

class PerformanceEngine:
    def _empty_metrics(self) -> Dict[str, Any]:
        return {
            "total_metrics": {
                "total_trades": 0,
                "total_profit": 0,
                "win_rate": 0.0,
                "risk_reward_ratio": 0.0,
                "profit_factor": 0.0,
                "max_consecutive_losses": 0,
                "mdd": 0.0,
                "cagr": 0.0,
                "initial_capital": 0
            },
            "strategy_metrics": {}
        }

    def calculate_account_metrics(self, data: List[Dict[str, Any]], initial_capital: float) -> Dict[str, Any]:
        if not data or initial_capital <= 0:
            return self._empty_metrics()

        # Map new English schema fields to expected Korean fields if they exist
        for item in data:
            if item.get("strategy") and not item.get("적용전략"): item["적용전략"] = item["strategy"]
            if item.get("entry_price") and not item.get("매수가"): item["매수가"] = item["entry_price"]
            if item.get("buy_price") and not item.get("매수가"): item["매수가"] = item["buy_price"]
            if item.get("exit_price") and not item.get("매도가"): item["매도가"] = item["exit_price"]
            if item.get("sell_price") and not item.get("매도가"): item["매도가"] = item["sell_price"]
            if "profit_loss" in item and "실현손익" not in item: item["실현손익"] = item["profit_loss"]
            if "profit_rate" in item and "수익률(%)" not in item: item["수익률(%)"] = item["profit_rate"]
            if item.get("quantity") and not item.get("수량"): item["수량"] = item["quantity"]
            if item.get("entry_date") and not item.get("매수일"): item["매수일"] = item["entry_date"]
            if item.get("buy_date") and not item.get("매수일"): item["매수일"] = item["buy_date"]
            if item.get("exit_date") and not item.get("매도일"): item["매도일"] = item["exit_date"]
            if item.get("sell_date") and not item.get("매도일"): item["매도일"] = item["sell_date"]
            if item.get("exit_reason") and not item.get("청산사유"): item["청산사유"] = item["exit_reason"]
            if item.get("strategy_type") and not item.get("적용전략"): item["적용전략"] = item["strategy_type"]
            if "market_status" not in item: item["market_status"] = "Unknown"


        # 데이터 프레임 생성 및 클렌징
        df = pd.DataFrame(data)
        
        # 수익률 컬럼명 통일 (수익률 또는 수익률(%) 지원)
        if "수익률" in df.columns and "수익률(%)" not in df.columns:
            df.rename(columns={"수익률": "수익률(%)"}, inplace=True)
            
        # 필수 컬럼 검증 (유연하게 대처하기 위해 누락 시 빈 컬럼 생성)
        required_cols = ["실현손익", "수익률(%)", "적용전략", "매수일", "매도일"]
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0.0 if col in ["실현손익", "수익률(%)"] else ""

        # 추가 보조 컬럼 (자동 계산용)
        for col in ["매수가", "매도가", "수량"]:
            if col not in df.columns:
                df[col] = 0.0

        # 숫자형 변환 (빈 문자열이나 잘못된 형식 처리)
        for col in ["실현손익", "수익률(%)", "매수가", "매도가", "수량"]:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '').str.replace('%', ''), errors='coerce').fillna(0)

        # 사용자가 구글 시트에 수식을 안 적었을 경우(값이 0인 경우), 매수가/매도가/수량을 바탕으로 자동 계산
        mask_profit = (df["실현손익"] == 0) & (df["매수가"] > 0) & (df["수량"] > 0)
        if mask_profit.any():
            df.loc[mask_profit, "실현손익"] = (df["매도가"] - df["매수가"]) * df["수량"]

        mask_return = (df["수익률(%)"] == 0) & (df["매수가"] > 0)
        if mask_return.any():
            df.loc[mask_return, "수익률(%)"] = ((df["매도가"] - df["매수가"]) / df["매수가"]) * 100
        
        # 날짜형 변환
        df["매수일"] = pd.to_datetime(df["매수일"], errors='coerce')
        df["매도일"] = pd.to_datetime(df["매도일"], errors='coerce')
        
        # 날짜 기준 정렬 (시계열 분석을 위해)
        df = df.sort_values(by="매도일").reset_index(drop=True)
        
        # 유효한 거래만 필터링 (매도일이 있는 경우)
        df = df.dropna(subset=["매도일"])
        
        if df.empty:
            return self._empty_metrics()

        # --- 1. 전체 계좌 통계 계산 ---
        total_trades = len(df)
        total_profit = df["실현손익"].sum()
        
        # 승률
        winning_trades = df[df["실현손익"] > 0]
        losing_trades = df[df["실현손익"] < 0]
        
        win_rate = (len(winning_trades) / total_trades * 100) if total_trades > 0 else 0.0
        
        # 손익비 & Profit Factor
        avg_win = winning_trades["실현손익"].mean() if not winning_trades.empty else 0
        avg_loss = abs(losing_trades["실현손익"].mean()) if not losing_trades.empty else 0
        risk_reward_ratio = (avg_win / avg_loss) if avg_loss > 0 else float('inf') if avg_win > 0 else 0.0
        
        gross_profit = winning_trades["실현손익"].sum()
        gross_loss = abs(losing_trades["실현손익"].sum())
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0
        
        # 최대 연속 손실 횟수
        max_consecutive_losses = 0
        current_losses = 0
        for profit in df["실현손익"]:
            if profit < 0:
                current_losses += 1
                max_consecutive_losses = max(max_consecutive_losses, current_losses)
            else:
                current_losses = 0
                
        # MDD (Max Drawdown)
        # 누적 자산 = 초기 자본금 + 누적 수익
        df["Cumulative_Profit"] = df["실현손익"].cumsum()
        df["Equity"] = initial_capital + df["Cumulative_Profit"]
        
        df["Peak_Equity"] = df["Equity"].cummax()
        df["Drawdown"] = (df["Equity"] - df["Peak_Equity"]) / df["Peak_Equity"]
        mdd = abs(df["Drawdown"].min() * 100) # 퍼센트로 변환
        
        # CAGR (연평균 수익률)
        first_date = df["매수일"].min()
        last_date = df["매도일"].max()
        
        if pd.isna(first_date) or pd.isna(last_date) or first_date >= last_date:
            cagr = 0.0
        else:
            days_diff = (last_date - first_date).days
            if days_diff <= 0:
                cagr = 0.0
            else:
                years = days_diff / 365.25
                final_equity = initial_capital + total_profit
                if final_equity > 0:
                    cagr = ((final_equity / initial_capital) ** (1 / years) - 1) * 100
                else:
                    cagr = -100.0

        total_metrics = {
            "total_trades": int(total_trades),
            "total_profit": float(total_profit),
            "win_rate": float(round(win_rate, 2)),
            "risk_reward_ratio": float(round(risk_reward_ratio, 2)) if risk_reward_ratio != float('inf') else 999.9,
            "profit_factor": float(round(profit_factor, 2)) if profit_factor != float('inf') else 999.9,
            "max_consecutive_losses": int(max_consecutive_losses),
            "mdd": float(round(mdd, 2)),
            "cagr": float(round(cagr, 2)),
            "initial_capital": float(initial_capital)
        }

        # --- 2. 전략 및 시장 상태별 통계 계산 ---
        strategy_metrics = {}
        
        # Ensure market_status column exists
        if "market_status" not in df.columns:
            df["market_status"] = "Unknown"
            
        grouped = df.groupby(["적용전략", "market_status"])
        
        for (strategy, market_status), group in grouped:
            key_name = f"{strategy} | {market_status}"
            s_total = len(group)
            s_profit = group["실현손익"].sum()
            s_wins = len(group[group["실현손익"] > 0])
            s_win_rate = (s_wins / s_total * 100) if s_total > 0 else 0.0
            
            s_avg_win = group[group["실현손익"] > 0]["실현손익"].mean()
            s_avg_win = s_avg_win if not pd.isna(s_avg_win) else 0
            
            s_avg_loss = abs(group[group["실현손익"] < 0]["실현손익"].mean())
            s_avg_loss = s_avg_loss if not pd.isna(s_avg_loss) else 0
            
            s_rrr = (s_avg_win / s_avg_loss) if s_avg_loss > 0 else float('inf') if s_avg_win > 0 else 0.0
            
            strategy_metrics[key_name] = {
                "total_trades": int(s_total),
                "total_profit": float(s_profit),
                "win_rate": float(round(s_win_rate, 2)),
                "risk_reward_ratio": float(round(s_rrr, 2)) if s_rrr != float('inf') else 999.9
            }

        return {
            "total_metrics": total_metrics,
            "strategy_metrics": strategy_metrics
        }
