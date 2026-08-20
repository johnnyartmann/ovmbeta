import streamlit as st
import os


def render():
    st.header("Download das Fontes de Dados")
    st.markdown("Faça o download dos arquivos de dados brutos utilizados para a construção deste painel.")
    st.markdown("---")
    
    dir_base = os.path.dirname(os.path.abspath(__file__))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Base Geral de Crimes")
        st.markdown("Registros de violência contra a mulher (exceto feminicídios).")
        st.info("Download indisponível devido à Lei Geral de Proteção de Dados (LGPD).")
    with col2:
        st.subheader("Base de Feminicídios")
        st.markdown("Registros detalhados de feminicídios consumados.")
        st.info("Download indisponível devido à Lei Geral de Proteção de Dados (LGPD).")
    with col3:
        st.subheader("Base Populacional")
        st.markdown("Dados da população feminina por município.")
        try:
            caminho_pop = os.path.join(dir_base, '..', 'data', 'base_populacao.xlsx')
            with open(caminho_pop, "rb") as fp:
                st.download_button(label="Download (XLSX)", data=fp, file_name="base_populacao.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="download_populacao")
        except FileNotFoundError:
            st.warning("Arquivo 'base_populacao.xlsx' não encontrado.")
            
    st.markdown("---")
    col4, col5, col6 = st.columns(3)
    with col4:
        st.subheader("Base de Regiões e Associações")
        st.markdown("Mapeamento de municípios para mesorregiões e associações de municípios.")
        try:
            caminho_regioes = os.path.join(dir_base, '..', 'data', 'base_regioes_associacoes.xlsx')
            with open(caminho_regioes, "rb") as fp:
                st.download_button(label="Download (XLSX)", data=fp, file_name="base_regioes_associacoes.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="download_regioes")
        except FileNotFoundError:
            st.warning("Arquivo 'base_regioes_associacoes.xlsx' não encontrado.")
    with col5:
        st.subheader("Base de Calendário")
        st.markdown("Mapeamento de feriados para análise sazonal.")
        try:
            caminho_calendario = os.path.join(dir_base, '..', 'data', 'base_calendario_feriados.xlsx')
            with open(caminho_calendario, "rb") as fp:
                st.download_button(label="Download (XLSX)", data=fp, file_name="base_calendario_feriados.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="download_calendario")
        except FileNotFoundError:
            st.warning("Arquivo 'base_calendario_feriados.xlsx' não encontrado.")
    with col6:
        st.subheader("Mapa de Municípios")
        st.markdown("Arquivo GeoJSON com as geometrias dos municípios de SC.")
        try:
            caminho_geojson = os.path.join(dir_base, '..', 'data', 'municipios_sc.json')
            with open(caminho_geojson, "rb") as fp:
                st.download_button(label="Download (JSON)", data=fp, file_name="municipios_sc.json",
                                   mime="application/json", key="download_geojson")
        except FileNotFoundError:
            st.warning("Arquivo 'municipios_sc.json' não encontrado.")
