import pandas as pd
import numpy as np
from ag.ag import (gerar_cromossomos_base, roda_do_acaso, crossover,
                mutacao_um, mutacao_dois, gerar_nova_geracao)

def moneta_ag(variacoes: pd.DataFrame, 
            qtd_iteracoes = 10, qtd_epocas = 40, qtd_croms_populacao_geral = 40):
    """
    Otimiza pesos de portfólio usando Algoritmo Genético (AG) minimizando risco.
    
    Implementa um algoritmo genético multi-geracional que evolui uma população de
    carteiras (cromossomos) para encontrar a alocação de pesos que maximiza o índice
    de Sharpe (retorno ajustado por risco). Utiliza seleção por roleta, crossover,
    e mutação para explorar o espaço de soluções.
    
    Parâmetros:
    -----------
    variacoes : pd.DataFrame
        DataFrame com as séries de retornos das ações
        (índice: datas, colunas: símbolos/tickers das ações)
        Cada coluna representa uma série de retornos periódicos de um ativo
        
    qtd_iteracoes : int, optional
        Número de iterações (cruzamentos e mutações) por época (default: 10)
        Controla a intensidade de exploração a cada geração
        
    qtd_epocas : int, optional
        Número de épocas (gerações) do algoritmo genético (default: 40)
        Maior número = mais evolução, mas maior tempo computacional
        
    qtd_croms_populacao_geral : int, optional
        Tamanho da população de cromossomos (default: 40)
        Cada cromossomo representa uma carteira candidata
    
    Retorna:
    --------
    pd.Series
        Série (cromossomo) com a melhor carteira encontrada contendo:
        - Índices: símbolos das ações (ex: 'PETR4.SA', 'VALE3.SA', ...)
        - Valores: pesos da alocação (somam 1.0, não-negativos)
        - Uma linha final com 'Fitnesses': valor do índice de Sharpe da carteira
        - Uma linha final com 'Retornos': retorno esperado da carteira
    
    Exemplos:
    ---------
    >>> df_retornos = pd.DataFrame({
    ...     'PETR4.SA': [0.01, -0.02, 0.03, ...],
    ...     'VALE3.SA': [0.02, 0.01, -0.01, ...],
    ...     'GGBR4.SA': [-0.01, 0.02, 0.01, ...]
    ... })
    >>> 
    >>> melhor_carteira = moneta_ag(
    ...     variacoes=df_retornos,
    ...     qtd_iteracoes=10,
    ...     qtd_epocas=40,
    ...     qtd_croms_populacao_geral=40
    ... )
    >>> 
    >>> print(melhor_carteira)
    PETR4.SA               0.35
    VALE3.SA               0.45
    GGBR4.SA               0.20
    Fitnesses             1.25
    Retornos              0.025
    dtype: float64
    >>> 
    >>> # Acessar pesos individuais
    >>> peso_petr = melhor_carteira['PETR4.SA']  # 0.35
    >>> sharpe = melhor_carteira['Fitnesses']     # 1.25
    
    Notes:
    ------
    Fluxo do Algoritmo:
    1. Gera população inicial de carteiras aleatórias
    2. Para cada época:
       - Seleciona 6 cromossomos aleatoriamente
       - Para cada iteração:
         * Roda da Sorte: seleciona 2 pais probabilisticamente
         * Crossover: cria 2 filhos combinando genes dos pais
         * Mutação Tipo 1: altera pesos aleatoriamente
         * Mutação Tipo 2: redistribui pesos entre ativos
         * Avalia fitness (Índice de Sharpe) dos novos cromossomos
         * Substitui cromossomo pior por melhor (elitismo)
       - Atualiza população geral
    3. Retorna carteira com maior fitness da população final
    
    O fitness de cada cromossomo é calculado como o Índice de Sharpe:
    Sharpe = E[Retorno] / Desvio Padrão = (μp) / (σp)
    
    Maior Sharpe = melhor relação risco-retorno
    
    Complexidade:
    - Temporal: O(épocas × iterações × população × n_ativos)
    - Espacial: O(população × n_ativos)
    """

    acoes = variacoes.columns

    medias = variacoes.mean(axis=0)
    matriz_covariancia = variacoes.cov()

    cromossomos = gerar_cromossomos_base(qtd_croms_populacao_geral, acoes, medias, 
                                        matriz_covariancia)

    for _ in range(qtd_epocas):
        indices_cromossomos_sorteados = np.random.choice(cromossomos.index,
                                                    size=6, replace=False)
        cromossomos_sorteados = cromossomos.loc[indices_cromossomos_sorteados]

        for _ in range(qtd_iteracoes):

            # RODA DO ACASO -------------------------------------
            # gera um series com as percentagens relativas:
            # 0.2, 0.45, 0.05, 0.10, 0.15, 0.05
            cromossomo_pai, cromossomo_mae = roda_do_acaso(cromossomos_sorteados)
            
            # RODA DO ACASO -------------------------------------

            # CROSSOVER -----------------------------------------

            cromossomo_filho_um = crossover(acoes, cromossomo_pai, cromossomo_mae)
            cromossomo_filho_dois = crossover(acoes, cromossomo_pai, cromossomo_mae)

            # CROSSOVER -----------------------------------------

            # MUTAÇÃO DO TIPO 1 ---------------------------------
            mutante_um = mutacao_um(acoes, cromossomo_filho_um)
            mutante_dois = mutacao_um(acoes, cromossomo_filho_dois)
            # MUTAÇÃO DO TIPO 1 ---------------------------------

            # MUTAÇÃO DO TIPO 2 ---------------------------------
            mutante_tres, mutante_quatro = mutacao_dois(acoes, cromossomo_filho_um)
            mutante_cinco, mutante_seis = mutacao_dois(acoes, cromossomo_filho_dois)
            # MUTAÇÃO DO TIPO 2 --------------------------------


            df_nova_geracao = gerar_nova_geracao(acoes, medias, matriz_covariancia, 
                                                cromossomo_filho_um, cromossomo_filho_dois, 
                                            mutante_um, mutante_dois, mutante_tres, 
                                                mutante_quatro, mutante_cinco, mutante_seis)

            nome_cromossomo_ruim = cromossomos_sorteados["Fitnesses"].idxmin()

            nome_cromossomo_bom = df_nova_geracao["Fitnesses"].idxmax()

            fitness_pior_pai = cromossomos_sorteados.loc[nome_cromossomo_ruim].loc["Fitnesses"]
            fitness_melhor_filho = df_nova_geracao.loc[nome_cromossomo_bom].loc["Fitnesses"]

            if fitness_melhor_filho > fitness_pior_pai:
                cromossomos_sorteados.loc[nome_cromossomo_ruim] = \
                    df_nova_geracao.loc[nome_cromossomo_bom].values
        
        cromossomos.loc[indices_cromossomos_sorteados] = \
            cromossomos_sorteados.values

    indice_melhor_cromossomo = cromossomos["Fitnesses"].idxmax()
    melhor_cromossomo = cromossomos.loc[indice_melhor_cromossomo]

    return melhor_cromossomo