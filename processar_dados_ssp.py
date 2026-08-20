"""
Processador de Dados SSP -> OVM
================================
Mapeia colunas dos arquivos recebidos da SSP (Secretaria de Seguranca Publica)
para o formato base do OVM e executa o ETL completo.

Uso:
    streamlit run processar_dados_ssp.py
"""

import os
import sys
import unicodedata
from datetime import datetime

import pandas as pd
import streamlit as st

# Garante que o diretorio de trabalho e o raiz do projeto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from preprocess_data import carregar_e_processar_dados, salvar_dados_processados

# =============================================================================
# Configuracao da pagina
# =============================================================================
st.set_page_config(
    page_title="Processador SSP → OVM",
    page_icon="🔄",
    layout="wide",
)

# =============================================================================
# Funcoes auxiliares de normalizacao
# =============================================================================

def normalizar(texto):
    """
    Normaliza uma string: strip, uppercase, remove acentos,
    converte ordinais (º->o, ª->a) e remove caracteres especiais.
    Retorna string vazia se nao for str ou for NaN.
    """
    if not isinstance(texto, str):
        return ''
    texto = texto.strip().upper()
    # Substitui indicadores ordinais antes da decomposicao
    texto = texto.replace('\u00ba', 'O').replace('\u00aa', 'A')  # º -> O, ª -> A
    # Remove acentos via decomposicao Unicode
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

# =============================================================================
# Dicionarios de mapeamento
# =============================================================================

# VD - ALESC (SSP) -> base_geral.xlsx (OVM)
# Chave: nome normalizado da coluna SSP
# Valor: nome original da coluna base (como aparece no base_geral.xlsx)
_VD = {
    'Data do Fato':     ' Data do Fato',
    'Municipio':        'Municipio',
    'Fato Comunicado':  ' Fato Comunicado',
    'Idade':            'Idade',
}
VD_MAPPING = {normalizar(k): v for k, v in _VD.items()}

# FEMINICIDIO - AUTOR (SSP) -> base_feminicidio.xlsx (OVM)
# Chave: (level0_normalizado, level1_normalizado) da header de 2 linhas
# Valor: nome EXATO da coluna no base_feminicidio.xlsx (com acentos, etc.)
_FEM = {
    ('FATO OCORRIDO',          ''):                     'FATO',
    ('DATA',                    ''):                     'DATA',
    ('HORA',                    ''):                     'HORA',
    ('LOCAL DA OCORRENCIA',    'MUNICIPIO'):             'MUNICÍPIO',
    ('LOCAL DA OCORRENCIA',    'TIPO DE LOCAL'):         'TIPO DE LOCAL',
    ('LOCAL DA OCORRENCIA',    'LOCALIDADE'):            'LOCALIDADE',
    ('VITIMA',                 'IDADE'):                 'IDADE VITIMA',
    ('VITIMA',                 'ETNIA/RACA'):            'ETNIA/RAÇA',
    ('VITIMA',                 'RELACAO COM O AUTOR'):   'RELAÇÃO COM O AUTOR',
    ('VITIMA',                 'TEMPO DE RELACIONAMENTO'):'TEMPO DE RELACIONAMENTO',
    ('VITIMA',                 'FILHOS COM O AUTOR'):    'FILHOS COM O AUTOR',
    ('VITIMA',                 'NO DE FILHOS COM O AUTOR'):'Nº DE FILHOS COM O AUTOR',
    ('VITIMA',                 'BO DE VD CONTRA O AUTOR'):'BO DE VD CONTRA O AUTOR',
    ('FATO',                   'MEIO'):                  'MEIO',
    ('AUTOR',                  'IDADE'):                 'IDADE AUTOR',
    ('AUTOR',                  'ETNIA/RACA'):            'ETNIA/RAÇA.1',
    ('AUTOR',                  'PASSAGEM POLICIAL'):     'PASSAGEM POLICIAL',
    ('AUTOR',                  'PASSAGEM POR VIOLENCIA DOMESTICA'): 'PASSAGEM POR VIOLÊNCIA DOMÉSTICA',
    ('AUTOR',                  'PRISAO'):                'PRISÃO',
}
FEMINICIDIO_MAPPING = {
    (normalizar(k[0]), normalizar(k[1])): v for k, v in _FEM.items()
}

# =============================================================================
# Colunas para comparacao e relatorio PDF
# =============================================================================

COLUNAS_CORE = [
    'fato_comunicado', 'data_fato', 'hora_fato', 'municipio',
    'tipo_local', 'localidade', 'idade_vitima', 'etnia_vitima',
    'relacao_autor', 'tempo_relacionamento', 'filhos_com_autor',
    'num_filhos_com_autor', 'bo_de_vd_contra_o_autor', 'meio_crime',
    'idade_autor', 'etnia_autor', 'passagem_policial',
    'passagem_por_violencia_domestica', 'autor_preso',
]

COLUNAS_DISPLAY = {
    'fato_comunicado':                  'Fato Comunicado',
    'data_fato':                        'Data do Fato',
    'hora_fato':                        'Hora',
    'municipio':                        'Município',
    'tipo_local':                       'Tipo de Local',
    'localidade':                       'Localidade',
    'idade_vitima':                     'Idade da Vítima',
    'etnia_vitima':                     'Etnia/Raça (Vítima)',
    'relacao_autor':                    'Relação com o Autor',
    'tempo_relacionamento':             'Tempo de Relacionamento',
    'filhos_com_autor':                 'Filhos com o Autor',
    'num_filhos_com_autor':             'Nº de Filhos com o Autor',
    'bo_de_vd_contra_o_autor':          'BO de VD contra o Autor',
    'meio_crime':                       'Meio do Crime',
    'idade_autor':                      'Idade do Autor',
    'etnia_autor':                      'Etnia/Raça (Autor)',
    'passagem_policial':                'Passagem Policial (Autor)',
    'passagem_por_violencia_domestica': 'Passagem por VD (Autor)',
    'autor_preso':                      'Autor Preso',
}


# =============================================================================
# Funcoes de mapeamento
# =============================================================================

def mapear_vd(uploaded_file):
    """
    Le o arquivo VD - ALESC (SSP) com header de 1 linha e mapeia as colunas
    para o formato base_geral.xlsx.

    Retorna (df_mapeado, lista_log_mapeadas, lista_log_descartadas).
    """
    df_raw = pd.read_excel(uploaded_file)
    cols_ssp = df_raw.columns.tolist()
    cols_normalizadas = {normalizar(c): c for c in cols_ssp}

    rename_map = {}
    mapeadas = []
    nao_encontradas = []

    for col_norm, col_base in VD_MAPPING.items():
        if col_norm in cols_normalizadas:
            nome_ssp = cols_normalizadas[col_norm]
            rename_map[nome_ssp] = col_base
            mapeadas.append(f'{nome_ssp}  ->  {col_base.strip()}')
        else:
            nao_encontradas.append(col_base.strip())

    descartadas = [c for c in cols_ssp if c not in rename_map]

    df = df_raw[list(rename_map.keys())].rename(columns=rename_map)
    return df, mapeadas, nao_encontradas, descartadas


def mapear_feminicidio(uploaded_file):
    """
    Le o arquivo FEMINICIDIO - AUTOR (SSP) com header de 2 linhas e mapeia
    as colunas para o formato base_feminicidio.xlsx.

    Retorna (df_mapeado, lista_log_mapeadas, lista_log_nao_encontradas, lista_log_descartadas).
    """
    df_raw = pd.read_excel(uploaded_file, header=None)

    # Linha 0: categorias (ex: "LOCAL DA OCORRENCIA")
    # Linha 1: subcolunas (ex: "MUNICIPIO")
    row0 = df_raw.iloc[0].ffill()
    row1 = df_raw.iloc[1]

    # Constroi chaves compostas normalizadas para cada coluna
    composites = []
    for col_idx in range(len(row0)):
        l0 = normalizar(row0.iloc[col_idx])
        l1 = normalizar(row1.iloc[col_idx])
        composites.append((l0, l1))

    # Dados a partir da linha 2
    data = df_raw.iloc[2:].reset_index(drop=True)

    mapeadas = []
    nao_encontradas = []
    selected_indices = []
    base_col_names = []

    for (l0_norm, l1_norm), col_base in FEMINICIDIO_MAPPING.items():
        try:
            idx = composites.index((l0_norm, l1_norm))
            selected_indices.append(idx)
            base_col_names.append(col_base)
            mapeadas.append(f'[{l0_norm} | {l1_norm}]  ->  {col_base}')
        except ValueError:
            nao_encontradas.append(col_base)
            mapeadas.append(f'[NAO ENCONTRADO: {l0_norm} | {l1_norm}]  ->  {col_base}')

    # Colunas SSP que nao foram mapeadas (descartadas)
    descartadas = []
    for i, (l0, l1) in enumerate(composites):
        if i not in selected_indices:
            descartadas.append(f'[{l0} | {l1}]')

    df = data.iloc[:, selected_indices].copy()
    df.columns = base_col_names
    return df, mapeadas, nao_encontradas, descartadas


# =============================================================================
# Funcao de comparacao e geracao de PDF
# =============================================================================

def gerar_relatorio_novos_feminicidios():
    """
    Compara o feminicidio.parquet recem-processado (processamento/)
    com o existente (data/processed/) e gera um PDF com os novos registros.

    Retorna (caminho_pdf, qtde_novos).
    """
    old_path = os.path.join(BASE_DIR, 'data', 'processed', 'feminicidio.parquet')
    new_path = os.path.join(BASE_DIR, 'processamento', 'feminicidio.parquet')

    if not os.path.exists(new_path):
        return None, 0

    new = pd.read_parquet(new_path)

    if os.path.exists(old_path):
        old = pd.read_parquet(old_path)

        # Preenche NaN em colunas numericas para o merge funcionar
        new_merge = new[COLUNAS_CORE].copy()
        old_merge = old[COLUNAS_CORE].copy()
        for col in COLUNAS_CORE:
            if new_merge[col].dtype in ('float64', 'int64'):
                new_merge[col] = new_merge[col].fillna(-1)
                if col in old_merge.columns:
                    old_merge[col] = old_merge[col].fillna(-1)

        merged = new_merge.merge(old_merge, on=COLUNAS_CORE, how='left', indicator=True)
        novos_mask = merged['_merge'] == 'left_only'
    else:
        # Sem arquivo antigo: todos os registros sao novos
        novos_mask = pd.Series(True, index=new.index)

    novos = new.loc[novos_mask]
    qtde_novos = len(novos)

    if qtde_novos == 0:
        return None, 0

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    pdf_path = os.path.join(BASE_DIR, 'processamento', 'relatorio_novos_feminicidios.pdf')

    with PdfPages(pdf_path) as pdf:
        for i, (_, row) in enumerate(novos.iterrows(), 1):
            fig, ax = plt.subplots(figsize=(8.27, 11.69))
            ax.axis('off')

            data_str = ''
            if pd.notna(row['data_fato']):
                try:
                    data_str = pd.Timestamp(row['data_fato']).strftime('%d/%m/%Y')
                except Exception:
                    data_str = str(row['data_fato'])

            titulo = f'Novo Registro de Feminicídio #{i}'
            subtitulo = f'Data: {data_str}  |  Município: {row["municipio"]}'

            ax.text(0.5, 0.96, titulo, transform=fig.transFigure,
                    ha='center', fontsize=13, fontweight='bold')
            ax.text(0.5, 0.93, subtitulo, transform=fig.transFigure,
                    ha='center', fontsize=10, color='#555555')

            table_data = []
            for col in COLUNAS_CORE:
                label = COLUNAS_DISPLAY[col]
                val = row[col]
                if pd.isna(val):
                    val = 'Não informado'
                elif isinstance(val, pd.Timestamp):
                    val = val.strftime('%d/%m/%Y %H:%M')
                elif isinstance(val, datetime):
                    val = val.strftime('%d/%m/%Y %H:%M')
                else:
                    val = str(val)
                table_data.append([label, val])

            tbl = ax.table(
                cellText=table_data,
                colLabels=['Campo', 'Valor'],
                cellLoc='left',
                loc='upper center',
                bbox=[0.08, 0.05, 0.84, 0.84],
                colWidths=[0.26, 0.58],
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(8)
            tbl.auto_set_column_width([0, 1])

            for j in range(2):
                tbl[0, j].set_facecolor('#4a148c')
                tbl[0, j].set_text_props(color='white', fontweight='bold', fontsize=9)

            for row_idx in range(1, len(table_data) + 1):
                bg = '#f3e5f5' if row_idx % 2 == 0 else '#ffffff'
                for col_idx in range(2):
                    tbl[row_idx, col_idx].set_facecolor(bg)

            pdf.savefig(fig)
            plt.close(fig)

    return pdf_path, qtde_novos


# =============================================================================
# Interface Streamlit
# =============================================================================

st.title("Processador de Dados SSP → OVM")
st.caption("Mapeia colunas dos arquivos da SSP e executa o ETL automaticamente.")
st.divider()

# --- Step 1: Upload ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("VD - ALESC.xlsx")
    arquivo_vd = st.file_uploader(
        "Base de violência doméstica",
        type=["xlsx"],
        key="upload_vd",
    )

with col2:
    st.subheader("FEMINICIDIO - AUTOR.xlsx")
    arquivo_fem = st.file_uploader(
        "Base de feminicídio",
        type=["xlsx"],
        key="upload_fem",
    )

st.divider()

# --- Step 2: Processar ---
pode_processar = arquivo_vd is not None and arquivo_fem is not None

if not pode_processar:
    st.info("Faça upload dos dois arquivos para habilitar o processamento.")

btn_processar = st.button(
    "PROCESSAR TUDO",
    type="primary",
    disabled=not pode_processar,
    use_container_width=True,
)

if btn_processar:
    log_container = st.container()

    with log_container:
        st.subheader("Resultado do Processamento")
        status = st.status("Iniciando processamento...", expanded=True)

        # ---- 1. Mapear VD ----
        status.update(label="Mapeando colunas do VD - ALESC...", state="running")
        try:
            df_vd, vd_map, vd_faltou, vd_desc = mapear_vd(arquivo_vd)
            status.write(f"**VD - ALESC:** {len(vd_map)} colunas verificadas")
            for linha in vd_map:
                status.write(f"  ✓ {linha}")
            if vd_faltou:
                for col in vd_faltou:
                    status.write(f"  ✗ NÃO ENCONTRADA: {col}")
            if vd_desc:
                status.write(f"  ✗ Descartadas ({len(vd_desc)}): {', '.join(vd_desc)}")
        except Exception as e:
            status.update(label=f"Erro no mapeamento do VD: {e}", state="error")
            st.stop()

        # ---- 2. Mapear Feminicidio ----
        status.update(label="Mapeando colunas do FEMINICIDIO - AUTOR...", state="running")
        try:
            df_fem, fem_map, fem_faltou, fem_desc = mapear_feminicidio(arquivo_fem)
            status.write(f"**FEMINICÍDIO - AUTOR:** {len(fem_map)} colunas verificadas")
            for linha in fem_map:
                status.write(f"  ✓ {linha}")
            if fem_faltou:
                for col in fem_faltou:
                    status.write(f"  ✗ NÃO ENCONTRADA: {col}")
            if fem_desc:
                status.write(f"  ✗ Descartadas ({len(fem_desc)}):")
                for d in fem_desc:
                    status.write(f"     {d}")
        except Exception as e:
            status.update(label=f"Erro no mapeamento do Feminicídio: {e}", state="error")
            st.stop()

        # ---- 3. Salvar intermediarios ----
        status.update(label="Salvando arquivos intermediários em processamento/...", state="running")
        DIR_SAIDA = os.path.join(BASE_DIR, 'processamento')
        os.makedirs(DIR_SAIDA, exist_ok=True)

        try:
            caminho_vd = os.path.join(DIR_SAIDA, 'vd_mapeado.xlsx')
            df_vd.to_excel(caminho_vd, index=False)
            status.write(f"  💾 vd_mapeado.xlsx ({len(df_vd)} linhas, {len(df_vd.columns)} colunas)")

            caminho_fem = os.path.join(DIR_SAIDA, 'feminicidio_mapeado.xlsx')
            df_fem.to_excel(caminho_fem, index=False)
            status.write(f"  💾 feminicidio_mapeado.xlsx ({len(df_fem)} linhas, {len(df_fem.columns)} colunas)")
        except Exception as e:
            status.update(label=f"Erro ao salvar intermediários: {e}", state="error")
            st.stop()

        # ---- 4. Executar ETL ----
        status.update(label="Executando ETL (preprocess_data)...", state="running")
        try:
            dfs, outros = carregar_e_processar_dados(
                df_geral_ssp=df_vd,
                df_feminicidio_ssp=df_fem,
            )
            if dfs is None:
                status.update(label="Erro: ETL retornou None.", state="error")
                st.stop()
            status.write("  ✓ ETL concluído com sucesso")
        except Exception as e:
            status.update(label=f"Erro no ETL: {e}", state="error")
            st.stop()

        # ---- 5. Salvar parquets ----
        status.update(label="Salvando parquets em processamento/...", state="running")
        try:
            salvar_dados_processados(dfs, outros, diretorio=DIR_SAIDA)
            for key in dfs:
                status.write(f"  📦 {key}.parquet")
            for key in outros:
                ext = 'json' if key == 'geojson_sc' else 'json'
                status.write(f"  📦 {key}.{ext}")
        except Exception as e:
            status.update(label=f"Erro ao salvar parquets: {e}", state="error")
            st.stop()

        # ---- 6. Comparar e gerar PDF de novos registros ----
        status.update(label="Comparando com dados existentes e gerando PDF...", state="running")
        try:
            pdf_path, qtde_novos = gerar_relatorio_novos_feminicidios()
            if qtde_novos == 0:
                status.write("  ℹ Nenhum registro novo de feminicídio encontrado.")
                pdf_path = None
            else:
                status.write(f"  📄 {qtde_novos} novo(s) registro(s) encontrado(s)")
                status.write(f"  💾 PDF gerado: {os.path.basename(pdf_path)}")
        except Exception as e:
            status.update(label=f"Erro na comparação/PDF: {e}", state="error")
            st.stop()

        # ---- Concluido ----
        status.update(
            label=f"Processamento concluído! Arquivos salvos em: {DIR_SAIDA}",
            state="complete",
        )

        resumo = f"""
        **Resumo:**
        - VD: {len(vd_map)-len(vd_faltou)}/{len(vd_map)} colunas mapeadas, {len(vd_desc)} descartadas
        - Feminicídio: {len(fem_map)-len(fem_faltou)}/{len(fem_map)} colunas mapeadas, {len(fem_desc)} descartadas
        - Total de registros: VD={len(df_vd):,}, Feminicídio={len(df_fem):,}
        - Parquets salvos em: `processamento/`"""

        if pdf_path and qtde_novos > 0:
            resumo += f"\n- {qtde_novos} novo(s) feminicídio(s) → `{os.path.basename(pdf_path)}`"
        elif qtde_novos == 0:
            resumo += "\n- Nenhum feminicídio novo encontrado"

        st.success(resumo)
