import os
from conexao import BinanceConnection
from backtest import Backtester
from strategy import TradingStrategy

# Carregue suas chaves da Binance do .env ou defina diretamente aqui
API_KEY = os.getenv('BINANCE_API_KEY', 'SUA_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'SEU_API_SECRET')

# Parâmetros de busca de dados
SYMBOL = 'BTC/USDT'
INTERVAL = '1h'
LIMIT = 500

# Conecte-se à Binance e obtenha os dados históricos
df = None
try:
    conn = BinanceConnection(API_KEY, API_SECRET, testnet=True)
    df = conn.get_historical_klines(SYMBOL, INTERVAL, LIMIT)
except Exception as e:
    print(f'Erro ao conectar ou obter dados: {e}')

if df is None:
    print('Erro ao obter dados históricos.')
    exit()

# Instancie o backtester
backtester = Backtester()

# Defina a estratégia
strategy = TradingStrategy(short_window=19, long_window=37)

# Execute o backtest
final_balance, trades = backtester.run(df, strategy, risk_percentage=10.0)

print('Saldo final:', final_balance)
print('Trades realizados:')
for trade in trades:
    print(trade)
