import os
import time
from dotenv import load_dotenv
from conexao import BinanceConnection
from strategy import TradingStrategy
import logging
import threading

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Função que executa o loop principal do bot de trading
# O loop só roda quando run_event está ativado (set)
def bot_loop(run_event):
    logger = logging.getLogger(__name__)
    # Busca as credenciais da API
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        return
    # Inicializa conexão e estratégia
    connection = BinanceConnection(api_key, api_secret)
    strategy = TradingStrategy(short_window=20, long_window=50)
    symbol = 'BTCUSDT'  # Par de negociação
    interval = '1h'     # Intervalo do candle
    risk_percentage = 0.02  # Risco por operação (2%)
    logger.info(f"Starting trading bot for {symbol} on {interval} timeframe")
    try:
        while True:
            run_event.wait()  # Pausa o loop se o evento estiver limpo (pausado)
            # Busca dados históricos
            df = connection.get_historical_klines(symbol, interval)
            if df is None:
                logger.error("Failed to fetch historical data")
                time.sleep(15)
                continue
            # Calcula sinais da estratégia
            df = strategy.calculate_signals(df)
            if df is None:
                logger.error("Failed to calculate signals")
                time.sleep(15)
                continue
            # Pega o último sinal gerado
            current_signal = df['signal'].iloc[-1]
            signal_changed = df['position_change'].iloc[-1] != 0
            if signal_changed:
                # Consulta saldo da conta
                balance = connection.get_account_balance()
                if not balance:
                    logger.error("Failed to fetch account balance")
                    time.sleep(15)
                    continue
                # Busca saldo em USDT
                usdt_balance = next((b['balance'] for b in balance if b['asset'] == 'USDT'), None)
                if not usdt_balance:
                    logger.error("USDT balance not found")
                    time.sleep(15)
                    continue
                # Calcula tamanho da posição
                current_price = float(df['close'].iloc[-1])
                position_size = strategy.get_position_size(
                    float(usdt_balance),
                    current_price,
                    risk_percentage
                )
                # Executa ordem de compra ou venda conforme o sinal
                if position_size:
                    if current_signal == 1:
                        connection.place_order(symbol, 'BUY', position_size)
                    elif current_signal == -1:
                        connection.place_order(symbol, 'SELL', position_size)
            # Aguarda 15 segundos antes de repetir o loop
            time.sleep(15)
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
