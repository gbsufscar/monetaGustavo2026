import pandas as pd
import numpy as np
from ces.ces import ces_retornos, ces_riscos, ces_fitnesses
from sklearn import preprocessing


def gerar_nova_geracao(acoes, medias, matriz_covariancia, cromossomo_filho_um, 
                    cromossomo_filho_dois, mutante_um, mutante_dois, mutante_tres, 
                    mutante_quatro, mutante_cinco, mutante_seis):
    
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
    genes_sorteados = np.random.choice(acoes, size=2, replace=False)
    mutante = cromossomo_filho.copy()
    mutante.loc[genes_sorteados] = \
                cromossomo_filho.loc[genes_sorteados].iloc[::-1].values
        
    return mutante

def crossover(acoes, cromossomo_pai, cromossomo_mae):
    al = np.random.rand()
    parte_genes_pai = al * cromossomo_pai.loc[acoes]
    parte_genes_mae = (1 - al) * cromossomo_mae.loc[acoes]
    cromossomo_filho_um = parte_genes_mae + parte_genes_pai
    return cromossomo_filho_um

def roda_do_acaso(cromossomos_sorteados):
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