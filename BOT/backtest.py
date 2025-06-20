import pandas as pd
import numpy as np
from strategy import TradingStrategy
import config  # Importa as configurações do arquivo config.py

class Backtester:
    """
    Classe para simular operações de trading com base nos sinais da estratégia.
    """
    def __init__(self, initial_balance=config.saldo_backtest, fee=0.04):
        # Saldo inicial da simulação
        self.initial_balance = initial_balance
        # Taxa de corretagem (exemplo: 0.04%)
        self.fee = fee

    def run(self, df: pd.DataFrame, strategy: TradingStrategy):
        # Inicializa variáveis de controle
        balance = self.initial_balance
        position = 0  # 1 para comprado, -1 para vendido, 0 para fora
        entry_price = 0
        entry_size = 0  # Armazena o tamanho da posição aberta
        trades = []
        # Calcula sinais da estratégia
        df = strategy.calculate_signals(df)
        for i in range(1, len(df)):
            signal = df['signal'].iloc[i]
            price = df['close'].iloc[i]
            if signal == 1 and position <= 0:
                # Fecha venda se houver
                if position == -1:
                    pnl = (entry_price - price) * entry_size - (price + entry_price) * entry_size * self.fee
                    balance += pnl
                    trades.append({'type': 'COVER', 'price': price, 'balance': balance})
                # Abre compra
                entry_size = config.valor_fixo_usdt / price  # Valor fixo em USDT
                entry_price = price
                position = 1
                trades.append({'type': 'BUY', 'price': price, 'balance': balance})
            elif signal == -1 and position >= 0:
                # Fecha compra se houver
                if position == 1:
                    pnl = (price - entry_price) * entry_size - (price + entry_price) * entry_size * self.fee
                    balance += pnl
                    trades.append({'type': 'SELL', 'price': price, 'balance': balance})
                # Abre venda
                entry_size = config.valor_fixo_usdt / price  # Valor fixo em USDT
                entry_price = price
                position = -1
                trades.append({'type': 'SHORT', 'price': price, 'balance': balance})
        # Fecha posição aberta no final da simulação
        if position != 0:
            price = df['close'].iloc[-1]
            if position == 1:
                pnl = (price - entry_price) * entry_size - (price + entry_price) * entry_size * self.fee
            else:
                pnl = (entry_price - price) * entry_size - (price + entry_price) * entry_size * self.fee
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

    def optimize(self, df: pd.DataFrame, param_grid: dict):
        # Busca os melhores parâmetros de médias móveis
        best_result = -np.inf
        best_params = None
        results = []
        for short in param_grid['short_window']:
            for long in param_grid['long_window']:
                if short >= long:
                    continue  # short_window deve ser menor que long_window
                strategy = self.strategy_class(short_window=short, long_window=long)
                final_balance, _ = self.backtester.run(df.copy(), strategy)
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
