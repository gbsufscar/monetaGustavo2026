
# Importações necessárias para o projeto
import streamlit as st
from cotacoes.cotacoes import busca_cotacoes, formata_cotacoes
from modelo.moneta import moneta_ag
from utils.gerais import gera_df_carteira, obter_data_vender
import plotly.graph_objects as go
from datetime import datetime

# -----------------------------------------------------------------------------------

def pagina_moneta(simbolos, paises, intervalos):
    st.title(body = "Modelo Moneta")
    st.write("O moneta é uma ferramenta quantitativa para diviversificação de cartiera")

    # -----------------------------------------------------------------------------------
    # Divisão do layout da barra lateral (sidebar) em duas colunas
    colunas= st.sidebar.columns(2)

    # Radio buttom para seleção do país
    pais = colunas[0].radio(label = "Selecione uma bolsa de ações",
                                options = paises,
                                index = 0)
    
    print(pais)
    print(paises)
    print(simbolos)
    
    # Seleção da moeda
    moeda = f"{'R$' if pais == 'Brasil' else f'US$'}"

    # Seleção do intervalo de tempo
    intervalo = colunas[1].radio(label = "Selecione o intervalo de dados",
                                options = intervalos,
                                index = 0)
    
    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------
    
    # Seleção do país e das ações correspondentes
    flag_acoes = st.sidebar.checkbox(label = f"Selecionar todas as ações do país {pais}")
    if flag_acoes == True:
        bolsa_acoes = simbolos[paises[pais]][1:] # Seleciona todas as ações da lista por slice da segunda posição até o final (excluindo o primeiro elemento que é o índice do país na lista BOVA11.SA para o Brasil e ^GSPC para os Estados Unidos que não são ações e sim índices de referência para o mercado de ações do país)
    else:
        bolsa_acoes = simbolos[paises[pais]][1:10] # Seleciona as 10 primeiras ações por slice (fatiamento) da lista
        
    # Seleção das ações
    acoes_selecionadas = st.sidebar.multiselect(
        label = "Selecione as ações para rodar o modelo",
        options = bolsa_acoes,
        default = bolsa_acoes
        )
    
    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------
    
    # Configuração do modelo
    valor_investimento = st.sidebar.number_input(
        label = f"Insira o valor do investimento",
        min_value = 1000,
        value = 1000,
        step = 50
        ),

    # Linha divisória no sidebar (quebra de layout)
    st.sidebar.divider()

    # -----------------------------------------------------------------------------------

    # Filtro para seleção de ações
    percentual_filtrar = st.sidebar.slider(
        label = "Selecione o percentual mínimo para uma ação aparecer na carteira",
        min_value = 0,
        value = 1,
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
    botao_rodar_modelo = st.sidebar.button(label = "Rodar o modelo")

    # Condição para rodar o modelo
    if botao_rodar_modelo == True:
        # => Implementação do modelo Moneta
        # Busca as cotações das ações selecionadas
        print("Buscando cotações!!!")
        df_cotacoes = busca_cotacoes(simbolos = acoes_selecionadas,
                                    cotacoes_anteriores = qtd_cotacoes_anteriores,
                                    cotacoes_segurar = qtd_cotacoes_segurar,
                                    intervalo = intervalos[intervalo])
        #print(df_cotacoes)

        # Formatação das cotações
        print("Formatando cotações!!!")
        df_variacoes = formata_cotacoes(cotacoes = df_cotacoes,
                                        intervalo = intervalos[intervalo],
                                        maiores_medias = qtd_maiores_medias)
        
        #print(df_variacoes)

        # Roda o modelo Moneta para otimização da carteira
        print("Rodando o modelo Moneta!!!")
        carteira_otima = moneta_ag(variacoes = df_variacoes)

        # Exibe a carteira ótima
        #print("Exibindo a carteira ótima!!!")
        #print(carteira_otima)

        # Gera o DataFrame da carteira final
        df_carteira = gera_df_carteira(carteira_final = carteira_otima,
                                    cotacoes = df_cotacoes,
                                    pais = paises[pais],
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