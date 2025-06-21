# Trading Bot Python

Este é um bot de trading automatizado desenvolvido em Python para operar na Binance Futures, utilizando uma estratégia de cruzamento de médias móveis exponenciais (EMAs). O projeto suporta operação real e testnet, além de módulos para backtest e otimização de parâmetros.

## Funcionalidades

- Operação automatizada na Binance Futures (real ou testnet)
- Estratégia baseada em cruzamento de EMAs
- Gerenciamento de risco por valor fixo em USDT
- Sistema de logs detalhado
- Módulo de backtest
- Otimizador de parâmetros multi-símbolo e multi-intervalo
- Configuração centralizada do ambiente (testnet/produção)

## Requisitos

- Python 3.11 ou superior
- Conta na Binance (e chaves de API)
- Pacotes: ccxt, pandas, matplotlib, python-dotenv

## Estrutura do Projeto

```
BOT/
├── backtest.py           # Módulo para backtesting de estratégias
├── conexao.py            # Módulo de conexão com a Binance
├── main.py               # Arquivo principal do bot
├── otimizador_multi.py   # Otimização de parâmetros da estratégia
├── run_backtest.py       # Execução de backtest com gráficos
├── strategy.py           # Implementação da estratégia de trading
├── config.py             # Configurações gerais do bot
└── ...
```

## Configuração

1. Clone este repositório
2. Instale as dependências necessárias:
   ```bash
   pip install -r requirements.txt
   ```
3. Crie um arquivo `.env` na raiz do projeto com suas credenciais:
   ```env
   BINANCE_API_KEY=sua_api_key
   BINANCE_API_SECRET=sua_api_secret
   ```
4. Configure o arquivo `BOT/config.py`:
   - Par de trading, intervalos, parâmetros das médias, saldo inicial, valor por operação e se deseja usar testnet:
   ```python
   simbolo = 'HBAR/USDT'
   intervalo = '12h'
   MArapida = 30
   MAlenta = 40
   saldo_backtest = 500.0
   valor_fixo_usdt = 20
   usar_testnet = False  # True para testnet, False para produção
   ```

## Como Usar

### Operação ao vivo
```bash
python BOT/main.py
```

### Backtest
```bash
python BOT/run_backtest.py
```

### Otimização de Parâmetros
```bash
python BOT/otimizador_multi.py
```
Os melhores parâmetros serão salvos em `resultados_otimizacao.csv`.

## Estratégia de Trading

O bot utiliza cruzamento de médias móveis exponenciais:
- Média móvel curta: configurável (`MArapida`)
- Média móvel longa: configurável (`MAlenta`)
- Valor fixo por operação: configurável (`valor_fixo_usdt`)

## Logs

Todas as operações e eventos importantes são registrados em `trading_bot.log`.

## Aviso de Risco

Este bot é fornecido apenas para fins educacionais. Trading de criptomoedas envolve riscos significativos. Use por sua conta e risco. Sempre teste no ambiente testnet antes de operar com dinheiro real.

## Contribuições

Contribuições são bem-vindas! Abra issues ou envie pull requests.

## Licença

MIT

## Recado

Fazer testes antes de usar, tem que saber fazer backtest e otimização, se fizer merda e perder dinheiro, a culpa é sua, não minha. Use por sua conta e risco, não sou responsável por perdas financeiras. Este bot é para fins educacionais e de aprendizado, não para fazer dinheiro fácil.
