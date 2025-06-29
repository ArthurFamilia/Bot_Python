import pandas as pd
from strategy import TradingStrategy
from backtest import Backtester
import config

def test_strategy_buy_sell_logs():
    # Testa se a estratégia gera operações e saldo muda
    data = {'close': [10, 11, 12, 13, 12, 11, 10, 9, 10, 11, 12, 13, 14, 13, 12, 11, 10, 9, 8, 7]}
    df = pd.DataFrame(data)
    for col in ['open', 'high', 'low', 'volume']:
        df[col] = df['close']
    strategy = TradingStrategy(short_window=2, long_window=3)
    backtester = Backtester(initial_balance=1000, fee=0.0)
    final_balance, trades = backtester.run(df, strategy)
    print('LOG DE OPERAÇÕES:')
    for t in trades:
        print(t)
    print(f'SALDO FINAL: {final_balance}')
    assert any(trade['type'] == 'BUY' for trade in trades), 'Nenhuma compra registrada!'
    assert any(trade['type'] == 'SELL' for trade in trades), 'Nenhuma venda registrada!'
    assert final_balance != 1000, 'O saldo final não mudou, estratégia não operou!'
    print('Teste automatizado passou!')

if __name__ == '__main__':
    test_strategy_buy_sell_logs()
