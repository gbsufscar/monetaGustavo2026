import pandas as pd

def ces_retornos(carteiras: pd.DataFrame, medias: pd.Series) -> pd.Series:
    """
    Esta função recebe multiplas carteiras e as médias periódicas das
    variações percentuais
    :param carteiras = N Carteiras (linhas) por M acoes (colunas)
    :param medias = Series com as médias das variacoes diárias das acoes

    :return todos os retornos das carteiras fornecidas de uma vez só!!!
    """
    return 2 ** carteiras.dot(medias)

def ces_riscos(carteiras: pd.DataFrame, 
            matriz_covariancia: pd.DataFrame) -> pd.Series:
    """
    Esta função recebe multiplas carteiras e a matriz de covariâncias
    entre os ativos (genes)
    :param carteiras = N Carteiras (linhas) por M acoes (colunas)
    :param matriz_covariancia = matriz das covariancias entre os ativos

    :return todos os riscos das carteiras fornecidas de uma vez só!!!
    """
    return (carteiras.dot(matriz_covariancia) * carteiras).\
                                            sum(axis=1).__abs__()

def ces_fitnesses(retornos: pd.Series, riscos: pd.Series) -> pd.Series:
    """
    Esta função recebe multiplos retornos (pd.series) e múltiplos 
    riscos (pd.series) e retorna multiplos fitnesses (pd.series)

    :param retornos = retornos dos cromossomos
    :param riscos = risco dos cromossomos

    :return todos os fitnesses dos cromossomos
    """
    return retornos / riscos