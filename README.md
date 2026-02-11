# Moneta Gustavo

Aplicação Streamlit para otimização de carteiras (modelo Moneta) e backtests com comparativo versus índice de referência.
O projeto utiliza Yahoo Finance ('yfinance'), algoritmo genético, métricas de risco/retorno e ferramentas auxiliares para manipulação de dados financeiros.

## ✨ Principais recursos
- Otimização de carteira com algoritmo genético.
- Backtests com comparação contra índice e carteiras aleatórias.
- Métricas de performance (Sharpe, Beta, Drawdown, etc.).
- Utilitários para geração e atualização de tickers.

## Referências
- [Streamlit](https://streamlit.io/)
- [Yahoo Finance API](https://pypi.org/project/yfinance/)
- [Repositório do projeto](https://github.com/gbsufscar/PrandianoPython2Moneta)

## 🧱 Estrutura do projeto
```
moneta_Gustavo/
├─ main.py
├─ paginas/
│  ├─ moneta.py
│  └─ backtestes.py
├─ modelo/
│  ├─ moneta.py
│  └─ backtestes.py
├─ cotacoes/
│  └─ cotacoes.py
├─ ag/
│  └─ ag.py
├─ ces/
│  └─ ces.py
├─ utils/
│  ├─ gerais.py
│  ├─ performance_tracker.py
│  ├─ gera_tikers/
│  └─ yahoo_finance.ipynb
├─ simbolos.py
├─ treinamento.py
├─ requirements.txt
└─ docs/
```

## ✅ Pré‑requisitos
- Python 3.13+ (recomendado)
- Ambiente virtual

## 🚀 Como executar
1) Ative o ambiente virtual:

```
.\venvMonetaGustavo\Scripts\activate.bat
```

2) Instale dependências:

```
pip install -r requirements.txt
```

3) Rode o app Streamlit:

```
streamlit run main.py
```

## 📊 Fluxo principal
1) Usuário escolhe ações e parâmetros na página **Moneta**.
2) `cotacoes/busca_cotacoes` baixa preços do Yahoo Finance.
3) `cotacoes/formata_cotacoes` calcula retornos e filtros.
4) `modelo/moneta.py` roda o algoritmo genético.
5) `utils/gerais.py` gera a tabela final da carteira.

## 🧪 Backtests
A página **Backtestes** permite avaliar o desempenho do Moneta em janelas de tempo e compara com:
- índice de referência (ex.: BOVA11.SA)
- carteiras aleatórias

## 📌 Dados e arquivos auxiliares
- Alguns JSONs e arquivos Excel em `utils/gera_tikers/` são usados para geração/ajuste de tickers.
- Saídas geradas automaticamente não são versionadas (ver `.gitignore`).

## 🗃️ Notebooks úteis
- `utils/yahoo_finance.ipynb`
- `utils/gera_tikers/gera_tickers.ipynb`

## Local de Armazenamento - Pasta de Rede
C:\Users\gbsuf\OneDrive\ambiente_programacao\moneta_Gustavo

## ☁️ Publicação no GitHub
```bash
git init
git add .
git commit -m "Primeira versão do Moneta"
git branch -M main
git remote add origin <[https://github.com/gbsufscar/monetaGustavo2026.git](https://github.com/gbsufscar/monetaGustavo2026.git)>
git push -u origin main
```

## 🛡️ Boas práticas ao publicar
- Não versionar `venvMonetaGustavo/`.
- Não versionar outputs gerados (JSON/Excel de saída).
- Manter `requirements.txt` atualizado.

## 📷 Diagrama do fluxo
Veja o diagrama em `docs/moneta_fluxo.svg`.


📘 Capítulo Final — Versão Futura do Projeto
Este capítulo descreve a evolução planejada do Moneta Gustavo, incluindo novas páginas, KPIs, banco de dados, temas e arquitetura modular.

🔮 Aplicações Futuras
📊 KPIs Financeiros
- Retorno acumulado
- Volatilidade anualizada
- Sharpe simplificado
- Drawdown máximo
- Gráficos interativos

📉 Comparação de Tickers
- Normalização de preços
- Comparação visual entre múltiplos ativos

💼 Carteiras Personalizadas
- Pesos definidos pelo usuário
- Evolução da carteira
- KPIs da carteira

📈 Backtesting (Buy & Hold)
- Evolução do capital investido
- Curva de patrimônio
🔥 Heatmap de Correlação
- Correlação entre ativos
- Visualização com Seaborn

⚠️ Risco (VaR e CVaR)
- Value at Risk (5%)
- Conditional VaR (5%)

🧠 Carteira Ótima (Markowitz)
- Fronteira eficiente
- Pesos recomendados
- Curva da carteira ótima

🗄 Banco de Dados Integrado
- SQLite local
- Suporte futuro para PostgreSQL
- Cache inteligente
- Armazenamento histórico

🎨 Tema Customizado
- Tema escuro
- Ícones e animações Lottie
- Menu lateral personalizado

🏗 Arquitetura Futura
```
projeto_financas/
│
├── data/
│   └── database.db
│
├── src/
│   ├── Home.py
│   │
│   ├── utils/
│   │   ├── db.py
│   │   ├── data_loader.py
│   │   ├── metrics.py
│   │   ├── backtesting.py
│   │   ├── risk.py
│   │   ├── markowitz.py
│   │   └── lottie.py
│   │
│   └── pages/
│       ├── 0_Resumo_Executivo.py
│       ├── 1_KPIs_Financeiros.py
│       ├── 2_Comparação_Tickers.py
│       ├── 3_Carteiras_Personalizadas.py
│       ├── 4_Backtesting.py
│       ├── 5_Heatmap_Correlacao.py
│       └── 6_Risco_VaR_CVaR.py
│
├── .streamlit/
│   └── config.toml
│
├── requirements.txt
└── README.md
```

🧭 Roadmap

- [ ] KPIs financeiros
- [ ] Carteiras personalizadas
- [ ] Backtesting
- [ ] Heatmap
- [ ] VaR e CVaR
- [x] Markowitz
- [ ] Banco SQLite
- [x] Tema customizado
- [ ] Alertas por e-mail
- [ ] Integração com APIs premium
- [ ] Deploy com PostgreSQL
- [ ] Dashboard mobile-friendly

---