# => Funções gerais para o projeto

# Importa as bibliotecas necessárias
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date

# -----------------------------------------------------------------------------------

def arredonda_para_baixo(numero, casas_decimais=0):
    multiplicador = 10 ** casas_decimais
    return int(numero * multiplicador) / multiplicador

# -----------------------------------------------------------------------------------

def gera_df_carteira(carteira_final: pd.Series, cotacoes: pd.DataFrame, pais: str,
                    percentual_filtrar: int = 5, valor_investir: float = 10000):
    """
    Função que gera um DataFrame com as informações da carteira final

    Args:
    carteira_final (pd.Series): Carteira final com os percentuais das ações
    simbolos (list): Lista com os símbolos (tickers) das ações
    cotacoes (pd.DataFrame): DataFrame com as cotações das ações
    percentual_filtrar (int): Percentual mínimo para filtrar as ações da carteira
    valor_investir (float): Valor a ser investido na carteira

    Returns:
    df_carteira (pd.DataFrame): DataFrame com as informações da carteira final

    """
    # pega os símbolos das ações
    simbolos = carteira_final.loc[~carteira_final.index.isin(["Retornos", "Riscos", "Fitnesses"])].index

    # ordena as ações com maiores percentuais na carteira
    carteira_final = carteira_final.loc[simbolos].sort_values(ascending=False)

    # filtra as ações com percentuais maiores que o percentual mínimo
    carteira_final_filtrada = carteira_final.loc[carteira_final.values > percentual_filtrar / 100]

    # se todas as ações da carteira, após o filtro, tiverem percentuais menores que o percentual mínimo, retorna um DataFrame vazio
    if carteira_final_filtrada.empty:
        return None

    # pega os símbolos das ações após o filtro
    simbolos_filtrados = carteira_final_filtrada.index

    # ultimos valores das ações que passaram pelo filtro
    ultimos_precos = cotacoes.loc[:, simbolos_filtrados].iloc[-1]

    # quantidade de ações a serem compradas para cada ação da carteira já filtrada
    qtd_acoes = carteira_final_filtrada * valor_investir / ultimos_precos

    # a quantidade de ações precisa ser filtrada para valores inteiros (mercado BR) e valores com 6 casas decimais (mercado US)
    qtd_acoes_ajustado = \
    pd.Series(map(lambda perc: arredonda_para_baixo(numero=perc, 
                                                    casas_decimais=0 if pais == "BR" else 6), 
                                                    qtd_acoes), 
                                                    index=simbolos_filtrados)
    
    # cria o DataFrame com as informações da carteira final
    df_carteira = (carteira_final_filtrada * 100).round(2).to_frame(name="Investido (%)")

    # cria a coluna 'Qtd de Acoes' para cada ação no DataFrame da carteira
    df_carteira.loc[:, 'Qtd de Acoes'] = qtd_acoes_ajustado.values

    # cria a coluna 'Investido (R$ ou US$)' para cada ação no DataFrame da carteira
    df_carteira.loc[:, f"Investido ({'R$' if pais == 'BR' else 'US$'})"] = (ultimos_precos * df_carteira.loc[:, 'Qtd de Acoes']).round(2)

    # insere a coluna 'Precos (R$ ou US$)' pada cada ação no DataFrame da carteira
    df_carteira.insert(0, f"Precos ({'R$' if pais == 'BR' else 'US$'})", ultimos_precos.round(2))

    return df_carteira

# -----------------------------------------------------------------------------------

def gerar_carteira_aleatoria(acoes, seed=None):

    """
    acoes: lista de ações
    seed: semente para geração de números aleatórios
    Esta função gera uma carteira aleatória com pesos aleatórios para cada ação
    """

    if seed:
        np.random.seed(seed)
    
    n_acoes = np.random.randint(1, len(acoes) + 1)

    acoes_escolhidas = np.random.choice(acoes, size=n_acoes, replace=False)
    sorteio = np.random.randint(1, 11, size=n_acoes)
    percentuais = sorteio / sorteio.sum()
    return pd.Series(percentuais, index=acoes_escolhidas)

# -----------------------------------------------------------------------------------

def obter_data_vender(data_compra: str, cotacoes_segurar: int, intervalo: str) -> str:

    """
    Função que calcula a data de venda das ações

    Args:
    data_compra (str): Data de compra das ações
    cotacoes_segurar (int): Quantidade de cotações a serem seguradas para a venda das ações (formato: aaaa-mm-dd)
    intervalo (str): Intervalo das cotações (d: diário ou w: semanal)

    Returns:
    dv (datetime.date): Data de venda das ações (formato: aaaa-mm-dd)
    """

    data_compra = datetime.strptime(data_compra, "%Y-%m-%d").date()
    
    if intervalo == "d":
        data_venda = data_compra + timedelta(days=cotacoes_segurar)
    elif intervalo == "w":
        data_venda = data_compra + timedelta(weeks=cotacoes_segurar)

    return data_venda.strftime("%Y-%m-%d")

# -----------------------------------------------------------------------------------

# Função para gerar uma nova data com base na data de referência, na quantidade de dias e no intervalo
def gerar_data(data: date, qtd_dias: int, intervalo: str, 
                tipo: str = "anterior") -> date:

    """
    data: data de referência
    qtd_dias: quantidade de dias para adicionar ou subtrair
    intervalo: "d" para dias e "s" para semanas
    tipo: "anterior" para subtrair e "posterior" para adicionar

    Esta função gera uma nova data com base na data de referência, 
    na quantidade de dias e no intervalo
    """
    
    if intervalo == "d":
        if tipo == "anterior":
            return data - timedelta(days=qtd_dias)
        else:
            return data + timedelta(days=qtd_dias)
    else:
        if tipo == "anterior":
            return data - timedelta(weeks=qtd_dias)
        else:
            return data + timedelta(weeks=qtd_dias)
        
# -----------------------------------------------------------------------------------

# Função para juntar os retornos dos backtestes em um único DataFrame
def jungir_retornos(resultados: dict, 
                    data_inicial: date) -> pd.Series:

    """
    resultados: dicionário com os resultados dos backtestes
    data_inicial: data inicial do backtest

    Esta função junta os retornos dos backtestes em um único DataFrame
    """

    total_carteiras = len(resultados)
    retornos_jungidos = pd.Series([0], index=[data_inicial])

    for i in range(total_carteiras):
        retornos = resultados[i]["retornos"]
        retornos_jungidos = pd.concat([retornos_jungidos, retornos])

    return retornos_jungidos

# -----------------------------------------------------------------------------------