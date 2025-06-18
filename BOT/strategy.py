import pandas as pd
import numpy as np
import logging

class TradingStrategy:
    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        Initialize the trading strategy with moving average parameters
        
        Parameters:
            short_window (int): Short-term moving average period
            long_window (int): Long-term moving average period
        """
        self.short_window = short_window
        self.long_window = long_window
        self.logger = logging.getLogger(__name__)
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate trading signals based on moving average crossover
        
        Parameters:
            df (pandas.DataFrame): Historical price data with OHLCV columns
            
        Returns:
            pandas.DataFrame: DataFrame with added signal columns
        """
        try:
            # Calculate moving averages
            df['SMA_short'] = df['close'].rolling(window=self.short_window).mean()
            df['SMA_long'] = df['close'].rolling(window=self.long_window).mean()
            
            # Calculate trading signals
            df['signal'] = 0
            df.loc[df['SMA_short'] > df['SMA_long'], 'signal'] = 1  # Buy signal
            df.loc[df['SMA_short'] < df['SMA_long'], 'signal'] = -1  # Sell signal
            
            # Calculate signal changes for trade execution
            df['position_change'] = df['signal'].diff()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error calculating signals: {str(e)}")
            return None
    
    def get_position_size(self, account_balance: float, current_price: float, risk_percentage: float = 0.02):
        """
        Calculate position size based on account balance and risk percentage
        
        Parameters:
            account_balance (float): Current account balance
            current_price (float): Current asset price
            risk_percentage (float): Percentage of account to risk per trade
            
        Returns:
            float: Position size in units of the asset
        """
        try:
            risk_amount = account_balance * risk_percentage
            position_size = risk_amount / current_price
            return round(position_size, 3)  # Round to 3 decimal places
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {str(e)}")
            return None
