
# Importações necessárias para o projeto
import streamlit as st
from cotacoes.cotacoes import busca_cotacoes, formata_cotacoes
from modelo.moneta import moneta_ag
from utils.gerais import gera_df_carteira, obter_data_vender
import plotly.graph_objects as go
from datetime import datetime
from simbolos import (obter_classificacoes_besst, obter_segmentos_b3_disponiveis, 
                    obter_tickers_filtrados)

# -----------------------------------------------------------------------------------

def pagina_moneta(simbolos, paises, intervalos):
    st.title(body = "Modelo Moneta")
    st.write("O moneta é uma ferramenta quantitativa para diversificação de carteira")
    st.info("📊 **Ações Brasileiras com Classificação BESST** (método Jeito Barsi de Investir)")

    # -----------------------------------------------------------------------------------
    # Configuração fixa para Brasil
    pais = "Brasil"
    moeda = "R$"
    
    # Seleção do intervalo de tempo
    intervalo = st.sidebar.radio(
        label = "Selecione o intervalo de dados",
        options = intervalos,
        index = 0
    )
    
    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------
    # FILTRO 1: Classificação BESST
    st.sidebar.subheader("🎯 Filtros de Seleção")
    
    classificacoes_disponiveis = obter_classificacoes_besst()
    classificacoes_selecionadas = st.sidebar.multiselect(
        label = "1️⃣ Classificação BESST",
        options = classificacoes_disponiveis,
        default = classificacoes_disponiveis,
        help = "Filtro por classificação da metodologia Jeito Barsi de Investir (JBI)"
    )
    
    # -----------------------------------------------------------------------------------
    # FILTRO 2: Segmento B3
    if classificacoes_selecionadas:
        segmentos_disponiveis = obter_segmentos_b3_disponiveis(classificacao_besst=None)
        segmentos_selecionados = st.sidebar.multiselect(
            label = "2️⃣ Segmento B3",
            options = segmentos_disponiveis,
            default = segmentos_disponiveis,
            help = "Filtro por segmento de listagem da B3"
        )
        
        # Mostra quantidade de segmentos selecionados
        if segmentos_selecionados:
            st.sidebar.caption(f"💼 {len(segmentos_selecionados)} segmento(s) selecionado(s)")
    else:
        segmentos_selecionados = []
        st.sidebar.warning("⚠️ Selecione ao menos uma Classificação BESST")
    
    # Linha divisória no sidebar
    st.sidebar.divider()
    
    # -----------------------------------------------------------------------------------
    # FILTRO 3: Seleção de Tickers
    if classificacoes_selecionadas and segmentos_selecionados:
        # Obtém os tickers filtrados
        tickers_dict = obter_tickers_filtrados(
            classificacoes_besst=classificacoes_selecionadas,
            segmentos_b3=segmentos_selecionados
        )
        
        # Mostra estatísticas dos tickers disponíveis
        st.sidebar.caption(f"📊 {len(tickers_dict)} ticker(s) disponível(is) após filtros")
        
        # Cria lista formatada para exibição: "TICKER - Nome da Empresa"
        tickers_formatados = {}
        for ticker, info in tickers_dict.items():
            label = f"{ticker} - {info['Empresa']}"
            tickers_formatados[label] = ticker
        
        # Checkbox para selecionar todos os tickers
        flag_todos_tickers = st.sidebar.checkbox(
            label = f"Selecionar todos os {len(tickers_formatados)} tickers filtrados",
            value = False
        )
        
        # Define tickers padrão
        if flag_todos_tickers:
            tickers_default = list(tickers_formatados.keys())
        else:
            # Seleciona os 10 primeiros como padrão
            tickers_default = list(tickers_formatados.keys())[:min(10, len(tickers_formatados))]
        
        # Seleção dos tickers
        tickers_selecionados_formatados = st.sidebar.multiselect(
            label = "3️⃣ Selecione os Tickers",
            options = list(tickers_formatados.keys()),
            default = tickers_default,
            help = "Selecione os tickers que deseja incluir no modelo"
        )
        
        # Converte de volta para lista de tickers (sem o nome da empresa)
        acoes_selecionadas = [tickers_formatados[item] for item in tickers_selecionados_formatados]
        
        # Mostra contador de tickers selecionados
        st.sidebar.success(f"✅ {len(acoes_selecionadas)} ticker(s) selecionado(s)")
        
        # Expander com detalhes dos tickers selecionados
        if acoes_selecionadas:
            with st.sidebar.expander("📋 Ver Detalhes dos Tickers Selecionados"):
                for ticker in acoes_selecionadas:
                    info = tickers_dict[ticker]
                    st.text(f"• {ticker}")
                    st.caption(f"  {info['Empresa']}")
                    st.caption(f"  BESST: {info['Classificacao_BESST']}")
                    st.caption(f"  Segmento: {info['Segmento_B3']}")
                    st.caption(f"  Setor: {info['Setor']}")
                    st.divider()
        
    else:
        acoes_selecionadas = []
        if not segmentos_selecionados and classificacoes_selecionadas:
            st.sidebar.warning("⚠️ Selecione ao menos um Segmento B3")
    
    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------
    
    # Configuração do modelo
    valor_investimento = st.sidebar.number_input(
        label = f"💰 Valor do Investimento ({moeda})",
        min_value = 1000,
        value = 10000,
        step = 1000
        )

    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------

    # Filtro para seleção de ações
    percentual_filtrar = st.sidebar.slider(
        label = "Selecione o percentual mínimo para uma ação aparecer na carteira",
        min_value = 0,
        value = 1, # Por padrão, filtra ações com menos de 1% de peso na carteira
        max_value = 5, # Máximo de 5% de uma ação na carteira
    )

    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------

    # Definição da quantidade de cotações anteriores para rodar o modelo
    qtd_cotacoes_anteriores = st.sidebar.slider(
        label = f"Selecione a quantidade de " \
            f"{'dias' if intervalo == 'Diário' else 'semanas'} para rodar o modelo",
        min_value = 5, # mínima quantidade de 5 períodos
        value = 200,
        max_value = 200, # máxima quantidade de períodos
        step = 1 # passo de 1 período
    )

    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------

    # Definição da quantidade de cotações para segurar a carteira
    qtd_cotacoes_segurar = st.sidebar.slider(
        label = f"Selecione a quantidade de " \
            f"{'dias' if intervalo == 'Diário' else 'semanas'} para segurar a carteira",
        min_value = 5,
        value = 90, # Por padrão, segura a carteira por 90 dias (3 meses). Atenção quando o intervalo for semanal, pois 90 semanas são 1 ano e 9 meses.
        max_value = 200,
        step = 1
    )

    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------
    
    # Filtro para seleção de ações com maiores médias
    qtd_maiores_medias = st.sidebar.slider(
        label = "Selecione a quantidade de maiores médias para filtrar os dados de variações",
        min_value = 0, # Mínimo de 0 médias (todas as ações selecionadas aparecerão na carteira)
        value = 10, # Por padrão, seleciona as 10 maiores médias
        max_value = 50, # Máximo de 50 médias para filtrar os dados de variações
    )

    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------

    # Botão para rodar o modelo
    botao_rodar_modelo = st.sidebar.button(label = "▶️ Rodar o Modelo", type="primary", use_container_width=True)

    # -----------------------------------------------------------------------------------
    # ÁREA PRINCIPAL - Estatísticas e Informações
    
    # Mostra estatísticas dos filtros aplicados na área principal
    if classificacoes_selecionadas and segmentos_selecionados and acoes_selecionadas:
        st.divider()
        st.subheader("📈 Resumo da Seleção")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Classificações BESST",
                value=len(classificacoes_selecionadas),
                help="Quantidade de classificações BESST selecionadas"
            )
        
        with col2:
            st.metric(
                label="Segmentos B3",
                value=len(segmentos_selecionados),
                help="Quantidade de segmentos B3 selecionados"
            )
        
        with col3:
            st.metric(
                label="Tickers Disponíveis",
                value=len(tickers_dict),
                help="Total de tickers após aplicar filtros"
            )
        
        with col4:
            st.metric(
                label="Tickers Selecionados",
                value=len(acoes_selecionadas),
                help="Quantidade de tickers que serão usados no modelo"
            )
        
        # Mostra tabela com distribuição por classificação BESST
        with st.expander("📊 Ver Distribuição dos Tickers Selecionados"):
            # Conta tickers por classificação
            distribuicao_besst = {}
            for ticker in acoes_selecionadas:
                classificacao = tickers_dict[ticker]['Classificacao_BESST']
                distribuicao_besst[classificacao] = distribuicao_besst.get(classificacao, 0) + 1
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("**Por Classificação BESST:**")
                for classif, qtd in sorted(distribuicao_besst.items()):
                    st.text(f"• {classif}: {qtd} ticker(s)")
            
            with col_b:
                # Conta tickers por segmento
                distribuicao_segmento = {}
                for ticker in acoes_selecionadas:
                    segmento = tickers_dict[ticker]['Segmento_B3']
                    distribuicao_segmento[segmento] = distribuicao_segmento.get(segmento, 0) + 1
                
                st.markdown("**Por Segmento B3:**")
                for seg, qtd in sorted(distribuicao_segmento.items(), key=lambda x: x[1], reverse=True)[:5]:
                    st.text(f"• {seg}: {qtd} ticker(s)")

    # -----------------------------------------------------------------------------------

    # Condição para rodar o modelo
    if botao_rodar_modelo == True:
        if not acoes_selecionadas:
            st.error("Selecione ao menos uma ação para rodar o modelo.")
            return # Interrompe a execução do código se nenhuma ação for selecionada

        # => Implementação do modelo Moneta
        # Busca as cotações das ações selecionadas
        print("Buscando cotações!!!")
        df_cotacoes = busca_cotacoes(simbolos = acoes_selecionadas,
                                    cotacoes_anteriores = qtd_cotacoes_anteriores,
                                    cotacoes_segurar = qtd_cotacoes_segurar,
                                    intervalo = intervalos[intervalo])
        #print(df_cotacoes)

        if df_cotacoes.empty or df_cotacoes.shape[1] == 0:
            st.error("Não foi possível obter cotações para as ações selecionadas. Tente outro período ou outro conjunto de tickers.")
            return

        # Formatação das cotações
        print("Formatando cotações!!!")
        df_variacoes = formata_cotacoes(cotacoes = df_cotacoes,
                                        intervalo = intervalos[intervalo],
                                        maiores_medias = qtd_maiores_medias)
        
        print(df_variacoes)

        if df_variacoes.empty or df_variacoes.shape[1] == 0:
            st.error("Após o tratamento, não restaram séries válidas para o modelo. Diminua o filtro de médias ou escolha mais tickers.")
            return # Interrompe a execução do código se não restarem séries válidas

        # Roda o modelo Moneta para otimização da carteira
        print("Rodando o modelo Moneta!!!")
        carteira_otima = moneta_ag(variacoes = df_variacoes)

        # Exibe a carteira ótima
        #print("Exibindo a carteira ótima!!!")
        #print(carteira_otima)

        # Gera o DataFrame da carteira final
        df_carteira = gera_df_carteira(carteira_final = carteira_otima,
                                    cotacoes = df_cotacoes,
                                    pais = "BR",
                                    percentual_filtrar = percentual_filtrar,
                                    valor_investir = valor_investimento)
        
        # Exibe o DataFrame da carteira final
        st.subheader("Carteira Final")
        st.dataframe(df_carteira)

        # Exibe o valor total investido e o percentual total da carteira
        valor_investir_final = df_carteira[f"Investido ({moeda})"].sum()
        colunas = st.columns(2)
        colunas[0].metric(label="Valor total investir", value=f"{moeda} {valor_investir_final:.2f}")
        colunas[1].metric(label="Perc total carteira", value=f"{df_carteira['Investido (%)'].sum():.1f}%")

        # Exibe a data aproximada para vender a carteira
        hoje = datetime.today().strftime("%Y-%m-%d")
        data_vender = obter_data_vender(data_compra=hoje, cotacoes_segurar=qtd_cotacoes_segurar, intervalo=intervalos[intervalo])
        st.warning(f":date: Vender a carteira aproximadamente em: **{data_vender}**")

        # Gráficos
        # Gráfico de pizza com a quantidade de ações na carteira
        fig = go.Figure(data=go.Pie(labels=df_carteira.index, values=df_carteira["Qtd de Acoes"]))
        # Configurações do gráfico
        fig.update_traces(hoverinfo="label+percent+value", textinfo="label+percent", textfont_size=12, textfont_family="Ubuntu",
                            marker={"line": {"color": "white", "width": 2}})
        # Configurações do layout
        fig.update_layout(title="Gráfico de Pizza", title_font_size=30, title_font_family="Ubuntu", title_font_color="black")
        # Exibe o gráfico
        st.plotly_chart(fig)
        # Mensagem de sucesso
        st.success(":tada: Modelo Moneta rodado com sucesso!") # :tada: é um emoji de fogos de artifício