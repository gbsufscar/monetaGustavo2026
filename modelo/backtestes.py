
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
    
    resultados_moneta = []
    resultados_index = []
    resultados_bebados = []
    data_rodar_moneta = data_inicial_bt

    todas_acoes = cotacoes.columns
    
    while data_rodar_moneta < data_final_bt:
        data_inicial_moneta = gerar_data(data_rodar_moneta, 
                                        cotacoes_anteriores, 
                                        intervalo, 
                                        "anterior")

        data_final_testar_carteira = gerar_data(data_rodar_moneta, 
                                                cotacoes_segurar, 
                                                intervalo, 
                                                "posterior")

        cotacoes_rodar_moneta = cotacoes.loc[data_inicial_moneta:data_rodar_moneta].copy()
        variacoes_rodar_moneta = formata_cotacoes(cotacoes=cotacoes_rodar_moneta, 
                                                intervalo=intervalo, 
                                                maiores_medias=maiores_medias)
        acoes = variacoes_rodar_moneta.columns
        carteira = moneta_ag(variacoes=variacoes_rodar_moneta)
        retorno_esperado = log2(carteira.loc["Retornos"])
        carteira = carteira.loc[acoes]

        cotacoes_testar_carteira = cotacoes.loc \
            [data_rodar_moneta:min(data_final_bt, data_final_testar_carteira), acoes].copy()
        
        variacoes_testar_carteira = formata_cotacoes(cotacoes=cotacoes_testar_carteira, 
                                                    intervalo=intervalo, 
                                                    maiores_medias=0)
        retornos_moneta = variacoes_testar_carteira.dot(carteira)

        cotacoes_index_testar = cotacoes_index.loc[data_rodar_moneta:min(data_final_bt, data_final_testar_carteira)]

        variacoes_index_testar = formata_cotacoes(cotacoes=pd.DataFrame(cotacoes_index_testar),
                                                intervalo=intervalo,
                                                maiores_medias=0)
        retornos_index = variacoes_index_testar["Adj Close"]

        retorno_esperado_periodo = \
                    (1 + retorno_esperado) ** \
                    (data_final_testar_carteira - data_rodar_moneta).days - 1
        resultados_moneta.append(
            {
                "data_inicio": data_rodar_moneta,
                "data_fim": data_final_testar_carteira,
                "carteira": carteira,
                "retornos": retornos_moneta,
                "retorno_esperado": retorno_esperado_periodo
            }
        )

        resultados_index.append(
            {
                "data_inicio": data_rodar_moneta,
                "data_fim": data_final_testar_carteira,
                "retornos": retornos_index
            }
        )

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

            retornos_bebado = variacoes_testar_bebado.dot(carteira_aleatoria)

            dados_bebado = {"data_inicio": data_rodar_moneta,
                            "data_fim": data_final_testar_carteira,
                            "carteira": carteira_aleatoria,
                            "retornos": retornos_bebado}
            
            bebados.append(dados_bebado)

        resultados_bebados.append(bebados)

        data_rodar_moneta = gerar_data(data_final_testar_carteira, 1, 
                                        intervalo, "posterior")
        
        print(f"Rodando Backteste do Moneta: {data_rodar_moneta}")
            
    retornos_jungidos_moneta = jungir_retornos(resultados_moneta, data_inicial_bt)
    resultados_acumulados_moneta = (retornos_jungidos_moneta + 1).cumprod()

    retornos_jungidos_index = jungir_retornos(resultados_index, data_inicial_bt)
    resultados_acumulados_index = (retornos_jungidos_index + 1).cumprod()


    resultados_acumulados_bebados = []
    for indice_bebado in range(qtd_bebados):
        retornos_bebado = [retornos[indice_bebado] 
                            for retornos in resultados_bebados]
        
        retornos_jungidos_bebado = jungir_retornos(retornos_bebado, data_inicial_bt)
        resultados_acumulados_bebado = (retornos_jungidos_bebado + 1).cumprod()
        resultados_acumulados_bebados.append(resultados_acumulados_bebado)

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

# Função para rodar os backtestes
# esta função vai parar no arquivo modelo/backtestes.py
def rodar_backtestes(acoes_selecionadas,
                    data_inicial_bt, data_final_bt, 
                    intervalo, cotacoes_anteriores, 
                    cotacoes_segurar, maiores_medias, qtd_bebados,
                    simbolo_index):
    
    data_minima = gerar_data(data_inicial_bt, cotacoes_anteriores, intervalo, "anterior")
    data_maxima = gerar_data(data_final_bt, cotacoes_segurar, intervalo, "posterior")

    cotacoes = busca_cotacoes(simbolos=acoes_selecionadas,
                            intervalo=intervalo,
                            data_inicio=data_minima.strftime("%Y-%m-%d"),
                            data_fim=data_maxima.strftime("%Y-%m-%d"))
    cotacoes.dropna(axis=1, inplace=True)

    cotacoes_index = busca_cotacoes(simbolos=[simbolo_index],
                                    intervalo=intervalo,
                                    data_inicio=data_minima.strftime("%Y-%m-%d"),
                                    data_fim=data_maxima.strftime("%Y-%m-%d"))
    cotacoes_index.dropna(axis=0, inplace=True)

    datas_comuns = cotacoes.index.intersection(cotacoes_index.index)
    cotacoes = cotacoes.loc[datas_comuns]
    cotacoes_index = cotacoes_index.loc[datas_comuns]

    resultados_backtestes = moneta_backtestes(data_inicial_bt, data_final_bt, 
                                            intervalo, cotacoes_anteriores, cotacoes_segurar, maiores_medias,
                                            qtd_bebados, cotacoes, cotacoes_index)

    return resultados_backtestes