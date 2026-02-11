# Importa as bibliotecas necessárias para o projeto
import streamlit as st
from paginas.moneta import pagina_moneta
from paginas.backtestes import pagina_backtestes
from simbolos import simbolos

# Dicionário com as páginas disponíveis
paginas = {
    "Moneta": pagina_moneta,
    "Backtestes": pagina_backtestes
}

paises = {"Brasil": "BR", "Estados Unidos": "US"}
intervalos = {"Diário": "d", "Semanal": "w"}

# Função principal que renderiza a página selecionada
def main():
    # renderiza o menu lateral com as opções de páginas.
    st.sidebar.title(body = "Menu")
    # renderiza o selectbox com as opções de páginas.
    modelo_selecionado = \
        st.sidebar.selectbox(label = "Selecione a página desejada:",
                        options = paginas.keys())
    # renderiza a página selecionada
    paginas[modelo_selecionado](simbolos, paises, intervalos)

if __name__ == "__main__":
    main()