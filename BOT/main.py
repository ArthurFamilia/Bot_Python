import os
import time
from dotenv import load_dotenv
from conexao import BinanceConnection
from strategy import TradingStrategy
import logging
import threading
import json
from datetime import datetime

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Função que executa o loop principal do bot de trading
# O loop só roda quando run_event está ativado (set)
def bot_loop(run_event):
    logger = logging.getLogger(__name__)
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        return
    connection = BinanceConnection(api_key, api_secret, testnet=True)  # Mudar para False em produção
    # Testa a conexão antes de iniciar o loop
    if not connection.test_connection():
        logger.error("Falha ao conectar com a API da Binance. O bot será encerrado.")
        print("[ERRO] Falha ao conectar com a API da Binance. Verifique suas credenciais e conexão com a internet.")
        return
    strategy = TradingStrategy(short_window=20, long_window=50)
    symbol = 'BTC/USDT'  # Par de negociação para ccxt
    interval = '5m'     # Intervalo do candle
    risk_percentage = 0.02  # Risco por operação (2%)
    logger.info(f"Starting trading bot for {symbol} on {interval} timeframe")
    trade_state = {
        'open': False,
        'side': None,
        'entry_time': None,
        'entry_price': None,
        'entry_volume': None
    }
    try:
        while True:
            run_event.wait()
            # Log de status: ping
            try:
                ping = connection.client.fetch_time()
                from datetime import datetime
                ping_str = datetime.utcfromtimestamp(ping / 1000).strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"Ping/Time da API: {ping_str} (timestamp: {ping})")
            except Exception as e:
                logger.error(f"Erro no ping: {str(e)}")
            # Busca dados históricos
            df = connection.get_historical_klines(symbol, interval)
            if df is not None:
                logger.info("Status: Dados históricos captados com sucesso.")
            else:
                logger.error("Status: Falha ao captar dados históricos.")
                time.sleep(15)
                continue
            # Consulta saldo da conta
            balance = connection.get_account_balance()
            usdt_cross = None
            bnb_cross = None
            if balance and 'info' in balance and 'assets' in balance['info']:
                for asset in balance['info']['assets']:
                    if asset['asset'] == 'USDT':
                        usdt_cross = float(asset['crossWalletBalance'])
                    if asset['asset'] == 'BNB':
                        bnb_cross = float(asset['crossWalletBalance'])
                logger.info(f"Saldo USDT (margem cruzada): {usdt_cross:.8f}")
                logger.info(f"Saldo BNB (margem cruzada): {bnb_cross:.8f}")
                print(f"[INFO] Saldo USDT (margem cruzada): {usdt_cross:.8f}")
                print(f"[INFO] Saldo BNB (margem cruzada): {bnb_cross:.8f}")
            else:
                logger.error("Não foi possível obter saldo em USDT e BNB.")
                print("[ERRO] Não foi possível obter saldo em USDT e BNB.")
            # Consulta alavancagem e posições abertas
            try:
                positions = balance['info']['positions'] if balance and 'info' in balance and 'positions' in balance['info'] else []
                open_positions = [p for p in positions if float(p.get('positionAmt', 0)) != 0]
                for pos in open_positions:
                    logger.info(f"Posição aberta: {pos['symbol']} | Quantidade: {pos['positionAmt']} | Alavancagem: {pos['leverage']}")
                if not open_positions:
                    logger.info("Nenhuma posição aberta no momento.")
            except Exception as e:
                logger.error(f"Erro ao consultar posições/alavancagem: {str(e)}")
            # Calcula sinais da estratégia
            df = strategy.calculate_signals(df)
            if df is None:
                logger.error("Failed to calculate signals")
                time.sleep(15)
                continue
            # Pega o último sinal gerado
            current_signal = df['signal'].iloc[-1]
            signal_changed = df['position_change'].iloc[-1] != 0
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            if signal_changed:
                if not balance or not ('total' in balance and 'USDT' in balance['total']):
                    logger.error("Failed to fetch account balance")
                    time.sleep(2)
                    continue
                current_price = float(df['close'].iloc[-1])
                position_size = strategy.get_position_size(
                    float(balance['total']['USDT']) if 'total' in balance and 'USDT' in balance['total'] else 0.0,
                    current_price,
                    risk_percentage
                )
                # Se não há posição aberta e sinal de compra/venda, abre posição
                if not trade_state['open'] and position_size:
                    if current_signal == 1:
                        order = connection.place_order(symbol, 'buy', position_size)
                        trade_state.update({
                            'open': True,
                            'side': 'buy',
                            'entry_time': now,
                            'entry_price': current_price,
                            'entry_volume': position_size
                        })
                    elif current_signal == -1:
                        order = connection.place_order(symbol, 'sell', position_size)
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
                    trade_record = {
                        'side': trade_state['side'],
                        'entry_time': trade_state['entry_time'],
                        'exit_time': exit_time,
                        'entry_price': trade_state['entry_price'],
                        'exit_price': exit_price,
                        'entry_volume': trade_state['entry_volume'],
                        'exit_volume': trade_state['entry_volume'],
                        'profit': pnl
                    }
                    # Salva trade no arquivo JSON
                    try:
                        with open('BOT/trades.json', 'r+', encoding='utf-8') as f:
                            trades = json.load(f)
                            trades.append(trade_record)
                            f.seek(0)
                            json.dump(trades, f, indent=4)
                    except Exception as e:
                        logger.error(f"Erro ao salvar trade: {str(e)}")
                    # Reseta estado da posição
                    trade_state = {
                        'open': False,
                        'side': None,
                        'entry_time': None,
                        'entry_price': None,
                        'entry_volume': None
                    }
            # Aguarda 2 segundos antes de repetir o loop
            time.sleep(2)
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
    run_event.clear()  # Começa pausado
    # Cria thread para rodar o loop do bot em paralelo ao menu
    bot_thread = threading.Thread(target=bot_loop, args=(run_event,), daemon=True)
    bot_thread.start()
    # Exibe menu interativo
    print("\n=== MENU DO BOT DE TRADING ===")
    print("[1] Iniciar bot")
    print("[2] Pausar bot")
    print("[3] Retomar bot")
    print("[4] Sair")
    while True:
        op = input("Escolha uma opção: ").strip()
        if op == '1':
            # Inicia o bot (ativa o evento)
            if not run_event.is_set():
                run_event.set()
                print("Bot iniciado!")
            else:
                print("Bot já está rodando.")
        elif op == '2':
            # Pausa o bot (limpa o evento)
            if run_event.is_set():
                run_event.clear()
                print("Bot pausado.")
            else:
                print("Bot já está pausado.")
        elif op == '3':
            # Retoma o bot (ativa o evento)
            if not run_event.is_set():
                run_event.set()
                print("Bot retomado!")
            else:
                print("Bot já está rodando.")
        elif op == '4':
            # Encerra o programa
            print("Encerrando...")
            run_event.clear()
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
