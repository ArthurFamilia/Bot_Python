import os
import pandas as pd
from conexao import BinanceConnection
from backtest import Backtester, Optimizer
from strategy import TradingStrategy

# Carregue suas chaves da Binance do .env ou defina diretamente aqui
API_KEY = os.getenv('BINANCE_API_KEY', 'SUA_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'SEU_API_SECRET')

# Lista de símbolos e intervalos para testar
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'XRP/USDT', 'SOL/USDT', 'HBAR/USDT', 'DOGE/USDT', 'MATIC/USDT', 'DOT/USDT', 'TRX/USDT', 'LTC/USDT', 'AVAX/USDT', 'LINK/USDT']
INTERVALS = ['1h', '2h', '4h', '1d']
LIMIT = 5000

# Grade de parâmetros para otimização
GRID = {
    'short_window': range(8, 50, 2),
    'long_window': range(20, 100, 2)
}

def otimizar_parametros():
    # Conecte-se à Binance
    conn = BinanceConnection(API_KEY, API_SECRET, testnet=False)
    
    # Dicionário para armazenar os melhores resultados
    melhores_resultados = {}
    
    # Para cada símbolo e intervalo
    for symbol in SYMBOLS:
        melhores_resultados[symbol] = {}
        
        for interval in INTERVALS:
            print(f"\nOtimizando {symbol} - Intervalo: {interval}")
            
            try:
                # Obtenha dados históricos
                df = conn.get_historical_klines(symbol, interval, LIMIT)
                
                if df is None:
                    print(f'Erro ao obter dados para {symbol} - {interval}')
                    continue
                
                # Instancie o backtester e otimizador
                backtester = Backtester()
                optimizer = Optimizer(backtester, TradingStrategy)
                
                # Execute a otimização
                best_params, best_result, results_df = optimizer.optimize(df, GRID)
                
                # Armazene os resultados
                melhores_resultados[symbol][interval] = {
                    'params': best_params,
                    'result': best_result,
                    'detailed_results': results_df
                }
                
                print(f'Melhores parâmetros para {symbol} - {interval}:')
                print(f'Parâmetros: {best_params}')
                print(f'Resultado: {best_result}')
                
            except Exception as e:
                print(f'Erro ao otimizar {symbol} - {interval}: {e}')
    
    return melhores_resultados

def salvar_resultados(resultados):
    # Cria um DataFrame com todos os resultados
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
    
    # Salva em CSV
    df_resultados.to_csv('resultados_otimizacao.csv', index=False)
    print('\nResultados salvos em resultados_otimizacao.csv')
    
    # Mostra os melhores resultados ordenados
    print('\nMelhores resultados (ordenados por resultado):')
    print(df_resultados.sort_values('result', ascending=False))

if __name__ == '__main__':
    print('Iniciando otimização multi-símbolo e multi-intervalo...')
    resultados = otimizar_parametros()
    salvar_resultados(resultados)
