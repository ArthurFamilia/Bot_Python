import ccxt
import dotenv
import os
import pandas as pd
import logging

# Carrega variáveis de ambiente do arquivo .env
dotenv.load_dotenv()

class BinanceConnection:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = None):
        """
        Inicializa a conexão com a Binance usando ccxt.
        Parâmetros:
            api_key (str): Sua chave de API da Binance
            api_secret (str): Seu segredo de API da Binance
            testnet (bool): Se None, usa config.usar_testnet; se True/False, sobrescreve
        """
        import config
        if testnet is None:
            testnet = config.usar_testnet
        # Configura o cliente ccxt para Binance Futures
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
                'options': {'defaultType': 'future', 'adjustForTimeDifference': True}  # Adiciona ajuste de tempo
            })
        
        # Sincroniza o tempo com o servidor
        try:
            self.client.load_time_difference()
        except Exception as e:
            self.logger.warning(f"Não foi possível sincronizar o tempo com o servidor: {e}")
            
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
            # Busca os dados OHLCV (open, high, low, close, volume)
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
            # Cria a ordem de acordo com os parâmetros
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
            # Busca o saldo da conta
            balance = self.client.fetch_balance()
            return balance
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo da conta: {str(e)}")
            return None
    
    def test_connection(self):
        """
        Testa a conexão com a API da Binance Futures.
        Retorna:
            bool: True se a conexão for bem-sucedida, False caso contrário
        """
        try:
            # O método fetch_time retorna o timestamp do servidor se a conexão estiver ok
            server_time = self.client.fetch_time()
            if isinstance(server_time, int):
                self.logger.info(f"Conexão com a Binance Futures bem-sucedida! Timestamp: {server_time}")
                return True
            else:
                self.logger.warning(f"Resposta inesperada ao testar conexão: {server_time}")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão com a Binance Futures: {e}")
            return False

