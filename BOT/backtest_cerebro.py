import backtrader as bt
import datetime
import pandas as pd
from conexao import BinanceConnection

class EstrategiaCruzamentoMedias(bt.Strategy):
    params = (
        ('periodo_curto', 20),
        ('periodo_longo', 50),
        ('risco_operacao', 0.02),  # 2% do capital por operação
    )

    def __init__(self):
        # Médias móveis
        self.sma_curta = bt.indicators.SMA(
            self.data.close, period=self.params.periodo_curto)
        self.sma_longa = bt.indicators.SMA(
            self.data.close, period=self.params.periodo_longo)
        
        # Cruzamento das médias
        self.crossover = bt.indicators.CrossOver(self.sma_curta, self.sma_longa)
        
        # Variáveis de controle
        self.ordem = None
        self.preco_entrada = None

    def next(self):
        # Se já tem ordem pendente, não faz nada
        if self.ordem:
            return

        # Calcula o tamanho da posição baseado no risco
        valor_risco = self.broker.getvalue() * self.params.risco_operacao
        tamanho = valor_risco / self.data.close[0]

        # Sinal de COMPRA: média curta cruza acima da longa
        if self.crossover > 0:
            self.ordem = self.buy(size=tamanho)
            self.preco_entrada = self.data.close[0]

        # Sinal de VENDA: média curta cruza abaixo da longa
        elif self.crossover < 0:
            self.ordem = self.sell(size=tamanho)
            self.preco_entrada = self.data.close[0]

    def notify_order(self, ordem):
        if ordem.status in [ordem.Submitted, ordem.Accepted]:
            return

        if ordem.status in [ordem.Completed]:
            if ordem.isbuy():
                self.log(f'COMPRA EXECUTADA - Preço: {ordem.executed.price:.2f}, Custo: {ordem.executed.value:.2f}, Comissão: {ordem.executed.comm:.2f}')
            else:
                self.log(f'VENDA EXECUTADA - Preço: {ordem.executed.price:.2f}, Custo: {ordem.executed.value:.2f}, Comissão: {ordem.executed.comm:.2f}')

        self.ordem = None

    def notify_trade(self, trade):
        if trade.isclosed:
            self.log(f'OPERAÇÃO FECHADA - PnL Bruto: {trade.pnl:.2f}, PnL Líquido: {trade.pnlcomm:.2f}')

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()} {txt}')

def rodar_backtest(symbol='BTC/USDT', interval='1h', periodo_inicial='2023-01-01'):
    # Configuração da conexão com a Binance
    conn = BinanceConnection(api_key='sua_api_key', api_secret='seu_api_secret')
    
    # Obtenção dos dados
    df = conn.get_historical_klines(symbol, interval, 1000)
    if df is None:
        print("Erro ao obter dados históricos")
        return
    
    # Prepara os dados para o Backtrader
    data = bt.feeds.PandasData(
        dataname=df,
        datetime='timestamp',
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest=-1
    )
    
    # Cria e configura o Cerebro
    cerebro = bt.Cerebro()
    
    # Adiciona os dados
    cerebro.adddata(data)
    
    # Adiciona a estratégia
    cerebro.addstrategy(EstrategiaCruzamentoMedias)
    
    # Configura o dinheiro inicial
    cerebro.broker.setcash(1000.0)
    
    # Configura a comissão (0.04% para Binance Futures)
    cerebro.broker.setcommission(commission=0.0004)
    
    # Adiciona analisadores
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    
    # Executa o backtest
    print('Saldo Inicial: %.2f' % cerebro.broker.getvalue())
    resultados = cerebro.run()
    estrategia = resultados[0]
    
    # Mostra os resultados
    print('Saldo Final: %.2f' % cerebro.broker.getvalue())
    print('Sharpe Ratio:', estrategia.analyzers.sharpe.get_analysis()['sharperatio'])
    print('Drawdown Máximo: %.2f%%' % estrategia.analyzers.drawdown.get_analysis()['max']['drawdown'])
    
    # Plota os gráficos
    cerebro.plot(style='candlestick', barup='green', bardown='red', volume=True)

if __name__ == '__main__':
    rodar_backtest()
