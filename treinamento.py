from itertools import product
from datetime import date
import numpy as np
from utils.performance_tracker import PerformanceTracker
from modelo.backtestes import moneta_backtestes
from simbolos import simbolos
import pandas as pd
from cotacoes.cotacoes import busca_cotacoes

pais = "BR"
index_id = simbolos[pais][0]
acoes_ids = simbolos[pais][1:]

# configuração dos campeonatos que cada parametrização de Moneta vai jogar
colecao_comecos = [date(2018, 3, 15), date(2019, 3, 15), date(2020, 3, 15)]
colecao_finais = [date(2021, 4, 20), date(2021, 10, 20), date(2022, 4, 20)]

# configuracoes de Moneta
colecao_cotacoes_segurar = [400, 500]
colecao_cotacoes_anteriores = [100, 150]
colecao_maiores_medias = [10, 20]
colecao_intervalos = ["d"]
qtd_bebados = 100


def gera_campeonatos():
    """
    Esta função gera os campeonatos de Moneta para cada combinação de parâmetros

    Retorna um DataFrame com os resultados dos campeonatos
    """

    # data para buscar os dados para rodar todos os campeonatos
    data_inicio_buscar_dados = \
        min(colecao_comecos) - pd.Timedelta(days=max(colecao_cotacoes_anteriores))

    # data para buscar os dados para rodar todos os campeonatos    
    data_final_buscar_dados = \
        max(colecao_finais) + pd.Timedelta(days=max(colecao_cotacoes_segurar))
    
    # buscando os dados para as ações
    df_cotacoes = busca_cotacoes(
            simbolos=acoes_ids,
            intervalo="d",
            data_inicio=data_inicio_buscar_dados,
            data_fim=data_final_buscar_dados
        )

    # buscando os dados para o índice
    series_cotacoes_index = busca_cotacoes(
        simbolos=[index_id],
        intervalo="d",
        data_inicio=data_inicio_buscar_dados,
        data_fim=data_final_buscar_dados
    )

    # igualando os dados das ações com os indices, pois
    # os dados podem vir com datas presentes em um e não no outro
    datas_comuns = \
        df_cotacoes.index.intersection(series_cotacoes_index.index)
    df_cotacoes = df_cotacoes.loc[datas_comuns]
    series_cotacoes_index = series_cotacoes_index.loc[datas_comuns]

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

    n_aleatorios = len(patrimonios_aleatorios)

    arr = np.zeros(shape=(len(patrimonios_aleatorios) + 2, 
                        len(patrimonio_acum_moneta)), dtype=np.float64)
    arr[0, :] = patrimonio_acum_moneta
    arr[1, :] = patrimonio_acum_index

    for i, cumprod_aleatorios in enumerate(patrimonios_aleatorios, 2):
        arr[i:, :] = cumprod_aleatorios

    asort = np.argsort(arr[:, 1:], axis=0)

    quartis_moneta = np.quantile(n_aleatorios + 2 - np.where(asort == 0)[0], 
                                q=[0.25, 0.5, 0.75])

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
    grouped = df_resultados.groupby(cols)

    ranking = []
    for i, (comb, df_comb) in enumerate(grouped):
        
        pontuacao_quartis = \
            (qtd_aleatorios - df_resultados.loc[:, ["q1_moneta", "q2_moneta", "q3_moneta"]].mean().mean()) / \
                qtd_aleatorios

        pontuacao_patrimonio = (df_comb["patrimonio_final_moneta"] / \
                                df_resultados["patrimonio_final_moneta"].max()).mean()

        pontuacao_vs_index = (df_comb["patrimonio_final_moneta"] / df_comb[f"patrimonio_final_{index_id}"] / \
        (df_resultados["patrimonio_final_moneta"] / df_resultados[f"patrimonio_final_{index_id}"]).max()).mean()

        pontuacao_sharpe = (1.1 ** df_comb["sharpe_moneta"] / \
                            (1.1 ** df_resultados["sharpe_moneta"]).max()).mean()

        pontuacao_beta = 1 - (df_comb["beta_moneta"] / df_resultados["beta_moneta"].max()).mean()

        pontuacao_max_drawdown = 1 - (df_comb["max_drawdown_moneta"] / \
                                    df_resultados["max_drawdown_moneta"].min()).mean()

        ob = fo(pontuacao_quartis, pontuacao_patrimonio, pontuacao_vs_index, 
                pontuacao_sharpe, pontuacao_beta, pontuacao_max_drawdown,
                1, 1, 1, 1, 1, 1)     

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

    df_final = pd.DataFrame(ranking).sort_values(by="fo", ascending=False).reset_index(drop=True)
    df_final["fo_ajustada"] = 10 * (df_final["fo"] - df_final["fo"].min()) / \
                                    (df_final["fo"].max() - df_final["fo"].min())
    return df_final


if __name__ == "__main__":
    df_resultados_campeonatos = gera_campeonatos()
    df_pontuacoes = pontuar_monetas(df_resultados=df_resultados_campeonatos,
                                    qtd_aleatorios=qtd_bebados,
                                    index_id=index_id)
    
    print("Salvando os resultados do treinamento estatistico...")
    df_pontuacoes.to_excel("resultados_treinamento.xlsx", index=False)
