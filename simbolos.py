"""
Módulo de símbolos de ações brasileiras
Utiliza classificação BESST (metodologia Jeito Barsi de Investir)
e informações de Segmento B3
"""

import json
import os

# Caminho para o arquivo JSON com os dados dos tickers
CAMINHO_JSON = os.path.join(os.path.dirname(__file__), 'utils', 'gera_tikers', 'ticker_besst_yf.json')

# Carrega os dados do arquivo JSON
def carregar_dados_tickers():
    """
    Carrega os dados dos tickers do arquivo JSON
    """
    try:
        with open(CAMINHO_JSON, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Erro: Arquivo {CAMINHO_JSON} não encontrado")
        return {}
    except json.JSONDecodeError:
        print(f"Erro: Falha ao decodificar o arquivo JSON")
        return {}

# Dados dos tickers brasileiros
dados_tickers_br = carregar_dados_tickers()

def obter_classificacoes_besst():
    """
    Retorna a lista de classificações BESST disponíveis
    """
    # Retorna as chaves do dicionário, que correspondem às classificações BESST
    return list(dados_tickers_br.keys())

def obter_setores_por_classificacao(classificacao_besst):
    """
    Retorna os setores disponíveis para uma classificação BESST
    """
    # Verifica se a classificação existe nos dados e retorna os setores
    if classificacao_besst in dados_tickers_br:
        return list(dados_tickers_br[classificacao_besst].keys())
    # Se a classificação não existir, retorna lista vazia
    return []

def obter_segmentos_b3_disponiveis(classificacao_besst=None):
    """
    Retorna lista única de segmentos B3 disponíveis
    Se classificacao_besst for fornecida, retorna apenas os segmentos dessa classificação
    """
    # Utiliza um set para garantir unicidade dos segmentos
    segmentos = set()
    # Percorre os dados dos tickers para coletar os segmentos B3
    if classificacao_besst and classificacao_besst in dados_tickers_br: # Validação de guarda dupla para evitar KeyError
        # Percorre apenas a classificação especificada
        for setor in dados_tickers_br[classificacao_besst].values(): # Percorre os setores da classificação
            for ticker_info in setor.values(): # Percorre os tickers do setor
                if 'Segmento_B3' in ticker_info: # Verifica se a chave 'Segmento_B3' existe no dicionário do ticker
                    segmentos.add(ticker_info['Segmento_B3']) # Adiciona o segmento ao set, garantindo unicidade
    else:
        # Percorre todas as classificações
        for classificacao in dados_tickers_br.values(): # Percorre as classificações do BESST
            for setor in classificacao.values(): # Percorre os setores da classificação
                for ticker_info in setor.values(): # Percorre os tickers do setor
                    if 'Segmento_B3' in ticker_info: # Verifica se a chave 'Segmento_B3' existe no dicionário do ticker
                        segmentos.add(ticker_info['Segmento_B3']) # Adiciona o segmento ao set, garantindo unicidade
    # Retorna a lista de segmentos B3 ordenada
    return sorted(list(segmentos))

def obter_tickers_filtrados(classificacoes_besst=None, segmentos_b3=None):
    """
    Retorna dicionário de tickers filtrados por classificação BESST e/ou Segmento B3
    
    Args:
        classificacoes_besst: Lista de classificações BESST ou None para todas
        segmentos_b3: Lista de segmentos B3 ou None para todos
    
    Returns:
        Dict com estrutura: {ticker: {'Empresa': str, 'Segmento_B3': str, 'Classificacao_BESST': str, 'Setor': str}}
    """
    tickers_filtrados = {} # Dicionário para armazenar os tickers filtrados
    
    # Se classificacoes_besst não for fornecido, usa todas
    if classificacoes_besst is None:
        classificacoes_besst = obter_classificacoes_besst() # Obtém todas as classificações BESST disponíveis
    
    # Garante que é uma lista
    if isinstance(classificacoes_besst, str):
        classificacoes_besst = [classificacoes_besst] # Se for uma string, converte para lista
    
    # Percorre as classificações selecionadas
    for classificacao in classificacoes_besst:
        if classificacao not in dados_tickers_br:
            continue # Pula classificações que não existem nos dados
        # Percorre os setores e tickers da classificação selecionada
        for setor, tickers in dados_tickers_br[classificacao].items():
            for ticker, info in tickers.items():
                # Aplica filtro de segmento B3 se fornecido
                if segmentos_b3 is not None: # Se segmentos_b3 for fornecido, filtra os tickers que não pertencem aos segmentos selecionados
                    # Garante que é uma lista
                    if isinstance(segmentos_b3, str):
                        segmentos_b3 = [segmentos_b3] # Se for uma string, converte para lista
                    # Verifica se o ticker possui a chave 'Segmento_B3' e se o valor está na lista de segmentos selecionados
                    if info.get('Segmento_B3') not in segmentos_b3:
                        continue
                
                # Adiciona o ticker com informações completas
                tickers_filtrados[ticker] = {
                    'Empresa': info.get('Empresa', 'N/A'), # Nome da empresa, ou 'N/A' se não disponível
                    'Segmento_B3': info.get('Segmento_B3', 'N/A'), # Segmento B3, ou 'N/A' se não disponível
                    'Classificacao_BESST': classificacao, # Classificação BESST
                    'Setor': setor # Setor da empresa
                }
    # Retorna o dicionário de tickers filtrados
    return tickers_filtrados

# Mantém compatibilidade com código legacy (se necessário)
simbolos = {
    "BR": list(obter_tickers_filtrados().keys()) # Lista de tickers filtrados para o Brasil (sem filtros adicionais)
}