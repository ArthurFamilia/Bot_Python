from conexao import BinanceConnection
from strategy import TradingStrategy
from backtest import Backtester, Optimizer
import os
import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from datetime import datetime, timedelta

# Defina suas chaves de API (ou use as do .env)
api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

testnet = True  # Altere para False se quiser rodar na conta real
conn = BinanceConnection(api_key, api_secret, testnet=testnet)
symbol = 'BTC/USDT'
interval = '1d'
num_candles = 500   # Aproximadamente 6 meses de candles de 1d
limit_per_call = 500  # Reduzido para evitar timeout
candles = []
now = datetime.utcnow()
end_time = int(now.timestamp() * 1000)
fetch_since = int((now - timedelta(days=num_candles)).timestamp() * 1000)
current_since = fetch_since
while len(candles) * limit_per_call < num_candles:
    try:
        df_temp = conn.client.fetch_ohlcv(symbol, timeframe=interval, since=current_since, limit=limit_per_call)
        if df_temp:
            df_temp = pd.DataFrame(df_temp, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df_temp['timestamp'] = pd.to_datetime(df_temp['timestamp'], unit='ms')
            candles.append(df_temp)
            current_since = int(df_temp['timestamp'].iloc[-1].timestamp() * 1000) + 1
            if len(df_temp) < limit_per_call:
                break
            import time
            time.sleep(1)  # Delay para evitar limite da API
        else:
            break
    except Exception as e:
        print(f"Erro ao buscar candles: {e}")
        break
if candles:
    df = pd.concat(candles, ignore_index=True).drop_duplicates(subset='timestamp').sort_values('timestamp').reset_index(drop=True)
    df = df.tail(num_candles)  # Garante que só pega os últimos 6 meses
else:
    raise Exception('Não foi possível obter dados históricos suficientes.')

# Instancie o backtester
backtester = Backtester(initial_balance=1000.0)

# Defina o grid de parâmetros para otimização
param_grid = {
    'short_window': range(5, 20, 1),   # Testa 5, 6, 7, ..., 19
    'long_window': range(30, 70, 2)  # Testa 30, 32, 34, ..., 68
}

# Instancie o otimizador
optimizer = Optimizer(backtester, TradingStrategy)

# Função para calcular drawdown máximo
def max_drawdown(equity_curve):
    roll_max = equity_curve.cummax()
    drawdown = (equity_curve - roll_max) / roll_max
    return drawdown.min()

# Rode a otimização
best_params, best_result, results_df = optimizer.optimize(df, param_grid)

# Calcula métricas adicionais para as 20 melhores
results_df = results_df.sort_values('final_balance', ascending=False).head(20)
melhores = []
for _, row in results_df.iterrows():
    # Simula curva de capital para cada parâmetro
    strat = TradingStrategy(short_window=int(row['short_window']), long_window=int(row['long_window']))
    df_signals = strat.calculate_signals(df.copy())
    saldo = [backtester.initial_balance]
    pos = 0
    entry = 0
    for i in range(1, len(df_signals)):
        signal = df_signals['signal'].iloc[i]
        price = df_signals['close'].iloc[i]
        if signal == 1 and pos <= 0:
            pos = (saldo[-1] * 2) / price
            entry = price
        elif signal == -1 and pos >= 0:
            if pos > 0:
                saldo.append(saldo[-1] + (price - entry) * pos)
            pos = -(saldo[-1] * 2) / price
            entry = price
        else:
            saldo.append(saldo[-1])
    equity_curve = pd.Series(saldo)
    dd = max_drawdown(equity_curve)
    lucro_total = equity_curve.iloc[-1] - equity_curve.iloc[0]
    fator_lucro = (equity_curve.iloc[-1] / equity_curve.iloc[0]) if equity_curve.iloc[0] != 0 else 0
    melhores.append({
        'short_window': int(row['short_window']),
        'long_window': int(row['long_window']),
        'final_balance': float(row['final_balance']),
        'fator_lucro': fator_lucro,
        'drawdown': dd,
        'curva_capital': list(equity_curve)
    })

# Salva as 20 melhores em um arquivo JSON
with open('BOT/melhores_estrategias.json', 'w', encoding='utf-8') as f:
    json.dump(melhores, f, indent=4)

# Plota curva de capital da melhor estratégia
equity_best = melhores[0]['curva_capital']
plt.figure(figsize=(10,5))
plt.plot(equity_best, label=f"Curva de Capital (short={melhores[0]['short_window']}, long={melhores[0]['long_window']})")
plt.title('Curva de Capital da Melhor Estratégia')
plt.xlabel('Operações')
plt.ylabel('Saldo')
plt.legend()
plt.tight_layout()
plt.savefig('BOT/curva_capital_melhor.png')
plt.close()

