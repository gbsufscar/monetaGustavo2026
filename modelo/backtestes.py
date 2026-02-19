
# Função para realizar os backtestes da Moneta

from utils.gerais import gerar_data, jungir_retornos, gerar_carteira_aleatoria
from modelo.moneta import moneta_ag
from math import log2
from cotacoes.cotacoes import busca_cotacoes, formata_cotacoes
import pandas as pd


# esta função vai parar no arquivo modelo/backtestes.py
def moneta_backtestes(data_inicial_bt, data_final_bt, 
                    intervalo, cotacoes_anteriores, cotacoes_segurar, maiores_medias,
                    qtd_bebados, cotacoes, cotacoes_index):
    """
    Executa backtestes do modelo Moneta com carteiras aleatórias e índice de referência.
    
    Realiza simulações de trading com a estratégia Moneta em múltiplos períodos sequenciais,
    comparando o desempenho contra um índice de mercado e contra 'qtd_bebados' carteiras
    completamente aleatórias. Cada período começa com a otimização de carteira baseada
    em histórico e termina após um período de rebalanceamento.
    
    Parâmetros:
    -----------
    data_inicial_bt : datetime.date
        Data de início do período de backtest
        
    data_final_bt : datetime.date
        Data de encerramento do período de backtest
        
    intervalo : str
        Frequência dos dados: 'd' para diário ou 'w' para semanal
        
    cotacoes_anteriores : int
        Número de períodos históricos necessários para otimização de carteira
        (janela de lookback para cálculo de variações)
        
    cotacoes_segurar : int
        Número de períodos para manter a carteira sem rebalanceamento
        
    maiores_medias : int
        Quantidade de ações com maiores médias de retorno a incluir na carteira otimizada
        
    qtd_bebados : int
        Quantidade de carteiras aleatórias para comparação de desempenho
        (ex: 100 carteiras geradas aleatoriamente)
        
    cotacoes : pd.DataFrame
        DataFrame com séries de preços das ações (índice: datas, colunas: tickers)
        Deve conter dados suficientes para o período completo de backtest
        
    cotacoes_index : pd.Series ou pd.DataFrame
        Série/DataFrame com preços do índice de referência para o mesmo período
        
    Retorna:
    --------
    dict
        Dicionário contendo os resultados agregados do backtest:
        
        - 'acumulados' : dict
            - 'moneta' : pd.Series - patrimônio acumulado da carteira Moneta
            - 'index' : pd.Series - patrimônio acumulado do índice de referência
            - 'bebados' : list[pd.Series] - patrimônios acumulados das carteiras aleatórias
            
        - 'variacoes' : dict
            - 'moneta' : pd.Series - retornos periódicos da carteira Moneta
            - 'index' : pd.Series - retornos periódicos do índice
            
        - 'dados' : list[dict]
            Lista com dados detalhados de cada período de backtest:
            - 'moneta' : dados da exécução da Moneta (datas, carteira, retornos)
            - 'index' : dados do índice para o mesmo período
    
    Raises:
    -------
    ValueError
        Se cotações ou cotacoes_index estão vazios ou sem dados válidos
        
    Exemplos:
    ---------
    >>> resultados = moneta_backtestes(
    ...     data_inicial_bt=date(2022, 3, 1),
    ...     data_final_bt=date(2025, 3, 1),
    ...     intervalo='d',
    ...     cotacoes_anteriores=100,
    ...     cotacoes_segurar=400,
    ...     maiores_medias=10,
    ...     qtd_bebados=100,
    ...     cotacoes=df_cotacoes,
    ...     cotacoes_index=series_index
    ... )
    >>> 
    >>> # Acessar resultados
    >>> patrimonio_moneta = resultados['acumulados']['moneta']
    >>> patrimonio_index = resultados['acumulados']['index']
    >>> retornos_moneta = resultados['variacoes']['moneta']
    >>> bebados_performance = resultados['acumulados']['bebados']
    
    Notes:
    ------
    - A função itera sobre períodos sequenciais, rebalanceando a carteira periodicamente
    - Cada "bebado" é uma carteira com pesos aleatórios para comparação estatística
    - Os retornos são compostos usando cumprod() para calcular patrimônio acumulado
    - Os períodos que não têm dados suficientes são automaticamente pulados
    """
    
    # Verifica se temos dados disponíveis
    if cotacoes.empty or len(cotacoes) == 0:
        print(f"[ERROR] Nenhum dado disponível para cotações. Retornando vazio.")
        empty_series = pd.Series(dtype=float)
        return {
            "acumulados": {"moneta": empty_series, "index": empty_series, "bebados": []},
            "variacoes": {"moneta": empty_series, "index": empty_series},
            "dados": []
        }
    
    # Verifica se dados do índice estão disponíveis
    if cotacoes_index.empty or len(cotacoes_index) == 0:
        print(f"[ERROR] Nenhum dado disponível para cotacoes_index. Retornando vazio.")
        empty_series = pd.Series(dtype=float)
        return {
            "acumulados": {"moneta": empty_series, "index": empty_series, "bebados": []},
            "variacoes": {"moneta": empty_series, "index": empty_series},
            "dados": []
        }
    
    # Garante que usamos datas que existem nos dados
    data_minima_dados = cotacoes.index.min()
    data_maxima_dados = cotacoes.index.max()
    
    # Verifica se as datas são válidas (não NaT)
    if pd.isna(data_minima_dados) or pd.isna(data_maxima_dados):
        print(f"[ERROR] Datas inválidas (NaT) nos dados. Retornando vazio.")
        empty_series = pd.Series(dtype=float)
        return {
            "acumulados": {"moneta": empty_series, "index": empty_series, "bebados": []},
            "variacoes": {"moneta": empty_series, "index": empty_series},
            "dados": []
        }
    
    print(f"[DATA] Intervalo de dados disponível: {data_minima_dados} a {data_maxima_dados}")
    
    # Converte para .date() para compatibilidade com objetos date Python
    # hasattr é usado para verificar se o objeto tem o método date() antes de chamar, para evitar erros caso já sejam do tipo date
    if hasattr(data_minima_dados, 'date'):
        data_minima_dados = data_minima_dados.date()
    if hasattr(data_maxima_dados, 'date'):
        data_maxima_dados = data_maxima_dados.date()
    
    resultados_moneta = []
    resultados_index = []
    resultados_bebados = []
    data_rodar_moneta = data_inicial_bt

    # Lista de todas as ações disponíveis nos dados para gerar carteiras aleatórias com os mesmos ativos da Moneta
    todas_acoes = cotacoes.columns 
    
    # Loop principal para rodar os backtestes da Moneta, do índice e dos bebados
    while data_rodar_moneta < data_final_bt and data_rodar_moneta <= data_maxima_dados:
        # Gera a data de início para rodar o Moneta com base na data de referência (data_rodar_moneta) e na quantidade de cotações anteriores necessárias (cotacoes_anteriores), considerando o intervalo (diário ou semanal).
        data_inicial_moneta = gerar_data(data_rodar_moneta, 
                                        cotacoes_anteriores, 
                                        intervalo, 
                                        "anterior")
        
        # Garante que data_inicial_moneta não é anterior aos dados disponíveis
        if data_inicial_moneta < data_minima_dados:
            print(f"  [WARN] data_inicial_moneta ({data_inicial_moneta}) anterior aos dados ({data_minima_dados}). Ajustando...")
            data_inicial_moneta = data_minima_dados

        # Gera a data de venda das ações com base na data de referência (data_rodar_moneta) e na quantidade de cotações a segurar (cotacoes_segurar), considerando o intervalo (diário ou semanal).
        data_final_testar_carteira = gerar_data(data_rodar_moneta, 
                                                cotacoes_segurar, 
                                                intervalo, 
                                                "posterior")

        # Garante que data_final_testar_carteira não é posterior aos dados disponíveis
        cotacoes_rodar_moneta = cotacoes.loc[data_inicial_moneta:data_rodar_moneta].copy()
        
        # Imprime informações sobre o período e a quantidade de dados disponíveis para rodar o Moneta
        print(f"  [DATE] Período: {data_inicial_moneta} a {data_rodar_moneta} - {cotacoes_rodar_moneta.shape[0]} datas, {cotacoes_rodar_moneta.shape[1]} tickers")
        
        # Verifica se o período tem dados suficientes
        if cotacoes_rodar_moneta.empty or cotacoes_rodar_moneta.shape[0] < 2:
            print(f"  [WARN] Período sem dados suficientes (<2 datas). Avançando...")
            data_rodar_moneta = gerar_data(data_final_testar_carteira, 1, intervalo, "posterior")
            print(f"  Rodando Backteste do Moneta: {data_rodar_moneta}")
            continue
        
        # Formata as cotações para o período de rodar o Moneta, aplicando o filtro de maiores médias se necessário
        variacoes_rodar_moneta = formata_cotacoes(cotacoes=cotacoes_rodar_moneta, 
                                                intervalo=intervalo, 
                                                maiores_medias=maiores_medias)
        
        # Verifica se variacoes_rodar_moneta está vazio
        if variacoes_rodar_moneta.empty:
            print(f"  [ERROR] variacoes_rodar_moneta vazio! Pulando para próxima iteração")
            data_rodar_moneta = gerar_data(data_final_testar_carteira, 1, intervalo, "posterior")
            print(f"  Rodando Backteste do Moneta: {data_rodar_moneta}")
            continue
        
        # Seleciona as ações disponíveis para rodar o Moneta com base nas colunas de variacoes_rodar_moneta
        acoes = variacoes_rodar_moneta.columns
        
        # Gera a carteira da Moneta para o período usando as variações formatadas e calcula o retorno esperado com base na carteira gerada
        carteira = moneta_ag(variacoes=variacoes_rodar_moneta)
        
        # Calcula o retorno esperado para a carteira gerada usando a função log2 para transformar os retornos em uma escala logarítmica, 
        # o que é comum em finanças para lidar com retornos compostos e facilitar a comparação entre diferentes períodos e ativos.
        retorno_esperado = log2(carteira.loc["Retornos"])
        
        # Alinha a carteira com as ações disponíveis para testar e renormaliza os pesos para garantir que somem 1, 
        # caso algumas ações tenham sido filtradas ou não estejam disponíveis no período de teste
        carteira = carteira.loc[acoes]

        # Prepara as cotações para testar a carteira da Moneta no período de teste, 
        # garantindo que usamos o mesmo intervalo e filtrando pelas ações disponíveis
        cotacoes_testar_carteira = cotacoes.loc \
            [data_rodar_moneta:min(data_final_bt, data_final_testar_carteira), acoes].copy()
        
        # Formata as cotações para o período de teste, aplicando o mesmo filtro de maiores médias se necessário
        variacoes_testar_carteira = formata_cotacoes(cotacoes=cotacoes_testar_carteira, 
                                                    intervalo=intervalo, 
                                                    maiores_medias=0)
        
        # Alinha carteira com as colunas de variacoes_testar_carteira e renormaliza
        carteira_alinhada = carteira.reindex(variacoes_testar_carteira.columns, fill_value=0)
        
        # Normaliza os pesos caso alguns tenham sido zerados
        if carteira_alinhada.sum() > 0:
            carteira_alinhada = carteira_alinhada / carteira_alinhada.sum()
        
        # Calcula os retornos da carteira da Moneta para o período de teste multiplicando 
        # as variações pelas alocações da carteira e somando os resultados
        retornos_moneta = variacoes_testar_carteira.dot(carteira_alinhada)

        # Prepara as cotações do índice para o mesmo período de teste, garantindo que usamos o mesmo intervalo 
        # e filtrando pelas ações disponíveis
        cotacoes_index_testar = cotacoes_index.loc[data_rodar_moneta:min(data_final_bt, data_final_testar_carteira)]

        # Formata as cotações do índice para o período de teste, aplicando o mesmo filtro de maiores médias se necessário
        variacoes_index_testar = formata_cotacoes(cotacoes=pd.DataFrame(cotacoes_index_testar),
                                                intervalo=intervalo,
                                                maiores_medias=0)
        
        # Usa 'Adj Close' se disponível, senão usa 'Close' para calcular os retornos do índice, 
        # garantindo que temos uma coluna de preços para calcular os retornos mesmo que o formato dos dados do índice seja diferente
        if "Adj Close" in variacoes_index_testar.columns:
            retornos_index = variacoes_index_testar["Adj Close"]
        elif "Close" in variacoes_index_testar.columns:
            retornos_index = variacoes_index_testar["Close"]
        else:
            # Se nenhuma coluna padrão existir, usa a primeira coluna disponível
            retornos_index = variacoes_index_testar.iloc[:, 0]

        # Calcula o retorno esperado para o período de teste usando a função log2 para transformar os retornos em uma escala logarítmica, 
        # o que é comum em finanças para lidar com retornos compostos e facilitar a comparação entre diferentes períodos e ativos.
        retorno_esperado_periodo = \
                    (1 + retorno_esperado) ** \
                    (data_final_testar_carteira - data_rodar_moneta).days - 1
        
        # Armazena os resultados do backteste da Moneta, do índice e dos bebados para o 
        # período atual em listas para posterior análise e comparação, incluindo as datas de início e fim, 
        # a carteira gerada, os retornos da Moneta, os retornos do índice e os retornos dos bebados para cada período testado.
        resultados_moneta.append(
            {
                "data_inicio": data_rodar_moneta,
                "data_fim": data_final_testar_carteira,
                "carteira": carteira,
                "retornos": retornos_moneta,
                "retorno_esperado": retorno_esperado_periodo
            }
        )

        # Armazena os resultados do backteste do índice para o período atual, 
        # incluindo as datas de início e fim e os retornos do índice para cada período testado.
        resultados_index.append(
            {
                "data_inicio": data_rodar_moneta,
                "data_fim": data_final_testar_carteira,
                "retornos": retornos_index
            }
        )
    
        # Armazena os resultados do backteste dos bebados para o período atual, 
        # incluindo as datas de início e fim, a carteira gerada e os retornos para cada período testado.
        bebados = []
        for _ in range(qtd_bebados):
            carteira_aleatoria = gerar_carteira_aleatoria(acoes=todas_acoes, seed=None)
            acoes_aleatorias = carteira_aleatoria.index

            cotacoes_testar_bebado = \
                cotacoes.loc[data_rodar_moneta:min(data_final_bt, data_final_testar_carteira), 
                            acoes_aleatorias].copy()
            
            variacoes_testar_bebado = formata_cotacoes(cotacoes=cotacoes_testar_bebado,
                                                    intervalo=intervalo,
                                                    maiores_medias=0)
            
            # Alinha carteira aleatória com as colunas de variacoes_testar_bebado e renormaliza
            carteira_aleatoria_alinhada = carteira_aleatoria.reindex(variacoes_testar_bebado.columns, fill_value=0)
            
            # Normaliza os pesos caso alguns tenham sido zerados
            if carteira_aleatoria_alinhada.sum() > 0:
                carteira_aleatoria_alinhada = carteira_aleatoria_alinhada / carteira_aleatoria_alinhada.sum()

            # Calcula os retornos da carteira aleatória para o período de teste multiplicando 
            # as variações pelas alocações da carteira e somando os resultados para obter o retorno 
            # total da carteira aleatória no período de teste.
            retornos_bebado = variacoes_testar_bebado.dot(carteira_aleatoria_alinhada)

            # Armazena os resultados do backteste do bebado para o período atual, incluindo as datas de início e fim,
            # a carteira gerada e os retornos para cada período testado.
            dados_bebado = {"data_inicio": data_rodar_moneta, # 
                            "data_fim": data_final_testar_carteira,
                            "carteira": carteira_aleatoria,
                            "retornos": retornos_bebado}
            bebados.append(dados_bebado)

        # Armazena os resultados do backteste dos bebados para o período atual em uma lista para posterior análise e comparação, 
        # incluindo as datas de início e fim, a carteira gerada e os retornos para cada período testado.
        resultados_bebados.append(bebados)
        
        # Gera a próxima data para rodar o Moneta avançando a data de referência (data_rodar_moneta) 
        # para a data de venda das ações do período atual (data_final_testar_carteira) mais um intervalo, 
        # garantindo que o próximo período de teste comece após o período de teste atual e considerando o intervalo (diário ou semanal). 
        data_rodar_moneta = gerar_data(data_final_testar_carteira, 1, 
                                        intervalo, "posterior")
        
        # Imprime a próxima data para rodar o Moneta, garantindo que temos um registro claro do progresso dos backtestes 
        # e das datas de cada período testado.
        print(f"Rodando Backteste do Moneta: {data_rodar_moneta}")
    
    # Após rodar todos os backtestes, jungimos os retornos da Moneta, do índice e dos bebados para cada período testado, 
    # calculando os retornos acumulados para cada um e armazenando os resultados em um dicionário para posterior análise e comparação, 
    # incluindo os retornos acumulados, as variações e os dados de cada período testado para a Moneta, o índice e os bebados.        
    retornos_jungidos_moneta = jungir_retornos(resultados_moneta, data_inicial_bt)
    resultados_acumulados_moneta = (retornos_jungidos_moneta + 1).cumprod()

    # Jungimos os retornos do índice para cada período testado, calculando os retornos acumulados para o índice e armazenando 
    # os resultados em um dicionário para posterior análise e comparação, incluindo os retornos acumulados, 
    # as variações e os dados de cada período testado para o índice.
    retornos_jungidos_index = jungir_retornos(resultados_index, data_inicial_bt)
    resultados_acumulados_index = (retornos_jungidos_index + 1).cumprod()

    # Jungimos os retornos dos bebados para cada período testado, calculando os retornos acumulados para cada bebado e armazenando 
    # os resultados em um dicionário para posterior análise e comparação, incluindo os retornos acumulados, 
    # as variações e os dados de cada período testado para os bebados.
    resultados_acumulados_bebados = []
    for indice_bebado in range(qtd_bebados):
        retornos_bebado = [retornos[indice_bebado] 
                            for retornos in resultados_bebados]
        
        retornos_jungidos_bebado = jungir_retornos(retornos_bebado, data_inicial_bt)
        resultados_acumulados_bebado = (retornos_jungidos_bebado + 1).cumprod()
        resultados_acumulados_bebados.append(resultados_acumulados_bebado)

    # Imprime informações sobre os resultados acumulados para a Moneta, o índice e os bebados, 
    # garantindo que temos um registro claro dos resultados dos backtestes e das comparações entre a Moneta, o índice e os bebados.
    print(f"    [DATA] moneta_backtestes() - retornando resultados:")
    print(f"    [DATA] resultados_acumulados_moneta.shape={resultados_acumulados_moneta.shape if hasattr(resultados_acumulados_moneta, 'shape') else len(resultados_acumulados_moneta)}")
    print(f"    [DATA] resultados_acumulados_index.shape={resultados_acumulados_index.shape if hasattr(resultados_acumulados_index, 'shape') else len(resultados_acumulados_index)}")
    print(f"    [DATA] len(resultados_acumulados_bebados)={len(resultados_acumulados_bebados)}")

    # Retorna os resultados dos backtestes da Moneta, do índice e dos bebados em um dicionário para posterior análise e comparação, 
    # incluindo os retornos acumulados, as variações e os dados de cada período testado para a Moneta, o índice e os bebados.
    return {
        "acumulados": {"moneta": resultados_acumulados_moneta,
                    "index": resultados_acumulados_index,
                    "bebados": resultados_acumulados_bebados},
        "variacoes": {"moneta": retornos_jungidos_moneta,
                    "index": retornos_jungidos_index},
        "dados": [{"moneta": rm, "index": ri} 
                    for rm, ri in zip(resultados_moneta, resultados_index)]
    }


# -----------------------------------------------------------------------------------
# Função para executar o backteste da Moneta, do índice e dos bebados para um período específico.
def rodar_backtestes(acoes_selecionadas,
                    data_inicial_bt, data_final_bt, 
                    intervalo, cotacoes_anteriores, 
                    cotacoes_segurar, maiores_medias, qtd_bebados,
                    simbolo_index):
    """
    Executa backtestes do modelo Moneta comparando com índice e carteiras aleatórias.
    
    Esta função prepara os dados necessários (cotações históricas) para executar backtestes
    do algoritmo Moneta de otimização de portfólio em um período específico, comparando
    o desempenho da carteira otimizada com um índice de referência e com 'qtd_bebados'
    carteiras aleatórias.
    
    Parâmetros:
    -----------
    acoes_selecionadas : list
        Lista de símbolos/tickers das ações a serem incluídas nos backtestes
        (ex: ['PETR4.SA', 'VALE3.SA', 'GGBR4.SA'])
        
    data_inicial_bt : datetime.date
        Data de início do período de backtest (data do primeiro rebalanceamento)
        
    data_final_bt : datetime.date
        Data de encerramento do período de backtest
        
    intervalo : str
        Frequência dos dados: 'd' para diário ou 'w' para semanal
        
    cotacoes_anteriores : int
        Número de períodos históricos anteriores necessários para calcular as variações
        das ações (ex: 100 dias de histórico para otimização)
        
    cotacoes_segurar : int
        Número de períodos que a carteira é mantida antes de rebalanceamento
        (ex: 400 dias de rebalanceamento)
        
    maiores_medias : int
        Quantidade de ações com maiores médias de retorno para compor a carteira otimizada
        (ex: 10 ou 20 ações)
        
    qtd_bebados : int
        Quantidade de carteiras aleatórias para comparação de desempenho
        (ex: 100 carteiras aleatórias)
        
    simbolo_index : str
        Símbolo/ticker do índice de referência para comparação
        (ex: 'BOVA11.SA' para Brasil ou '^GSPC' para EUA)
    
    Retorna:
    --------
    dict
        Dicionário contendo os resultados dos backtestes com as seguintes chaves:
        - 'acumulados': patrimônio acumulado da Moneta, índice e bebados
        - 'variacoes': retornos periódicos da Moneta e índice
        - 'dados': informações detalhadas de cada período de backtest
        
    Exemplos:
    ---------
    >>> resultados = rodar_backtestes(
    ...     acoes_selecionadas=['PETR4.SA', 'VALE3.SA'],
    ...     data_inicial_bt=date(2022, 3, 1),
    ...     data_final_bt=date(2025, 3, 1),
    ...     intervalo='d',
    ...     cotacoes_anteriores=100,
    ...     cotacoes_segurar=400,
    ...     maiores_medias=10,
    ...     qtd_bebados=100,
    ...     simbolo_index='BOVA11.SA'
    ... )
    """
    
    # Calcula a data mínima necessária para obter dados suficientes em relação ao início do backtest
    # Recua a data inicial considerando o período histórico necessário (cotacoes_anteriores)
    data_minima = gerar_data(data_inicial_bt, cotacoes_anteriores, intervalo, "anterior")
    
    # Calcula a data máxima necessária para obter dados suficientes em relação ao fim do backtest
    # Avança a data final considerando o período de rebalanceamento (cotacoes_segurar)
    data_maxima = gerar_data(data_final_bt, cotacoes_segurar, intervalo, "posterior")

    # Diagnóstico de tickers
    diagnosticos = {
        "total_tickers": len(acoes_selecionadas),
        "tickers_baixados": 0,
        "tickers_validos": 0,
        "tickers_excluidos": len(acoes_selecionadas)
    }

    # Busca os dados históricos de cotações das ações selecionadas no período ampliado
    # Formata as datas para o padrão YYYY-MM-DD exigido pela função busca_cotacoes
    cotacoes = busca_cotacoes(simbolos=acoes_selecionadas,
                            intervalo=intervalo,
                            data_inicio=data_minima.strftime("%Y-%m-%d"),
                            data_fim=data_maxima.strftime("%Y-%m-%d"))
    
    # Log de debug antes de limpar dados
    print(f"[DEBUG] cotacoes antes de dropna: shape={cotacoes.shape}, empty={cotacoes.empty}")
    
    # Remove colunas (ações) totalmente vazias (todos os valores NaN)
    # Evita eliminar séries com poucos NaNs; o filtro fino ocorre em formata_cotacoes
    if not cotacoes.empty:
        colunas_antes = cotacoes.shape[1]
        cotacoes = cotacoes.dropna(axis=1, how='all')
        colunas_depois = cotacoes.shape[1]
        diagnosticos["tickers_baixados"] = colunas_antes
        diagnosticos["tickers_validos"] = colunas_depois
        diagnosticos["tickers_excluidos"] = max(0, diagnosticos["total_tickers"] - colunas_depois)
        print(f"[DEBUG] cotacoes após remover colunas vazias: shape={cotacoes.shape}, colunas removidas={colunas_antes - colunas_depois}")
    else:
        print(f"[WARN] cotacoes vazio após busca_cotacoes!")

    # Busca os dados históricos de cotações do índice de referência no mesmo período ampliado
    # Usa lista com um elemento porque busca_cotacoes espera uma lista de símbolos
    cotacoes_index = busca_cotacoes(simbolos=[simbolo_index],
                                    intervalo=intervalo,
                                    data_inicio=data_minima.strftime("%Y-%m-%d"),
                                    data_fim=data_maxima.strftime("%Y-%m-%d"))
    
    # Remove linhas (datas) que possuem dados faltantes (NaN) no índice com método mais seguro
    if not cotacoes_index.empty:
        print(f"[DEBUG] cotacoes_index antes de dropna: shape={cotacoes_index.shape}")
        # Remove linhas com NaN
        cotacoes_index_original_len = len(cotacoes_index)
        cotacoes_index = cotacoes_index.dropna(axis=0)
        print(f"[DEBUG] cotacoes_index após dropna: shape={cotacoes_index.shape}, linhas removidas={cotacoes_index_original_len - len(cotacoes_index)}")
    else:
        print(f"[WARN] cotacoes_index vazio após busca_cotacoes para {simbolo_index}")

    # VALIDAÇÃO CRÍTICA: Verifica se cotações ficou vazia
    if cotacoes.empty or len(cotacoes) == 0 or cotacoes.shape[1] == 0:
        print(f"[ERROR] cotacoes ficou vazia após limpeza! Shape: {cotacoes.shape}")
        empty_series = pd.Series(dtype=float)
        return {
            "acumulados": {"moneta": empty_series, "index": empty_series, "bebados": []},
            "variacoes": {"moneta": empty_series, "index": empty_series},
            "dados": [],
            "diagnosticos": diagnosticos
        }

    # Validação: verifica se há dados do índice
    if cotacoes_index.empty or len(cotacoes_index) == 0:
        print(f"[WARN] Nenhum dado disponível para o índice: {simbolo_index}")
        print(f"[INFO] Tentando usar apenas as ações selecionadas para o backtest...")
        # Se o índice estiver vazio, cria um índice fictício com as mesmas datas das ações
        if not cotacoes.empty:
            cotacoes_index = pd.DataFrame(
                [100.0] * len(cotacoes),  # Começa com 100
                index=cotacoes.index,
                columns=[simbolo_index]
            )
            print(f"[OK] Índice fictício criado com {len(cotacoes_index)} datas")
        else:
            print(f"[ERROR] Nenhum dado disponível para ações ou índice!")
            empty_series = pd.Series(dtype=float)
            return {
                "acumulados": {"moneta": empty_series, "index": empty_series, "bebados": []},
                "variacoes": {"moneta": empty_series, "index": empty_series},
                "dados": [],
                "diagnosticos": diagnosticos
            }

    # Encontra as datas comuns entre as duas bases de dados (ações e índice)
    # Usa intersecção de índices para garantir que ambas têm dados para as mesmas datas
    datas_comuns = cotacoes.index.intersection(cotacoes_index.index)
    
    # Validação: verifica se há datas em comum
    if len(datas_comuns) == 0:
        print(f"[ERROR] Nenhuma data em comum entre as ações e o índice!")
        print(f"[INFO] Datas das ações: {len(cotacoes)} registros")
        print(f"[INFO] Datas do índice: {len(cotacoes_index)} registros")
        empty_series = pd.Series(dtype=float)
        return {
            "acumulados": {"moneta": empty_series, "index": empty_series, "bebados": []},
            "variacoes": {"moneta": empty_series, "index": empty_series},
            "dados": [],
            "diagnosticos": diagnosticos
        }
    
    # Filtra as cotações das ações para manter apenas as datas comuns
    # Garante alinhamento temporal entre ações e índice para os cálculos posteriores
    cotacoes = cotacoes.loc[datas_comuns]
    
    # Filtra as cotações do índice para manter apenas as datas comuns
    # Assegura que ações e índice têm o mesmo período de dados sincronizados
    cotacoes_index = cotacoes_index.loc[datas_comuns]
    
    # Garante que cotacoes é um DataFrame (não uma Series)
    # Se .loc retornar uma Series (quando tem apenas uma coluna), converte para DataFrame
    if isinstance(cotacoes, pd.Series):
        cotacoes = cotacoes.to_frame()
    
    # Garante que cotacoes_index é um DataFrame (não uma Series)
    # Se .loc retornar una Series (quando tem apenas uma coluna), converte para DataFrame
    if isinstance(cotacoes_index, pd.Series):
        cotacoes_index = cotacoes_index.to_frame()
    
    print(f"[OK] Dados preparados para backtest:")
    print(f"[INFO] - Ações: {cotacoes.shape[0]} datas x {cotacoes.shape[1]} tickers")
    print(f"[INFO] - Índice: {cotacoes_index.shape[0]} datas x {cotacoes_index.shape[1]} coluna(s)")

    # Executa o backtest principal passando todos os dados preparados
    # Retorna os resultados acumulados para Moneta, índice e carteiras aleatórias
    resultados_backtestes = moneta_backtestes(data_inicial_bt, data_final_bt, 
                                            intervalo, cotacoes_anteriores, cotacoes_segurar, maiores_medias,
                                            qtd_bebados, cotacoes, cotacoes_index)

    # Validação de segurança: verifica se a estrutura de retorno é válida
    if not isinstance(resultados_backtestes, dict):
        print(f"[ERROR] rodar_backtestes() retornou tipo inválido: {type(resultados_backtestes)}")
        empty_series = pd.Series(dtype=float)
        return {
            "acumulados": {"moneta": empty_series, "index": empty_series, "bebados": []},
            "variacoes": {"moneta": empty_series, "index": empty_series},
            "dados": [],
            "diagnosticos": diagnosticos
        }
    
    # Retorna o dicionário com todos os resultados dos backtestes para análise posterior
    resultados_backtestes["diagnosticos"] = diagnosticos
    return resultados_backtestes