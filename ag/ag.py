import pandas as pd
import numpy as np
from ces.ces import ces_retornos, ces_riscos, ces_fitnesses
from sklearn import preprocessing


def gerar_nova_geracao(acoes, medias, matriz_covariancia, cromossomo_filho_um, 
                    cromossomo_filho_dois, mutante_um, mutante_dois, mutante_tres, 
                    mutante_quatro, mutante_cinco, mutante_seis):
    """
    Cria e avalia uma nova geração de cromossomos (carteiras) do algoritmo genético.
    
    Recebe 6 cromossomos candidatos (2 filhos de crossover + 4 mutantes) e os avalia
    calculando suas métricas de desempenho: retorno esperado, risco (volatilidade)
    e fitness (índice de Sharpe). Retorna um DataFrame com os 6 cromossomos e suas
    respectivas métricas, permitindo comparação para seleção de elite.
    
    Parâmetros:
    -----------
    acoes : Index ou list
        Nomes/símbolos das ações que compõem os cromossomos
        (ex: ['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
        
    medias : pd.Series
        Retorno médio (esperado) de cada ação calculado a partir do histórico
        Índices: símbolos das ações
        Valores: retorno esperado para cada ativa
        
    matriz_covariancia : pd.DataFrame
        Matriz de covariância entre os retornos das ações
        Dimensão: (n_ativos × n_ativos)
        Usada para calcular o risco (volatilidade) da carteira
        
    cromossomo_filho_um : pd.Series
        Primeiro cromossomo filho gerado por crossover
        Índices: símbolos das ações
        Valores: pesos da alocação (devem somar 1.0)
        
    cromossomo_filho_dois : pd.Series
        Segundo cromossomo filho gerado por crossover
        
    mutante_um : pd.Series
        Primeiro cromossomo mutante gerado por mutação tipo 1
        (troca/inversão de genes)
        
    mutante_dois : pd.Series
        Segundo cromossomo mutante gerado por mutação tipo 1
        
    mutante_tres : pd.Series
        Terceiro cromossomo mutante gerado por mutação tipo 2
        (redistribuição de pesos entre dois genes)
        
    mutante_quatro : pd.Series
        Quarto cromossomo mutante gerado por mutação tipo 2
        
    mutante_cinco : pd.Series
        Quinto cromossomo mutante gerado por mutação tipo 2
        
    mutante_seis : pd.Series
        Sexto cromossomo mutante gerado por mutação tipo 2
    
    Retorna:
    --------
    pd.DataFrame
        DataFrame com 8 linhas (os 6 cromossomos) e colunas contendo:
        - Colunas de ativos: pesos alocados para cada ação (soma = 1.0)
        - 'Retornos' : float
            Retorno esperado da carteira (média ponderada dos retornos)
        - 'Riscos' : float
            Risco da carteira (desvio padrão dos retornos)
            Calculado como: sqrt(w^T × Σ × w)
        - 'Fitnesses' : float
            Índice de Sharpe (Retorno / Risco)
            Maior valor indica melhor relação risco-retorno
    
    Exemplos:
    ---------
    >>> # Suponha medias e matriz_covariancia já calculadas
    >>> acoes = pd.Index(['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
    >>> filho_1 = pd.Series([0.3, 0.5, 0.2], index=acoes)
    >>> # ... outros 5 cromossomos ...
    >>> 
    >>> df_geracao = gerar_nova_geracao(
    ...     acoes=acoes,
    ...     medias=medias,
    ...     matriz_covariancia=matriz_covariancia,
    ...     cromossomo_filho_um=filho_1,
    ...     cromossomo_filho_dois=filho_2,
    ...     mutante_um=mut_1,
    ...     mutante_dois=mut_2,
    ...     mutante_tres=mut_3,
    ...     mutante_quatro=mut_4,
    ...     mutante_cinco=mut_5,
    ...     mutante_seis=mut_6
    ... )
    >>> 
    >>> print(df_geracao)
    # Output:
    #         PETR4.SA  VALE3.SA  GGBR4.SA  Retornos   Riscos  Fitnesses
    # 0          0.30      0.50      0.20    0.0245    0.035      0.70
    # 1          0.25      0.45      0.30    0.0230    0.032      0.72
    # 2          0.35      0.40      0.25    0.0250    0.038      0.66
    # ...
    >>> 
    >>> # Encontrar o melhor cromassomo da geração
    >>> melhor_idx = df_geracao['Fitnesses'].idxmax()
    >>> melhor = df_geracao.loc[melhor_idx]
    
    Notes:
    ------
    Fluxo de Avaliação:
    1. Agrupa os 6 cromossomos em um DataFrame
    2. Calcula retorno esperado de cada carteira usando ces_retornos()
    3. Calcula risco (volatilidade) de cada carteira usando ces_riscos()
    4. Calcula fitness (Índice de Sharpe) de cada carteira usando ces_fitnesses()
    
    Métricas Calculadas:
    - Retorno = w1×μ1 + w2×μ2 + ... + wn×μn (média ponderada)
    - Risco = sqrt(w^T × Σ × w) (volatilidade do portfólio)
    - Fitness = Retorno / Risco (razão de Sharpe)
    
    Use este DataFrame com .idxmax()['Fitnesses'] para selecionar o melhor
    cromossomo da geração (estratégia elitista de seleção).
    """
    
    df_nova_geracao = pd.DataFrame(data=[cromossomo_filho_um, cromossomo_filho_dois,
                                                    mutante_um, mutante_dois,
                                                    mutante_tres, mutante_quatro,
                                                    mutante_cinco, mutante_seis])
            
    df_nova_geracao["Retornos"] = \
                ces_retornos(carteiras=df_nova_geracao, medias=medias)

    df_nova_geracao["Riscos"] = ces_riscos(
                carteiras=df_nova_geracao.loc[:, acoes], 
                matriz_covariancia=matriz_covariancia)

    df_nova_geracao["Fitnesses"] = ces_fitnesses(
                retornos=df_nova_geracao.loc[:, "Retornos"],
                riscos=df_nova_geracao.loc[:, "Riscos"]
            )
    
    return df_nova_geracao


def mutacao_dois(acoes, cromossomo_filho):
    """
    Aplica mutação tipo 2: redistribui pesos entre dois genes mantendo soma constante.
    
    Gera dois cromossomos mutantes a partir de um cromossomo filho, redistribuindo
    os pesos de dois genes aleatoriamente selecionados. Cada mutante recebe a soma
    dos dois genes em uma posição diferente, mantendo a restrição de que os pesos
    devem somar 1.0. Útil para explorar alocações concentradas em menos ativos.
    
    Parâmetros:
    -----------
    acoes : Index ou list
        Nomes/símbolos das ações que compõem o cromossomo
        (ex: ['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
        
    cromossomo_filho : pd.Series
        Cromossomo (carteira) a ser mutado
        Índices: símbolos das ações
        Valores: pesos da alocação (devem somar 1.0)
    
    Retorna:
    --------
    tuple[pd.Series, pd.Series]
        Tupla contendo dois cromossomos mutantes:
        
        - mutante_a : pd.Series
            Primeiro mutante onde:
            - genes_sorteados[0] recebe a soma dos dois pesos originais
            - genes_sorteados[1] recebe peso 0
            - demais genes mantêm valores originais
            
        - mutante_b : pd.Series
            Segundo mutante onde:
            - genes_sorteados[0] recebe peso 0
            - genes_sorteados[1] recebe a soma dos dois pesos originais
            - demais genes mantêm valores originais
    
    Exemplos:
    ---------
    >>> acoes = pd.Index(['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
    >>> cromossomo = pd.Series([0.3, 0.4, 0.3], index=acoes)
    >>> 
    >>> # Suponha que foram sorteados os índices 0 e 1 (PETR4.SA e VALE3.SA)
    >>> # Soma: 0.3 + 0.4 = 0.7
    >>> 
    >>> mutante_a, mutante_b = mutacao_dois(acoes, cromossomo)
    >>> 
    >>> print("Cromossomo original:")
    >>> print(cromossomo)
    # PETR4.SA    0.3
    # VALE3.SA    0.4
    # GGBR4.SA    0.3
    # dtype: float64
    >>> 
    >>> print("\\nMutante A (concentra em PETR4.SA):")
    >>> print(mutante_a)
    # PETR4.SA    0.7  (0.3 + 0.4)
    # VALE3.SA    0.0  (zerado)
    # GGBR4.SA    0.3  (mantido)
    # dtype: float64
    >>> 
    >>> print("\\nMutante B (concentra em VALE3.SA):")
    >>> print(mutante_b)
    # PETR4.SA    0.0  (zerado)
    # VALE3.SA    0.7  (0.3 + 0.4)
    # GGBR4.SA    0.3  (mantido)
    # dtype: float64
    
    Notes:
    ------
    Características da Mutação Tipo 2:
    
    1. **Preservação da Restrição**: A soma total dos pesos permanece 1.0
       Original: w1 + w2 + w_resto = 1.0
       Mutante A: (w1 + w2) + 0 + w_resto = 1.0
       
    2. **Exploração de Concentração**: Cria carteiras com alocações mais
       concentradas em menos ativos, ajudando a explorar o espaço de soluções
       
    3. **Dois Candidatos**: Retorna 2 mutantes diferentes (a e b) explorando
       as duas formas de redistribuição possíveis
       
    4. **Diversidade Genética**: Complementa mutação_um (troca/inversão) com
       operador de redução de dimensionalidade do espaço de busca
    
    Diferenças com Mutação Tipo 1:
    - Tipo 1: troca/inverte dois genes (permutação)
    - Tipo 2: redistribui e zeroa genes (exploração concentrada)
    
    Use em conjunto com mutacao_um() e crossover() para máxima exploração
    durante a evolução do algoritmo genético.
    """
    
    genes_sorteados = np.random.choice(acoes, size=2, replace=False)
    soma_genes = cromossomo_filho.loc[genes_sorteados].sum()
    mutante_a = cromossomo_filho.copy()
    mutante_a.loc[genes_sorteados[0]] = soma_genes
    mutante_a.loc[genes_sorteados[1]] = 0

    mutante_b = cromossomo_filho.copy()
    mutante_b.loc[genes_sorteados[0]] = 0
    mutante_b.loc[genes_sorteados[1]] = soma_genes
    return mutante_a,mutante_b

def mutacao_um(acoes, cromossomo_filho):
    """
    Aplica mutação tipo 1: troca/inverte os pesos de dois genes aleatórios.
    
    Gera um cromossomo mutante a partir de um cromossomo filho, trocando
    (invertendo) os valores de dois genes aleatoriamente selecionados. Mantém
    a restrição de que os pesos devem somar 1.0. Útil para explorar diferentes
    permutações de alocação mantendo a mesma quantidade total de capital.
    
    Parâmetros:
    -----------
    acoes : Index ou list
        Nomes/símbolos das ações que compõem o cromossomo
        (ex: ['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
        
    cromossomo_filho : pd.Series
        Cromossomo (carteira) a ser mutado
        Índices: símbolos das ações
        Valores: pesos da alocação (devem somar 1.0)
    
    Retorna:
    --------
    pd.Series
        Cromossomo mutante onde:
        - Os valores dos dois genes sorteados foram trocados entre si
        - Todos os demais genes mantêm seus valores originais
        - A soma total dos pesos permanece 1.0
    
    Exemplos:
    ---------
    >>> acoes = pd.Index(['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
    >>> cromossomo = pd.Series([0.3, 0.4, 0.3], index=acoes)
    >>> 
    >>> # Suponha que foram sorteados os índices 0 e 1 (PETR4.SA e VALE3.SA)
    >>> 
    >>> mutante = mutacao_um(acoes, cromossomo)
    >>> 
    >>> print("Cromossomo original:")
    >>> print(cromossomo)
    # PETR4.SA    0.3
    # VALE3.SA    0.4
    # GGBR4.SA    0.3
    # dtype: float64
    >>> 
    >>> print("\\nMutante (PETR4 e VALE3 trocados):")
    >>> print(mutante)
    # PETR4.SA    0.4     (invertido com VALE3.SA)
    # VALE3.SA    0.3     (invertido com PETR4.SA)
    # GGBR4.SA    0.3     (mantido)
    # dtype: float64
    >>> 
    >>> # Verificar que a soma permanece a mesma
    >>> print(f"\\nSoma original: {cromossomo.sum():.4f}")
    # Soma original: 1.0000
    >>> print(f"Soma mutante: {mutante.sum():.4f}")
    # Soma mutante: 1.0000
    
    Notes:
    ------
    Características da Mutação Tipo 1:
    
    1. **Operação de Permutação**: Troca (swap) dois valores de posição
       Original:  [0.3, 0.4, 0.3]
       Mutante:   [0.4, 0.3, 0.3]
       
    2. **Preservação de Restrições**: Mantém a soma = 1.0
       Se w1 + w2 + w_resto = 1.0
       Então w2 + w1 + w_resto = 1.0 (comutatividade)
       
    3. **Exploração Local**: Cria variações pequenas e locais no espaço
       de soluções, mantendo a estrutura geral da carteira
       
    4. **Diversidade Genética**: Complementa mutacao_dois (concentração)
       com operador de permutação/reorganização
    
    Comparação com Mutação Tipo 2:
    - Tipo 1: inverte dois pesos (permutação) - exploração local
    - Tipo 2: redistribui e zeroa (concentração) - exploração concentrada
    
    Uso no Algoritmo Genético:
    Aplicada após crossover para gerar variações nos filhos, permitindo
    que o AG explore permutações diferentes mantendo diversidade.
    Use em conjunto com mutacao_dois() e crossover() para máxima exploração.
    
    Complexidade:
    - Tempo: O(n) onde n é o número de ações
    - Espaço: O(n) para cópia do cromossomo
    """
    
    genes_sorteados = np.random.choice(acoes, size=2, replace=False)
    mutante = cromossomo_filho.copy()
    mutante.loc[genes_sorteados] = \
                cromossomo_filho.loc[genes_sorteados].iloc[::-1].values
        
    return mutante

def crossover(acoes, cromossomo_pai, cromossomo_mae):
    """
    Gera um cromossomo filho através de crossover aritmético ponderado.
    
    Cria um cromossomo filho combinando os genes do pai e da mãe de forma
    aritmética. Uma proporção aleatória (al) dos genes é herdada do pai,
    enquanto a proporção complementar (1-al) é herdada da mãe. Mantém a
    restrição de que os pesos devem somar 1.0.
    
    Parâmetros:
    -----------
    acoes : Index ou list
        Nomes/símbolos das ações que compõem os cromossomos
        (ex: ['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
        
    cromossomo_pai : pd.Series
        Cromossomo do pai (carteira parental 1)
        Índices: símbolos das ações
        Valores: pesos da alocação (devem somar 1.0)
        
    cromossomo_mae : pd.Series
        Cromossomo da mãe (carteira parental 2)
        Índices: símbolos das ações
        Valores: pesos da alocação (devem somar 1.0)
    
    Retorna:
    --------
    pd.Series
        Cromossomo filho gerado através de crossover, onde:
        - Cada gene é uma combinação ponderada dos genes dos pais
        - filho[i] = al × pai[i] + (1-al) × mãe[i]
        - A soma total dos pesos permanece 1.0
    
    Exemplos:
    ---------
    >>> acoes = pd.Index(['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
    >>> cromossomo_pai = pd.Series([0.5, 0.3, 0.2], index=acoes)
    >>> cromossomo_mae = pd.Series([0.2, 0.4, 0.4], index=acoes)
    >>> 
    >>> # Suponha que foi sorteado al = 0.6
    >>> # Esperamos:
    >>> # PETR4.SA: 0.6 × 0.5 + 0.4 × 0.2 = 0.30 + 0.08 = 0.38
    >>> # VALE3.SA: 0.6 × 0.3 + 0.4 × 0.4 = 0.18 + 0.16 = 0.34
    >>> # GGBR4.SA: 0.6 × 0.2 + 0.4 × 0.4 = 0.12 + 0.16 = 0.28
    >>> # Soma: 0.38 + 0.34 + 0.28 = 1.00
    >>> 
    >>> filho = crossover(acoes, cromossomo_pai, cromossomo_mae)
    >>> 
    >>> print("Cromossomo pai:")
    >>> print(cromossomo_pai)
    # PETR4.SA    0.5
    # VALE3.SA    0.3
    # GGBR4.SA    0.2
    # dtype: float64
    >>> 
    >>> print("\\nCromossomo mãe:")
    >>> print(cromossomo_mae)
    # PETR4.SA    0.2
    # VALE3.SA    0.4
    # GGBR4.SA    0.4
    # dtype: float64
    >>> 
    >>> print("\\nCromossomo filho (al ≈ 0.6):")
    >>> print(filho)
    # PETR4.SA    0.38  (0.6×0.5 + 0.4×0.2)
    # VALE3.SA    0.34  (0.6×0.3 + 0.4×0.4)
    # GGBR4.SA    0.28  (0.6×0.2 + 0.4×0.4)
    # dtype: float64
    >>> 
    >>> # Verificar que a soma permanece 1.0
    >>> print(f"\\nSoma do filho: {filho.sum():.6f}")
    # Soma do filho: 1.000000
    
    Notes:
    ------
    Características do Crossover Aritmético:
    
    1. **Herança Intermediária**: O filho herda uma combinação ponderada de
       ambos os pais, não uma simples seleção de genes (como em crossover
       tradicional com pontos de corte)
       
    2. **Preservação de Restrições**: A soma ponderada mantém a propriedade
       de que os pesos somam 1.0:
       ∑filho[i] = ∑(al × pai[i] + (1-al) × mãe[i])
                 = al×∑pai[i] + (1-al)×∑mãe[i]
                 = al×1 + (1-al)×1
                 = 1.0
       
    3. **Aleatoriedade Contínua**: O parâmetro al é sorteado uniformemente
       em [0,1], permitindo qualquer proporção de herança do pai
       
    4. **Exploração do Espaço**: Cria filhos que interpolam entre os pais no
       espaço de soluções, ajudando o AG a explorar o espaço contínuo
       
    5. **Sem Efeito de Memória**: Ao contrário de crossover com ponto de corte,
       cada gene é tratado independentemente
    
    Comparação de Tipos de Crossover:
    - Crossover Aritmético (este): filho = α×pai + (1-α)×mãe
    - Crossover de Ponto Único: filho herda genes 1..k do pai, k+1..n da mãe
    - Crossover de Ponto Duplo: filho alterna entre pais em dois pontos
    
    O crossover aritmético é ideal para problemas de otimização contínua
    (como alocação de portfólio) pois mantém a natureza contínua do espaço
    de soluções.
    
    Uso no Algoritmo Genético:
    Chamada in moneta_ag() para criar filhos a partir de pais selecionados
    pela roda da sorte. Dois filhos podem ser criados com dois valores
    diferentes de al para máxima diversidade.
    
    Complexidade:
    - Tempo: O(n) onde n é o número de ações
    - Espaço: O(n) para o cromossomo filho
    """
    
    al = np.random.rand()
    parte_genes_pai = al * cromossomo_pai.loc[acoes]
    parte_genes_mae = (1 - al) * cromossomo_mae.loc[acoes]
    cromossomo_filho_um = parte_genes_mae + parte_genes_pai
    return cromossomo_filho_um


def roda_do_acaso(cromossomos_sorteados):
    """
    Seleciona dois cromossomos pais distintos usando seleção proporcional ao fitness.
    
    Implementa o mecanismo de "roda da sorte" (roulette wheel selection), uma técnica
    clássica de seleção em algoritmos genéticos que favorece cromossomos com maior
    fitness. Cromossomos com melhor desempenho têm maior probabilidade de serem
    selecionados como pais, proporcionalmente ao seu fitness relativo. Garante que
    os dois pais selecionados sejam diferentes.
    
    Parâmetros:
    -----------
    cromossomos_sorteados : pd.DataFrame
        DataFrame contendo cromossomos (carteiras) com suas métricas de avaliação.
        Colunas esperadas:
        - Colunas de ativos: pesos alocados para cada ação
        - 'Fitnesses' : float
            Índice de Sharpe ou outra métrica de qualidade de cada cromossomo.
            Valores maiores indicam melhor desempenho.
        Linhas: cada linha é um cromossomo candidato para seleção
    
    Retorna:
    --------
    tuple[pd.Series, pd.Series]
        Tupla contendo:
        
        - cromossomo_pai : pd.Series
            Primeiro cromossomo selecionado via roda da sorte.
            Contém: pesos de cada ação + coluna 'Fitnesses'
            
        - cromossomo_mae : pd.Series
            Segundo cromossomo selecionado via roda da sorte.
            Garantidamente diferente do pai (linhas diferentes).
            Contém: pesos de cada ação + coluna 'Fitnesses'
    
    Exemplos:
    ---------
    >>> # Suponha uma população com 6 cromossomos
    >>> cromossomos_populacao = pd.DataFrame({
    ...     'PETR4.SA': [0.3, 0.5, 0.2, 0.4, 0.6, 0.25],
    ...     'VALE3.SA': [0.4, 0.3, 0.5, 0.3, 0.2, 0.40],
    ...     'GGBR4.SA': [0.3, 0.2, 0.3, 0.3, 0.2, 0.35],
    ...     'Fitnesses': [0.85, 1.20, 0.65, 0.95, 1.10, 0.75]
    ... })
    >>> 
    >>> pai, mae = roda_do_acaso(cromossomos_populacao)
    >>> 
    >>> print("Cromossomo Pai (índice mais provável: 1 ou 4):")
    >>> print(pai)
    # PETR4.SA     0.5
    # VALE3.SA     0.3
    # GGBR4.SA     0.2
    # Fitnesses    1.2   (melhor fitness → maior probabilidade de seleção)
    # Name: 1, dtype: float64
    >>> 
    >>> print("\\nCromossomo Mãe (índice diferente do pai):")
    >>> print(mae)
    # PETR4.SA     0.4
    # VALE3.SA     0.3
    # GGBR4.SA     0.3
    # Fitnesses    0.95
    # Name: 3, dtype: float64
    
    Notes:
    ------
    Algoritmo de Seleção (Roda da Sorte):
    
    1. **Normalização de Fitness**:
       percentagens = fitnesses / sum(fitnesses)
       Exemplo: fitnesses = [0.85, 1.20, 0.75] → [0.33, 0.47, 0.20]
       
    2. **Cálculo de Probabilidades Acumuladas**:
       cumsum([0.33, 0.47, 0.20]) = [0.33, 0.80, 1.00]
       Estas são as "fatias" da roda da sorte
       
    3. **Sorteio via Valor Aleatório**:
       - Gera número aleatório al ∈ [0, 1)
       - Cada intervalo representa um cromossomo:
         * al ∈ [0, 0.33)     → cromossomo 0 (fitness 0.85)
         * al ∈ [0.33, 0.80)  → cromossomo 1 (fitness 1.20)
         * al ∈ [0.80, 1.00]  → cromossomo 2 (fitness 0.75)
       - Exemplo: al = 0.68 → seleciona cromossomo 1 (fitness mais alto)
       
    4. **Garantia de Pais Diferentes**:
       Loop: se cromossomo_mae == cromossomo_pai, sorteia novamente
       Assegura diversidade genética na próxima geração
    
    Vantagens da Roda da Sorte:
    - Cromossomos com melhor fitness têm probabilidade proporcional maior
    - Permite que cromossomos fracos ainda tenham chance de reprodução (exceto 0)
    - Simples de implementar e computacionalmente eficiente
    - Mantém pressão seletiva sem ser muito elitista
    
    Limitações:
    - Cromossomos com fitness muito alto podem dominar (convergência prematura)
    - Cromossomos com fitness zero nunca são selecionados
    - Sensível a escala de fitness (cromossomos muito diferentes em magnitude)
    
    Comparação com Outras Estratégias de Seleção:
    - **Seleção por Torneio**: seleciona melhor de k aleatórios (mais rápido)
    - **Seleção Rankada**: ordena por fitness, usa ranking (menos sensível a escala)
    - **Roda da Sorte**: fitness-proporcional (este método)
    - **Seleção Elitista**: garante sobrevivência dos melhores (complementada com estratégia)
    
    Aplicação no Moneta AG:
    Chamada em moneta_ag() para selecionar dois cromossomos pais da população
    atual. Os pais selecionados são então usados em crossover() para gerar
    filhos e em mutacao_um() / mutacao_dois() para gerar mutantes, criando
    a próxima geração com gerar_nova_geracao().
    
    Complexidade:
    - Tempo: O(n log n) para cálculo de cumsum, O(1) para sorteio
    - Espaço: O(n) para armazenar probabilidades acumuladas
    """
    percentagens_relativas_fitnesses = \
                cromossomos_sorteados.loc[:, "Fitnesses"] / \
                    cromossomos_sorteados.loc[:, "Fitnesses"].sum()

            # gera um series com as percentagens acumuladas
            # 0.2, 0.65, 0.70, 0.80, 0.95, 1.00
    percentagens_acumuladas_fitnesses = \
                percentagens_relativas_fitnesses.cumsum()
            
            # esse comando gera um aleatorio de 0 até 1
            # ex. 0.68
    al = np.random.rand()

            # retorna a posição do cromossomo sorteado
            # no exemplo acima seria o cromossomo de posição
            # 2 (terceiro cromossomo)
    posicao_cromossomo_sorteado = \
                (al > percentagens_acumuladas_fitnesses).sum()

    cromossomo_pai = cromossomos_sorteados.iloc[posicao_cromossomo_sorteado]

    cromossomo_mae = cromossomo_pai.copy()

    while (cromossomo_mae == cromossomo_pai).all():
        al = np.random.rand()
        posicao_cromossomo_sorteado = \
                    (al > percentagens_acumuladas_fitnesses).sum()

        cromossomo_mae = cromossomos_sorteados.iloc[posicao_cromossomo_sorteado]
    return cromossomo_pai,cromossomo_mae


def gerar_cromossomos_base(qtd_croms_populacao_geral, acoes, medias, matriz_covariancia):
    """
    Gera e avalia uma população inicial de cromossomos com pesos aleatórios.
    
    Cria uma população base de cromossomos representando carteiras com alocações
    aleatórias. Cada cromossomo tem pesos para cada ativo gerados aleatoriamente,
    normalizados para somar 1.0. Calcula métricas de desempenho (retorno esperado,
    risco e fitness/Sharpe) para cada cromossomo, preparando-os para evolução
    genética através do algoritmo de otimização.
    
    Parâmetros:
    -----------
    qtd_croms_populacao_geral : int
        Número de cromossomos (carteiras) a gerar na população inicial.
        Exemplos típicos: 20, 50, 100 cromossomos para exploição inicial
        
    acoes : Index ou list
        Nomes/símbolos das ações que compõem os cromossomos
        (ex: ['PETR4.SA', 'VALE3.SA', 'GGBR4.SA', 'ITUB4.SA'])
        Determina o número de genes de cada cromossomo
        
    medias : pd.Series
        Retorno médio (esperado) de cada ação calculado a partir do histórico
        Índices: símbolos das ações (devem corresponder a 'acoes')
        Valores: retorno esperado para cada ativa (ex: 0.015 = 1.5% ao dia)
        
    matriz_covariancia : pd.DataFrame
        Matriz de covariância entre os retornos das ações
        Dimensão: (n_ativos × n_ativos)
        Índices/colunas: símbolos das ações
        Usada para calcular o risco (volatilidade) de cada carteira
    
    Retorna:
    --------
    pd.DataFrame
        DataFrame com qtd_croms_populacao_geral linhas (cromossomos) e colunas:
        
        - Colunas por ativo (ex: 'PETR4.SA', 'VALE3.SA', ...):
            float entre 0 e 1, representando peso alocado para essa ação
            Propriedade garantida: soma de pesos por cromossomo = 1.0
            
        - 'Retornos' : float
            Retorno esperado da carteira (média ponderada dos retornos)
            Calculado como: w1×μ1 + w2×μ2 + ... + wn×μn
            
        - 'Riscos' : float
            Risco da carteira (desvio padrão dos retornos / volatilidade)
            Calculado como: sqrt(w^T × Σ × w)
            
        - 'Fitnesses' : float
            Índice de Sharpe da carteira (retorno / risco)
            Maior valor indica melhor relação risco-retorno
    
    Exemplos:
    ---------
    >>> acoes = pd.Index(['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
    >>> medias = pd.Series([0.0150, 0.0120, 0.0140], index=acoes)
    >>> matriz_cov = pd.DataFrame(
    ...     [[0.0025, 0.0012, 0.0015],
    ...      [0.0012, 0.0020, 0.0010],
    ...      [0.0015, 0.0010, 0.0022]],
    ...     index=acoes, columns=acoes
    ... )
    >>> 
    >>> populacao = gerar_cromossomos_base(
    ...     qtd_croms_populacao_geral=5,
    ...     acoes=acoes,
    ...     medias=medias,
    ...     matriz_covariancia=matriz_cov
    ... )
    >>> 
    >>> print(populacao)
    # Output:
    #      PETR4.SA  VALE3.SA  GGBR4.SA  Retornos   Riscos  Fitnesses
    # 0      0.333     0.334     0.333    0.0137    0.0450      0.304
    # 1      0.200     0.500     0.300    0.0132    0.0445      0.297
    # 2      0.450     0.250     0.300    0.0140    0.0460      0.304
    # 3      0.300     0.300     0.400    0.0131    0.0442      0.296
    # 4      0.350     0.400     0.250    0.0138    0.0455      0.303
    >>> 
    >>> # Quantidade de cromossomos e genes
    >>> print(f"Cromossomos: {len(populacao)}")
    # Cromossomos: 5
    >>> print(f"Genes por cromossomo: {len(acoes)}")
    # Genes por cromossomo: 3
    >>> 
    >>> # Verificar que pesos somam 1.0
    >>> pesos = populacao.loc[:, acoes]
    >>> print(pesos.sum(axis=1))
    # 0    1.0
    # 1    1.0
    # 2    1.0
    # 3    1.0
    # 4    1.0
    >>> 
    >>> # Melhor cromossomo inicial
    >>> melhor_idx = populacao['Fitnesses'].idxmax()
    >>> print(populacao.loc[melhor_idx])
    
    Notes:
    ------
    Processo de Inicialização:
    
    1. **Geração Aleatória**:
       - Cria matriz qtd_croms × n_ativos com valores inteiros [0, 10)
       - Exemplo: [[3, 7, 4], [5, 2, 8], ...]
       
    2. **Normalização (L1-norm)**:
       - Normaliza cada linha para que soma = 1.0
       - Usa preprocessing.normalize(., norm="l1", axis=1)
       - Exemplo: [3, 7, 4] → [0.2, 0.467, 0.267] (soma = 1.0)
       
    3. **Conversão para DataFrame**:
       - Transforma array normalizado em DataFrame com nomes de ações
       - Cria índices de coluna com símbolos das ações
       
    4. **Cálculo de Métricas**:
       - Retornos: usa ces_retornos() para média ponderada
       - Riscos: usa ces_riscos() para volatilidade da carteira
       - Fitnesses: usa ces_fitnesses() para Índice de Sharpe
    
    Características da População Inicial:
    
    - **Aleatória**: Garante exploração inicial do espaço de soluções
    - **Diversa**: Pesos uniformemente distribuídos permite variação máxima
    - **Avaliada**: Cada cromossomo tem fitness calculado, pronto para seleção
    - **Restringida**: Todos respeitam com garantia que pesos somam 1.0
    
    Distribuição Esperada:
    - Pesos aproximadamente uniformes: ~1/n_ativos para cada ativo
    - Com variação aleatória que explora o espaço contínuo simplex
    - Alguns cromossomos com alta concentração, outros diversificados
    
    Por que Normalização L1?
    - L1-norm (soma absoluta) preserva restrição de pesos > 0 e soma = 1.0
    - Alterna com L2-norm (Euclidiana) ou outras, mas L1 é ideal para
      distribuições de probabilidade / alocações de portfólio
    
    Integração no Algoritmo Genético:
    Chamada em moneta_ag() para criar a população inicial antes de iniciar
    as gerações evolutivas. A qualidade inicial não é crítica pois o AG
    explorará e evoluirá os cromossomos através de seleção, crossover e mutação.
    
    Complexidade:
    - Tempo: O(qtd_croms × n_ativos) para geração e normalização
    - Espaço: O(qtd_croms × n_ativos) para armazenar população
    - Cálculo de métricas: O(qtd_croms × n_ativos^2) para matriz de covariância
    
    Exemplo de Uso Típico:
    >>> populacao_inicial = gerar_cromossomos_base(100, acoes, medias, cov)
    >>> # Agora populacao_inicial pode ser passada para evolução genética
    >>> # melhor_inicial = populacao_inicial.loc[populacao_inicial['Fitnesses'].idxmax()]
    """
    qtd_genes = len(acoes)

    carteiras = np.random.randint(low=0, high=10, 
                                size=(qtd_croms_populacao_geral, qtd_genes))
    cromossomos = preprocessing.normalize(carteiras, norm="l1", axis=1)
    cromossomos = pd.DataFrame(data=cromossomos, columns=acoes)

    cromossomos["Retornos"] = ces_retornos(cromossomos, medias)
    cromossomos["Riscos"] = ces_riscos(cromossomos.loc[:, acoes],
                                    matriz_covariancia)
    cromossomos["Fitnesses"] = ces_fitnesses(cromossomos.loc[:, "Retornos"],
                                            cromossomos.loc[:, "Riscos"])
                                            
    return cromossomos