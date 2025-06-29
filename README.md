# Trading Bot Python

Um bot de trading para Binance Futures, com backtest, otimização e execução real, totalmente configurável e fácil de usar. Desenvolvido para profissionais de TI, traders quantitativos e entusiastas de automação financeira.

## Funcionalidades
- **Execução real e em testnet** (Binance Futures via CCXT)
- **Backtest** com os mesmos parâmetros e lógica do bot real
- **Otimização automática** de parâmetros de estratégia
- **Filtros de tendência e distância mínima** entre médias móveis
- **Logs detalhados** e fácil integração com sistemas de monitoramento
- **Configuração centralizada** via `config.py`

## Requisitos
- Python 3.9+
- Conta na Binance (API Key e Secret)
- [CCXT](https://github.com/ccxt/ccxt), [pandas](https://pandas.pydata.org/), [ta-lib](https://github.com/bukosabino/ta), [python-dotenv](https://github.com/theskumar/python-dotenv), [matplotlib](https://matplotlib.org/)

Instale as dependências:
```bash
pip install -r requirements.txt
```

## Configuração
1. **Crie um arquivo `.env`** com suas chaves:
   ```env
   BINANCE_API_KEY=SEU_API_KEY
   BINANCE_API_SECRET=SEU_API_SECRET
   ```
2. **Edite o arquivo `config.py`** para definir:
   - Par de trading (`simbolo`)
   - Intervalo dos candles (`intervalo`)
   - Parâmetros das médias móveis
   - Saldo inicial, valor por operação, filtros, etc.

## Como usar

### 1. Backtest
Execute o backtest para avaliar a estratégia:
```bash
python BOT/run_backtest.py
```

### 2. Otimização de Parâmetros
Encontre os melhores parâmetros para sua estratégia:
```bash
python BOT/otimizador_multi.py
```
Os resultados ficam em `resultados_otimizacao.csv`.

### 3. Execução do Bot Real
O bot principal está em `main.py` e pode ser executado com:
```bash
python BOT/main.py
```
> **Dica:** Use um gerenciador de processos (ex: PM2, Supervisor, Docker) para rodar o bot em produção.

### 4. Teste Unitário da Estratégia
```bash
python BOT/test_strategy.py
```

## Estrutura dos Arquivos
- `config.py`: Parâmetros globais e filtros
- `main.py`: Bot de trading real
- `run_backtest.py`: Backtest da estratégia
- `otimizador_multi.py`: Otimização de parâmetros
- `strategy.py`: Lógica da estratégia (médias móveis, filtros)
- `backtest.py`: Motor de simulação
- `conexao.py`: Interface com a Binance (CCXT)
- `test_strategy.py`: Teste unitário da estratégia

## Estratégia
- Baseada em cruzamento de médias móveis exponenciais
- Filtros opcionais de tendência e distância mínima
- Parâmetros ajustáveis via `config.py` ou otimização automática

## Logs e Monitoramento
- Todos os logs são salvos em `trading_bot.log`
- Prints importantes no console
- Fácil integração com sistemas de alerta (adapte o logger se necessário)

## Segurança
- **Nunca compartilhe suas chaves de API.**
- Use a testnet para validar antes de operar com dinheiro real.
- Limite o valor de cada operação em `config.py`.

## Dicas para Deploy Profissional
- Use Docker ou ambiente virtual isolado
- Monitore o processo e o arquivo de log
- Faça backup dos arquivos de configuração e resultados
- Teste exaustivamente em testnet antes de operar ao vivo

## Suporte e Customização
- O código é modular e fácil de adaptar para outras estratégias
- Para dúvidas ou melhorias, abra uma issue ou faça um fork

---

**Desenvolvido por Arthur Age se você nao sabe o que esta fazendo não use este sistema e se sabe use por sua conta e risco.**
