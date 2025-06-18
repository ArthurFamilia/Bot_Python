import pandas as pd
import numpy as np
import logging

class TradingStrategy:
    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        Inicializa a estratégia de trading com parâmetros de médias móveis.
        
        Parâmetros:
            short_window (int): Período da média móvel curta
            long_window (int): Período da média móvel longa
        """
        self.short_window = short_window
        self.long_window = long_window
        self.logger = logging.getLogger(__name__)
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula os sinais de trading com base no cruzamento de médias móveis.
        
        Parâmetros:
            df (pandas.DataFrame): Dados históricos de preços com colunas OHLCV
            
        Retorna:
            pandas.DataFrame: DataFrame com colunas de sinal adicionadas
        """
        try:
            # Calcula as médias móveis
            df['SMA_short'] = df['close'].rolling(window=self.short_window).mean()
            df['SMA_long'] = df['close'].rolling(window=self.long_window).mean()
            
            # Gera sinais de trading
            df['signal'] = 0
            df.loc[df['SMA_short'] > df['SMA_long'], 'signal'] = 1  # Sinal de compra
            df.loc[df['SMA_short'] < df['SMA_long'], 'signal'] = -1  # Sinal de venda
            
            # Calcula mudanças de posição para execução das operações
            df['position_change'] = df['signal'].diff()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular sinais: {str(e)}")
            return None
    
    def get_position_size(self, account_balance: float, current_price: float, risk_percentage: float = 0.02):
        """
        Calcula o tamanho da posição com base no saldo da conta e percentual de risco.
        
        Parâmetros:
            account_balance (float): Saldo atual da conta
            current_price (float): Preço atual do ativo
            risk_percentage (float): Percentual do saldo a ser arriscado por operação
            
        Retorna:
            float: Tamanho da posição em unidades do ativo
        """
        try:
            # Calcula o valor a ser arriscado
            risk_amount = account_balance * risk_percentage
            # Calcula o tamanho da posição
            position_size = risk_amount / current_price
            return round(position_size, 3)  # Arredonda para 3 casas decimais
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular tamanho da posição: {str(e)}")
            return None
