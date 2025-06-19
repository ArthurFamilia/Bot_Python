import os
from conexao import BinanceConnection
from backtest import Backtester, Optimizer
from strategy import TradingStrategy

# Carregue suas chaves da Binance do .env ou defina diretamente aqui
API_KEY = os.getenv('BINANCE_API_KEY', 'SUA_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'SEU_API_SECRET')

# Parâmetros de busca de dados
SYMBOL = 'BTC/USDT'
INTERVAL = '1h'
LIMIT = 500

# Conecte-se à Binance e obtenha os dados históricos
conn = BinanceConnection(API_KEY, API_SECRET, testnet=False)
df = conn.get_historical_klines(SYMBOL, INTERVAL, LIMIT)

if df is None:
    print('Erro ao obter dados históricos.')
    exit()

# Instancie o backtester
backtester = Backtester()

# Defina a grade de parâmetros para otimização
grid = {
    'short_window': range(5, 30, 1),
    'long_window': range(15, 100, 1)
}

# Instancie o otimizador
optimizer = Optimizer(backtester, TradingStrategy)

# Execute a otimização
best_params, best_result, results_df = optimizer.optimize(df, grid)

print('Melhores parâmetros encontrados:', best_params)
print('Melhor resultado:', best_result)
print('Resultados detalhados:')
print(results_df)
