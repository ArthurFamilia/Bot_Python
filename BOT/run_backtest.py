import os
import matplotlib.pyplot as plt
import pandas as pd
from conexao import BinanceConnection
from backtest import Backtester
from strategy import TradingStrategy

# Carregue suas chaves da Binance do .env ou defina diretamente aqui
API_KEY = os.getenv('BINANCE_API_KEY', 'SUA_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET', 'SEU_API_SECRET')

# Parâmetros de busca de dados
SYMBOL = 'ETH/USDT'
INTERVAL = '1d'
LIMIT = 5000

# Conecte-se à Binance e obtenha os dados históricos
df = None
try:
    conn = BinanceConnection(API_KEY, API_SECRET, testnet=False)
    df = conn.get_historical_klines(SYMBOL, INTERVAL, LIMIT)
except Exception as e:
    print(f'Erro ao conectar ou obter dados: {e}')

if df is None:
    print('Erro ao obter dados históricos.')
    exit()

# Instancie o backtester
backtester = Backtester()

# Defina a estratégia
strategy = TradingStrategy(short_window=24, long_window=50)

# Execute o backtest
final_balance, trades = backtester.run(df, strategy, risk_percentage=0.03)

# Converter trades para DataFrame
trades_df = pd.DataFrame(trades)

# Gráfico da curva de capital
plt.figure(figsize=(12, 6))
plt.plot(trades_df['balance'], marker='o')
plt.title('Curva de Capital')
plt.xlabel('Operação')
plt.ylabel('Saldo')
plt.grid()
plt.show()

# Gráfico de lucro/prejuízo por operação
lucros = trades_df['balance'].diff().fillna(0)
plt.figure(figsize=(12, 4))
plt.bar(trades_df.index, lucros)
plt.title('Lucro/Prejuízo por Operação')
plt.xlabel('Operação')
plt.ylabel('Lucro/Prejuízo')
plt.grid()
plt.show()

# Fator de lucro
ganhos = lucros[lucros > 0].sum()
perdas = -lucros[lucros < 0].sum()
fator_lucro = ganhos / perdas if perdas != 0 else float('inf')
print(f'Fator de Lucro: {fator_lucro:.2f}')

# Drawdown
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
