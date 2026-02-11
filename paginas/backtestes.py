import streamlit as st
from datetime import date, datetime
from modelo.backtestes import rodar_backtestes
import pandas as pd
import plotly.graph_objects as go
from utils.performance_tracker import PerformanceTracker

def pagina_backtestes(simbolos, paises, intervalos):
    st.title(body = "Modelo Backtestes")
    st.write(body = "Realiza backtestes para o modelo Moneta")

    colunas = st.columns(2)
    data_inicial = colunas[0].date_input(label = "Data Inicial", value = date(2019, 1, 1))
    data_final = colunas[1].date_input(label = "Data Final", min_value = data_inicial, value = datetime.now().date())

    st.divider()

    # ---------------------------------------------------
    colunas = st.sidebar.columns(2)
    pais = colunas[0].radio(label="Selecione uma bolsa de ações", options=paises, index=0)
    intervalo = colunas[1].radio(label="Selecione o intervalo", options=intervalos, index=0)
    st.sidebar.divider()
    # ---------------------------------------------------

    # ---------------------------------------------------
    flag_acoes = st.sidebar.checkbox(label=f"Selecionar todas as ações do país ({pais})")
    if flag_acoes:
        bolsa_acoes = simbolos[paises[pais]][1:]
    else:
        bolsa_acoes = simbolos[paises[pais]][1:6]
    
    acoes_selecionadas = st.sidebar.multiselect(label="Selecione as ações para rodar o modelo",
                                                options=bolsa_acoes,
                                                default=bolsa_acoes)

    st.sidebar.divider()
    # ---------------------------------------------------

    # ---------------------------------------------------
    qtd_cotacoes_anteriores = st.sidebar.slider(label=f"Selecione a quantidade de " \
                                                    f"{'dias' if intervalo == 'Diário' else 'semanas'} anteriores",
                                                min_value=5,
                                                value=200,
                                                max_value=500,
                                                step=1
                                                )
    st.sidebar.divider()
    # ---------------------------------------------------

    # ---------------------------------------------------

    qtd_cotacoes_segurar = st.sidebar.slider(label=f"Selecione a quantidade de " \
                                                f"{'dias' if intervalo == 'Diário' else 'semanas'} para segurar a carteira",
                                            min_value=0,
                                            value=200,
                                            max_value=200,
                                            step=1
                                            )
    st.sidebar.divider()

    # ---------------------------------------------------

    # ---------------------------------------------------
    qtd_maiores_medias = st.sidebar.slider(label=f"Selecione a quantidade de maiores médias de retornos ({intervalo})",
                                            min_value=0,
                                            value=5,
                                            max_value=50,
                                            step=1
                                            )
    st.sidebar.divider()
    # ---------------------------------------------------

    # ---------------------------------------------------
    qtd_bebados = st.sidebar.slider(label="Selecione a quantidade de bebados",
                                    min_value=0,
                                    value=5,
                                    max_value=100,
                                    step=1)

    botao = st.sidebar.button(label="Rodar Backtestes")

    if botao == True:
        simbolo_index = simbolos[paises[pais]][0]
        resultados_backtestes = rodar_backtestes(acoes_selecionadas=acoes_selecionadas,
                                                data_inicial_bt=data_inicial,
                                                data_final_bt=data_final,
                                                intervalo=intervalos[intervalo],
                                                cotacoes_anteriores=qtd_cotacoes_anteriores,
                                                cotacoes_segurar=qtd_cotacoes_segurar,
                                                maiores_medias=qtd_maiores_medias,
                                                qtd_bebados=qtd_bebados,
                                                simbolo_index=simbolo_index)
        
        patrimonio_acumulado_moneta = resultados_backtestes["acumulados"]["moneta"]

        patrimonio_acumulado_index = resultados_backtestes["acumulados"]["index"]

        patrimonio_acumulado_bebados = resultados_backtestes["acumulados"]["bebados"]

        # Exibir resultados no prompt de comando (console)
        print(patrimonio_acumulado_moneta)

        # => Exibir os gráficos no Streamlit
        # Cria um objeto do tipo Figure
        fig = go.Figure() 

        # Adiciona a linha do gráfico ao objeto Figure: Moneta
        fig.add_trace(go.Scatter(x=patrimonio_acumulado_moneta.index, 
                                y=patrimonio_acumulado_moneta, 
                                name="Moneta",
                                line=dict(color="blue", width=2)))
        
        # Adiciona a linha do gráfico ao objeto Figure: Index (Bovespa)
        fig.add_trace(go.Scatter(x=patrimonio_acumulado_index.index, 
                                y=patrimonio_acumulado_index, 
                                name=simbolo_index, # Carrega o índice de referência do país selecionado
                                line=dict(color="red", width=2)))
        
        # Adiciona a linha do gráfico ao objeto Figure: Bêbados (Referência de aleatoriedade)
        for indice_bebado in range(qtd_bebados):
            fig.add_trace(go.Scatter(x=patrimonio_acumulado_bebados[indice_bebado].index, 
                                    y=patrimonio_acumulado_bebados[indice_bebado], 
                                    name=f"Bêbado {indice_bebado}",
                                    line=dict(color ="gray", width=1)))

        # Plotar o gráfico
        st.plotly_chart(fig)


        # ---------------------------------------------------

        # Variacoes do Moneta que ocorrem em intervalos periodicos (diários ou semanais)
        variacoes_periodicas_moneta = resultados_backtestes["variacoes"]["moneta"] 

        # Variacoes do Index que ocorrem em intervalos periodicos (diários ou semanais)
        variacoes_periodicas_index = resultados_backtestes["variacoes"]["index"]

        # Instancia o objeto PerformanceTracker para calcular o desempenho do Moneta
        tracker = PerformanceTracker(
            data_returns=variacoes_periodicas_moneta,
            market_returns=variacoes_periodicas_index,
            annual_risk_free=0.10, # Taxa de juros livre de risco anual
            period=intervalos[intervalo], # Período de cálculo das variações
        )

        # Calcula o Sharpe Ratio do Moneta (quanto que a carteira rende em relação a um índice de referência)
        sharpe = tracker.sharpe_ratio()

        # Calcula o Beta do Moneta (quanto que a carteira se correlaciona com o índice de referência)
        beta = tracker.portfolio_beta()

        # Calcula o retorno anual (quanto que a carteira rende acima do índice de referência)
        retorno_anual = tracker.annualized_return()

        # Calcula o Máximo Drawdown do Moneta (quanto que a carteira perde em relação ao seu pico)
        max_drawdown = tracker.max_drawdown()

        # Calcula o resultado final do Moneta
        resultado_final_moneta = patrimonio_acumulado_moneta.iloc[-1] - 1 

        # Calcula o resultado final do Index (de referência)
        resultado_final_index = patrimonio_acumulado_index.iloc[-1] - 1

        # Diferença entre os resultados do Moneta e do Index (de referência) 
        delta = resultado_final_moneta - resultado_final_index

        # Criar colunas no streamlit para exibir os resultados
        col1, col2, col3= st.columns(3) # Cria 3 colunas
        
        # Configurações das colunas
        col1.metric(label=f"Retorno Final Moneta",
                    value=f"{resultado_final_moneta:.2%}",
                    delta=f"{delta:.2%}") # Nota: .2% formata o número para duas casas decimais. ":" indica "formatar como...".
        col2.metric(label=f"Retorno Final Index",
                    value=f"{resultado_final_index:.2%}")
        col3.metric(label=f"Beta",
                    value=f"{beta:.2f}")
        
        col4, col5, col6 = st.columns(3)
        col4.metric(label=f"Sharpe Ratio",
                    value=f"{sharpe:.2f}")
        col5.metric(label=f"Max Drawdown",
                    value=f"{max_drawdown:.2f}%")
        col6.metric(label=f"Retorno Anual",
                    value=f"{retorno_anual:.0f}%")


        # ---------------------------------------------------

        # Subtítulo para as carteiras geradas no backtest
        st.subheader("Carteiras geradas no backtest") 
        st.divider()

        # Dados gerais das carteiras geradas no backtest (data, ações, pesos, etc.)
        dados_gerais = resultados_backtestes["dados"] 
        qtd_carteiras = len(dados_gerais)

        # Exibir as carteiras geradas no backtest
        qtd_venceu_index = 0
        qtd_positivo = 0
        for i in range(qtd_carteiras):
            # dados do jogo moneta
            dados_moneta = dados_gerais[i]["moneta"]
            data_inicial = dados_moneta["data_inicio"]
            data_final = dados_moneta["data_fim"]
            carteira_otima = dados_moneta["carteira"]
            retornos_moneta : pd.Series = dados_moneta["retornos"] # Anotou como uma variável do tipo pd.Series
            retorno_esperado = dados_moneta["retorno_esperado"]

            # dados do index
            dados_index = dados_gerais[i]["index"]
            retornos_index : pd.Series = dados_index["retornos"] # Anotou como uma variável do tipo pd.Series

            # Calcula os retornos acumulados das carteiras geradas no backtest (Moneta e Index)
            ret_acum_moneta = (1 + retornos_moneta).cumprod()
            ret_acum_index = (1 + retornos_index).cumprod()
            retorno_obtido_moneta = ret_acum_moneta.iloc[-1] - 1
            retorno_obtido_index = ret_acum_index.iloc[-1] - 1

            # Subtítulo para cada carteira gerada no backtest
            st.subheader(f"Carteira {i + 1}")
            st.write(f"{data_inicial:%d/%m/%Y} até {data_final:%d/%m/%Y}")

            # Formatação dos dados para exibição no Streamlit (tabela) 
            carteira_otima.name = "Percs"
            carteira_otima = carteira_otima.round(2)*100 # Multiplica por 100 para exibir em porcentagem
            carteira_otima = carteira_otima[carteira_otima > 1] # Filtra os pesos maiores que 1% para exibir na tabela de carteiras otimizadas.                                                                              

            # Cria 3 colunas para exibir as carteiras geradas no backtest
            col1, col2, col3, col4 = st.columns(4) 
            col1.dataframe(carteira_otima)
            col2.metric(label=f"Retorno Esperado Moneta",
                        value=f"{retorno_esperado:.2%}")
            col3.metric(label="Retorno Moneta",
                        value=f"{retorno_obtido_moneta:.2%}")
            col4.metric(label=f"Retorno {simbolo_index}",
                        value=f"{retorno_obtido_index:.2%}")
            

            # ---------------------------------------------------

            # Plotar o gráfico dos retornos acumulados das carteiras geradas no backtest

            # Cria um objeto do tipo Figure
            fig = go.Figure() # Cria um objeto do tipo Figure para plotar o gráfico (ainda vazio)

            # Adiciona a linha do gráfico ao objeto Figure: Moneta
            fig.add_trace(go.Scatter(x=ret_acum_moneta.index, 
                                    y=ret_acum_moneta, 
                                    name="Moneta",
                                    line=dict(color="blue", width=2)))
            
            # Adiciona a linha do gráfico ao objeto Figure: Index (Bovespa)
            fig.add_trace(go.Scatter(x=ret_acum_index.index, 
                                    y=ret_acum_index, 
                                    name=f"{simbolo_index}",
                                    line=dict(color="red", width=2)))
            
            # Plotar o gráfico no Streamlit
            st.plotly_chart(fig)


            # Índices quantitativos de desempenho entre as carteiras geradas no backtest
            if retorno_obtido_moneta > 0: 
                qtd_positivo += 1

            if retorno_obtido_moneta > retorno_obtido_index:
                qtd_venceu_index += 1

            st.divider()

        # ---------------------------------------------------

        # Exibir os índices de comparação quantitativas gerados no backtest no Streamlit 
        st.subheader("Resultados Gerais")

        # Cria 2 colunas para exibir os índices de comparação quantitativas gerados no backtest
        col1, col2 = st.columns(2)
        col1.metric(label="Quantidade de carteiras com retornos positivos",
                    value=f"{qtd_positivo}/{qtd_carteiras}",
                    delta=f"{qtd_positivo/qtd_carteiras:.2%}")
        col2.metric(label="Quantidade de carteiras que venceram o {simbolo_index}",
                    value=f"{qtd_venceu_index}/{qtd_carteiras}",
                    delta=f"{qtd_venceu_index/qtd_carteiras:.2%}")






        