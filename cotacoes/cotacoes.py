import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import warnings

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


    cotacoes_anteriores = kwargs.get('cotacoes_anteriores', None) # Quantidade de cotações anteriores a serem buscadas para as variações das ações
    cotacoes_segurar = kwargs.get('cotacoes_segurar', None) # Quantidade de cotações para segurar a carteira

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

    # Suprime warnings do yfinance (tickers delisted, sem dados, etc.)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        
        try:
            print(f"🔍 Buscando cotações para {len(simbolos)} ticker(s): {simbolos[:5]}{'...' if len(simbolos) > 5 else ''}")
            print(f"📅 Período: {data_inicio} até {data_fim}")
            
            # busca as cotações das ações para o intervalo especificado
            # progress=False: não mostra barra de progresso
            dados_download = yf.download(
                simbolos, 
                start=data_inicio, 
                end=data_fim,
                progress=False
            )
            
            print(f"📊 Tipo de dados retornado: {type(dados_download)}")
            print(f"📊 Shape: {dados_download.shape if hasattr(dados_download, 'shape') else 'N/A'}")
            print(f"📊 Colunas: {dados_download.columns.tolist() if hasattr(dados_download, 'columns') else 'N/A'}")
            
            # Verifica se o download retornou dados
            if dados_download.empty:
                print("⚠️ Yahoo Finance não retornou dados para os tickers solicitados")
                return pd.DataFrame()
            
            # Extrai a coluna 'Adj Close' ou 'Close' como fallback
            # Prioriza 'Adj Close' (ajustado por splits/dividendos), mas usa 'Close' se necessário
            if isinstance(dados_download.columns, pd.MultiIndex):
                # MultiIndex: múltiplos tickers
                if 'Adj Close' in dados_download.columns.get_level_values(0):
                    cotacoes = dados_download['Adj Close']
                    # Remove colunas completamente vazias (tickers sem dados em Adj Close)
                    cotacoes = cotacoes.dropna(axis=1, how='all')
                    
                    # Se Adj Close está vazio, tenta usar Close
                    if cotacoes.empty and 'Close' in dados_download.columns.get_level_values(0):
                        print("ℹ️ 'Adj Close' vazio, usando 'Close' como alternativa")
                        cotacoes = dados_download['Close']
                        cotacoes = cotacoes.dropna(axis=1, how='all')
                elif 'Close' in dados_download.columns.get_level_values(0):
                    print("ℹ️ 'Adj Close' não disponível, usando 'Close'")
                    cotacoes = dados_download['Close']
                    cotacoes = cotacoes.dropna(axis=1, how='all')
                else:
                    print("⚠️ Nenhuma coluna de preços encontrada")
                    return pd.DataFrame()
            elif 'Adj Close' in dados_download.columns:
                # SingleIndex com 'Adj Close'
                cotacoes = dados_download['Adj Close']
            elif 'Close' in dados_download.columns:
                # SingleIndex com 'Close'
                cotacoes = dados_download['Close']
            else:
                # Assume que o DataFrame já contém apenas preços
                cotacoes = dados_download
            
            print(f"✅ Cotações extraídas - Shape: {cotacoes.shape}")
            
            # Se apenas 1 ticker foi solicitado, yfinance retorna Series ao invés de DataFrame
            # Converte para DataFrame para manter consistência
            if isinstance(cotacoes, pd.Series):
                cotacoes = cotacoes.to_frame(name=simbolos[0] if len(simbolos) == 1 else 'Close')
            
            # Se não restou nenhum dado válido, retorna DataFrame vazio
            if cotacoes.empty:
                print("⚠️ Nenhum ticker retornou dados válidos do Yahoo Finance")
                return pd.DataFrame()
            
            # Informa quantos tickers foram obtidos com sucesso
            tickers_validos = cotacoes.shape[1] if len(cotacoes.shape) > 1 else 1
            tickers_perdidos = len(simbolos) - tickers_validos
            
            if tickers_perdidos > 0:
                print(f"ℹ️ {tickers_perdidos} ticker(s) não retornou(aram) dados (delisted/sem dados)")
                print(f"✅ {tickers_validos} ticker(s) com dados válidos")
            
            return cotacoes
            
        except Exception as e:
            print(f"❌ Erro ao buscar cotações: {str(e)}")
            return pd.DataFrame()

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

    # Verifica se o DataFrame está vazio
    if cotacoes.empty:
        print("⚠️ DataFrame de cotações vazio")
        return pd.DataFrame()
    
    # elimina as colunas (axis = 1: nome das ações) que possuem valores nulos para datas específicas dentro do intervalo de busca    
    #cotacoes.dropna(axis=1, inplace=True)
    # Admite até 5% de valores nulos para eliminar uma coluna
    threshold = max(1, int(0.95 * len(cotacoes)))  # Garante threshold mínimo de 1
    cotacoes.dropna(axis=1, thresh=threshold, inplace=True)
    
    # Verifica se ainda restam colunas após filtrar NaN
    if cotacoes.empty or cotacoes.shape[1] == 0:
        print("⚠️ Todos os tickers foram removidos por dados insuficientes (>5% NaN)")
        return pd.DataFrame()

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