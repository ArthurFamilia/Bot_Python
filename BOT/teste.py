# Exemplo de uso em outro arquivo, por exemplo: teste_conexao.py

from conexao import TrailingStop

bot = TrailingStop()
bot.testar_conexao()
bot.buy_with_trailing_stop(
    symbol="BTCUSDT",
    quantity=0.001,
    callback_rate=0.5
)