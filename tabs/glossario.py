import streamlit as st
import os

def render():
    try:
        # Caminho absoluto baseado na localização deste arquivo
        dir_base = os.path.dirname(os.path.abspath(__file__))
        caminho_arquivo = os.path.join(dir_base, '..', 'metodologia_glossario.txt')
        caminho_arquivo = os.path.normpath(caminho_arquivo)

        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            texto_metodologia = f.read()
        st.markdown(texto_metodologia, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("Arquivo 'metodologia_glossario.txt' não encontrado.")
        st.info("Por favor, certifique-se de que o arquivo com a metodologia e o glossário está na mesma pasta que o script principal.")
    except Exception as e:
        st.error(f"Erro ao carregar a metodologia: {e}")