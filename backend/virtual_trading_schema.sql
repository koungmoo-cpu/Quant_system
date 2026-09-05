-- 1. 포트폴리오 상태 추적 테이블 (실시간 가상 자산 및 팩터 정보 포함)
CREATE TABLE virtual_portfolio (
    id SERIAL PRIMARY KEY,
    factor_score NUMERIC NOT NULL,          -- 필수: AI가 계산한 포트폴리오 팩터 점수
    strategy_type VARCHAR(50) NOT NULL,    -- 필수: 현재 적용된 전략 종류 (예: 'mean_reversion', 'momentum')
    cash_balance NUMERIC DEFAULT 1000000.0, -- 가상 현금 잔액
    total_equity NUMERIC,                   -- 총 자산 가치 (현금 + 보유 자산)
    last_updated TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- 2. 가상 거래 기록 테이블 (모든 매수/매도 기록)
CREATE TABLE virtual_trade_history (
    trade_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    ticker VARCHAR(20) NOT NULL,
    trade_type VARCHAR(10) NOT NULL,      -- 'BUY' 또는 'SELL'
    quantity INTEGER NOT NULL,
    price NUMERIC NOT NULL,
    pnl_impact NUMERIC DEFAULT 0,          -- 거래로 인한 손익 영향
    is_successful BOOLEAN DEFAULT TRUE    -- 거래 성공 여부
);

-- 3. 일별 성능 및 시스템 로그 테이블
CREATE TABLE virtual_daily_logs (
    log_id SERIAL PRIMARY KEY,
    log_date DATE UNIQUE NOT NULL,
    total_return NUMERIC,                   -- 일간 총 수익률
    max_drawdown NUMERIC,                   -- 최대 낙폭
    overall_risk_score NUMERIC,            -- 일별 리스크 점수
    notes TEXT,                             -- 시스템 또는 트레이딩 노트
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);
