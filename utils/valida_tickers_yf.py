#####################################################################
# Funções para gerar a lista de tickers a partir de um arquivo Excel 
# e validar os tickers usando a API do Yahoo Finance.
# Ao final, gera um DataFrame com correspondente arquivo csv quer 
# será o arquivo base de tickers que será utilizado no código Moneta.
#####################################################################

# Biblioteca para validar os tickers usando a API do Yahoo Finance
import yfinance as yf
import pandas as pd
import warnings
import os
from pathlib import Path

def gerar_df_b3_empresas_setor(caminho_arquivo: str, 
                                    planilha: str = 'Setor', 
                                    colunas_intervalo: str = 'B:H', 
                                    pula_linhas: int = 2, 
                                    numero_linhas: int = 370) -> pd.DataFrame:
    """
    Carrega e retorna um DataFrame com as informações de empresas e setores da B3.
    
    Esta função lê um arquivo Excel contendo dados de empresas listadas na Bolsa
    de Valores do Brasil (B3), com informações sobre setores econômicos,
    subsetores, segmentos de negociação e outros dados estruturais.
    
    Parâmetros
    ----------
    caminho_arquivo : str
        Caminho completo ou relativo do arquivo Excel contendo dados das empresas e setores.
        Exemplo: '../utils/gera_tikers/B3_Empresas_Setor_20260206.xlsx'
    
    planilha : str, optional
        Nome da aba/planilha no arquivo Excel (padrão: 'Setor').
        A planilha deve conter uma coluna chamada 'CÓDIGO' que será usada como índice.
    
    colunas_intervalo : str, optional
        Intervalo de colunas a ler no formato Excel (padrão: 'B:H').
        Exemplos válidos: 'A:E', 'B:H', 'C:F'.
    
    pula_linhas : int, optional
        Número de linhas iniciais a pular na leitura (padrão: 2).
        Útil para ignorar cabeçalhos ou informações adicionais no início do arquivo.
    
    numero_linhas : int, optional
        Número máximo de linhas de dados a ler (padrão: 370).
        Se o arquivo tiver menos linhas, todas serão lidas.
    
    Retorno
    -------
    pd.DataFrame
        DataFrame com a coluna 'CÓDIGO' definida como índice, contendo as seguintes
        informações estruturais:
        - BEEST (ou similar)
        - SETOR ECONÔMICO
        - SUBSETOR
        - SEGMENTO
        - NOME DE PREGÃO
        - SEGMENTO DE NEGOCIAÇÃO
        
        O índice do DataFrame conterá os códigos das empresas (ex: 'PETR', 'VALE', 'ITUB').
    """
    try:
        # Ler o arquivo Excel com os parâmetros especificados
        df_b3_empresas_setor = pd.read_excel(
            io=caminho_arquivo,
            sheet_name=planilha,
            usecols=colunas_intervalo,
            skiprows=pula_linhas,
            nrows=numero_linhas,
            index_col='CÓDIGO'  # Definir a coluna 'CÓDIGO' como índice do DataFrame
        )
        
        return df_b3_empresas_setor
    
    # Tratamento de exceções para garantir que erros sejam informativos
    except FileNotFoundError:
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")
    except ValueError as e:
        raise ValueError(f"Erro ao ler o arquivo Excel: {str(e)}")
    except Exception as e:
        raise Exception(f"Erro inesperado ao processar o arquivo: {str(e)}")



# Função para gerar a lista de tickers do Yahoo Finance
def gerar_tickers_yf(df_b3_empresas_setor: pd.DataFrame) -> list:
    """
    Gera uma lista de tickers do Yahoo Finance a partir de um DataFrame com dados da B3.
    
    Esta função recebe um DataFrame contendo informações de empresas listadas na B3
    e gera tickers correspondentes para as três classes de ações: Ordinárias (ON),
    Preferenciais (PN) e Units. Os tickers gerados seguem o padrão do Yahoo Finance.
    
    Parâmetros
    ----------
    df_b3_empresas_setor : pd.DataFrame
        DataFrame contendo dados das empresas e setores da B3.
    
    Retorno
    -------
    list
        Lista contendo tickers do Yahoo Finance no formato 'CÓDIGO#.SA', onde:
        - CÓDIGO#3.SA : Ações Ordinárias (ON)
        - CÓDIGO#4.SA : Ações Preferenciais (PN)
        - CÓDIGO#11.SA : Units
    
    Notas
    -----
    - O DataFrame deve conter uma coluna chamada 'CÓDIGO' que será usada como índice.
    - Cada símbolo base gera 3 tickers (ON, PN e Units).
    - O sufixo '.SA' é adicionado automaticamente para indicar ações da bolsa brasileira no Yahoo Finance.
    """
    # Símbolos base dos papeis negociados na B3
    simbolos_base_b3 = df_b3_empresas_setor.index.tolist()

    # Gerar os tickers correspondentes para cada símbolo base, 
    # considerando as diferentes classes de ações (ON, PN, Units)
    lista_tickers_yf = []
    for simbolo in simbolos_base_b3:
        ticker_on = simbolo + '3.SA'  # Ações ordinárias (ON)
        ticker_pn = simbolo + '4.SA'  # Ações preferenciais (PN)
        ticker_units = simbolo + '11.SA'  # Units
        lista_tickers_yf.extend([ticker_on, ticker_pn, ticker_units])
    
    return lista_tickers_yf


# Filtrar os tickers válidos, excluindo aqueles que geram erro 404 
# ou retornam informações vazias.
def filtrar_tickers_validos(lista_tickers_yf) -> tuple:
    """
    Recebe uma lista de tickers e retorna apenas os válidos para 
    o Yahoo Finance.
    Tickers que geram mensagem contendo "HTTP Error 404" são excluídos.
    
    Ordem de verificação:
    1. Captura de exceções HTTP 404 (prioridade)
    2. Validação de info não vazio
    3. Verificação de campos essenciais (symbol)
    
    Parâmetros
    ----------
    lista_tickers_yf : list
        Lista de tickers a serem validados.
    
    Retorno
    -------
    list, list
        - tickers_validos_yf: Lista de tickers válidos para o Yahoo Finance.
        - tickers_erro_404_yf: Lista de tickers que geraram erro 404 ou retornaram informações vazias.
    """
    # Listas para armazenar os tickers válidos e os que geraram erro 404
    tickers_validos_yf = []
    tickers_erro_404_yf = []
    
    # Iterar sobre cada ticker e realizar as verificações
    for ticker in lista_tickers_yf:
        try:
            warnings.filterwarnings("ignore")  # Ignorar avisos de depreciação ou outros tipos de avisos
            info = yf.Ticker(ticker).info
            
        except Exception as e:
            # PRIORIDADE 1: Capturar e verificar primeiro se é um erro 404
            erro_str = str(e)
            
            if "HTTP Error 404" in erro_str or "Not Found" in erro_str:
                tickers_erro_404_yf.append(ticker)
                print(f"Ticker {ticker} gerou erro 404: {erro_str[:80]}")
            else:
                # Outros erros também são considerados inválidos
                tickers_erro_404_yf.append(ticker)
                print(f"Ticker {ticker} gerou erro: {erro_str[:80]}")
            continue
        
        # PRIORIDADE 2: Se não houve exceção, verificar se info é válido
        if not info or len(info) == 0:
            tickers_erro_404_yf.append(ticker)
            print(f"Ticker {ticker} retornou informações vazias.")
            continue
        
        # PRIORIDADE 3: Verificar se contém campos essenciais
        if 'symbol' not in info or info.get('symbol') is None:
            tickers_erro_404_yf.append(ticker)
            print(f"Ticker {ticker} não contém símbolo válido.")
            continue
        
        # Se passou por todas as verificações, o ticker é válido
        tickers_validos_yf.append(ticker)
        print(f"Ticker {ticker} é válido.")

    return tickers_validos_yf, tickers_erro_404_yf # Retorna uma tupla com as duas listas: válidos e erro 404/vazios


# Função para gerar o arquivo csv que será utilizado no código Moneta
def gerar_csv_tickers_info(df_b3_empresas_setor, tickers_validos, caminho_saida_csv=None):
    """
    Gera um DataFrame com informações da B3 para os tickers válidos do Yahoo Finance
    e, opcionalmente, salva o resultado em um arquivo CSV.

    A função usa o DataFrame `df_b3_empresas_setor` (com índice em 'CÓDIGO') e
    combina as informações para cada ticker válido, utilizando os 4 primeiros
    caracteres do ticker como chave de busca.

    Parâmetros
    ----------
    df_b3_empresas_setor : pd.DataFrame
        DataFrame com informações da B3 e índice na coluna 'CÓDIGO'.
    tickers_validos : list
        Lista de tickers válidos do Yahoo Finance (ex: 'AZTE3.SA', 'BRAV3.SA').
    caminho_saida_csv : str, optional
        Caminho para salvar o CSV. Se None, não salva (padrão: None).

    Retorno
    -------
    pd.DataFrame
        DataFrame com tickers como índice e informações da B3 como colunas.
    """
    # Criar lista para armazenar dados
    tickers_info_list = []
    
    # Iterar sobre os tickers válidos
    for ticker in tickers_validos:
        # Extrair os 4 primeiros caracteres do ticker
        t = ticker[:4]
        # Localizar informações correspondentes no DataFrame
        info = df_b3_empresas_setor.loc[df_b3_empresas_setor.index.str.startswith(t)]
        # Para cada linha encontrada, adicionar o ticker como nova coluna
        for _, row in info.iterrows():
            row_dict = row.to_dict()
            row_dict['TICKER'] = ticker
            tickers_info_list.append(row_dict)
    
    # Criar DataFrame a partir da lista de dicionários
    tickers_info = pd.DataFrame(tickers_info_list)
    
    # Definir TICKER como índice do DataFrame
    tickers_info = tickers_info.set_index('TICKER')
    
    # Salvar como CSV se caminho foi fornecido
    if caminho_saida_csv:
        tickers_info.to_csv(caminho_saida_csv, index=True)
        print(f"Arquivo CSV salvo em: {caminho_saida_csv}")
    
    return tickers_info


##############################################################
# Gerar o DataFrame de empresas e setores da B3

# Obter caminho absoluto baseado no diretório do script atual
## __file__ = caminho do script
## .parent = diretório onde o script está (/utils)
## .absolute() = caminho absoluto
## script_dir = C:\Users\gbsuf\OneDrive\ambiente_programacao\moneta_Gustavo\utils
script_dir = Path(__file__).parent.absolute()

# Caminho de rede onde está o arquivo Excel
arquivo_b3 = "gera_tickers/B3_Empresas_Setor_20260206.xlsx"

# Concatena para localizar o arquivo Excel
caminho_arquivo_b3 = script_dir / arquivo_b3

# Chama a função para gerar o df
df_b3_empresas_setor = gerar_df_b3_empresas_setor(
    caminho_arquivo=str(caminho_arquivo_b3),
    planilha='Setor',
    colunas_intervalo='B:H',
    pula_linhas=2,
    numero_linhas=370
)

print("=" * 70)
print("DataFrame de Empresas e Setores da B3")
print("=" * 70)
print(f"\nDimensões do DataFrame: {df_b3_empresas_setor.shape}")
print(f"Linhas: {df_b3_empresas_setor.shape[0]} | Colunas: {df_b3_empresas_setor.shape[1]}")
print(f"\nColunas disponíveis:\n{df_b3_empresas_setor.columns.tolist()}")
print(f"\nÍndice (Códigos das Empresas):\n{df_b3_empresas_setor.index.tolist()[:10]}...")
print(f"\nPrimeiras linhas do DataFrame:")
print(df_b3_empresas_setor.head())
print("=" * 70)


##############################################################
# Gerar a lista de tickers do Yahoo Finance a partir do arquivo Excel
lista_tickers_yf = gerar_tickers_yf(df_b3_empresas_setor)

# Exibir a quantidade total de tickers gerados e a lista completa
print("==============================================================")
print(f"A quantidade total de tickers gerados é: {len(lista_tickers_yf)}")
print(lista_tickers_yf)
print("==============================================================")


##############################################################
# Filtrar os tickers válidos, excluindo aqueles que geram erro 404 ou retornam informações vazias
tickers_validos_yf, tickers_erro_404_yf = filtrar_tickers_validos(lista_tickers_yf)

# Exibir a quantidade de tickers válidos e os que geraram erro 404
print("==============================================================")
print(f"A quantidade de tickers válidos é: {len(tickers_validos_yf)}")
print(f"Tickers válidos: {tickers_validos_yf}")
print()
print(f"A quantidade de tickers que geraram erro 404 ou informações vazias é: {len(tickers_erro_404_yf)}")
print(f"Tickers que geraram erro 404 ou informações vazias: {tickers_erro_404_yf}")
print("==============================================================")


##############################################################
# Gerar o DataFrame com informações dos tickers válidos e salvar como CSV
arquivo_saida = "gera_tickers/tickers_info.csv"
caminho_saida_csv = str(script_dir / arquivo_saida)
tickers_info = gerar_csv_tickers_info(df_b3_empresas_setor, tickers_validos_yf, caminho_saida_csv)

# Exibir o DataFrame com as informações dos tickers válidos
print("DataFrame com informações dos tickers válidos:")
print(tickers_info.head())