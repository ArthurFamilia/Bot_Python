from binance.um_futures import UMFutures  
import dotenv
import os
dotenv.load_dotenv()

class TrailingStop:
    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")
        # Para testnet de futuros
        self.client = UMFutures(key=api_key, secret=api_secret)

    def testar_conexao(self):
        """Testa a conexão com a API de Futuros da Binance."""
        try:
            status = self.client.ping()
            if status == {}:
                print("Conexão com a Binance Futures bem-sucedida!")
                return True
            else:
                print("Resposta inesperada ao testar conexão:", status)
                return False
        except Exception as e:
            print(f"Erro ao testar conexão com a Binance Futures: {e}")
            return False

    def buy_with_trailing_stop(self, symbol, quantity, callback_rate, activation_price=None):
        """Abre posição LONG e cria trailing stop de venda."""
        try:
            # 1. Compra a mercado (abre LONG)
            buy_order = self.client.new_order(
                symbol=symbol,
                side="BUY",
                type="MARKET",
                quantity=quantity
            )
            print("Compra executada:", buy_order)

            # 2. Cria trailing stop de venda
            params = {
                "symbol": symbol,
                "side": "SELL",
                "type": "TRAILING_STOP_MARKET",
                "quantity": quantity,
                "callbackRate": callback_rate
            }
            if activation_price:
                params["activationPrice"] = activation_price

            trailing_order = self.client.new_order(**params)
            print("Trailing stop SELL criado:", trailing_order)
            return buy_order, trailing_order

        except Exception as e:
            print(f"Erro ao comprar e criar trailing stop: {e}")
            return None, None

    def sell_with_trailing_stop(self, symbol, quantity, callback_rate, activation_price=None):
        """Abre posição SHORT e cria trailing stop de compra."""
        try:
            # 1. Venda a mercado (abre SHORT)
            sell_order = self.client.new_order(
                symbol=symbol,
                side="SELL",
                type="MARKET",
                quantity=quantity
            )
            print("Venda executada:", sell_order)

            # 2. Cria trailing stop de compra
            params = {
                "symbol": symbol,
                "side": "BUY",
                "type": "TRAILING_STOP_MARKET",
                "quantity": quantity,
                "callbackRate": callback_rate
            }
            if activation_price:
                params["activationPrice"] = activation_price

            trailing_order = self.client.new_order(**params)
            print("Trailing stop BUY criado:", trailing_order)
            return sell_order, trailing_order

        except Exception as e:
            print(f"Erro ao vender e criar trailing stop: {e}")
            return None, None


