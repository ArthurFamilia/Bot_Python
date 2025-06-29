import pandas as pd
import numpy as np
from strategy import TradingStrategy
import config

class Backtester:
    """Simula operações de trading com base nos sinais da estratégia."""
    def __init__(self, initial_balance=config.saldo_backtest, fee=0.04):
        self.initial_balance = initial_balance
        self.fee = fee

    def run(self, df: pd.DataFrame, strategy: TradingStrategy):
        balance = self.initial_balance
        position = 0
        entry_price = 0
        entry_size = 0
        trades = []
        df = strategy.calculate_signals(df)
        for i in range(1, len(df)):
            trade_signal = df['trade_signal'].iloc[i]
            price = df['close'].iloc[i]
            if position == 0:
                if trade_signal == 2:
                    entry_size = config.valor_fixo_usdt / price
                    entry_price = price
                    position = 1
                    print(f"[BUY] {i} | Preço: {price:.2f} | Saldo: {balance:.2f}")
                    trades.append({'type': 'BUY', 'price': price, 'balance': balance})
                elif trade_signal == -2:
                    entry_size = config.valor_fixo_usdt / price
                    entry_price = price
                    position = -1
                    print(f"[SHORT] {i} | Preço: {price:.2f} | Saldo: {balance:.2f}")
                    trades.append({'type': 'SHORT', 'price': price, 'balance': balance})
            elif position == 1 and trade_signal == -2:
                fee = entry_price * entry_size * self.fee + price * entry_size * self.fee
                pnl = (price - entry_price) * entry_size - fee
                balance += pnl
                print(f"[SELL] {i} | Preço: {price:.2f} | Saldo: {balance:.2f} | PnL: {pnl:.2f}")
                trades.append({'type': 'SELL', 'price': price, 'balance': balance})
                entry_size = config.valor_fixo_usdt / price
                entry_price = price
                position = -1
                print(f"[SHORT] {i} | Preço: {price:.2f} | Saldo: {balance:.2f}")
                trades.append({'type': 'SHORT', 'price': price, 'balance': balance})
            elif position == -1 and trade_signal == 2:
                fee = entry_price * entry_size * self.fee + price * entry_size * self.fee
                pnl = (entry_price - price) * entry_size - fee
                balance += pnl
                print(f"[COVER] {i} | Preço: {price:.2f} | Saldo: {balance:.2f} | PnL: {pnl:.2f}")
                trades.append({'type': 'COVER', 'price': price, 'balance': balance})
                entry_size = config.valor_fixo_usdt / price
                entry_price = price
                position = 1
                print(f"[BUY] {i} | Preço: {price:.2f} | Saldo: {balance:.2f}")
                trades.append({'type': 'BUY', 'price': price, 'balance': balance})
        if position != 0:
            price = df['close'].iloc[-1]
            fee = entry_price * entry_size * self.fee + price * entry_size * self.fee
            if position == 1:
                pnl = (price - entry_price) * entry_size - fee
                trades.append({'type': 'SELL', 'price': price, 'balance': balance + pnl})
            else:
                pnl = (entry_price - price) * entry_size - fee
                trades.append({'type': 'COVER', 'price': price, 'balance': balance + pnl})
            balance += pnl
        return balance, trades

class Optimizer:
    """Otimiza parâmetros da estratégia usando backtest."""
    def __init__(self, backtester: Backtester, strategy_class):
        self.backtester = backtester
        self.strategy_class = strategy_class

    def optimize(self, df: pd.DataFrame, param_grid: dict, criterio='final_balance'):
        best_result = -np.inf if criterio == 'final_balance' else float('inf')
        best_params = None
        results = []
        for short in param_grid['short_window']:
            for long in param_grid['long_window']:
                if short >= long:
                    continue
                strategy = self.strategy_class(short_window=short, long_window=long)
                final_balance, trades = self.backtester.run(df.copy(), strategy)
                balances = [t['balance'] for t in trades]
                drawdown = pd.Series(balances).cummax() - pd.Series(balances)
                max_drawdown = drawdown.max() if not drawdown.empty else 0
                lucros = pd.Series(balances).diff().fillna(0)
                ganhos = lucros[lucros > 0].sum()
                perdas = -lucros[lucros < 0].sum()
                fator_lucro = ganhos / perdas if perdas != 0 else float('inf')
                if criterio == 'final_balance':
                    result = final_balance
                    melhor = result > best_result
                elif criterio == 'max_drawdown':
                    result = -max_drawdown
                    melhor = result > best_result
                elif criterio == 'fator_lucro':
                    result = fator_lucro
                    melhor = result > best_result
                else:
                    result = final_balance
                    melhor = result > best_result
                results.append({'short_window': short, 'long_window': long, 'final_balance': final_balance, 'max_drawdown': max_drawdown, 'fator_lucro': fator_lucro})
                if melhor:
                    best_result = result
                    best_params = {'short_window': short, 'long_window': long}
        return best_params, best_result, pd.DataFrame(results)
