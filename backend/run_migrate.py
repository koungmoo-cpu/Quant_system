import sqlite3
import os

def migrate_virtual_trading_db(db_name="investing_db.sqlite"):
    """
    가상 매매 데이터베이스를 마이그레이션하고, virtual_portfolio 테이블에 
    factor_score와 strategy_type 필드를 추가합니다.
    """
    conn = None
    try:
        # 기존 데이터베이스 연결 또는 생성
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        print(f"[{db_name}] 데이터베이스 연결 및 테이블 스키마 점검 시작...")

        # 1. virtual_portfolio 테이블 생성 (핵심 수정 부분)
        # factor_score와 strategy_type 필드를 반드시 포함합니다.
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS virtual_portfolio (
                portfolio_date TEXT PRIMARY KEY,
                cash REAL,
                total_value REAL,
                -- --- 추가된 필드 ---
                factor_score REAL,
                strategy_type TEXT,
                -- -------------------
                initial_equity REAL
            );
        """)

        # 2. virtual_trade_history 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS virtual_trade_history (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_date TEXT,
                ticker TEXT,
                transaction_type TEXT, -- BUY/SELL
                quantity REAL,
                price REAL,
                total_cost REAL
            );
        """)

        # 3. virtual_daily_logs 테이블 생성
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS virtual_daily_logs (
                log_date TEXT PRIMARY KEY,
                daily_profit REAL,
                volatility_score REAL,
                analysis_notes TEXT
            );
        """)

        # 모든 변경 사항 커밋
        conn.commit()
        print("✨ 스키마 업데이트 및 데이터베이스 준비 완료.")
        
        # 필수 출력 메시지 출력
        print("✅ 가상 매매 DB 마이그레이션 완료 (virtual_portfolio, virtual_trade_history, virtual_daily_logs 테이블 생성 성공)")

    except sqlite3.Error as e:
        print(f"🚨 SQLite 오류가 발생했습니다: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # 실제 환경에서는 이 함수를 호출하여 스크립트를 실행합니다.
    migrate_virtual_trading_db()
