import os
import pandas as pd
import time
import datetime
from conexao import BinanceConnection
from backtest import Backtester, Optimizer
from strategy import TradingStrategy

API_KEY = os.getenv('BINANCE_API_KEY', 'SUA_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'SEU_API_SECRET')

SYMBOLS = ['BTC/USDT']
INTERVALS = ['5m', '30m', '2h']
LIMIT = 100000

GRID = {
    'short_window': range(2, 50, 2),
    'long_window': range(8, 150, 2),
    'distancia_minima_percent': [0.0, 0.001, 0.002, 0.005, 0.01, 0.02, 0.05]
}

SINCE = int(datetime.datetime(2025, 1, 1).timestamp() * 1000)

def fetch_all_klines(conn, symbol, interval, total_candles=100000, limit_per_call=1000, sleep_sec=10, save_csv_path=None, since=None):
    """
    Busca candles históricos até total_candles a partir de since (timestamp em ms).
    """
    candles_fetched = 0
    full_df = None
    while candles_fetched < total_candles:
        df = conn.get_historical_klines(symbol, interval, limit=limit_per_call, since=since)
        if df is None or df.empty:
            break
        if full_df is not None and df['timestamp'].iloc[0] <= full_df['timestamp'].iloc[-1]:
            df = df[df['timestamp'] > full_df['timestamp'].iloc[-1]]
        if df.empty:
            break
        if full_df is None:
            full_df = df.copy()
        else:
            full_df = pd.concat([full_df, df], ignore_index=True)
        candles_fetched += len(df)
        since = int(df['timestamp'].iloc[-1].timestamp() * 1000) + 1
        time.sleep(sleep_sec)
        if len(df) < limit_per_call:
            break
    if full_df is None or full_df.empty:
        return pd.DataFrame()
    full_df = full_df.drop_duplicates(subset='timestamp')
    full_df = full_df.sort_values('timestamp').reset_index(drop=True)
    if len(full_df) > total_candles:
        full_df = full_df.iloc[-total_candles:]
    if save_csv_path:
        full_df.to_csv(save_csv_path, index=False)
        print(f"[INFO] Dados salvos em {save_csv_path}.")
    return full_df

def otimizar_parametros(criterio='final_balance', validacao_cruzada=False, split_ratio=0.7, total_candles=10000):
    conn = BinanceConnection(API_KEY, API_SECRET)
    melhores_resultados = {}
    for symbol in SYMBOLS:
        melhores_resultados[symbol] = {}
        for interval in INTERVALS:
            print(f"\nOtimizando {symbol} - {interval}")
            try:
                csv_path = f"dados_otimizacao_{symbol.replace('/', '')}_{interval}.csv"
                df = fetch_all_klines(conn, symbol, interval, total_candles=total_candles, limit_per_call=1000, save_csv_path=csv_path, since=SINCE)
                print(f"[INFO] {symbol} {interval}: {len(df)} candles baixados. {df['timestamp'].iloc[0]} até {df['timestamp'].iloc[-1]}")
                if df is None or df.empty:
                    print(f'Erro ao obter dados para {symbol} - {interval}')
                    continue
                backtester = Backtester()
                optimizer = Optimizer(backtester, TradingStrategy)
                best_result = -float('inf')
                best_params = None
                results = []
                for short in GRID['short_window']:
                    for long in GRID['long_window']:
                        if short >= long:
                            continue
                        for dist in GRID['distancia_minima_percent']:
                            import config
                            config.distancia_minima_percent = dist
                            strategy = TradingStrategy(short_window=short, long_window=long)
                            final_balance, trades = backtester.run(df.copy(), strategy)
                            balances = [t['balance'] for t in trades]
                            drawdown = pd.Series(balances).cummax() - pd.Series(balances)
                            max_drawdown = drawdown.max() if not drawdown.empty else 0
                            lucros = pd.Series(balances).diff().fillna(0)
                            ganhos = lucros[lucros > 0].sum()
                            perdas = -lucros[lucros < 0].sum()
                            fator_lucro = ganhos / perdas if perdas != 0 else float('inf')
                            if criterio == 'final_balance':
                                result = final_balance
                            elif criterio == 'max_drawdown':
                                result = -max_drawdown
                            elif criterio == 'fator_lucro':
                                result = fator_lucro
                            else:
                                result = final_balance
                            melhor = result > best_result
                            results.append({'short_window': short, 'long_window': long, 'distancia_minima_percent': dist, 'final_balance': final_balance, 'max_drawdown': max_drawdown, 'fator_lucro': fator_lucro})
                            if melhor:
                                best_result = result
                                best_params = {'short_window': short, 'long_window': long, 'distancia_minima_percent': dist}
                melhores_resultados[symbol][interval] = {
                    'params': best_params,
                    'result': best_result,
                }
                print(f'Melhores parâmetros para {symbol} - {interval}: {best_params} | Resultado: {best_result}')
            except Exception as e:
                print(f'Erro ao otimizar {symbol} - {interval}: {e}')
    return melhores_resultados

def salvar_resultados(resultados):
    rows = []
    for symbol in resultados:
        for interval in resultados[symbol]:
            row = {
                'symbol': symbol,
                'interval': interval,
                'short_window': resultados[symbol][interval]['params']['short_window'],
                'long_window': resultados[symbol][interval]['params']['long_window'],
                'result': resultados[symbol][interval]['result']
            }
            rows.append(row)
    df_resultados = pd.DataFrame(rows)
    df_resultados.to_csv('resultados_otimizacao.csv', index=False)
    print('\nResultados salvos em resultados_otimizacao.csv')
    print('\nMelhores resultados (ordenados por resultado):')
    print(df_resultados.sort_values('result', ascending=False))

if __name__ == '__main__':
    print('Iniciando otimização...')
    resultados = otimizar_parametros()
    salvar_resultados(resultados)
