import json
import os
import pandas as pd
import streamlit as st

@st.cache_data(ttl=86400)
def carregar_parquets():
    """Carrega todos os DataFrames da pasta 'data/processed'. Usa cache_data para segurança contra mutação."""
    diretorio = 'data/processed'
    dfs = {}

    try:
        for filename in os.listdir(diretorio):
            if filename.endswith('.parquet'):
                key = filename.replace('.parquet', '')
                caminho_arquivo = os.path.join(diretorio, filename)
                dfs[key] = pd.read_parquet(caminho_arquivo)
    except FileNotFoundError:
        st.error(f"Diretório '{diretorio}' não encontrado. Execute o script 'preprocess_data.py' primeiro.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar os dados processados: {e}")
        return None

    return dfs


@st.cache_resource
def carregar_geojson():
    """Carrega o GeoJSON com @st.cache_resource para evitar cópias desnecessárias na RAM."""
    caminho_geojson = os.path.join('data', 'processed', 'geojson_sc.json')
    try:
        if os.path.exists(caminho_geojson):
            with open(caminho_geojson, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            st.error("Arquivo 'geojson_sc.json' não encontrado no diretório de dados processados.")
            return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao carregar o GeoJSON: {e}")
        return None


def carregar_dados_processados():
    """
    Carrega todos os dados pré-processados.
    Retorna um dicionário de DataFrames e o GeoJSON.
    Mantida para compatibilidade com chamadas existentes.
    """
    dfs = carregar_parquets()
    geojson_data = carregar_geojson()

    return dfs, geojson_data