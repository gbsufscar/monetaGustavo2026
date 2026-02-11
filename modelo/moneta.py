import pandas as pd
import numpy as np
from ag.ag import (gerar_cromossomos_base, roda_do_acaso, crossover,
                mutacao_um, mutacao_dois, gerar_nova_geracao)

def moneta_ag(variacoes: pd.DataFrame, 
            qtd_iteracoes = 10, qtd_epocas = 40, qtd_croms_populacao_geral = 40):

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