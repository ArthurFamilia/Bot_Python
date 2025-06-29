import ccxt
import dotenv
import os
import pandas as pd
import logging

dotenv.load_dotenv()

class BinanceConnection:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = None):
        import config
        if testnet is None:
            testnet = config.usar_testnet
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
                'options': {'defaultType': 'future', 'adjustForTimeDifference': True}
            })
        try:
            self.client.load_time_difference()
        except Exception as e:
            self.logger.warning(f"Não foi possível sincronizar o tempo: {e}")
        self.setup_logging()
    
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('trading_bot.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_historical_klines(self, symbol: str, interval: str, limit: int = 10000, since: int = None):
        try:
            if since is not None:
                ohlcv = self.client.fetch_ohlcv(symbol, timeframe=interval, since=since, limit=limit)
            else:
                ohlcv = self.client.fetch_ohlcv(symbol, timeframe=interval, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            self.logger.error(f"Erro ao buscar candles: {e}")
            return None
    
    def place_order(self, symbol: str, side: str, quantity: float, order_type: str = 'market'):
        try:
            order = self.client.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=quantity
            )
            self.logger.info(f"Ordem enviada: {order}")
            return order
        except Exception as e:
            self.logger.error(f"Erro ao enviar ordem: {e}")
            return None
    
    def get_account_balance(self):
        try:
            balance = self.client.fetch_balance()
            return balance
        except Exception as e:
            self.logger.error(f"Erro ao obter saldo: {e}")
            return None
    
    def test_connection(self):
        try:
            server_time = self.client.fetch_time()
            if isinstance(server_time, int):
                self.logger.info(f"Conexão bem-sucedida! Timestamp: {server_time}")
                return True
            else:
                self.logger.warning(f"Resposta inesperada: {server_time}")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao testar conexão: {e}")
            return False

