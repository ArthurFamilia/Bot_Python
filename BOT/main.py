import os
import time
from dotenv import load_dotenv
from conexao import BinanceConnection
from strategy import TradingStrategy
import logging
import threading
import json
from datetime import datetime
import config 

load_dotenv()

def bot_loop(run_event):
    logger = logging.getLogger(__name__)
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        return
    connection = BinanceConnection(api_key, api_secret)
    if not connection.test_connection():
        logger.error("Falha ao conectar com a API da Binance.")
        print("[ERRO] Falha ao conectar com a API da Binance.")
        return
    strategy = TradingStrategy(short_window=config.MArapida, long_window=config.MAlenta)
    symbol = config.simbolo
    interval = config.intervalo
    logger.info(f"Starting trading bot for {symbol} on {interval}")
    trade_state = {
        'open': False,
        'side': None,
        'entry_time': None,
        'entry_price': None,
        'entry_volume': None
    }
    try:
        print('Bot rodando')
        while True:
            run_event.wait()
            df = connection.get_historical_klines(symbol, interval)
            if df is None:
                time.sleep(15)
                continue
            balance = connection.get_account_balance()
            usdt_cross = None
            if balance and 'info' in balance and 'assets' in balance['info']:
                for asset in balance['info']['assets']:
                    if asset['asset'] == 'USDT':
                        usdt_cross = float(asset['crossWalletBalance'])
            df = strategy.calculate_signals(df)
            if df is None:
                time.sleep(15)
                continue
            # Pega o último sinal gerado
            current_signal = df['signal'].iloc[-1]
            trade_signal = df['trade_signal'].iloc[-1]
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Só executa trade se houver mudança de posição
            if trade_signal != 0:
                if not balance or not ('total' in balance and 'USDT' in balance['total']):
                    time.sleep(2)
                    continue
                current_price = float(df['close'].iloc[-1])
                position_size = strategy.get_position_size(
                    float(balance['total']['USDT']) if 'total' in balance and 'USDT' in balance['total'] else 0.0,
                    current_price
                )
                # Se não há posição aberta e sinal de compra/venda, abre posição
                if not trade_state['open'] and position_size:
                    if current_signal == 1:
                        order = connection.place_order(symbol, 'buy', position_size)
                        print(f"Abertura de operação: COMPRA {position_size} @ {current_price} | Saldo USDT: {usdt_cross if usdt_cross is not None else 'N/A'}")
                        trade_state.update({
                            'open': True,
                            'side': 'buy',
                            'entry_time': now,
                            'entry_price': current_price,
                            'entry_volume': position_size
                        })
                    elif current_signal == -1:
                        order = connection.place_order(symbol, 'sell', position_size)
                        print(f"Abertura de operação: VENDA {position_size} @ {current_price} | Saldo USDT: {usdt_cross if usdt_cross is not None else 'N/A'}")
                        trade_state.update({
                            'open': True,
                            'side': 'sell',
                            'entry_time': now,
                            'entry_price': current_price,
                            'entry_volume': position_size
                        })
                # Se há posição aberta e o sinal mudou, fecha a posição e registra trade
                elif trade_state['open'] and (
                    (trade_state['side'] == 'buy' and current_signal == -1) or
                    (trade_state['side'] == 'sell' and current_signal == 1)
                ):
                    # Fecha posição
                    close_side = 'sell' if trade_state['side'] == 'buy' else 'buy'
                    order = connection.place_order(symbol, close_side, trade_state['entry_volume'])
                    exit_time = now
                    exit_price = current_price
                    pnl = (exit_price - trade_state['entry_price']) * trade_state['entry_volume']
                    if trade_state['side'] == 'sell':
                        pnl = -pnl
                    print(f"Fechamento de operação: {trade_state['side'].upper()} lucro/prejuízo: {pnl:.2f} | Saldo USDT: {usdt_cross if usdt_cross is not None else 'N/A'}")
                    # Salva trade no arquivo JSON
                    try:
                        # Garante que o arquivo existe
                        if not os.path.exists('BOT/trades.json'):
                            with open('BOT/trades.json', 'w', encoding='utf-8') as f:
                                json.dump([], f)
                        with open('BOT/trades.json', 'r+', encoding='utf-8') as f:
                            try:
                                trades = json.load(f)
                            except json.JSONDecodeError:
                                trades = []
                            trades.append({
                                'side': trade_state['side'],
                                'entry_time': trade_state['entry_time'],
                                'exit_time': exit_time,
                                'entry_price': trade_state['entry_price'],
                                'exit_price': exit_price,
                                'entry_volume': trade_state['entry_volume'],
                                'exit_volume': trade_state['entry_volume'],
                                'profit': pnl
                            })
                            f.seek(0)
                            json.dump(trades, f, indent=4)
                            f.truncate()
                    except Exception as e:
                        logger.error(f'Erro ao salvar trade no arquivo trades.json: {e}')
                    # Reseta estado da posição
                    trade_state = {
                        'open': False,
                        'side': None,
                        'entry_time': None,
                        'entry_price': None,
                        'entry_volume': None
                    }
            time.sleep(10)  # Espera 10 segundos antes de buscar novos dados
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

# Função principal que exibe o menu interativo e controla o bot
def main():
    # Configura o sistema de logs
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_bot.log'),
            logging.StreamHandler()
        ]
    )
    # Evento para controlar execução do bot (iniciar/pausar)
    run_event = threading.Event()
    run_event.set()  # Começa rodando imediatamente
    # Roda o loop do bot na thread principal (sem menu)
    bot_loop(run_event)

if __name__ == "__main__":
    main()
