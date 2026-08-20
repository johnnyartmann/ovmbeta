import pandas as pd
import json
import os
from utils import normalizar_nome
import pyarrow as pa
import pyarrow.parquet as pq
from shapely.geometry import shape, mapping
from shapely import simplify as shapely_simplify

def carregar_e_processar_dados(df_geral_ssp=None, df_feminicidio_ssp=None):
    """
    Carrega todos os dados brutos, processa-os e retorna dicionários
    de dataframes e outros dados.

    Parâmetros opcionais (para integração com o processador SSP):
        df_geral_ssp: DataFrame já mapeado da SSP (VD - ALESC).
                      Se fornecido, substitui a leitura de data/base_geral.xlsx.
        df_feminicidio_ssp: DataFrame já mapeado da SSP (FEMINICÍDIO - AUTOR).
                            Se fornecido, substitui a leitura de data/base_feminicidio.xlsx.
    """
    dfs = {}
    outros_dados = {}

    # Carregar e processar cada conjunto de dados
    try:
        df_regioes = pd.read_excel('data/base_regioes_associacoes.xlsx')
        df_regioes.columns = (df_regioes.columns.str.strip().str.lower()
                      .str.replace(' ', '_', regex=False)
                      .str.replace('ã', 'a', regex=False)
                      .str.replace('ç', 'c', regex=False)
                      .str.replace('ô', 'o', regex=False)
                      .str.replace('í', 'i', regex=False))
        df_regioes['municipio_normalizado'] = df_regioes['municipio'].apply(normalizar_nome)
        dfs['regioes'] = df_regioes

        df_populacao = pd.read_excel('data/base_populacao.xlsx')
        df_populacao.columns = (df_populacao.columns.str.strip().str.lower()
                      .str.replace(' ', '_', regex=False)
                      .str.replace('ã', 'a', regex=False)
                      .str.replace('ç', 'c', regex=False)
                      .str.replace('ô', 'o', regex=False)
                      .str.replace('í', 'i', regex=False))
        df_populacao['municipio_normalizado'] = df_populacao['municipio'].apply(normalizar_nome)
        dfs['populacao'] = df_populacao

        df_calendario = pd.read_excel('data/base_calendario_feriados.xlsx')
        df_calendario['data'] = pd.to_datetime(df_calendario['data'])
        dfs['calendario'] = df_calendario

        # --- PROCESSAMENTO DA BASE GERAL ---
        if df_geral_ssp is not None:
            df_geral = df_geral_ssp.copy()
        else:
            df_geral = pd.read_excel('data/base_geral.xlsx')

        df_geral.columns = (df_geral.columns.str.strip().str.lower()
                            .str.replace(' ', '_', regex=False).str.replace('ã', 'a', regex=False)
                            .str.replace('ç', 'c', regex=False).str.replace('ú', 'u', regex=False))
        df_geral.rename(columns={
            'data_do_fato': 'data_fato', 'município': 'municipio',
            'fato_comunicado': 'fato_comunicado', 'idade': 'idade_vitima'
        }, inplace=True)

        # --- INÍCIO DO ETL: PADRONIZAÇÃO DE FATOS ---
        correcoes_fatos = {
            "Lesão Corporal Dolosa": "Lesão corporal grave ou gravíssima - Dolosa",
            "Estupro coletivo": "Estupro"
        }
        if 'fato_comunicado' in df_geral.columns:
            # O replace procura o valor exato da chave e substitui pelo valor
            df_geral['fato_comunicado'] = df_geral['fato_comunicado'].replace(correcoes_fatos)
            print("ETL de 'Fato Comunicado' aplicado com sucesso na base geral.")
        # --- FIM DO ETL ---

        df_geral['data_fato'] = pd.to_datetime(df_geral['data_fato'])
        df_geral['idade_vitima'] = pd.to_numeric(df_geral['idade_vitima'], errors='coerce')
        df_geral['municipio_normalizado'] = df_geral['municipio'].apply(normalizar_nome)
        df_geral = pd.merge(df_geral, df_regioes[['municipio_normalizado', 'mesoregiao', 'associacao']],
                            on='municipio_normalizado', how='left')
        df_geral['mesoregiao'] = df_geral['mesoregiao'].fillna('Não informado')
        df_geral['associacao'] = df_geral['associacao'].fillna('Não informado')
        # --------------------------

        # --- ATUALIZAÇÃO AQUI (BASE FEMINICÍDIO) ---
        if df_feminicidio_ssp is not None:
            df_feminicidio = df_feminicidio_ssp.copy()
        else:
            df_feminicidio = pd.read_excel('data/base_feminicidio.xlsx')
        
        # Renomeação baseada na nova imagem enviada e inspeção do arquivo
        df_feminicidio.rename(columns={
            'FATO': 'fato_comunicado',          
            'DATA': 'data_fato',
            'HORA': 'hora_fato',                
            'MUNICÍPIO': 'municipio',
            'TIPO DE LOCAL': 'tipo_local',
            'LOCALIDADE': 'localidade',
            'IDADE VITIMA': 'idade_vitima',
            'ETNIA/RAÇA': 'etnia_vitima', 
            'RELAÇÃO COM O AUTOR': 'relacao_autor',
            'TEMPO DE RELACIONAMENTO': 'tempo_relacionamento',
            'FILHOS COM O AUTOR': 'filhos_com_autor',
            'Nº DE FILHOS COM O AUTOR': 'num_filhos_com_autor',
            'BO DE VD CONTRA O AUTOR': 'bo_de_vd_contra_o_autor',
            'MEIO': 'meio_crime',
            'IDADE AUTOR': 'idade_autor',
            'ETNIA/RAÇA.1': 'etnia_autor',
            'PASSAGEM POLICIAL': 'passagem_policial',
            'PASSAGEM POR VIOLÊNCIA DOMÉSTICA': 'passagem_por_violencia_domestica',
            'PRISÃO': 'autor_preso'
        }, inplace=True)

        # Limpeza padrão dos nomes das colunas
        df_feminicidio.columns = (df_feminicidio.columns.str.strip().str.lower()
                      .str.replace(' ', '_', regex=False)
                      .str.replace('ã', 'a', regex=False)
                      .str.replace('ç', 'c', regex=False)
                      .str.replace('ú', 'u', regex=False)
                      .str.replace('ô', 'o', regex=False)
                      .str.replace('ê', 'e', regex=False)
                      .str.replace('á', 'a', regex=False))

        # --- MAP EARLIER RELATIONSHIPS ---
        # Conversão de Vínculo entre o Autor e a Vítima (Foco da vítima para o autor)
        mapa_relacoes = {
            "ESPOSA": "MARIDO",
            "COMPANHEIRA": "COMPANHEIRO",
            "EX-ESPOSA": "EX-MARIDO",
            "NAMORADA": "NAMORADO",
            "EX-COMPANHEIRA": "EX-COMPANHEIRO",
            "MÃE": "FILHO",
            "EX-NAMORADA": "EX-NAMORADO",
            "FILHA": "PAI",
            "NÃO INFORMADA": "NÃO INFORMADO",
            "SOGRA": "GENRO",
            "EX-SOGRA": "EX-GENRO",
            "IRMÃ": "IRMÃO",
            "PRIMA": "PRIMO",
            "CUNHADA": "CUNHADO",
            "VÓ": "NETO",
            "EX-CUNHADA": "EX-CUNHADO",
            "ENTEADA": "PADRASTO"
        }
        
        if 'relacao_autor' in df_feminicidio.columns:
             # Normaliza para maiúsculas para garantir o match (embora o dropna/fillna venha depois, é bom garantir)
             # Mas o mapa está em caixa alta. Vamos garantir que a coluna esteja pronta.
             # O replace funciona bem se os valores forem exatos. Se tiver espaço extra, pode falhar.
             # Vamos fazer um strip e upper antes, se for string.
             df_feminicidio['relacao_autor'] = df_feminicidio['relacao_autor'].astype(str).str.strip().str.upper()
             df_feminicidio['relacao_autor'] = df_feminicidio['relacao_autor'].replace(mapa_relacoes)
             # Caso algum valor não esteja no mapa, ele permanece o original (ou 'NAN' se era nan).
             # O tratamento de 'nan' para 'Não informado' vem logo abaixo em colunas_texto.
        
        # ---------------------------------

        # Converte objetos datetime no campo autor_preso para "SIM"
        if 'autor_preso' in df_feminicidio.columns:
            from datetime import datetime
            mask_datetime = df_feminicidio['autor_preso'].apply(
                lambda x: isinstance(x, (pd.Timestamp, datetime))
            )
            df_feminicidio.loc[mask_datetime, 'autor_preso'] = 'SIM'

        # --- CORREÇÃO DO ERRO DE DATETIME ---
        # Força colunas que podem ter sido lidas erradas pelo Excel para texto (string)
        colunas_texto = [
            'autor_preso', 
            'bo_de_vd_contra_o_autor', 
            'passagem_policial', 
            'passagem_por_violencia_domestica', 
            'etnia_autor', 
            'etnia_vitima',
            'hora_fato', # Hora muitas vezes vem como objeto datetime, melhor garantir como string
            'localidade',
            'tipo_local',
            'tempo_relacionamento',
            'filhos_com_autor'
        ]
        
        for col in colunas_texto:
            if col in df_feminicidio.columns:
                df_feminicidio[col] = df_feminicidio[col].astype(str).replace('nan', 'Não informado')

        # Conversão de tipos numéricos e data
        df_feminicidio['data_fato'] = pd.to_datetime(df_feminicidio['data_fato'], errors='coerce')
        df_feminicidio['idade_vitima'] = pd.to_numeric(df_feminicidio['idade_vitima'], errors='coerce')
        df_feminicidio['idade_autor'] = pd.to_numeric(df_feminicidio['idade_autor'], errors='coerce')
        if 'num_filhos_com_autor' in df_feminicidio.columns:
             df_feminicidio['num_filhos_com_autor'] = pd.to_numeric(df_feminicidio['num_filhos_com_autor'], errors='coerce')
        
        # Normalização de município e merge com regiões
        df_feminicidio['municipio_normalizado'] = df_feminicidio['municipio'].apply(normalizar_nome)
        df_feminicidio = pd.merge(df_feminicidio, df_regioes[['municipio_normalizado', 'mesoregiao', 'associacao']], on='municipio_normalizado',
                      how='left')
        df_feminicidio['mesoregiao'] = df_feminicidio['mesoregiao'].fillna('Não informado')
        df_feminicidio['associacao'] = df_feminicidio['associacao'].fillna('Não informado')
        df_feminicidio['ano'] = df_feminicidio['data_fato'].dt.year
        
        # Remove linhas onde a data do fato ficou NaT (erro de conversão ou linha vazia no excel)
        df_feminicidio = df_feminicidio.dropna(subset=['data_fato'])

        dfs['feminicidio'] = df_feminicidio

        # Preparação para união com a base geral (se necessário)
        df_feminicidio_para_geral = df_feminicidio.copy()
        # Garante que a coluna de fato comunicado seja padronizada para 'Feminicídio'
        df_feminicidio_para_geral['fato_comunicado'] = 'Feminicídio'

        df_final = pd.concat([df_geral, df_feminicidio_para_geral], ignore_index=True)
        df_final['ano'] = df_final['data_fato'].dt.year
        df_final['mes'] = df_final['data_fato'].dt.month_name()
        dfs['geral'] = df_final

        colunas_categoricas = ['municipio', 'municipio_normalizado', 'fato_comunicado',
                               'mesoregiao', 'associacao', 'mes']
        for col in colunas_categoricas:
            if col in df_final.columns:
                df_final[col] = df_final[col].astype('category')
        colunas_numericas = {'ano': 'Int16', 'idade_vitima': 'Int16'}
        for col, dtype in colunas_numericas.items():
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce').astype(dtype)
        colunas_essenciais = ['data_fato', 'ano', 'mes', 'municipio', 'municipio_normalizado',
                              'fato_comunicado', 'mesoregiao', 'associacao', 'idade_vitima']
        colunas_presentes = [c for c in colunas_essenciais if c in df_final.columns]
        df_final = df_final[colunas_presentes]
        dfs['geral'] = df_final

        with open('data/municipios_sc.json', 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
        for feature in geojson_data['features']:
            nome_original = feature['properties'].get('NM_MUN')
            if nome_original:
                feature['properties']['NM_MUN_NORMALIZADO'] = normalizar_nome(nome_original)
            if feature.get('geometry'):
                geom = shape(feature['geometry'])
                simplified = shapely_simplify(geom, tolerance=0.001)
                feature['geometry'] = mapping(simplified)
        outros_dados['geojson_sc'] = geojson_data

    except FileNotFoundError as e:
        print(f"Erro: Arquivo não encontrado - {e}")
        return None, None
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return None, None

    return dfs, outros_dados

def salvar_dados_processados(dfs, outros_dados, diretorio='data/processed'):
    """
    Salva cada dataframe como um arquivo Parquet e outros dados como JSON.
    """
    try:
        os.makedirs(diretorio, exist_ok=True)
        
        for key, df in dfs.items():
            caminho_arquivo = os.path.join(diretorio, f"{key}.parquet")
            df.to_parquet(caminho_arquivo)
            print(f"DataFrame '{key}' salvo em '{caminho_arquivo}'")

        for key, data in outros_dados.items():
            caminho_arquivo = os.path.join(diretorio, f"{key}.json")
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(data, f)
            print(f"Dado '{key}' salvo em '{caminho_arquivo}'")

    except Exception as e:
        print(f"Erro ao salvar os arquivos processados: {e}")


if __name__ == "__main__":
    print("Iniciando o pré-processamento dos dados...")
    dataframes, outros_dados_dict = carregar_e_processar_dados()
    if dataframes is not None:
        salvar_dados_processados(dataframes, outros_dados_dict)
        print("Pré-processamento concluído.")