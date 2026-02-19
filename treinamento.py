""" 
O arquivo treinamento.py implementa um sistema de otimização de hiperparâmetros 
para o modelo Moneta através de backtesting estatístico sistemático.

Objetivo Principal
Encontrar a melhor combinação de parâmetros para o algoritmo genético de otimização de carteira, 
testando múltiplas configurações em diferentes períodos históricos e comparando os resultados.

"""

from itertools import product
from datetime import date, datetime
import numpy as np
from utils.performance_tracker import PerformanceTracker
from modelo.backtestes import moneta_backtestes
from simbolos import simbolos
import pandas as pd
from cotacoes.cotacoes import busca_cotacoes
import os

# Configurações iniciais para o treinamento
pais = "BR"
index_id = "BOVA11.SA" # Índice de referência para o país selecionado (BOVA11.SA para o Brasil e ^GSPC para os Estados Unidos)
acoes_ids = simbolos[pais][1:] # Lista de ações para o país selecionado (excluindo o índice de referência que é o primeiro elemento da lista)

# configuração dos campeonatos que cada parametrização de Moneta vai jogar
colecao_comecos = [date(2022, 3, 1), date(2022, 9, 1), date(2023, 3, 1)]
colecao_finais = [date(2025, 3, 1), date(2025, 9, 1), date(2026, 1, 31)]

# configuracoes de Moneta
colecao_cotacoes_segurar = [400, 500] # quantidade de cotações para segurar a carteira (ex: 400 dias, 500 dias, etc.)
colecao_cotacoes_anteriores = [100, 150] # quantidade de cotações anteriores a serem buscadas para as variações das ações (ex: 100 dias, 150 dias, etc.)
colecao_maiores_medias = [10, 20] # quantidade de ações com maiores médias para compor a carteira (ex: 10, 20, etc.)
colecao_intervalos = ["d"] # intervalos de tempo para as cotações (ex: diário, semanal, etc.)
qtd_bebados = 100 # quantidade de "bebados" para o campeonato (ex: 100 carteiras aleatórias competindo com a carteira Moneta)


def gera_campeonatos():
    """
    Esta função gera os campeonatos de Moneta para cada combinação de parâmetros

    Retorna um DataFrame com os resultados dos campeonatos
    """

    # data para buscar os dados para rodar todos os campeonatos - 
    # a data de início do campeonato mais antiga menos a quantidade máxima de cotações anteriores 
    # para garantir que teremos dados suficientes para rodar todos os campeonatos.
    data_inicio_buscar_dados = \
        min(colecao_comecos) - pd.Timedelta(days=max(colecao_cotacoes_anteriores))

    # data para buscar os dados para rodar todos os campeonatos - 
    # a data de fim do campeonato mais recente mais a quantidade máxima de cotações para segurar a carteira     
    data_final_buscar_dados = \
        max(colecao_finais) + pd.Timedelta(days=max(colecao_cotacoes_segurar))
    
    # buscando os dados para as ações do país selecionado e 
    # para o índice de referência do país selecionado para o período necessário para rodar todos os campeonatos
    df_cotacoes = busca_cotacoes(
            simbolos=acoes_ids,
            intervalo="d",
            data_inicio=data_inicio_buscar_dados,
            data_fim=data_final_buscar_dados
        )

    # buscando os dados para o índice de referência do país selecionado para o 
    # período necessário para rodar todos os campeonatos (para comparar o desempenho da carteira Moneta com o índice de referência)
    series_cotacoes_index = busca_cotacoes(
        simbolos=[index_id], # índice de referência para o país selecionado (ex: BOVA11.SA para o Brasil e ^GSPC para os Estados Unidos)
        intervalo="d",
        data_inicio=data_inicio_buscar_dados,
        data_fim=data_final_buscar_dados
    )
    
    # Validação: verifica se o índice foi baixado corretamente
    if series_cotacoes_index.empty:
        print(f"\n[ERROR] ERRO CRÍTICO: Não foi possível baixar dados para o índice '{index_id}'!")
        print(f"  [WARN] Verifique se o ticker está delisted ou indisponível")
        return pd.DataFrame()  # Retorna DataFrame vazio
    
    # Extrai a primeira coluna válida como Series se for um DataFrame
    if isinstance(series_cotacoes_index, pd.DataFrame) and len(series_cotacoes_index.columns) > 0:
        series_cotacoes_index = series_cotacoes_index.iloc[:, 0]  # Pega a primeira coluna

    # igualando os dados das ações com os indices, pois
    # os dados podem vir com datas presentes em um e não no outro
    """ 
    Aqui fazemos a interseção das datas presentes nos dados das ações e do índice de referência 
    para garantir que ambos os DataFrames tenham as mesmas datas, evitando problemas de alinhamento 
    durante os cálculos dos retornos e métricas de desempenho.
    """
    datas_comuns = \
        df_cotacoes.index.intersection(series_cotacoes_index.index) # Interseção das datas presentes nos dados das ações e do índice de referência
    
    # Validação: verifica se há datas comuns entre os dados
    if len(datas_comuns) == 0:
        print(f"\n[ERROR] ERRO CRÍTICO: Nenhuma data comum encontrada entre as ações e o índice!")
        print(f"  [DATA] Datas das ações: {len(df_cotacoes)} linhas")
        print(f"  [DATA] Datas do índice: {len(series_cotacoes_index)} linhas")
        print(f"  [WARN] Verifique se o índice '{index_id}' está disponível no período solicitado")
        return pd.DataFrame()  # Retorna DataFrame vazio
    
    # Filtra os DataFrames para manter apenas as datas comuns
    df_cotacoes = df_cotacoes.loc[datas_comuns]
    # Filtra a série de cotações do índice para manter apenas as datas comuns
    series_cotacoes_index = series_cotacoes_index.loc[datas_comuns]
    
    # Validação final: verifica se os dados após filtragem são válidos
    if df_cotacoes.empty or len(df_cotacoes) < 2:
        print(f"\n[ERROR] ERRO CRÍTICO: Dados de ações insuficientes após filtragem!")
        print(f"  [DATA] Linhas de dados: {len(df_cotacoes)}")
        return pd.DataFrame()  # Retorna DataFrame vazio
    
    if series_cotacoes_index.empty or len(series_cotacoes_index) < 2:
        print(f"\n[ERROR] ERRO CRÍTICO: Dados do índice insuficientes após filtragem!")
        print(f"  [DATA] Linhas de dados: {len(series_cotacoes_index)}")
        return pd.DataFrame()  # Retorna DataFrame vazio
    
    print(f"\n[OK] Dados validados com sucesso!")
    print(f"  [DATA] Ações carregadas: {len(df_cotacoes.columns)} colunas")
    print(f"  [DATE] Período de dados: {df_cotacoes.index.min()} a {df_cotacoes.index.max()}")

    # combinatória de todas as configurações de Moneta
    combinacoes = \
    list(
        product(
            colecao_comecos,
            colecao_finais,
            colecao_cotacoes_anteriores,
            colecao_cotacoes_segurar,
            colecao_intervalos,
            colecao_maiores_medias
        )
    )

    # começa a rodar os campeonatos para cada combinação de parâmetros
    resultados_campeonatos = []
    for i, combinacao in enumerate(combinacoes):

        print(f"{i + 1}/{len(combinacoes)}")

        comeco_campeonato = combinacao[0]
        final_campeonato = combinacao[1]
        cotacoes_anteriores = combinacao[2]
        cotacoes_segurar = combinacao[3]
        intervalo = combinacao[4]
        maiores_medias = combinacao[5]

        resultado_campeonato = moneta_backtestes(
            data_inicial_bt=comeco_campeonato,
            data_final_bt=final_campeonato,
            intervalo=intervalo,
            cotacoes_anteriores=cotacoes_anteriores,
            cotacoes_segurar=cotacoes_segurar,
            maiores_medias=maiores_medias,
            qtd_bebados=qtd_bebados,
            cotacoes=df_cotacoes,
            cotacoes_index=series_cotacoes_index
        )
        
        print(f"  [DATA] resultado_campeonato keys: {resultado_campeonato.keys() if isinstance(resultado_campeonato, dict) else 'NOT A DICT'}")
        if isinstance(resultado_campeonato, dict) and 'acumulados' in resultado_campeonato:
            acum = resultado_campeonato["acumulados"]
            print(f"  [DATA] acumulados['moneta']: {type(acum.get('moneta'))}, len={len(acum.get('moneta', [])) if hasattr(acum.get('moneta'), '__len__') else 'N/A'}")
            print(f"  [DATA] acumulados['index']: {type(acum.get('index'))}, len={len(acum.get('index', [])) if hasattr(acum.get('index'), '__len__') else 'N/A'}")
            print(f"  [DATA] acumulados['bebados']: {type(acum.get('bebados'))}, len={len(acum.get('bebados', [])) if hasattr(acum.get('bebados'), '__len__') else 'N/A'}")

        # encontra os quartis para o patrimônio acumulado da carteira Moneta
        # no campeonato
        quartis_moneta = gerar_quartis(
            patrimonio_acum_moneta=resultado_campeonato["acumulados"]["moneta"],
            patrimonio_acum_index=resultado_campeonato["acumulados"]["index"],
            patrimonios_aleatorios=resultado_campeonato["acumulados"]["bebados"])

        # cria o objeto PerformanceTracker para calcular o Sharpe, Beta e Max Drawdown
        tracker = PerformanceTracker(
        data_returns=resultado_campeonato["variacoes"]["moneta"],
        market_returns=resultado_campeonato["variacoes"]["index"],
        period="d"
        )

        # calcula o Sharpe, Beta e Max Drawdown
        sharpe_moneta = tracker.sharpe_ratio()
        beta_moneta = tracker.portfolio_beta()
        max_drawdown_moneta = tracker.max_drawdown()

        dados_registrar = {
            "data_inicio": comeco_campeonato, "data_fim": final_campeonato,
            "cotacoes_segurar": cotacoes_segurar,
            "maiores_medias": maiores_medias,
            "cotacoes_anteriores": cotacoes_anteriores,
            "intervalo": intervalo,
            "q1_moneta": quartis_moneta[0], "q2_moneta": quartis_moneta[1], "q3_moneta": quartis_moneta[2],
            "patrimonio_final_moneta": resultado_campeonato["acumulados"]["moneta"].iloc[-1],
            f"patrimonio_final_{index_id}": resultado_campeonato["acumulados"]["index"].iloc[-1],
            "sharpe_moneta": sharpe_moneta,
            "beta_moneta": beta_moneta,
            "max_drawdown_moneta": max_drawdown_moneta
        }

        # registra os dados deste campeonato
        resultados_campeonatos.append(dados_registrar)
    
    # retorna os resultados dos campeonatos em um DataFrame
    return pd.DataFrame(resultados_campeonatos)


def gerar_quartis(patrimonio_acum_moneta, 
                patrimonio_acum_index, 
                patrimonios_aleatorios):
    """
    patrimonio_acum_moneta: patrimônio acumulado da carteira Moneta
    patrimonio_acum_index: patrimônio acumulado do índice BOVA11
    patrimonios_aleatorios: patrimônio acumulado das carteiras aleatórias

    Esta função retorna os quartis para o patrimônio acumulado da carteira Moneta
    """
    # quantidade de carteiras aleatórias para o campeonato
    n_aleatorios = len(patrimonios_aleatorios)
    
    print(f"    [DATA] gerar_quartis() - n_aleatorios={n_aleatorios}")
    print(f"    [DATA] patrimonio_acum_moneta.shape={patrimonio_acum_moneta.shape if hasattr(patrimonio_acum_moneta, 'shape') else len(patrimonio_acum_moneta)}")
    print(f"    [DATA] patrimonio_acum_index.shape={patrimonio_acum_index.shape if hasattr(patrimonio_acum_index, 'shape') else len(patrimonio_acum_index)}")
    print(f"    [DATA] patrimonios_aleatorios[0].shape={patrimonios_aleatorios[0].shape if len(patrimonios_aleatorios) > 0 else 'empty'}")

    # criando um array com o patrimônio acumulado da carteira Moneta, 
    # do índice de referência e das carteiras aleatórias para calcular os quartis
    
    # Garante que todos os arrays têm o mesmo tamanho
    tamanho_moneta = len(patrimonio_acum_moneta)
    patrimonios_aleatórios_alinhados = []
    
    for pa in patrimonios_aleatorios:
        if len(pa) == tamanho_moneta:
            patrimonios_aleatórios_alinhados.append(pa)
        elif len(pa) > tamanho_moneta:
            # Pega apenas os últimos tamanho_moneta elementos
            patrimonios_aleatórios_alinhados.append(pa.iloc[-tamanho_moneta:] if isinstance(pa, pd.Series) else pa[-tamanho_moneta:])
        else:
            # Padding com NaN ou valor anterior - usar forward fill
            pa_extended = pa.copy() if isinstance(pa, pd.Series) else pd.Series(pa)
            while len(pa_extended) < tamanho_moneta:
                pa_extended = pd.concat([pd.Series([pa_extended.iloc[0]]), pa_extended])
            patrimonios_aleatórios_alinhados.append(pa_extended.iloc[-tamanho_moneta:])
    
    arr = np.zeros(shape=(len(patrimonios_aleatórios_alinhados) + 2, 
                        tamanho_moneta), dtype=np.float64)
    # o patrimônio acumulado da carteira Moneta fica na primeira linha do array,
    # o patrimônio acumulado do índice de referência fica na segunda linha do array
    arr[0, :] = patrimonio_acum_moneta
    arr[1, :] = patrimonio_acum_index

    # os patrimônios acumulados das carteiras aleatórias ficam nas linhas seguintes do array
    for i, cumprod_aleatorios in enumerate(patrimonios_aleatórios_alinhados, 2): # 2 porque as duas primeiras linhas do array já estão ocupadas pelo patrimônio acumulado da carteira Moneta e do índice de referência
        arr[i, :] = cumprod_aleatorios if hasattr(cumprod_aleatorios, 'values') and not isinstance(cumprod_aleatorios, np.ndarray) else (cumprod_aleatorios.values if isinstance(cumprod_aleatorios, pd.Series) else cumprod_aleatorios)

    print(f"    [DATA] arr.shape={arr.shape}, arr[:, 1:].shape={arr[:, 1:].shape}")
    print(f"    [DATA] arr[0, -1:] (Moneta final)={arr[0, -1:]}, arr[1, -1:] (Index final)={arr[1, -1:]}")

    # ordenando o array para calcular os quartis
    asort = np.argsort(arr[:, 1:], axis=0)
    
    print(f"    [DATA] asort.shape={asort.shape}")
    print(f"    [DATA] np.where(asort == 0)={np.where(asort == 0)}")
    
    # Verifica se asort tem dados
    if asort.size == 0 or asort.shape[1] == 0:
        print(f"    [WARN] asort vazio! Retornando quartis padrão (25, 50, 75)")
        return np.array([25, 50, 75])  # Valores neutros como fallback

    # calculando os quartis para o patrimônio acumulado da carteira Moneta
    quartis_moneta = np.quantile(n_aleatorios + 2 - np.where(asort == 0)[0], 
                                q=[0.25, 0.5, 0.75])
    # retornando os quartis para o patrimônio acumulado da carteira Moneta
    return quartis_moneta

# funcao objetivo para pontuar os resultados resumidos de cada configuracao de moneta
def fo(media_quartis, media_patrimonio, 
    media_vs_index, media_sharpe, media_beta, media_max_drawdown,
    a, b, c, d, e, f):
    """
    media_quartis: pontuação sobre os quartis
    media_patrimonio: pontuação sobre o patrimônio acumulado
    media_vs_index: pontuação sobre o patrimônio acumulado em relação ao índice
    media_sharpe: pontuação sobre o Sharpe
    media_beta: pontuação sobre o Beta
    media_max_drawdown: pontuação sobre o Max Drawdown
    a, b, c, d, e, f: pesos para cada métrica

    Esta função calcula a função objetivo para pontuar o "conjunto da obra"
    """
    # aqui podemos ajustar os pesos para cada métrica de acordo com a importância que queremos dar para cada uma delas na pontuação final
    return a * media_quartis + \
            b * media_patrimonio + \
            c * media_vs_index + \
            d * media_sharpe + \
            e * media_beta + \
            f * media_max_drawdown


def pontuar_monetas(df_resultados: pd.DataFrame, qtd_aleatorios: int, index_id: str,
                cols: list = ["cotacoes_segurar", "maiores_medias", 
                                "cotacoes_anteriores", "intervalo"]):
    """
    df_resultados: DataFrame com os resultados dos backtests
    qtd_aleatorios: quantidade de carteiras aleatórias
    index_id: índice a ser comparado (BOVA11.SA ou ^GSPC)
    cols: colunas para agrupar

    Esta função gera o ranking das combinações de parâmetros
    """
    # Validação: verifica se há resultados para processar
    if df_resultados.empty:
        print(f"\n[ERROR] ERRO: Nenhum resultado de backtest para processar!")
        print(f"  Verifique se os dados do índice '{index_id}' estão disponíveis")
        return pd.DataFrame()  # Retorna DataFrame vazio
    
    # agrupando os resultados dos backtests por combinação de parâmetros
    grouped = df_resultados.groupby(cols)

    # lista para armazenar o ranking das combinações de parâmetros
    ranking = []
    for i, (comb, df_comb) in enumerate(grouped):
        # calculando as médias para cada métrica de desempenho para a combinação de parâmetros
        pontuacao_quartis = \
            (qtd_aleatorios - df_resultados.loc[:, ["q1_moneta", "q2_moneta", "q3_moneta"]].mean().mean()) / \
                qtd_aleatorios
                
        # calculando a pontuação para o patrimônio acumulado da carteira Moneta
        pontuacao_patrimonio = (df_comb["patrimonio_final_moneta"] / \
                                df_resultados["patrimonio_final_moneta"].max()).mean()
        
        # calculando a pontuação para o patrimônio acumulado da carteira Moneta em relação ao índice de referência
        pontuacao_vs_index = (df_comb["patrimonio_final_moneta"] / df_comb[f"patrimonio_final_{index_id}"] / \
        (df_resultados["patrimonio_final_moneta"] / df_resultados[f"patrimonio_final_{index_id}"]).max()).mean()
    
        # calculando a pontuação para o Sharpe da carteira Moneta
        pontuacao_sharpe = (1.1 ** df_comb["sharpe_moneta"] / \
                            (1.1 ** df_resultados["sharpe_moneta"]).max()).mean()

        # calculando a pontuação para o Beta da carteira Moneta
        pontuacao_beta = 1 - (df_comb["beta_moneta"] / df_resultados["beta_moneta"].max()).mean()

        # calculando a pontuação para o Max Drawdown da carteira Moneta
        pontuacao_max_drawdown = 1 - (df_comb["max_drawdown_moneta"] / \
                                    df_resultados["max_drawdown_moneta"].min()).mean()

        # calculando a função objetivo para pontuar o "conjunto da obra" de cada combinação de parâmetros
        ob = fo(pontuacao_quartis, pontuacao_patrimonio, pontuacao_vs_index, 
                pontuacao_sharpe, pontuacao_beta, pontuacao_max_drawdown,
                1, 1, 1, 1, 1, 1)     

        # registrando a pontuação e as métricas de desempenho para esta combinação de parâmetros no ranking
        ranking.append({
            "indice_comb": i,
            "cotacoes_segurar": comb[0],
            "maiores_medias": comb[1],
            "cotacoes_anteriores": comb[2],
            "intervalo": comb[3],
            "media_quartis": pontuacao_quartis,
            "media_patrimonio": pontuacao_patrimonio,
            "media_vs_index": pontuacao_vs_index,
            "media_sharpe": pontuacao_sharpe,
            "media_beta": pontuacao_beta,
            "media_max drawdown": pontuacao_max_drawdown,
            "fo": ob
        })

    # criando um DataFrame com o ranking das combinações de parâmetros e ordenando pela função objetivo
    df_final = pd.DataFrame(ranking).sort_values(by="fo", ascending=False).reset_index(drop=True)
    
    # normalizando a função objetivo para ficar entre 0 e 10 para facilitar a interpretação da pontuação final
    df_final["fo_ajustada"] = 10 * (df_final["fo"] - df_final["fo"].min()) / \
                                    (df_final["fo"].max() - df_final["fo"].min())
    
    # retornando o DataFrame com o ranking das combinações de parâmetros
    return df_final

# Importando as funções necessárias para o algoritmo genético de otimização de carteira
if __name__ == "__main__":
    # Criar diretório de resultados se não existir
    os.makedirs("resultados", exist_ok=True)
    
    df_resultados_campeonatos = gera_campeonatos()
    
    # Validação: verifica se há resultados de campeonatos
    if df_resultados_campeonatos.empty:
        print("\n[ERROR] Nenhum resultado de campeonato gerado.")
        print("  Verifique se há dados suficientes de cotações disponíveis.")
        exit(1) # Encerra o programa com código de erro
    
    df_pontuacoes = pontuar_monetas(df_resultados=df_resultados_campeonatos,
                                    qtd_aleatorios=qtd_bebados,
                                    index_id=index_id)
    
    # salvando os resultados do treinamento estatístico em um arquivo Excel para análise posterior
    print("Salvando os resultados do treinamento estatistico...")
    
    # salvando o DataFrame com os resultados dos campeonatos e as pontuações das combinações de parâmetros 
    # em um arquivo Excel para análise posterior concatenando a data e hora atual no nome do arquivo para 
    # evitar sobrescrever os resultados anteriores
    #df_pontuacoes.to_excel("resultados_treinamento.xlsx", index=False)
    agora = datetime.now().strftime("%Y%m%d_%H%M")
    df_pontuacoes.to_excel(f"resultados/treinamento_{agora}.xlsx", index=False)
