import pprint

def calculate_performance_stats(history: list) -> dict:
    if not history:
        print("경고: 분석할 거래 기록이 없습니다.")
        return {}

    total_trades = len(history)
    winning_trades = 0
    losing_trades = 0
    total_profit = 0.0
    
    strategy_stats = {}
    strategies = set(trade['strategy_type'] for trade in history)
    for strategy in strategies:
        strategy_stats[strategy] = {
            'total': 0,
            'wins': 0,
            'losses': 0,
            'profit_sum': 0.0,
            'total_profit': 0.0
        }

    for trade in history:
        profit = trade['profit_loss']
        strategy = trade['strategy_type']

        total_profit += profit
        if profit > 0:
            winning_trades += 1
            total_profit += profit
        else:
            losing_trades += 1

        stats = strategy_stats[strategy]
        stats['total'] += 1
        stats['profit_sum'] += profit
        
        if profit > 0:
            stats['wins'] += 1
        else:
            stats['losses'] += 1

    overall_win_rate = winning_trades / total_trades
    overall_avg_profit = total_profit / total_trades

    strategy_results = {}
    for strategy, stats in strategy_stats.items():
        strat_win_rate = stats['wins'] / stats['total']
        strat_avg_profit = stats['profit_sum'] / stats['total']
        
        strategy_results[strategy] = {
            'total_trades': stats['total'],
            'win_rate': strat_win_rate,
            'avg_profit': strat_avg_profit
        }

    stats = {
        'overall': {
            'total_trades': total_trades,
            'win_rate': overall_win_rate,
            'avg_profit': overall_avg_profit
        },
        'strategy_performance': strategy_results
    }
    
    return stats

def print_performance_stats(stats: dict):
    if not stats:
        return

    print("=================================================")
    print("📊 트레이딩 성과 분석 보고서")
    print("=================================================")

    overall = stats['overall']
    print("\n[✨ 전체 거래 성과 요약]")
    print(f"  - 총 거래 건수: {overall['total_trades']} 건")
    print(f"  - 전체 승률: {overall['win_rate'] * 100:.2f}%")
    print(f"  - 평균 수익률 (Avg P/L): ${overall['avg_profit']:.2f}")
    print("-" * 40)

    print("\n[🔬 전략별 성능 분석]")
    strategy_results = stats['strategy_performance']
    
    for strategy, res in strategy_results.items():
        print(f"\n--- ⚙️ 전략: {strategy} ---")
        print(f"  - 총 거래 건수: {res['total_trades']} 건")
        print(f"  - 평균 수익률 (Avg P/L): ${res['avg_profit']:.2f}")
        print(f"  - 승률: {res['win_rate'] * 100:.2f}%")
    
    print("\n=================================================")

if __name__ == '__main__':
    print("👉 Mock 데이터 생성 및 분석을 시작합니다...")
    
    virtual_trade_history = [
        {'strategy_type': 'EP', 'profit_loss': 150.5, 'date': '2023-11-01'},
        {'strategy_type': 'EP', 'profit_loss': 50.2, 'date': '2023-11-02'},
        {'strategy_type': 'EP', 'profit_loss': 120.0, 'date': '2023-11-03'},
        {'strategy_type': 'VCP', 'profit_loss': -30.0, 'date': '2023-11-04'},
        {'strategy_type': 'VCP', 'profit_loss': -80.5, 'date': '2023-11-05'},
        {'strategy_type': 'EP', 'profit_loss': 250.0, 'date': '2023-11-06'},
        {'strategy_type': 'VCP', 'profit_loss': 10.0, 'date': '2023-11-07'},
        {'strategy_type': 'EP', 'profit_loss': -20.0, 'date': '2023-11-08'},
        {'strategy_type': 'VCP', 'profit_loss': -15.0, 'date': '2023-11-09'},
    ]

    performance_stats = calculate_performance_stats(virtual_trade_history)
    print_performance_stats(performance_stats)
    print("✅ 성과 분석 통계 엔진 동작 확인 완료")
