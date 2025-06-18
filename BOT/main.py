import os
import time
from dotenv import load_dotenv
from conexao import BinanceConnection
from strategy import TradingStrategy
import logging

# Load environment variables
load_dotenv()

def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('trading_bot.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Initialize connection with API keys from environment variables
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("API credentials not found in environment variables")
        return
    
    # Initialize connection and strategy
    connection = BinanceConnection(api_key, api_secret)
    strategy = TradingStrategy(short_window=20, long_window=50)
    
    # Trading parameters
    symbol = 'BTCUSDT'  # Trading pair
    interval = '1h'     # Timeframe
    risk_percentage = 0.02  # 2% risk per trade
    
    logger.info(f"Starting trading bot for {symbol} on {interval} timeframe")
    
    try:
        while True:
            # Get historical data
            df = connection.get_historical_klines(symbol, interval)
            if df is None:
                logger.error("Failed to fetch historical data")
                time.sleep(60)
                continue
            
            # Calculate signals
            df = strategy.calculate_signals(df)
            if df is None:
                logger.error("Failed to calculate signals")
                time.sleep(60)
                continue
            
            # Get latest signal
            current_signal = df['signal'].iloc[-1]
            signal_changed = df['position_change'].iloc[-1] != 0
            
            if signal_changed:
                # Get account balance
                balance = connection.get_account_balance()
                if not balance:
                    logger.error("Failed to fetch account balance")
                    time.sleep(60)
                    continue
                
                # Find USDT balance
                usdt_balance = next((b['balance'] for b in balance if b['asset'] == 'USDT'), None)
                if not usdt_balance:
                    logger.error("USDT balance not found")
                    time.sleep(60)
                    continue
                
                # Calculate position size
                current_price = float(df['close'].iloc[-1])
                position_size = strategy.get_position_size(
                    float(usdt_balance),
                    current_price,
                    risk_percentage
                )
                
                if position_size:
                    # Execute trade based on signal
                    if current_signal == 1:  # Buy signal
                        connection.place_order(symbol, 'BUY', position_size)
                    elif current_signal == -1:  # Sell signal
                        connection.place_order(symbol, 'SELL', position_size)
            
            # Wait for next candle
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()
