import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd

# -----------------------------------------------------------------------------------

def busca_cotacoes(simbolos: list, intervalo: str, **kwargs) -> pd.DataFrame:

    """
    Função que busca as variações periódicas das ações

    Args:
    simbolos (list): Lista com os símbolos (tickers) das ações
    cotacoes_anteriores (int): Quantidade de cotações anteriores a serem buscadas para as variações das ações
    kwargs (dict): dicionário com as chaves 'cotacoes_anteriores' e 'cotacoes_segurar' OU 'data_inicio' e 'data_fim'

    Returns:
    variacoes (pd.DataFrame): DataFrame com as variações periódicas das ações
    """

    # data de hoje (formato datetime)
    hoje_dtm: datetime = datetime.today()


    cotacoes_anteriores = kwargs.get('cotacoes_anteriores', None)
    cotacoes_segurar = kwargs.get('cotacoes_segurar', None)

    if cotacoes_anteriores is not None and cotacoes_segurar is not None:
        # data de início da busca (data de hoje menos a quantidade de cotações anteriores)
        if intervalo == "d":
            # se o intervalo for diário, subtrai a quantidade de dias
            data_inicio: datetime = hoje_dtm - timedelta(days=cotacoes_anteriores)
            data_fim: datetime = hoje_dtm + timedelta(days=cotacoes_segurar)
        elif intervalo == "w":
            # se o intervalo for semanal, subtrai a quantidade de semanas
            data_inicio: datetime = hoje_dtm - timedelta(weeks=cotacoes_anteriores)
            data_fim: datetime = hoje_dtm + timedelta(weeks=cotacoes_segurar)
        
        # converte a data de início para string (aaaa-mm-dd)
        data_inicio: str = data_inicio.strftime('%Y-%m-%d')
        data_fim: str = data_fim.strftime('%Y-%m-%d')
    else:
        data_inicio = kwargs.get('data_inicio', None)
        data_fim = kwargs.get('data_fim', None)

        if data_inicio is None or data_fim is None:
            raise ValueError("É necessário fornecer os parâmetros 'cotacoes_anteriores' e 'cotacoes_segurar'.")

    # busca as cotações das ações para o intervalo especificado
    cotacoes: pd.DataFrame = yf.download(simbolos, start=data_inicio, end=data_fim)['Adj Close']

    return cotacoes

# -----------------------------------------------------------------------------------

def formata_cotacoes(cotacoes: pd.DataFrame, intervalo: str, maiores_medias: int) -> pd.DataFrame:

    """
    Função que formata as cotações das ações para variações periódicas e filtra as ações com maiores médias de retorno

    Args:
    cotacoes (pd.DataFrame): DataFrame com as cotações das ações
    intervalo (str): Intervalo de busca das variações periódicas das ações. 'd' para diário, 'w' para semanal
    maiores_medias (int): Quantidade de ações com maiores médias de retorno a serem filtradas

    Returns:
    variacoes_intervaladas_filtradas (pd.DataFrame): DataFrame com as variações periódicas das ações filtradas
    """

    # elimina as colunas (axis = 1: nome das ações) que possuem valores nulos para datas específicas dentro do intervalo de busca    
    cotacoes.dropna(axis=1, inplace=True)

    # filtra as variações periódicas das ações (a cada 5 dias ou todos os dias)
    cotacoes_intervaladas: pd.DataFrame = cotacoes.iloc[::5] if intervalo == "w" else cotacoes

    # calcula as variações diárias das ações e elimina as linhas com valores nulos.
    # valores nulos podem ocorrer quando a ação não possui cotação em um determinado dia
    variacoes_intervaladas: pd.DataFrame = cotacoes_intervaladas.pct_change().dropna()

    # se a quantidade de ações com maiores médias de retorno for maior que 0
    if maiores_medias > 0:
        # filtra as maiores médias de retorno pelo intervalo escolhido
        # variacoes_intervaladas_filtradas = filtra_maiores_medias(variacoes_intervaladas, n=maiores_medias)

        # calcula as médias dos retornos das ações
        medias: pd.Series = variacoes_intervaladas.mean(axis=0)

        # o método 'nlargest' está presente em qualquer objeto do tipo 'Series'. Esse método retorna outro 'Series' com os 'n' maiores valores
        acoes_maiores_medias: pd.Series = medias.nlargest(maiores_medias)

        # pega as ações com as maiores médias de retorno
        variacoes_intervaladas_filtradas: pd.DataFrame = \
            variacoes_intervaladas.loc[:, acoes_maiores_medias.index]

        return variacoes_intervaladas_filtradas
    
    return variacoes_intervaladas

# -----------------------------------------------------------------------------------