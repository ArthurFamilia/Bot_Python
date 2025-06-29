import pandas as pd
import logging
import config
import ta

class TradingStrategy:
    def __init__(self, short_window = config.MArapida, long_window = config.MAlenta):
        self.short_window = short_window
        self.long_window = long_window
        self.logger = logging.getLogger(__name__)
    
    def calculate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula sinais de trading com base em médias móveis e filtros do config."""
        try:
            df['SMA_short'] = df['close'].ewm(span=self.short_window, adjust=False).mean()
            df['SMA_long'] = df['close'].ewm(span=self.long_window, adjust=False).mean()
            df['signal'] = 0
            df.loc[df['SMA_short'] > df['SMA_long'], 'signal'] = 1
            df.loc[df['SMA_short'] < df['SMA_long'], 'signal'] = -1
            if config.ativar_filtro_tendencia or config.ativar_filtro_distancia:
                tendencia = df['SMA_long'].diff()
                min_dist = df['close'] * config.distancia_minima_percent
                for i in range(1, len(df)):
                    if config.ativar_filtro_tendencia:
                        if df['signal'].iloc[i] == 1 and tendencia.iloc[i] <= 0:
                            df.at[df.index[i], 'signal'] = 0
                        if df['signal'].iloc[i] == -1 and tendencia.iloc[i] >= 0:
                            df.at[df.index[i], 'signal'] = 0
                    if config.ativar_filtro_distancia:
                        if abs(df['SMA_short'].iloc[i] - df['SMA_long'].iloc[i]) < min_dist.iloc[i]:
                            df.at[df.index[i], 'signal'] = 0
            df['position_change'] = df['signal'].diff().fillna(0)
            df['trade_signal'] = df['position_change']
            return df
        except Exception as e:
            self.logger.error(f"Erro ao calcular sinais: {str(e)}")
            return None
    
    def get_position_size(self, account_balance: float, current_price: float, risk_percentage: float = None):
        """Calcula o tamanho da posição com base em valor fixo em USDT."""
        try:
            position_size = config.valor_fixo_usdt / current_price
            return round(position_size, 3)  # Arredonda para 3 casas decimais
            
        except Exception as e:
            self.logger.error(f"Erro ao calcular tamanho da posição: {str(e)}")
            return None
