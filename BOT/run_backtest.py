import os
import matplotlib.pyplot as plt
import pandas as pd
from conexao import BinanceConnection
from backtest import Backtester
from strategy import TradingStrategy
import config
import mplfinance as mpf
import time
import datetime

SINCE = int(datetime.datetime(2024, 1, 1).timestamp() * 1000)

API_KEY = os.getenv('BINANCE_API_KEY', 'SUA_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'SEU_API_SECRET')

default_SYMBOL = config.simbolo
default_INTERVAL = config.intervalo  
default_LIMIT = 100000

def fetch_all_klines(conn, symbol, interval, total_candles=100000, limit_per_call=1000, sleep_sec=1, save_csv_path=None, since=None):
    """
    Busca candles históricos a partir de since (timestamp em ms).
    """
    candles_fetched = 0
    full_df = None
    call_count = 0
    while candles_fetched < total_candles:
        call_count += 1
        df = conn.get_historical_klines(symbol, interval, limit=limit_per_call, since=since)
        if df is None or df.empty:
            print(f"[DEBUG] Parou: df vazio na chamada {call_count}.")
            break
        if full_df is not None and df['timestamp'].iloc[0] <= full_df['timestamp'].iloc[-1]:
            df = df[df['timestamp'] > full_df['timestamp'].iloc[-1]]
        if df.empty:
            print(f"[DEBUG] Parou: df ficou vazio após remover sobreposição na chamada {call_count}.")
            break
        if full_df is None:
            full_df = df.copy()
        else:
            full_df = pd.concat([full_df, df], ignore_index=True)
        candles_fetched += len(df)
        print(f"[DEBUG] Total acumulado: {candles_fetched} candles.")
        since = int(df['timestamp'].iloc[-1].timestamp() * 1000) + 1
        time.sleep(sleep_sec)
        if len(df) < limit_per_call:
            print(f"[DEBUG] Parou: menos de {limit_per_call} candles retornados na chamada {call_count}.")
            break
    if full_df is None or full_df.empty:
        print("[DEBUG] Nenhum dado baixado!")
        return pd.DataFrame()
    full_df = full_df.drop_duplicates(subset='timestamp')
    full_df = full_df.sort_values('timestamp').reset_index(drop=True)
    if len(full_df) > total_candles:
        full_df = full_df.iloc[-total_candles:]
    if save_csv_path:
        full_df.to_csv(save_csv_path, index=False)
        print(f"[INFO] Dados salvos em {save_csv_path}.")
    return full_df

TOTAL_CANDLES = 100000
SYMBOL = default_SYMBOL
INTERVAL = default_INTERVAL
SINCE_TO_USE = SINCE

df = None
try:
    conn = BinanceConnection(API_KEY, API_SECRET)
    csv_path = f"dados_backtest_{SYMBOL.replace('/', '')}_{INTERVAL}.csv"
    df = fetch_all_klines(conn, SYMBOL, INTERVAL, total_candles=TOTAL_CANDLES, limit_per_call=1000, save_csv_path=csv_path, since=SINCE_TO_USE)
except Exception as e:
    print(f'Erro ao conectar ou obter dados: {e}')

if df is None or df.empty:
    print('Erro ao obter dados históricos.')
    exit()

backtester = Backtester()
strategy = TradingStrategy(short_window=config.MArapida, long_window=config.MAlenta)
final_balance, trades = backtester.run(df, strategy)

trades_df = pd.DataFrame(trades)
saldo_inicial = config.saldo_backtest
if trades_df.empty:
    trades_df = pd.DataFrame([{'type': 'START', 'price': None, 'balance': saldo_inicial}])
else:
    trades_df = pd.concat([
        pd.DataFrame([{'type': 'START', 'price': None, 'balance': saldo_inicial}]),
        trades_df
    ], ignore_index=True)

plt.figure(figsize=(12, 6))
plt.plot(trades_df['balance'], marker='o')
plt.title('Curva de Capital')
plt.xlabel('Operação')
plt.ylabel('Saldo')
plt.grid()
plt.show()

lucros = trades_df['balance'].diff().fillna(0)
plt.figure(figsize=(12, 4))
plt.bar(trades_df.index, lucros)
plt.title('Lucro/Prejuízo por Operação')
plt.xlabel('Operação')
plt.ylabel('Lucro/Prejuízo')
plt.grid()
plt.show()

ganhos = lucros[lucros > 0].sum()
perdas = -lucros[lucros < 0].sum()
fator_lucro = ganhos / perdas if perdas != 0 else float('inf')
print(f'Fator de Lucro: {fator_lucro:.2f}')

acum = trades_df['balance'].cummax()
drawdown = trades_df['balance'] - acum
drawdown_pct = drawdown / acum
max_drawdown = drawdown_pct.min()
print(f'Max Drawdown: {max_drawdown:.2%}')

plt.figure(figsize=(12, 4))
plt.plot(drawdown_pct, color='red')
plt.title('Drawdown (%)')
plt.xlabel('Operação')
plt.ylabel('Drawdown (%)')
plt.grid()
plt.show()

