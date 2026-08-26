import streamlit as st
import pandas as pd
import plotly.express as px
from plotting import (plot_barras_sazonal, plot_barras_vulnerabilidade, plot_dia_semana, plot_efetividade_denuncia,
                    plot_faixa_etaria, plot_heatmap_sazonal, plot_heatmap_vulnerabilidade, plot_mapa_geral,
                    plot_por_ano, plot_por_mes, plot_serie_temporal, plot_tipo_crime, plot_barras_feriados)
from utils import (to_csv, to_excel, calcular_tendencia_mensal, calcular_tendencia_mensal_vetorizada,
                   colorir_percentual, formatar_seta_percentual, format_number_br, format_int_br, render_plotly_safe)



def criar_tabela_consolidada(df, coluna_agrupamento, nome_agrupamento, df_original_filtrado=None):
    """Cria uma tabela consolidada com dados de crimes por [agrupamento]."""
    df = df.copy()
    df['ano'] = df['ano'].astype(int)
    df_agrupado = df.groupby([coluna_agrupamento, 'fato_comunicado', 'ano'], observed=True).size().reset_index(name='total_crime')
    df_pivot = df_agrupado.pivot_table(index=[coluna_agrupamento, 'fato_comunicado'], columns='ano',
                                       values='total_crime', fill_value=0, observed=True)

    anos_int = sorted([col for col in df_pivot.columns if isinstance(col, int)])
    ano_corrente = pd.Timestamp.now().year

    df_pivot = df_pivot.reindex(sorted(df_pivot.columns), axis=1)
    df_pivot['total'] = df_pivot.sum(axis=1)

    if len(anos_int) > 1:
        for i in range(1, len(anos_int)):
            ano_atual = anos_int[i]
            if ano_atual == ano_corrente:
                break
            ano_anterior = anos_int[i - 1]
            coluna_evolucao = f'Diferença {ano_anterior}-{ano_atual}'
            df_pivot[coluna_evolucao] = (
                                                (df_pivot[ano_atual] - df_pivot[ano_anterior]) / df_pivot[
                                            ano_anterior].replace(0, pd.NA) * 100
                                        )

    # Tendência via regressão linear mensal vetorizada (usa todos os meses, sem exclusão)
    if df_original_filtrado is not None and not df_original_filtrado.empty:
        serie_tendencias = calcular_tendencia_mensal_vetorizada(
            df_original_filtrado, [coluna_agrupamento, 'fato_comunicado']
        )
        if serie_tendencias.notna().any():
            df_pivot['Tendência (% ao ano)'] = serie_tendencias

    if ano_corrente in df_pivot.columns:
        df_pivot.rename(columns={ano_corrente: f'{ano_corrente} (Parcial)'}, inplace=True)

    ordem_colunas = []
    if anos_int:
        ordem_colunas.append(anos_int[0])
        for i in range(1, len(anos_int)):
            ano_anterior = anos_int[i - 1]
            ano_atual = anos_int[i]

            if ano_atual == ano_corrente:
                ordem_colunas.append(f'{ano_atual} (Parcial)')
            else:
                ordem_colunas.append(ano_atual)

            coluna_evolucao = f'Diferença {ano_anterior}-{ano_atual}'
            if coluna_evolucao in df_pivot.columns:
                ordem_colunas.append(coluna_evolucao)

    ordem_colunas.append('total')
    if 'Tendência (% ao ano)' in df_pivot.columns:
        ordem_colunas.append('Tendência (% ao ano)')

    ordem_final = [col for col in ordem_colunas if col in df_pivot.columns]

    df_pivot.columns = df_pivot.columns.map(str)
    ordem_final = [str(col) for col in ordem_final]

    df_consolidado = df_pivot[ordem_final].reset_index()
    if nome_agrupamento == "Município":
        nome_coluna = "Nome do Município"
    elif "Associação" in nome_agrupamento:
        nome_coluna = "Nome da Associação de Municípios"
    else:
        nome_coluna = nome_agrupamento
    df_consolidado.rename(columns={coluna_agrupamento: nome_coluna, 'fato_comunicado': 'Tipo de Crime'}, inplace=True)

    return df_consolidado


def criar_tabela_total_consolidada(df, df_original_filtrado=None):
    """Cria uma tabela consolidada com o total de crimes por tipo."""
    df = df.copy()
    df['ano'] = df['ano'].astype(int)
    df_agrupado = df.groupby(['fato_comunicado', 'ano'], observed=True).size().reset_index(name='total_crime')
    df_pivot = df_agrupado.pivot_table(index='fato_comunicado', columns='ano', values='total_crime', fill_value=0, observed=True)

    anos_existentes = [col for col in df_pivot.columns if isinstance(col, (int, float))]
    if anos_existentes:
        anos_todos = range(int(min(anos_existentes)), int(max(anos_existentes)) + 1)
        for ano in anos_todos:
            if ano not in df_pivot.columns:
                df_pivot[ano] = 0

    anos_int = sorted([col for col in df_pivot.columns if isinstance(col, int)])
    ano_corrente = pd.Timestamp.now().year

    df_pivot = df_pivot.reindex(sorted(df_pivot.columns), axis=1)
    df_pivot['total'] = df_pivot.sum(axis=1)

    if len(anos_int) > 1:
        for i in range(1, len(anos_int)):
            ano_atual = anos_int[i]
            if ano_atual == ano_corrente:
                break
            ano_anterior = anos_int[i - 1]
            coluna_evolucao = f'Diferença {ano_anterior}-{ano_atual}'
            denominador = df_pivot[ano_anterior].replace(0, pd.NA)
            df_pivot[coluna_evolucao] = (df_pivot[ano_atual] - df_pivot[ano_anterior]) / denominador * 100

    # Tendência via regressão linear mensal vetorizada (usa todos os meses, sem exclusão)
    if df_original_filtrado is not None and not df_original_filtrado.empty:
        serie_tendencias = calcular_tendencia_mensal_vetorizada(
            df_original_filtrado, 'fato_comunicado'
        )
        if serie_tendencias.notna().any():
            df_pivot['Tendência (% ao ano)'] = serie_tendencias

    if ano_corrente in df_pivot.columns:
        df_pivot.rename(columns={ano_corrente: f'{ano_corrente} (Parcial)'}, inplace=True)

    ordem_colunas = []
    if anos_int:
        ordem_colunas.append(anos_int[0])
        for i in range(1, len(anos_int)):
            ano_anterior = anos_int[i - 1]
            ano_atual = anos_int[i]

            if ano_atual == ano_corrente:
                ordem_colunas.append(f'{ano_atual} (Parcial)')
            else:
                ordem_colunas.append(ano_atual)

            coluna_evolucao = f'Diferença {ano_anterior}-{ano_atual}'
            if coluna_evolucao in df_pivot.columns:
                ordem_colunas.append(coluna_evolucao)

    ordem_colunas.append('total')
    if 'Tendência (% ao ano)' in df_pivot.columns:
        ordem_colunas.append('Tendência (% ao ano)')

    ordem_final = [col for col in ordem_colunas if col in df_pivot.columns]

    df_pivot.columns = df_pivot.columns.map(str)
    ordem_final = [str(col) for col in ordem_final]

    df_consolidado = df_pivot[ordem_final].reset_index()
    df_consolidado.rename(columns={'fato_comunicado': 'Tipo de Crime'}, inplace=True)

    return df_consolidado


def criar_tabela_populacional_agrupada(df_crimes, df_pop, df_regioes, agrupamento, num_anos):
    """Cria uma tabela de análise populacional, permitindo o agrupamento por diferentes níveis."""

    if num_anos == 0: num_anos = 1

    df_pop_com_regioes = pd.merge(df_pop, df_regioes.drop(columns='municipio'), on='municipio_normalizado', how='left')

    if agrupamento == "Consolidado":
        total_fatos = df_crimes.shape[0]
        municipios_presentes = df_crimes['municipio_normalizado'].unique()
        pop_filtrada = df_pop_com_regioes[df_pop_com_regioes['municipio_normalizado'].isin(municipios_presentes)]
        total_populacao = pop_filtrada['populacao_feminina'].sum()

        media_anual = total_fatos / num_anos
        taxa = (media_anual / total_populacao) * 1000 if total_populacao > 0 else 0
        percentual = (media_anual / total_populacao) * 100 if total_populacao > 0 else 0

        tabela = pd.DataFrame([{'Localidade': 'Santa Catarina (Filtro Aplicado)', 'População Feminina': total_populacao,
                                'Média Anual de Fatos Ocorridos': media_anual, 'Fatos por Mil Mulheres (anual)': taxa,
                                '% de Mulheres Vítimas (anual)': percentual}])
        return tabela.set_index('Localidade')

    coluna_agrupamento = {
        "Município": "municipio",
        "Mesorregião": "mesoregiao",
        "Associação": "associacao",
        "Associação de Municípios": "associacao"
    }[agrupamento]

    presentes = [p for p in df_crimes[coluna_agrupamento].dropna().unique() if str(p).strip() not in ['', 'Não informado']]
    crimes_series = df_crimes[coluna_agrupamento].value_counts()
    crimes_series = crimes_series[crimes_series.index.isin(presentes) & (crimes_series > 0)]
    crimes_agrupado = crimes_series.reset_index()
    crimes_agrupado.columns = [coluna_agrupamento, 'total_fatos']

    if agrupamento == "Município":
        pop_agrupada = df_pop_com_regioes[df_pop_com_regioes[coluna_agrupamento].isin(presentes)][[coluna_agrupamento, 'populacao_feminina']].drop_duplicates(subset=[coluna_agrupamento])
    else:
        df_pop_sub = df_pop_com_regioes[df_pop_com_regioes[coluna_agrupamento].isin(presentes)]
        pop_agrupada = df_pop_sub.groupby(coluna_agrupamento, observed=True)['populacao_feminina'].sum().reset_index()

    df_agregado = pd.merge(crimes_agrupado, pop_agrupada, on=coluna_agrupamento, how='left')

    df_agregado['media_anual_fatos'] = df_agregado['total_fatos'] / num_anos
    df_agregado['taxa_por_mil_mulheres'] = (
        (df_agregado['media_anual_fatos'] / df_agregado['populacao_feminina'].replace(0, pd.NA)) * 1000
    ).fillna(0)
    df_agregado['percentual_mulheres_vitimas'] = (
        (df_agregado['media_anual_fatos'] / df_agregado['populacao_feminina'].replace(0, pd.NA)) * 100
    ).fillna(0)

    tabela_final = df_agregado.rename(columns={
        coluna_agrupamento: agrupamento,
        'populacao_feminina': 'População Feminina',
        'media_anual_fatos': 'Média Anual de Fatos Ocorridos',
        'taxa_por_mil_mulheres': 'Fatos por Mil Mulheres (anual)',
        'percentual_mulheres_vitimas': '% de Mulheres Vítimas (anual)'
    })

    return tabela_final[
        [agrupamento, 'População Feminina', 'Média Anual de Fatos Ocorridos', 'Fatos por Mil Mulheres (anual)',
         '% de Mulheres Vítimas (anual)']].set_index(agrupamento)

def render(df_geral_filtrado, df_feminicidio_filtrado, df_populacao, df_regioes, df_calendario, geojson_sc):
  try:
    st.header("Violência contra a Mulher em Santa Catarina")
    st.markdown(
        "Visão geral dos registros de ocorrências de violência com a mulher no âmbito doméstico (Lei Maria da Penha), no Estado de Santa Catarina.")

    # --- (BLOCOS INTELIGENTES DE CONTEXTO MOVIDOS PARA O HEADER) ---

    total_registros = df_geral_filtrado.shape[0]
    
    media_idade_vitima = 0.0
    if not df_geral_filtrado.empty and df_geral_filtrado['idade_vitima'].notna().any():
        media_idade_vitima = df_geral_filtrado['idade_vitima'].mean()

    num_dias = (st.session_state.data_final - st.session_state.data_inicial).days + 1
    crimes_por_dia = total_registros / num_dias if num_dias > 0 else 0
    crimes_por_hora = total_registros / (num_dias * 24) if num_dias > 0 else 0

    if not df_geral_filtrado.empty:
        ocorrencias_fds = df_geral_filtrado[
            df_geral_filtrado['data_fato'].dt.dayofweek.isin([5, 6])
        ].shape[0]
        pct_fds = (ocorrencias_fds / total_registros * 100) if total_registros > 0 else 0
    else:
        pct_fds = 0

    # Tendência via regressão linear mensal (todos os meses, sem exclusão)
    tem_cagr = False
    delta_cagr = "N/A"
    icone_cagr = ""
    
    tendencia = calcular_tendencia_mensal(df_geral_filtrado)
    if pd.notna(tendencia):
        tem_cagr = True
        delta_cagr = f"{tendencia:.1f}% ao ano"
        icone_cagr = "📈" if tendencia > 0 else "📉"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Total de Registros", value=f"{total_registros:,}".replace(",", "."))
        st.metric(label="Média de Crimes por Dia", value=f"{crimes_por_dia:.1f}")

    with col2:
        if tem_cagr:
            st.metric(label=f"Tendência {icone_cagr}", value=delta_cagr,
                      help="Tendência anual calculada por regressão linear sobre todos os meses do período.")
        else:
            st.metric(label="Média de Crimes por Hora", value=f"{crimes_por_hora:.2f}")
            
        if tem_cagr:
             st.metric(label="Média de Crimes por Hora", value=f"{crimes_por_hora:.2f}")
        else:
             st.metric(label="Idade Média da Vítima", value=f"{media_idade_vitima:.1f} anos")

    with col3:
        if tem_cagr:
            st.metric(label="Idade Média da Vítima", value=f"{media_idade_vitima:.1f} anos")
            st.metric(label="% em Fins de Semana", value=f"{pct_fds:.1f}%",
                      help="Percentual de crimes ocorridos aos sábados e domingos.")
        else:
            st.metric(label="% em Fins de Semana", value=f"{pct_fds:.1f}%",
                      help="Percentual de crimes ocorridos aos sábados e domingos.")
            st.write("") 

    st.markdown("---")

    st.subheader(f"Distribuição Geográfica das Ocorrências por {st.session_state.agrupamento_selecionado}")
    with st.expander("Como interpretar este mapa?"):
        st.info(
            """
            - **O que mostra:** A concentração de ocorrências no território catarinense.
            - **Como ler:** Tons mais escuros indicam uma maior concentração de registros (seja em número absoluto ou em taxas por população).
            - **Interatividade:** Passe o mouse sobre uma localidade para ver os detalhes. Use os botões acima para alternar entre a visualização de números totais e as taxas por mil mulheres.
            """
        )
    if 'map_view_type' not in st.session_state:
        st.session_state.map_view_type = 'Soma dos Crimes'

    def set_map_view(view_type):
        st.session_state.map_view_type = view_type

    st.markdown("""
    <style>
        div[data-testid="stButton"] > button[kind="secondary"] { background-color: #ab47bc; color: rgba(255, 255, 255, 0.6); border: none; box-shadow: none; font-weight: 600; transition: all 0.2s ease-in-out; }
        div[data-testid="stButton"] > button[kind="secondary"]:hover { background-color: #9c27b0; color: rgba(255, 255, 255, 0.9); }
        div[data-testid="stButton"] > button[kind="primary"] { background: linear-gradient(135deg, #8e24aa 0%, #ab47bc 100%); color: white; border: none; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15); font-weight: 600; }
        div[data-testid="stButton"] > button:focus { box-shadow: 0 0 0 3px rgba(142, 36, 170, 0.5) !important; outline: none !important; }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.button(label="Soma dos Crimes", on_click=set_map_view, args=('Soma dos Crimes',), use_container_width=True,
                  type="primary" if st.session_state.map_view_type == 'Soma dos Crimes' else "secondary")
    with col2:
        st.button(label="Crimes por Mil Mulheres", on_click=set_map_view, args=('Crimes por Mil Mulheres',),
                  use_container_width=True,
                  type="primary" if st.session_state.map_view_type == 'Crimes por Mil Mulheres' else "secondary")
    with col3:
        st.button(label="% de Mulheres Vítimas", on_click=set_map_view, args=('% de Mulheres Vítimas',),
                  use_container_width=True,
                  type="primary" if st.session_state.map_view_type == '% de Mulheres Vítimas' else "secondary")

    view_type = st.session_state.map_view_type
    color_col, label_text = ('quantidade', f'Total de Registros ({st.session_state.agrupamento_selecionado})') if view_type == "Soma dos Crimes" else \
        ('taxa_por_mil_mulheres',
         f'Crimes por Mil Mulheres ({st.session_state.agrupamento_selecionado})') if view_type == "Crimes por Mil Mulheres" else \
            ('percentual_mulheres_vitimas', f'% de Mulheres Vítimas ({st.session_state.agrupamento_selecionado})')

    base_map_df = df_geral_filtrado['municipio_normalizado'].value_counts().reset_index()
    base_map_df.columns = ['municipio_normalizado', 'total_fatos']

    if view_type != "Soma dos Crimes":
        base_map_df = pd.merge(base_map_df, df_populacao, on='municipio_normalizado', how='left')
        base_map_df.dropna(subset=['populacao_feminina'], inplace=True)
        anos_no_filtro = df_geral_filtrado['ano'].unique()
        num_anos = len(anos_no_filtro) if len(anos_no_filtro) > 0 else 1
        base_map_df['media_anual_fatos'] = base_map_df['total_fatos'] / num_anos
        if view_type == "Crimes por Mil Mulheres":
            base_map_df[color_col] = (
                                                 (base_map_df['media_anual_fatos'] / base_map_df[
                                                     'populacao_feminina']) * 1000).fillna(
                0)
        else:
            base_map_df[color_col] = (
                                                 (base_map_df['media_anual_fatos'] / base_map_df[
                                                     'populacao_feminina']) * 100).fillna(
                0)
    else:
        base_map_df.rename(columns={'total_fatos': color_col}, inplace=True)

    # --- LÓGICA DO MAPA COM MERGE DE REGIÕES ---
    cols_regiao = df_regioes[['municipio_normalizado', 'mesoregiao', 'associacao']]

    if st.session_state.agrupamento_selecionado == "Município" or st.session_state.agrupamento_selecionado == "Consolidado":
        map_df = pd.merge(base_map_df, cols_regiao, on='municipio_normalizado', how='left')
        map_df = map_df[['municipio_normalizado', color_col, 'mesoregiao', 'associacao']]
    else:
        agrupamento_col = "mesoregiao" if st.session_state.agrupamento_selecionado == "Mesorregião" else "associacao"
        municipio_grupo_mapping = df_geral_filtrado[
            ['municipio_normalizado', agrupamento_col]].drop_duplicates()
        df_with_groups = pd.merge(base_map_df, municipio_grupo_mapping, on='municipio_normalizado', how='left')
        if view_type == "Soma dos Crimes":
            crimes_por_grupo = df_with_groups.groupby(agrupamento_col, observed=True)[color_col].sum().reset_index()
            map_df = pd.merge(municipio_grupo_mapping, crimes_por_grupo, on=agrupamento_col, how='left')
            colunas_num_map = map_df.select_dtypes(include=['number']).columns
            map_df[colunas_num_map] = map_df[colunas_num_map].fillna(0)
        else:
            grouped_pop = df_with_groups.groupby(agrupamento_col, observed=True).agg(
                total_fatos_grupo=('total_fatos', 'sum'),
                populacao_feminina_grupo=('populacao_feminina', 'sum')).reset_index()
            anos_no_filtro = df_geral_filtrado['ano'].unique()
            num_anos = len(anos_no_filtro) if len(anos_no_filtro) > 0 else 1
            grouped_pop['media_anual_grupo'] = grouped_pop['total_fatos_grupo'] / num_anos
            if view_type == "Crimes por Mil Mulheres":
                grouped_pop[color_col] = (
                                                     (grouped_pop['media_anual_grupo'] / grouped_pop[
                                                         'populacao_feminina_grupo']) * 1000).fillna(
                    0)
            else:
                grouped_pop[color_col] = (
                                                     (grouped_pop['media_anual_grupo'] / grouped_pop[
                                                         'populacao_feminina_grupo']) * 100).fillna(
                    0)
            map_df = pd.merge(municipio_grupo_mapping, grouped_pop[[agrupamento_col, color_col]], on=agrupamento_col,
                              how='left')
            colunas_num_map2 = map_df.select_dtypes(include=['number']).columns
            map_df[colunas_num_map2] = map_df[colunas_num_map2].fillna(0)
        
        map_df = pd.merge(map_df, cols_regiao, on='municipio_normalizado', how='left', suffixes=('', '_y'))
        
        if 'mesoregiao_y' in map_df.columns: 
            map_df['mesoregiao'] = map_df['mesoregiao'].fillna(map_df['mesoregiao_y'])
            del map_df['mesoregiao_y']
        if 'associacao_y' in map_df.columns:
            map_df['associacao'] = map_df['associacao'].fillna(map_df['associacao_y'])
            del map_df['associacao_y']

    if not map_df.empty:
        map_df['mesoregiao'] = map_df['mesoregiao'].fillna('Indefinido')
        map_df['associacao'] = map_df['associacao'].fillna('Indefinido')
        map_df = map_df[
            map_df['municipio_normalizado'].isin(df_geral_filtrado['municipio_normalizado'].unique())]

        fig_mapa = plot_mapa_geral(map_df, geojson_sc, color_col, label_text,
                                   st.session_state.agrupamento_selecionado)
        render_plotly_safe(fig_mapa, use_container_width=True, key="mapa_geral")
    else:
        st.info("Não há dados de ocorrências para exibir no mapa com os filtros selecionados.")
    st.markdown("---")


    st.subheader("Série Histórica de Ocorrências")
    chart_type_temporal = st.selectbox("Tipo de Gráfico", ("Linha", "Área", "Barras"), key="chart_type_temporal")
    df_temporal = df_geral_filtrado.copy()
    df_temporal['ano_mes'] = df_temporal['data_fato'].dt.to_period('M').astype(str)
    if st.session_state.agrupamento_selecionado == "Consolidado":
        registros_por_mes_ano = df_temporal.groupby('ano_mes', observed=True).size().reset_index(name='quantidade').sort_values(
            'ano_mes')
        color_param_temporal = None
    else:
        mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
        coluna_agrupamento = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
        registros_por_mes_ano = df_temporal.groupby(['ano_mes', coluna_agrupamento], observed=True).size().reset_index(
            name='quantidade').sort_values('ano_mes')
        color_param_temporal = coluna_agrupamento

    if not registros_por_mes_ano.empty:
        fig_temporal = plot_serie_temporal(registros_por_mes_ano, chart_type_temporal,
                                           st.session_state.agrupamento_selecionado, color_param_temporal)
        render_plotly_safe(fig_temporal, use_container_width=True, key="temporal_geral")
    else:
        st.info("Não há dados suficientes para exibir a série histórica.")
    st.markdown("---")


    st.subheader("Distribuição de Ocorrências por Dia da Semana")
    chart_type_dia_semana = st.selectbox("Tipo de Gráfico", ("Barras", "Pizza", "Linha", "Área"),
                                         key="chart_type_dia_semana")
    df_dia = df_geral_filtrado.copy()
    df_dia['dia_semana'] = df_dia['data_fato'].dt.day_name()
    dias_ordem = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    df_dia['dia_semana_cat'] = pd.Categorical(
        df_dia['dia_semana'],
        categories=dias_ordem, ordered=True)
    registros_por_dia = df_dia['dia_semana_cat'].value_counts().sort_index().reset_index()
    registros_por_dia.columns = ['Dia da Semana', 'Quantidade']
    nomes_dias_pt = {'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
                     'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
    registros_por_dia['Dia da Semana'] = registros_por_dia['Dia da Semana'].map(nomes_dias_pt)

    if not registros_por_dia.dropna(subset=['Quantidade']).empty and registros_por_dia['Quantidade'].sum() > 0:
        fig_dia_semana = plot_dia_semana(registros_por_dia, chart_type_dia_semana)
        render_plotly_safe(fig_dia_semana, use_container_width=True, key="dia_semana_geral")
    else:
        st.info("Não há dados suficientes para exibir a distribuição por dia da semana.")
    st.markdown("---")

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
    
        st.subheader("Registros de Ocorrências por Ano")
        chart_type_ano = st.selectbox("Tipo de Gráfico", ("Barras", "Pizza", "Linha", "Área"), key="chart_type_ano")

        ano_corrente = pd.Timestamp.now().year
        if st.session_state.agrupamento_selecionado == "Consolidado":
            registros_por_ano = df_geral_filtrado['ano'].value_counts().sort_index().reset_index()
            registros_por_ano.columns = ['ano', 'Quantidade']
            color_param = None
        else:
            mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            coluna_agrupamento = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
            registros_por_ano = df_geral_filtrado.groupby(['ano', coluna_agrupamento], observed=True).size().reset_index(
                name='Quantidade')
            color_param = coluna_agrupamento

        if not registros_por_ano.empty:
            registros_por_ano['ano'] = registros_por_ano['ano'].apply(
                lambda x: f'{x} (Parcial)' if x == ano_corrente else str(x)
            )
            fig_ano = plot_por_ano(registros_por_ano, chart_type_ano, st.session_state.agrupamento_selecionado, color_param)
            render_plotly_safe(fig_ano, use_container_width=True, key="ano_geral")
        else:
            st.info("Não há dados de ocorrências por ano.")

    with col_graf2:
    
        st.subheader("Distribuição de Ocorrências por Mês")
        chart_type_mes = st.selectbox("Tipo de Gráfico", ("Pizza", "Barras", "Linha", "Área"), key="chart_type_mes")
        meses_ordem = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                       'October', 'November', 'December']
        df_mes = df_geral_filtrado.copy()
        df_mes['mes_cat'] = pd.Categorical(df_mes['mes'],
                                                                        categories=meses_ordem, ordered=True)
        registros_por_mes = df_mes['mes_cat'].value_counts().sort_index().reset_index()
        registros_por_mes.columns = ['Mês', 'Quantidade']
        nomes_meses_pt = {'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março', 'April': 'Abril',
                          'May': 'Maio', 'June': 'Junho', 'July': 'Julho', 'August': 'Agosto',
                          'September': 'Setembro', 'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'}
        registros_por_mes['Mês'] = registros_por_mes['Mês'].map(nomes_meses_pt)

        if not registros_por_mes.dropna(subset=['Quantidade']).empty and registros_por_mes['Quantidade'].sum() > 0:
            fig_mes = plot_por_mes(registros_por_mes, chart_type_mes)
            render_plotly_safe(fig_mes, use_container_width=True, key="mes_geral")
        else:
            st.info("Não há dados de ocorrências por mês.")

    st.markdown("---")

    col_graf3, col_graf4 = st.columns(2)
    with col_graf3:
    
        st.subheader("Distribuição por Faixa Etária da Vítima")
        chart_type_faixa_etaria = st.selectbox("Tipo de Gráfico", ("Barras", "Pizza"), key="chart_type_faixa_etaria")
        df_faixa_etaria = df_geral_filtrado.dropna(subset=['idade_vitima']).copy()
        bins = [0, 12, 17, 29, 40, 50, 60, 70, 79, 120]
        labels = ['0-12 anos', '13-17 anos', '18-29 anos', '30-40 anos', '41-50 anos', '51-60 anos', '61-70 anos',
                  '71-79 anos', '80+ anos']
        df_faixa_etaria['faixa_etaria'] = pd.cut(df_faixa_etaria['idade_vitima'], bins=bins, labels=labels,
                                                right=True)
        registros_por_faixa = df_faixa_etaria['faixa_etaria'].value_counts().sort_index().reset_index()
        registros_por_faixa.columns = ['Faixa Etária', 'Quantidade']

        if not registros_por_faixa.dropna(subset=['Quantidade']).empty and registros_por_faixa['Quantidade'].sum() > 0:
            fig_faixa_etaria = plot_faixa_etaria(registros_por_faixa, chart_type_faixa_etaria)
            render_plotly_safe(fig_faixa_etaria, use_container_width=True, key="faixa_etaria_geral")
        else:
            st.info("Não há dados de faixa etária para exibir.")

    with col_graf4:
    
        st.subheader("Natureza das Ocorrências Mais Frequentes")
        chart_type_fato = st.selectbox("Tipo de Gráfico", ("Barras", "Pizza"), key="chart_type_fato")
        if st.session_state.agrupamento_selecionado == "Consolidado":
            registros_por_fato = df_geral_filtrado['fato_comunicado'].value_counts().reset_index()
            registros_por_fato.columns = ['fato_comunicado', 'Quantidade']
            color_param = None
        else:
            mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            coluna_agrupamento = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
            registros_por_fato = df_geral_filtrado.groupby(
                ['fato_comunicado', coluna_agrupamento], observed=True).size().reset_index(name='Quantidade')
            color_param = coluna_agrupamento

        if not registros_por_fato.empty:
            fig_fato = plot_tipo_crime(registros_por_fato, chart_type_fato, st.session_state.agrupamento_selecionado,
                                       color_param)
            render_plotly_safe(fig_fato, use_container_width=True, key="fato_geral")
        else:
            st.info("Não há dados de natureza das ocorrências para exibir.")

    st.markdown("---")

    if st.session_state.agrupamento_selecionado != "Consolidado":
    
        mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
        coluna_agrupamento_tabela = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
        st.subheader(f"Tabela Consolidada de Ocorrências por {st.session_state.agrupamento_selecionado}")
        with st.expander("Como interpretar esta tabela?"):
            st.info(
                """
                - **O que mostra:** Um detalhamento anual do número de ocorrências por tipo de crime e localidade.
                - **Colunas de Diferença:** Mostram a variação percentual (aumento ou queda) de um ano para o outro.
                - **Tendência (% ao ano):** Indica a tendência de longo prazo calculada por regressão linear sobre todos os meses do período selecionado. Um valor positivo indica crescimento; negativo, queda.
                """
            )
        if not df_geral_filtrado.empty:
            tabela_consolidada = criar_tabela_consolidada(df_geral_filtrado,
                                                          coluna_agrupamento_tabela,
                                                          st.session_state.agrupamento_selecionado,
                                                          df_original_filtrado=df_geral_filtrado)
            if not tabela_consolidada.empty:
                st.markdown("##### Exportar Dados da Tabela")
                col1_export, col2_export = st.columns(2)  
                with col1_export:
                    st.download_button(
                        label="📥 Exportar para CSV",
                        data=to_csv(tabela_consolidada),
                        file_name=f'ocorrencias_por_{st.session_state.agrupamento_selecionado}.csv',
                        mime='text/csv',
                        key='csv_consolidada_geral'
                    )
                with col2_export:
                    st.download_button(
                        label="📥 Exportar para Excel",
                        data=to_excel(tabela_consolidada),
                        file_name=f'ocorrencias_por_{st.session_state.agrupamento_selecionado}.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        key='excel_consolidada_geral'
                    )

                colunas_evolucao = [col for col in tabela_consolidada.columns if 'Diferença' in str(col)]
                format_dict = {col: formatar_seta_percentual for col in colunas_evolucao}

                ano_corrente_parcial = f'{pd.Timestamp.now().year} (Parcial)'
                colunas_de_anos = [col for col in tabela_consolidada.columns if col.isdigit() and len(col) == 4]
                if ano_corrente_parcial in tabela_consolidada.columns:
                    colunas_de_anos.append(ano_corrente_parcial)

                for col in colunas_de_anos:
                    format_dict[col] = format_int_br
                format_dict['total'] = format_int_br

                if 'Tendência (% ao ano)' in tabela_consolidada.columns:
                    format_dict['Tendência (% ao ano)'] = '{:+.1f}%'

                colunas_para_colorir = colunas_evolucao[:]
                if 'Tendência (% ao ano)' in tabela_consolidada.columns:
                    colunas_para_colorir.append('Tendência (% ao ano)')

                styler = tabela_consolidada.style.map(colorir_percentual, subset=colunas_para_colorir).format(
                    format_dict)
                st.dataframe(styler, use_container_width=True, hide_index=True)
            else:
                st.warning("Não há dados para exibir na tabela consolidada com os filtros selecionados.")
        else:
            st.warning("Não há dados para exibir na tabela consolidada com os filtros selecionados.")
    else:
    
        st.subheader("Tabela Consolidada de Ocorrências (Total SC)")
        with st.expander("Como interpretar esta tabela?"):
            st.info(
                """
                - **O que mostra:** Um detalhamento anual do número de ocorrências por tipo de crime para todo o estado (considerando os filtros aplicados).
                - **Colunas de Diferença:** Mostram a variação percentual (aumento ou queda) de um ano para o outro.
                - **Tendência (% ao ano):** Indica a tendência de longo prazo calculada por regressão linear sobre todos os meses do período selecionado. Um valor positivo indica crescimento; negativo, queda.
                """
            )
        if not df_geral_filtrado.empty:
            tabela_total = criar_tabela_total_consolidada(df_geral_filtrado,
                                                          df_original_filtrado=df_geral_filtrado)
            if not tabela_total.empty:
                st.markdown("##### Exportar Dados da Tabela")
                col1_export, col2_export = st.columns(2)  
                with col1_export:
                    st.download_button(
                        label="📥 Exportar para CSV",
                        data=to_csv(tabela_total),
                        file_name='ocorrencias_consolidadas_sc.csv',
                        mime='text/csv',
                        key='csv_total_geral'
                    )
                with col2_export:
                    st.download_button(
                        label="📥 Exportar para Excel",
                        data=to_excel(tabela_total),
                        file_name='ocorrencias_consolidadas_sc.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        key='excel_total_geral'
                    )

                colunas_evolucao = [col for col in tabela_total.columns if 'Diferença' in str(col)]
                format_dict = {col: formatar_seta_percentual for col in colunas_evolucao}

                ano_corrente_parcial = f'{pd.Timestamp.now().year} (Parcial)'
                colunas_de_anos = [col for col in tabela_total.columns if (str(col).isdigit() and len(str(col)) == 4) or 'Parcial' in str(col)]
                
                for col in colunas_de_anos:
                    format_dict[col] = format_int_br
                if 'total' in tabela_total.columns:
                    format_dict['total'] = format_int_br

                if 'Tendência (% ao ano)' in tabela_total.columns:
                    format_dict['Tendência (% ao ano)'] = '{:+.1f}%'

                colunas_para_colorir = colunas_evolucao[:]
                if 'Tendência (% ao ano)' in tabela_total.columns:
                    colunas_para_colorir.append('Tendência (% ao ano)')

                styler = tabela_total.style.map(colorir_percentual, subset=colunas_para_colorir).format(format_dict)
                st.dataframe(styler, use_container_width=True, hide_index=True)
            else:
                st.warning("Não há dados para exibir na tabela consolidada com os filtros selecionados.")
        else:
            st.warning("Não há dados para exibir na tabela consolidada com os filtros selecionados.")

    st.markdown("---")


    st.subheader("Taxa de Ocorrências por População Feminina ")
    with st.expander("Como interpretar esta tabela?"):
        st.info(
            """
            - **O que mostra:** Esta tabela ajusta os números absolutos de crimes pela população feminina de cada localidade, permitindo uma comparação mais justa entre locais de tamanhos diferentes.
            - **Fatos por Mil Mulheres:** Indica quantas mulheres, em um grupo de mil, foram vítimas em média por ano. É a principal métrica para comparar o risco entre diferentes localidades.
            - **% de Mulheres Vítimas:** Mostra a porcentagem da população feminina total que foi vítima em média por ano.
            """
        )
    anos_no_filtro = df_geral_filtrado['ano'].unique()
    num_anos = len(anos_no_filtro) if len(anos_no_filtro) > 0 else 1
    tabela_populacional = criar_tabela_populacional_agrupada(df_geral_filtrado,
                                                            df_populacao,
                                                            df_regioes,
                                                            st.session_state.agrupamento_selecionado, num_anos)

    if not tabela_populacional.empty:
        df_para_exportar_pop = tabela_populacional.reset_index()
        st.markdown("##### Exportar Dados da Tabela")
        col1_export_pop, col2_export_pop = st.columns(2)  
        with col1_export_pop:
            st.download_button(
                label="📥 Exportar para CSV",
                data=to_csv(df_para_exportar_pop),
                file_name=f'taxa_populacional_{st.session_state.agrupamento_selecionado}.csv',
                mime='text/csv',
                key='csv_populacional'
            )
        with col2_export_pop:
            st.download_button(
                label="📥 Exportar para Excel",
                data=to_excel(df_para_exportar_pop),
                file_name=f'taxa_populacional_{st.session_state.agrupamento_selecionado}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                key='excel_populacional'
            )

    st.dataframe(tabela_populacional.style.format(
        {'Média Anual de Fatos Ocorridos': '{:.2f}', 'Fatos por Mil Mulheres (anual)': '{:.2f}',
         '% de Mulheres Vítimas (anual)': '{:.2f}%', 'População Feminina': '{:,.0f}',
         'Tendência (% ao ano)': '{:+.1f}%'}), use_container_width=True)

    st.markdown("---")


    st.header("Análise de Vulnerabilidade por Faixa Etária e Tipo de Crime")

    st.subheader("Visualização da Distribuição de Crimes por Faixa Etária")
    with st.expander("Como interpretar este gráfico?"):
        st.info(
            """
            - **O que mostra:** A proporção de cada tipo de crime dentro de uma mesma faixa etária.
            - **Como ler:** Cada barra representa 100% das ocorrências para aquela faixa etária. As cores mostram qual a porcentagem de cada tipo de crime.
            - **Utilidade:** Permite ver, por exemplo, se a ameaça é mais comum entre jovens e a lesão corporal entre mulheres mais velhas, indicando como a natureza da violência evolui com a idade.
            """
        )
    df_vulnerabilidade = df_geral_filtrado.dropna(subset=['idade_vitima']).copy()
    bins = [0, 12, 17, 29, 40, 50, 60, 70, 79, 120]
    labels = ['0-12 anos', '13-17 anos', '18-29 anos', '30-40 anos', '41-50 anos', '51-60 anos', '61-70 anos',
                '71-79 anos', '80+ anos']
    df_vulnerabilidade['faixa_etaria'] = pd.cut(df_vulnerabilidade['idade_vitima'], bins=bins, labels=labels,
                                                right=True)

    if not df_vulnerabilidade.empty:
        crime_counts = df_vulnerabilidade.groupby(['faixa_etaria', 'fato_comunicado'],
                                                    observed=False).size().unstack(fill_value=0)
        crime_percentages = crime_counts.div(crime_counts.sum(axis=1), axis=0) * 100
        crime_percentages = crime_percentages.reset_index()
        df_plot = crime_percentages.melt(id_vars='faixa_etaria', var_name='fato_comunicado', value_name='percentual')

        fig_barras_vulnerabilidade = plot_barras_vulnerabilidade(df_plot)
        render_plotly_safe(fig_barras_vulnerabilidade, use_container_width=True, key="barras_vulnerabilidade")
    else:
        st.warning("Não há dados suficientes para gerar o gráfico de vulnerabilidade com os filtros selecionados.")

    st.markdown("---")


    st.subheader("Análise de Concentração: Heatmap de Crimes por Faixa Etária")
    st.markdown(
        "O heatmap abaixo mostra a concentração de tipos de crime em cada faixa etária. A cor mais forte identifica a faixa etária com maior incidência daquele crime específico.")

    if not df_vulnerabilidade.empty:
        crime_counts_heatmap = df_vulnerabilidade.groupby(['faixa_etaria', 'fato_comunicado'],
                                                            observed=False).size().unstack(fill_value=0)
        
        fig_heatmap = plot_heatmap_vulnerabilidade(crime_counts_heatmap)
        
        fig_heatmap.update_layout(
            xaxis=dict(tickangle=45), 
            margin=dict(b=100)        
        )
        
        render_plotly_safe(fig_heatmap, use_container_width=True, key="heatmap_vulnerabilidade")
    else:
        st.warning("Não há dados suficientes para gerar o heatmap com os filtros selecionados.")
    
    st.markdown("---")


    st.header("Índice de Efetividade da Denúncia")
    st.markdown("""
    **Em um município, um alto número de denúncias de crimes "menores" (como ameaça) está correlacionado a um menor número de crimes graves (lesão corporal, feminicídio)? Ou seja, a denúncia está funcionando como um mecanismo de prevenção eficaz?** Este é um proxy para medir a efetividade da resposta do sistema de segurança e apoio. Um sistema eficaz deveria intervir após a primeira denúncia, impedindo a escalada da violência.
    """)

    crimes_leves = ["Ameaça", "Vias de fato"]
    crimes_graves = ["Lesão corporal leve - Dolosa", "Lesão corporal grave ou gravíssima - Dolosa", "Estupro", "Feminicídio"]

    if not df_geral_filtrado.empty and not df_populacao.empty:
        anos_no_filtro = df_geral_filtrado['ano'].unique()
        num_anos = len(anos_no_filtro) if len(anos_no_filtro) > 0 else 1

        df_leves = df_geral_filtrado[
            df_geral_filtrado['fato_comunicado'].isin(crimes_leves)]
        contagem_leves = df_leves.groupby('municipio_normalizado', observed=True).size().reset_index(name='total_crimes_leves')
        
        df_graves = df_geral_filtrado[
            df_geral_filtrado['fato_comunicado'].isin(crimes_graves)]
        contagem_graves = df_graves.groupby('municipio_normalizado', observed=True).size().reset_index(name='total_crimes_graves')
        
        df_efetividade = pd.merge(contagem_leves, contagem_graves, on='municipio_normalizado',
                                    how='outer')
        colunas_num = df_efetividade.select_dtypes(include=['number']).columns
        df_efetividade[colunas_num] = df_efetividade[colunas_num].fillna(0)
        df_efetividade = pd.merge(df_efetividade,
                                    df_populacao[
                                        ['municipio_normalizado', 'municipio', 'populacao_feminina']],
                                    on='municipio_normalizado', how='left')
        
        df_efetividade.dropna(subset=['populacao_feminina', 'municipio'], inplace=True)
        df_efetividade = df_efetividade[df_efetividade['populacao_feminina'] > 0]

        df_efetividade['media_anual_leves'] = df_efetividade['total_crimes_leves'] / num_anos
        df_efetividade['media_anual_graves'] = df_efetividade['total_crimes_graves'] / num_anos

        df_efetividade['taxa_crimes_leves'] = (df_efetividade['media_anual_leves'] / df_efetividade[
            'populacao_feminina']) * 1000
        df_efetividade['taxa_crimes_graves'] = (df_efetividade['media_anual_graves'] / df_efetividade[
            'populacao_feminina']) * 1000

        with st.expander("Como interpretar este gráfico?"):
            st.markdown("""
            - **O que mostra:** A relação entre a taxa média anual de crimes considerados "leves" (como ameaça) e a taxa média anual de crimes "graves" (como lesão corporal) em cada município. Cada ponto é um município.
            - **Linha de Tendência:** A linha tracejada mostra a tendência geral.
            - **Correlação Negativa (linha desce):** Cenário Ideal. Municípios onde as mulheres denunciam mais os crimes leves tendem a ter menos crimes graves. Isso sugere que a denúncia e a intervenção precoce estão funcionando.
            - **Correlação Positiva (linha sobe):** Pior Cenário. Municípios com muitas denúncias leves também têm muitos crimes graves. Isso pode indicar um sistema que apenas registra as ocorrências, mas falha em proteger a vítima e impedir a escalada da violência.            
            - **Pontos Fora da Tendência:** Municípios que estão muito acima ou abaixo da linha de tendência merecem atenção especial. Acima da linha pode indicar falhas no sistema de proteção, enquanto abaixo pode indicar boas práticas que poderiam ser replicadas.""")
            
        fig_efetividade = plot_efetividade_denuncia(df_efetividade)
        render_plotly_safe(fig_efetividade, use_container_width=True, key="scatter_efetividade")

    else:
        st.warning("Não há dados suficientes para gerar a análise de efetividade com os filtros selecionados.")
    
    st.markdown("---")


    st.header("Sazonalidade e Eventos-Chave: O Calendário do Risco")
    st.markdown("""
    A violência contra a mulher aumenta de forma previsível em torno de datas ou eventos específicos (feriados, fins de semana prolongados, períodos de férias)?
    """)

    df_geral_filtrado_sazonal = df_geral_filtrado.copy()
    df_geral_filtrado_sazonal['dia_semana'] = df_geral_filtrado_sazonal['data_fato'].dt.day_name()
    df_geral_filtrado_sazonal['mes'] = df_geral_filtrado_sazonal['data_fato'].dt.month_name()

    if not df_geral_filtrado_sazonal.empty:
        df_geral_filtrado_sazonal['data_fato_date'] = df_geral_filtrado_sazonal['data_fato'].dt.date
        calendario_merge = df_calendario.copy()
        calendario_merge['data_fato_date'] = calendario_merge['data'].dt.date
        df_geral_filtrado_sazonal = pd.merge(df_geral_filtrado_sazonal,
                                                calendario_merge[
                                                    ['data_fato_date', 'is_feriado', 'is_fim_de_semana',
                                                    'is_vespera_feriado', 'is_pos_feriado', 'nome_feriado']],
                                                on='data_fato_date', how='left')
        df_geral_filtrado_sazonal[
            ['is_feriado', 'is_vespera_feriado', 'is_pos_feriado']] = df_geral_filtrado_sazonal[
            ['is_feriado', 'is_vespera_feriado', 'is_pos_feriado']].fillna(False)
        df_periodo_completo = pd.DataFrame(
            pd.date_range(start=st.session_state.data_inicial, end=st.session_state.data_final),
            columns=['data'])
        df_periodo_completo['data_fato_date'] = df_periodo_completo['data'].dt.date
        df_periodo_completo_com_eventos = pd.merge(df_periodo_completo,
                                                    calendario_merge[
                                                        ['data_fato_date', 'is_feriado', 'is_fim_de_semana',
                                                        'is_vespera_feriado', 'is_pos_feriado']],
                                                    on='data_fato_date', how='left').fillna(False)
        total_dias_feriado = df_periodo_completo_com_eventos['is_feriado'].sum()
        total_dias_vespera = df_periodo_completo_com_eventos['is_vespera_feriado'].sum()
        total_dias_pos = df_periodo_completo_com_eventos['is_pos_feriado'].sum()
        total_dias_fds = df_periodo_completo_com_eventos['is_fim_de_semana'].sum()
        total_dias_uteis_comuns = len(df_periodo_completo_com_eventos[
                                            (df_periodo_completo_com_eventos['is_feriado'] == False) & (
                                                    df_periodo_completo_com_eventos[
                                                        'is_fim_de_semana'] == False) & (
                                                    df_periodo_completo_com_eventos[
                                                        'is_vespera_feriado'] == False) & (
                                                    df_periodo_completo_com_eventos[
                                                        'is_pos_feriado'] == False)])
        ocorrencias_feriado, ocorrencias_vespera, ocorrencias_pos, ocorrencias_fds = \
            df_geral_filtrado_sazonal[
                'is_feriado'].sum(), df_geral_filtrado_sazonal['is_vespera_feriado'].sum(), \
            df_geral_filtrado_sazonal[
                'is_pos_feriado'].sum(), df_geral_filtrado_sazonal['is_fim_de_semana'].sum()
        ocorrencias_uteis_comuns = len(df_geral_filtrado_sazonal[
                                            (df_geral_filtrado_sazonal['is_feriado'] == False) & (
                                                    df_geral_filtrado_sazonal['is_fim_de_semana'] == False) & (
                                                    df_geral_filtrado_sazonal[
                                                        'is_vespera_feriado'] == False) & (
                                                    df_geral_filtrado_sazonal['is_pos_feriado'] == False)])
        media_feriado, media_vespera, media_pos, media_fds, media_uteis_comuns = (
                                                                                        ocorrencias_feriado / total_dias_feriado) if total_dias_feriado > 0 else 0, (
                                                                                                                                                                            ocorrencias_vespera / total_dias_vespera) if total_dias_vespera > 0 else 0, (
                                                                                                                                                                                                                                                                ocorrencias_pos / total_dias_pos) if total_dias_pos > 0 else 0, (
                                                                                                                                                                                                                                                                                                                                    ocorrencias_fds / total_dias_fds) if total_dias_fds > 0 else 0, (
                                                                                                                                                                                                                                                                                                                                                                                                            ocorrencias_uteis_comuns / total_dias_uteis_comuns) if total_dias_uteis_comuns > 0 else 0
        df_medias = pd.DataFrame(
            {'Tipo de Dia': ['Dia Útil Comum', 'Fim de Semana', 'Véspera de Feriado', 'Feriado', 'Pós-Feriado'],
                'Média Diária de Ocorrências': [media_uteis_comuns, media_fds, media_vespera, media_feriado,
                                                media_pos]}).sort_values(
            'Média Diária de Ocorrências', ascending=False)
        fig_barras_sazonal = plot_barras_sazonal(df_medias)
        render_plotly_safe(fig_barras_sazonal, use_container_width=True, key="barras_sazonal")
        
        st.markdown("---")
        
    
        st.subheader("Ocorrências por Feriado Específico")
        st.markdown("Identifica quais feriados possuem o maior número absoluto de registros.")
        
        if 'nome_feriado' in df_geral_filtrado_sazonal.columns:
            df_feriados = df_geral_filtrado_sazonal[df_geral_filtrado_sazonal['is_feriado'] == True].copy()
            
            if not df_feriados.empty:
                contagem_feriados = df_feriados['nome_feriado'].value_counts().reset_index()
                contagem_feriados.columns = ['nome_feriado', 'total_ocorrencias']
                fig_feriados = plot_barras_feriados(contagem_feriados)
                render_plotly_safe(fig_feriados, use_container_width=True, key="barras_feriados")
                
            
                st.markdown("#### 🔎 Detalhar Tipo de Crime por Feriado")
                st.markdown("Selecione um feriado abaixo para ver quais tipos de crime são mais frequentes nesta data específica.")
                
                lista_feriados = sorted(df_feriados['nome_feriado'].unique())
                
                col_sel, col_kpi = st.columns([3, 1])
                with col_sel:
                    feriado_selecionado = st.selectbox("Escolha o Feriado:", lista_feriados, key="sel_feriado_detalhe")
                
                df_feriado_escolhido = df_feriados[df_feriados['nome_feriado'] == feriado_selecionado]
                
                contagem_crimes_feriado = df_feriado_escolhido['fato_comunicado'].value_counts().reset_index()
                contagem_crimes_feriado.columns = ['Tipo de Crime', 'Quantidade']
                contagem_crimes_feriado = contagem_crimes_feriado.sort_values(by='Quantidade', ascending=True)

                with col_kpi:
                    total_no_feriado = contagem_crimes_feriado['Quantidade'].sum()
                    st.metric(label=f"Total em '{feriado_selecionado}'", value=total_no_feriado)

                if not contagem_crimes_feriado.empty:
                    fig_detalhe_feriado = px.bar(
                        contagem_crimes_feriado, 
                        x='Quantidade', 
                        y='Tipo de Crime', 
                        text='Quantidade',
                        orientation='h',
                        color_discrete_sequence=['#ab47bc'] 
                    )
                    
                    fig_detalhe_feriado.update_traces(textposition='outside')
                    fig_detalhe_feriado.update_layout(
                        title=f"Distribuição de Crimes: {feriado_selecionado}",
                        xaxis_title=None,
                        yaxis_title=None,
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=0, r=0, t=40, b=0),
                        height=max(300, len(contagem_crimes_feriado) * 40)
                    )
                    
                    render_plotly_safe(fig_detalhe_feriado, use_container_width=True, key="grafico_detalhe_feriado")
                else:
                    st.info(f"Não há registros detalhados para o feriado selecionado nos filtros atuais.")

            else:
                st.info("Não há registros em feriados no período selecionado.")
        
        st.markdown("---")

    
        st.subheader("Heatmap de Risco: Dia da Semana vs. Mês")
        st.markdown("A cor de cada célula representa a quantidade média de crimes, destacando os períodos mais 'quentes' do ano.")
        df_periodo_completo_hm = pd.DataFrame(
            pd.to_datetime(pd.date_range(start=st.session_state.data_inicial, end=st.session_state.data_final)),
            columns=['data_fato'])
        df_periodo_completo_hm['mes'], df_periodo_completo_hm['dia_semana'] = df_periodo_completo_hm[
                                                                                    'data_fato'].dt.month_name(), \
                                                                                df_periodo_completo_hm[
                                                                                    'data_fato'].dt.day_name()
        contagem_dias_hm = df_periodo_completo_hm.groupby(['mes', 'dia_semana'], observed=True).size().reset_index(
            name='total_dias_no_periodo')
        ocorrencias_hm = df_geral_filtrado_sazonal.groupby(['mes', 'dia_semana'], observed=True).size().reset_index(
            name='total_ocorrencias')
        df_media_hm = pd.merge(contagem_dias_hm, ocorrencias_hm, on=['mes', 'dia_semana'], how='left').fillna(
            {'total_ocorrencias': 0})
        df_media_hm['media_diaria'] = df_media_hm['total_ocorrencias'] / df_media_hm['total_dias_no_periodo']
        heatmap_pivot = df_media_hm.pivot_table(index='mes', columns='dia_semana', values='media_diaria').fillna(0)
        meses_ordem, nomes_meses_pt = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                                        'September', 'October', 'November', 'December'], {'January': 'Janeiro',
                                                                                            'February': 'Fevereiro',
                                                                                            'March': 'Março',
                                                                                            'April': 'Abril',
                                                                                            'May': 'Maio',
                                                                                            'June': 'Junho',
                                                                                            'July': 'Julho',
                                                                                            'August': 'Agosto',
                                                                                            'September': 'Setembro',
                                                                                            'October': 'Outubro',
                                                                                            'November': 'Novembro',
                                                                                            'December': 'Dezembro'}
        dias_ordem, nomes_dias_pt = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
                                        'Saturday'], {'Monday': 'Segunda', 'Tuesday': 'Terça',
                                                    'Wednesday': 'Quarta', 'Thursday': 'Quinta',
                                                    'Friday': 'Sexta', 'Saturday': 'Sábado', 'Sunday': 'Domingo'}
        heatmap_pivot = heatmap_pivot.reindex(index=meses_ordem, columns=dias_ordem, fill_value=0)
        heatmap_pivot.index, heatmap_pivot.columns = heatmap_pivot.index.map(nomes_meses_pt), [nomes_dias_pt[col]
                                                                                                for col in
                                                                                                heatmap_pivot.columns]
        fig_heatmap_sazonal = plot_heatmap_sazonal(heatmap_pivot)
        render_plotly_safe(fig_heatmap_sazonal, use_container_width=True, key="heatmap_sazonal")
        st.markdown("---")
    else:
        st.warning("Não há dados para exibir a Análise Sazonal com os filtros selecionados.")
  except Exception as e:
        st.error(f"Ocorreu um erro ao renderizar a página de análise geral: {e}")
        st.info("Tente ajustar os filtros na barra lateral ou recarregue a página.")
