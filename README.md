# Trading Bot Python

Este é um bot de trading automatizado desenvolvido em Python para operar na exchange Binance. O bot utiliza uma estratégia de cruzamento de médias móveis para tomar decisões de compra e venda de criptomoedas.

## Funcionalidades

- Conexão com a API da Binance
- Estratégia de trading baseada em cruzamento de médias móveis
- Suporte a backtesting para teste de estratégias
- Otimização de parâmetros
- Sistema de logs para monitoramento
- Modo testnet para testes seguros

## Requisitos

- Python 3.11 ou superior
- Conta na Binance
- Chaves de API da Binance (API Key e Secret Key)

## Estrutura do Projeto

```
BOT/
├── backtest.py      # Módulo para backtesting de estratégias
├── conexao.py       # Módulo de conexão com a Binance
├── main.py          # Arquivo principal do bot
├── otimizador_.py   # Otimização de parâmetros da estratégia
└── strategy.py      # Implementação da estratégia de trading
```

## Configuração

1. Clone este repositório
2. Instale as dependências necessárias
3. Crie um arquivo `.env` na raiz do projeto com suas credenciais:

```
BINANCE_API_KEY=sua_api_key
BINANCE_API_SECRET=sua_api_secret
```

## Como Usar

1. Configure suas credenciais no arquivo `.env`
2. Execute o bot:
```bash
python BOT/main.py
```

## Estratégia de Trading

O bot utiliza uma estratégia de cruzamento de médias móveis:
- Média móvel curta: 20 períodos
- Média móvel longa: 50 períodos

Os parâmetros podem ser otimizados utilizando o módulo `otimizador_.py`.

## Backtesting

Para testar a estratégia com dados históricos:
```bash
python BOT/backtest.py
```

## Logs

O bot mantém um registro detalhado de suas operações no arquivo `trading_bot.log`.

## ⚠️ Aviso de Risco

Este bot é fornecido apenas para fins educacionais. Trading de criptomoedas envolve riscos significativos. Use por sua conta e risco. Recomenda-se sempre testar primeiro no ambiente testnet antes de usar com dinheiro real.

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença

Este projeto está sob a licença MIT.


Fazer testes antes de usar, tem q saber fazer backtest e otimizaçao e revisar o codigo tbm.
