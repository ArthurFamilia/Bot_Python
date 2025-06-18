import ccxt
import dotenv
import os
import pandas as pd
import logging

dotenv.load_dotenv()

class BinanceConnection:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        Inicializa a conexão com a Binance usando ccxt.
        
        Parâmetros:
            api_key (str): Sua chave de API da Binance
            api_secret (str): Seu segredo de API da Binance
            testnet (bool): Se True, conecta na testnet de futuros
        """
        if testnet:
            self.client = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'options': {'defaultType': 'future'},
                'urls': {'api': {'public': 'https://testnet.binancefuture.com/fapi/v1',
                                 'private': 'https://testnet.binancefuture.com/fapi/v1'}}
            })
        else:
            self.client = ccxt.binance({
                'apiKey': api_key,
                'secret': api_secret,
                'options': {'defaultType': 'future'}
            })
        self.setup_logging()
    
    def setup_logging(self):
        """
        Configura o sistema de logs do bot.
        """
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_historical_klines(self, symbol: str, interval: str, limit: int = 100):
        """
        Busca dados históricos de candles (klines) usando ccxt.
        
        Parâmetros:
            symbol (str): Par de negociação (ex: 'BTC/USDT')
            interval (str): Intervalo do candle (ex: '1h', '4h', '1d')
            limit (int): Quantidade de candles a buscar
        
        Retorna:
            pandas.DataFrame: Dados históricos de preços
        """
        try:
            ohlcv = self.client.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            self.logger.error(f"Erro ao buscar dados históricos: {str(e)}")
            return None
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = 'market'):
        """
        Envia uma ordem para os Futuros da Binance usando ccxt.
        
        Parâmetros:
            symbol (str): Par de negociação (ex: 'BTC/USDT')
            side (str): 'buy' para compra ou 'sell' para venda
            quantity (float): Quantidade da ordem
            order_type (str): Tipo de ordem (padrão: 'market')
        
        Retorna:
            dict: Resposta da Binance sobre a ordem
        """
        try:
            order = self.client.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=quantity
            )
            self.logger.info(f"Ordem enviada com sucesso: {order}")
            return order
        except Exception as e:
            self.logger.error(f"Erro ao enviar ordem: {str(e)}")
            return None
    
    def get_account_balance(self):
        """
        Consulta o saldo da conta de futuros usando ccxt.
        
        Retorna:
            dict: Informações de saldo da conta
        """
        try:
            balance = self.client.fetch_balance()
            self.logger.info(f"Saldo da conta obtido: {balance}")
            return balance
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo da conta: {str(e)}")
            return None

