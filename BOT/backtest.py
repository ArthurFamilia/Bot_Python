import pandas as pd
import numpy as np
from strategy import TradingStrategy

class Backtester:
    """
    Classe para simular operações de trading com base nos sinais da estratégia.
    """
    def __init__(self, initial_balance=1000.0, fee=0.0004):
        # Saldo inicial da simulação
        self.initial_balance = initial_balance
        # Taxa de corretagem (exemplo: 0.04%)
        self.fee = fee

    def run(self, df: pd.DataFrame, strategy: TradingStrategy, risk_percentage=2):
        # Inicializa variáveis de controle
        balance = self.initial_balance
        position = 0  # 1 para comprado, -1 para vendido, 0 para fora
        entry_price = 0
        trades = []
        # Calcula sinais da estratégia
        df = strategy.calculate_signals(df)
        for i in range(1, len(df)):
            signal = df['signal'].iloc[i]
            price = df['close'].iloc[i]
            if signal == 1 and position <= 0:
                # Fecha venda se houver
                if position == -1:
                    pnl = (entry_price - price) * size - (price + entry_price) * size * self.fee
                    balance += pnl
                    trades.append({'type': 'COVER', 'price': price, 'balance': balance})
                # Abre compra
                size = (self.initial_balance * risk_percentage) / price  # Corrigido para usar saldo inicial
                entry_price = price
                position = 1
                trades.append({'type': 'BUY', 'price': price, 'balance': balance})
            elif signal == -1 and position >= 0:
                # Fecha compra se houver
                if position == 1:
                    pnl = (price - entry_price) * size - (price + entry_price) * size * self.fee
                    balance += pnl
                    trades.append({'type': 'SELL', 'price': price, 'balance': balance})
                # Abre venda
                size = (self.initial_balance * risk_percentage) / price  # Corrigido para usar saldo inicial
                entry_price = price
                position = -1
                trades.append({'type': 'SHORT', 'price': price, 'balance': balance})
        # Fecha posição aberta no final da simulação
        if position != 0:
            price = df['close'].iloc[-1]
            if position == 1:
                pnl = (price - entry_price) * size - (price + entry_price) * size * self.fee
            else:
                pnl = (entry_price - price) * size - (price + entry_price) * size * self.fee
            balance += pnl
            trades.append({'type': 'CLOSE', 'price': price, 'balance': balance})
        # Retorna saldo final e lista de operações
        return balance, trades

class Optimizer:
    """
    Classe para otimizar parâmetros da estratégia usando backtest.
    """
    def __init__(self, backtester: Backtester, strategy_class):
        # Recebe o backtester e a classe da estratégia
        self.backtester = backtester
        self.strategy_class = strategy_class

    def optimize(self, df: pd.DataFrame, param_grid: dict, risk_percentage=3.0):
        # Busca os melhores parâmetros de médias móveis
        best_result = -np.inf
        best_params = None
        results = []
        for short in param_grid['short_window']:
            for long in param_grid['long_window']:
                if short >= long:
                    continue  # short_window deve ser menor que long_window
                strategy = self.strategy_class(short_window=short, long_window=long)
                final_balance, _ = self.backtester.run(df.copy(), strategy, risk_percentage)
                results.append({'short_window': short, 'long_window': long, 'final_balance': final_balance})
                if final_balance > best_result:
                    best_result = final_balance
                    best_params = {'short_window': short, 'long_window': long}
        # Retorna melhores parâmetros, melhor resultado e DataFrame com todos os testes
        return best_params, best_result, pd.DataFrame(results)

# Exemplo de uso:
# from conexao import BinanceConnection
# conn = BinanceConnection(api_key, api_secret)
# df = conn.get_historical_klines('BTCUSDT', '1h', 500)
# backtester = Backtester()
# strategy = TradingStrategy(short_window=20, long_window=50)
# final_balance, trades = backtester.run(df, strategy)
# optimizer = Optimizer(backtester, TradingStrategy)
# param_grid = {'short_window': range(5, 30, 5), 'long_window': range(20, 100, 10)}
# best_params, best_result, results_df = optimizer.optimize(df, param_grid)
