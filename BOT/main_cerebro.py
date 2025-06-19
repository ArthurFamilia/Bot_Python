import backtrader as bt
import datetime
import pandas as pd
from conexao import BinanceConnection
import time
import os
import dotenv

# Carrega variáveis de ambiente do arquivo .env
dotenv.load_dotenv()

# Obtém as credenciais do arquivo .env
API_KEY = os.getenv('BINANCE_API_KEY')
API_SECRET = os.getenv('BINANCE_API_SECRET')

class EstrategiaCruzamentoMedias(bt.Strategy):
    params = (
        ('periodo_curto', 20),
        ('periodo_longo', 50),
        ('risco_operacao', 0.02),  # 2% do capital por operação
        ('symbol', 'BTC/USDT'),
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
        self.posicao_atual = 0
        
        # Conexão com a Binance usando credenciais do .env
        self.conn = BinanceConnection(api_key=API_KEY, api_secret=API_SECRET)

    def next(self):
        # Atualiza saldo e posição atual
        saldo = self.broker.getvalue()
        self.posicao_atual = self.position.size

        # Se já tem ordem pendente, não faz nada
        if self.ordem:
            return

        # Calcula o tamanho da posição baseado no risco
        valor_risco = saldo * self.params.risco_operacao
        tamanho = valor_risco / self.data.close[0]

        # Sinal de COMPRA: média curta cruza acima da longa
        if self.crossover > 0 and self.posicao_atual <= 0:
            if self.posicao_atual < 0:  # Se tem posição vendida, fecha
                self.ordem = self.buy(size=abs(self.posicao_atual))
                self.log(f'FECHANDO VENDA - Quantidade: {abs(self.posicao_atual)}')
            
            self.ordem = self.buy(size=tamanho)  # Abre compra
            self.preco_entrada = self.data.close[0]
            
            # Executa ordem real na Binance
            try:
                ordem_binance = self.conn.place_order(
                    symbol=self.params.symbol,
                    side='buy',
                    quantity=tamanho,
                    order_type='market'
                )
                self.log(f'ORDEM BINANCE ENVIADA - {ordem_binance}')
            except Exception as e:
                self.log(f'ERRO AO ENVIAR ORDEM: {e}')

        # Sinal de VENDA: média curta cruza abaixo da longa
        elif self.crossover < 0 and self.posicao_atual >= 0:
            if self.posicao_atual > 0:  # Se tem posição comprada, fecha
                self.ordem = self.sell(size=self.posicao_atual)
                self.log(f'FECHANDO COMPRA - Quantidade: {self.posicao_atual}')
            
            self.ordem = self.sell(size=tamanho)  # Abre venda
            self.preco_entrada = self.data.close[0]
            
            # Executa ordem real na Binance
            try:
                ordem_binance = self.conn.place_order(
                    symbol=self.params.symbol,
                    side='sell',
                    quantity=tamanho,
                    order_type='market'
                )
                self.log(f'ORDEM BINANCE ENVIADA - {ordem_binance}')
            except Exception as e:
                self.log(f'ERRO AO ENVIAR ORDEM: {e}')

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

def rodar_bot(symbol='BTC/USDT', interval='1h'):
    # Configuração da conexão com a Binance usando credenciais do .env
    conn = BinanceConnection(api_key=API_KEY, api_secret=API_SECRET)
    
    # Cria e configura o Cerebro
    cerebro = bt.Cerebro()
    
    # Configura o dinheiro inicial (será atualizado com saldo real da conta)
    saldo_real = float(conn.get_account_balance()['total']['USDT'])
    cerebro.broker.setcash(saldo_real)
    
    # Configura a comissão
    cerebro.broker.setcommission(commission=0.0004)
    
    # Adiciona a estratégia
    cerebro.addstrategy(EstrategiaCruzamentoMedias, symbol=symbol)
    
    # Configura o data feed em tempo real
    store = bt.stores.IBStore()
    data = store.getdata(dataname=symbol, timeframe=bt.TimeFrame.Minutes, compression=60)
    cerebro.adddata(data)
    
    # Adiciona analisadores
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    
    # Loop principal do bot
    while True:
        try:
            # Atualiza os dados
            df = conn.get_historical_klines(symbol, interval, 100)
            if df is not None:
                # Executa a estratégia com os novos dados
                cerebro.run()
                
                # Mostra estatísticas
                estrategia = cerebro.runstrats[0][0]
                drawdown = estrategia.analyzers.drawdown.get_analysis()
                print(f'Saldo Atual: {cerebro.broker.getvalue():.2f}')
                print(f'Drawdown Atual: {drawdown.drawdown[-1]:.2%}')
            
            # Aguarda até o próximo intervalo
            time.sleep(60)  # Ajuste conforme necessário
            
        except Exception as e:
            print(f'Erro no loop principal: {e}')
            time.sleep(10)

if __name__ == '__main__':
    rodar_bot()
