import streamlit as st
import pandas as pd
import numpy as np
from plotting import (plot_autor_preso, plot_bo_contra_autor, plot_distribuicao_idade, plot_feminicidio_por_ano,
                    plot_feminicidio_serie_temporal, plot_heatmap_cruzado, plot_localidade_crime,
                    plot_mapa_feminicidio, plot_mapa_letalidade, plot_meio_crime, plot_passagem_policial,
                    plot_sankey_agressor, plot_scatter_idade, plot_vinculo_autor, plot_perfil_racial, 
                    plot_distribuicao_horaria, plot_tempo_relacionamento, plot_filhos_com_autor,
                    plot_correlacao_tempo_violencia, plot_tipo_local_detalhado)
from utils import (to_csv, to_excel, calcular_tendencia_mensal, calcular_tendencia_mensal_vetorizada,
                   colorir_percentual, formatar_seta_percentual, format_number_br, format_int_br, render_plotly_safe)

def criar_tabela_feminicidio_agrupado(df, coluna_agrupamento, nome_agrupamento, df_original_filtrado=None):
    """Cria uma tabela consolidada com dados de feminicídios por [agrupamento]."""
    df = df.copy()
    df['ano'] = df['ano'].astype(int)
    df_agrupado = df.groupby([coluna_agrupamento, 'ano'], observed=True).size().reset_index(name='total_crime')
    df_pivot = df_agrupado.pivot_table(index=coluna_agrupamento, columns='ano', values='total_crime', fill_value=0, observed=True)

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
            df_original_filtrado, coluna_agrupamento
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
    df_consolidado.rename(columns={coluna_agrupamento: nome_coluna}, inplace=True)

    return df_consolidado


def criar_tabela_total_feminicidio(df, df_original_filtrado=None):
    """Cria uma tabela consolidada com o total de feminicídios por ano."""
    if df.empty:
        return pd.DataFrame(columns=['Tipo de Crime', 'total'])
    df = df.copy()
    df['ano'] = df['ano'].astype(int)

    df_agrupado = df.groupby('ano').size().reset_index(name='total_crime')
    df_pivot = df_agrupado.pivot_table(columns='ano', values='total_crime', fill_value=0)

    anos_existentes = [col for col in df.ano.unique() if isinstance(col, (int, float))]
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

    # Tendência via regressão linear mensal (usa todos os meses, sem exclusão)
    if df_original_filtrado is not None and not df_original_filtrado.empty:
        tend = calcular_tendencia_mensal(df_original_filtrado)
        if pd.notna(tend):
            df_pivot['Tendência (% ao ano)'] = tend

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

    df_consolidado = df_pivot[ordem_final].reset_index(drop=True)
    df_consolidado.insert(0, 'Tipo de Crime', 'Feminicídio')

    return df_consolidado


def calcular_indice_letalidade(df_geral_filtrado, df_feminicidio_filtrado, agrupamento):
    """Calcula o Índice de Letalidade da Violência."""
    coluna_agrupamento_map = {
        "Município": "municipio_normalizado",
        "Mesorregião": "mesoregiao",
        "Associação": "associacao",
        "Associação de Municípios": "associacao"
    }
    if agrupamento not in coluna_agrupamento_map:
        return pd.DataFrame()

    coluna_agrupamento = coluna_agrupamento_map[agrupamento]

    df_ocorrencias_puras = df_geral_filtrado[df_geral_filtrado['fato_comunicado'] != 'Feminicídio']
    total_ocorrencias = df_ocorrencias_puras.groupby(coluna_agrupamento, observed=True).size().reset_index(name='total_ocorrencias')

    total_feminicidios = df_feminicidio_filtrado.groupby(coluna_agrupamento, observed=True).size().reset_index(
        name='total_feminicidios')

    df_letalidade = pd.merge(total_ocorrencias, total_feminicidios, on=coluna_agrupamento, how='outer')
    colunas_num_let = df_letalidade.select_dtypes(include=['number']).columns
    df_letalidade[colunas_num_let] = df_letalidade[colunas_num_let].fillna(0)

    df_letalidade['total_ocorrencias'] = df_letalidade['total_ocorrencias'].astype(int)
    df_letalidade['total_feminicidios'] = df_letalidade['total_feminicidios'].astype(int)

    soma_total = df_letalidade['total_ocorrencias'] + df_letalidade['total_feminicidios']
    df_letalidade['indice_letalidade'] = np.where(
        soma_total > 0,
        (df_letalidade['total_feminicidios'] / soma_total) * 100,
        0
    )

    df_letalidade['total_eventos'] = soma_total

    df_letalidade.rename(columns={coluna_agrupamento: 'localidade'}, inplace=True)

    df_final = df_letalidade[[
        'localidade',
        'total_eventos',
        'total_ocorrencias',
        'total_feminicidios',
        'indice_letalidade'
    ]]

    return df_final.sort_values(by='indice_letalidade', ascending=False)


def render(df_geral_filtrado, df_feminicidio_filtrado, df_populacao, df_regioes, df_calendario, geojson_sc):
  try:
    st.header("Análise de Feminicídios Consumados")

    # --- (BLOCOS INTELIGENTES DE CONTEXTO MOVIDOS PARA O HEADER) ---

    total_feminicidios = df_feminicidio_filtrado.shape[0]

    if total_feminicidios > 0:
        # Cálculo dos KPIs
        # Ajuste: verificação case-insensitive ou direta para 'SIM' (maiúsculo) identificado nos dados
        if 'bo_de_vd_contra_o_autor' in df_feminicidio_filtrado.columns:
            vitimas_com_bo = df_feminicidio_filtrado[
                df_feminicidio_filtrado['bo_de_vd_contra_o_autor'].astype(str).str.upper() == 'SIM'
            ].shape[0]
            pct_vitimas_bo = (vitimas_com_bo / total_feminicidios) * 100
        else:
            pct_vitimas_bo = 0

        if 'passagem_por_violencia_domestica' in df_feminicidio_filtrado.columns:
             autores_com_historico = df_feminicidio_filtrado[
                df_feminicidio_filtrado['passagem_por_violencia_domestica'].astype(str).str.upper() == 'SIM'
            ].shape[0]
        else:
            autores_com_historico = 0
        
        pct_autores_historico = (autores_com_historico / total_feminicidios) * 100

        # Renderização das Métricas
        col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

        with col_kpi1:
            st.metric("Total de Feminicídios", total_feminicidios)
        
        with col_kpi2:
            st.metric("% Vítimas com BO Anterior contra o Autor", f"{pct_vitimas_bo:.1f}%")
            
        with col_kpi3:
            st.metric("% Autores com Histórico de Violência Doméstica", f"{pct_autores_historico:.1f}%")
    else:
        st.info("Nenhum dado encontrado para os filtros selecionados.")

    st.markdown("---")


    st.subheader(f"Distribuição Geográfica dos Feminicídios por {st.session_state.agrupamento_selecionado}")
    with st.expander("Como interpretar este mapa?"):
        st.info(
            """
            - **O que mostra:** A localização dos feminicídios no estado.
            - **Como ler:** Tons mais escuros indicam um maior número de casos na localidade. Este mapa mostra os números absolutos, destacando as áreas com maior ocorrência do crime mais grave.
            """
        )
    
    # --- LÓGICA DO MAPA COM MERGE DE REGIÕES ---
    cols_regiao = df_regioes[['municipio_normalizado', 'mesoregiao', 'associacao']]

    if st.session_state.agrupamento_selecionado == "Município" or st.session_state.agrupamento_selecionado == "Consolidado":
        map_df_fem = df_feminicidio_filtrado['municipio_normalizado'].value_counts().reset_index()
        map_df_fem.columns = ['municipio_normalizado', 'quantidade']
        map_df_fem = pd.merge(map_df_fem, cols_regiao, on='municipio_normalizado', how='left')
    else:
        agrupamento_col_fem = "mesoregiao" if st.session_state.agrupamento_selecionado == "Mesorregião" else "associacao"
        feminicidios_por_grupo = df_feminicidio_filtrado.groupby(
            agrupamento_col_fem, observed=True).size().reset_index(
            name='quantidade_grupo')
        municipio_grupo_mapping_fem = df_feminicidio_filtrado[
            ['municipio_normalizado', agrupamento_col_fem]].drop_duplicates()
        map_df_fem = pd.merge(municipio_grupo_mapping_fem, feminicidios_por_grupo, on=agrupamento_col_fem)
        map_df_fem = map_df_fem.rename(columns={'quantidade_grupo': 'quantidade'})
        
        map_df_fem = pd.merge(map_df_fem, cols_regiao, on='municipio_normalizado', how='left', suffixes=('', '_y'))
        
        if 'mesoregiao_y' in map_df_fem.columns: 
            map_df_fem['mesoregiao'] = map_df_fem['mesoregiao'].fillna(map_df_fem['mesoregiao_y'])
            del map_df_fem['mesoregiao_y']
        if 'associacao_y' in map_df_fem.columns:
            map_df_fem['associacao'] = map_df_fem['associacao'].fillna(map_df_fem['associacao_y'])
            del map_df_fem['associacao_y']

    if not map_df_fem.empty:
        map_df_fem['mesoregiao'] = map_df_fem['mesoregiao'].fillna('Indefinido')
        map_df_fem['associacao'] = map_df_fem['associacao'].fillna('Indefinido')
        fig_mapa_fem = plot_mapa_feminicidio(map_df_fem, geojson_sc,
                                             st.session_state.agrupamento_selecionado)
        render_plotly_safe(fig_mapa_fem, use_container_width=True, key="mapa_fem")
    else:
        st.info("Não há dados de feminicídio para exibir no mapa com os filtros selecionados.")
    st.markdown("---")


    st.subheader("Quantidade de Feminicídios por Mês/Ano")
    chart_type_fem_mes_ano = st.selectbox("Tipo de Gráfico", ("Barras", "Linha", "Área"), key="chart_type_fem_mes_ano")
    df_feminicidio_filtrado = df_feminicidio_filtrado.copy()
    df_feminicidio_filtrado['ano_mes'] = df_feminicidio_filtrado[
        'data_fato'].dt.to_period(
        'M').astype(str)
    if st.session_state.agrupamento_selecionado == "Consolidado":
        feminicidios_por_mes = df_feminicidio_filtrado.groupby('ano_mes').size().reset_index(
            name='Quantidade')
        color_param = None
    else:
        mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
        coluna_agrupamento = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
        feminicidios_por_mes = df_feminicidio_filtrado.groupby(
            ['ano_mes', coluna_agrupamento], observed=True).size().reset_index(name='Quantidade')
        color_param = coluna_agrupamento
    feminicidios_por_mes.rename(columns={'ano_mes': 'Mês/Ano'}, inplace=True)

    fig_mes_ano = plot_feminicidio_serie_temporal(feminicidios_por_mes, chart_type_fem_mes_ano,
                                                  st.session_state.agrupamento_selecionado, color_param)
    render_plotly_safe(fig_mes_ano, use_container_width=True, key="mes_ano_fem")
    st.markdown("---")

    col_ano, col_local = st.columns(2)

    with col_ano:
    
        st.subheader("Quantidade de Feminicídios por Ano")
        chart_type_fem_ano = st.selectbox("Tipo de Gráfico", ("Barras", "Linha", "Área"), key="chart_type_fem_ano")

        ano_corrente = pd.Timestamp.now().year
        if st.session_state.agrupamento_selecionado == "Consolidado":
            feminicidios_por_ano = df_feminicidio_filtrado['ano'].value_counts().sort_index().reset_index()
            feminicidios_por_ano.columns = ['ano', 'Quantidade']
            color_param = None
        else:
            mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            coluna_agrupamento = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
            feminicidios_por_ano = df_feminicidio_filtrado.groupby(
                ['ano', coluna_agrupamento], observed=True).size().reset_index(
                name='Quantidade')
            color_param = coluna_agrupamento

        if not feminicidios_por_ano.empty:
            feminicidios_por_ano['ano'] = feminicidios_por_ano['ano'].apply(
                lambda x: f'{x} (Parcial)' if x == ano_corrente else str(x)
            )

        fig_ano_fem = plot_feminicidio_por_ano(feminicidios_por_ano, chart_type_fem_ano,
                                               st.session_state.agrupamento_selecionado, color_param)
        render_plotly_safe(fig_ano_fem, use_container_width=True, key="ano_fem")

    with col_local:
    
        if 'localidade' in df_feminicidio_filtrado.columns:
            st.subheader("Localidade do Crime")
            chart_type_localidade = st.selectbox("Tipo de Gráfico", ("Barras", "Pizza"), key="chart_type_localidade")
            if st.session_state.agrupamento_selecionado == "Consolidado":
                localidade_crime = df_feminicidio_filtrado['localidade'].value_counts().reset_index()
                localidade_crime.columns = ['localidade', 'Quantidade']
                color_param = None
            else:
                mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
                coluna_agrupamento = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
                localidade_crime = df_feminicidio_filtrado.groupby(
                    ['localidade', coluna_agrupamento], observed=True).size().reset_index(
                    name='Quantidade')
                color_param = coluna_agrupamento

            fig_localidade = plot_localidade_crime(localidade_crime, chart_type_localidade,
                                                   st.session_state.agrupamento_selecionado, color_param)
            render_plotly_safe(fig_localidade, use_container_width=True, key="localidade_fem")
        else:
            st.info("Dados de Localidade do Crime não disponíveis.")
    
    st.markdown("---")

    col_graf_fem1, col_graf_fem2 = st.columns(2)
    with col_graf_fem1:
    
        if 'relacao_autor' in df_feminicidio_filtrado.columns:
            st.subheader("Vínculo entre o Autor e a Vítima")
            chart_type_vinculo = st.selectbox("Tipo de Gráfico", ("Barras", "Pizza"), key="chart_type_vinculo")
            if st.session_state.agrupamento_selecionado == "Consolidado":
                vinculo_autor = df_feminicidio_filtrado['relacao_autor'].value_counts().reset_index()
                vinculo_autor.columns = ['relacao_autor', 'Quantidade']
                color_param = None
            else:
                mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
                coluna_agrupamento = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
                vinculo_autor = df_feminicidio_filtrado.groupby(
                    ['relacao_autor', coluna_agrupamento], observed=True).size().reset_index(name='Quantidade')
                color_param = coluna_agrupamento

            fig_vinculo = plot_vinculo_autor(vinculo_autor, chart_type_vinculo, st.session_state.agrupamento_selecionado,
                                             color_param)
            render_plotly_safe(fig_vinculo, use_container_width=True, key="vinculo_fem")
        else:
            st.info("Dados de Vínculo do Autor não disponíveis.")

    with col_graf_fem2:
    
        if 'bo_de_vd_contra_o_autor' in df_feminicidio_filtrado.columns:
            st.subheader("Vítima registrou Boletim de Ocorrência por violência doméstica contra o Autor?")
            chart_type_bo = st.selectbox("Tipo de Gráfico", ("Pizza", "Barras"), key="chart_type_bo")
            bo_contra_autor = df_feminicidio_filtrado[
                'bo_de_vd_contra_o_autor'].value_counts().reset_index()
            bo_contra_autor.columns = ['Resposta', 'Quantidade']

            fig_bo = plot_bo_contra_autor(bo_contra_autor, chart_type_bo)
            render_plotly_safe(fig_bo, use_container_width=True, key="bo_fem")
        else:
            st.info("Dados de B.O. contra o autor não disponíveis.")
    st.markdown("---")

    col_graf_fem3, col_graf_fem4 = st.columns(2)
    with col_graf_fem3:
    
        st.subheader("Distribuição de Idade da Vítima")
        chart_type_idade_vitima = st.selectbox("Tipo de Gráfico", ("Histograma", "Gráfico de Densidade"),
                                               key="chart_type_idade_vitima")
        df_idade_vitima = df_feminicidio_filtrado.dropna(subset=['idade_vitima'])

        fig_idade_vitima = plot_distribuicao_idade(df_idade_vitima, 'idade_vitima', chart_type_idade_vitima, 'Idade da Vítima',
                                                   '#8e24aa')
        render_plotly_safe(fig_idade_vitima, use_container_width=True, key="idade_vitima_fem")

    with col_graf_fem4:
    
        st.subheader("Distribuição de Idade do Autor")
        chart_type_idade_autor = st.selectbox("Tipo de Gráfico", ("Histograma", "Gráfico de Densidade"),
                                              key="chart_type_idade_autor")
        df_idade_autor = df_feminicidio_filtrado.dropna(subset=['idade_autor'])

        fig_idade_autor = plot_distribuicao_idade(df_idade_autor, 'idade_autor', chart_type_idade_autor, 'Idade do Autor', '#ab47bc')
        render_plotly_safe(fig_idade_autor, use_container_width=True, key="idade_autor_fem")
    st.markdown("---")

    col_raca, col_hora = st.columns(2)

    with col_raca:
        st.subheader("Raça/Cor: Vítima vs. Autor")
        
        if 'etnia_vitima' in df_feminicidio_filtrado.columns and 'etnia_autor' in df_feminicidio_filtrado.columns:
            fig_racial = plot_perfil_racial(df_feminicidio_filtrado)
            render_plotly_safe(fig_racial, use_container_width=True, key="grafico_racial")
        else:
            st.warning("Dados de Etnia/Raça não disponíveis.")

    with col_hora:
        st.subheader("Horário da Ocorrência")
        
        if 'hora_fato' in df_feminicidio_filtrado.columns:
            fig_hora = plot_distribuicao_horaria(df_feminicidio_filtrado)
            if fig_hora:
                render_plotly_safe(fig_hora, use_container_width=True, key="grafico_hora")
            else:
                st.info("Não foi possível processar os dados de horário.")
        else:
            st.warning("Dados de Horário não disponíveis.")

    st.markdown("---")

    # --- NOVA SEÇÃO: CONTEXTO DO RELACIONAMENTO E FAMILIAR ---

    st.subheader("Contexto do Relacionamento e Familiar")
    
    col_tempo, col_filhos = st.columns(2)
    
    with col_tempo:
        if 'tempo_relacionamento' in df_feminicidio_filtrado.columns:
            st.markdown("##### Tempo de Relacionamento")
            fig_tempo = plot_tempo_relacionamento(df_feminicidio_filtrado)
            render_plotly_safe(fig_tempo, use_container_width=True, key="fig_tempo_rel")
        else:
            st.info("Dado de tempo de relacionamento indisponível.")
            
    with col_filhos:
        st.markdown("##### Filhos em Comum")
        figs_filhos = plot_filhos_com_autor(df_feminicidio_filtrado)
        
        tab_filho1, tab_filho2 = st.tabs(["Existência", "Quantidade"])
        
        with tab_filho1:
            if 'existencia' in figs_filhos:
                render_plotly_safe(figs_filhos['existencia'], use_container_width=True, key="fig_filho_exist")
            else:
                st.info("Dado sobre existência de filhos indisponível.")
                
        with tab_filho2:
            if 'quantidade' in figs_filhos:
                render_plotly_safe(figs_filhos['quantidade'], use_container_width=True, key="fig_filho_qtd")
            else:
                st.info("Dado sobre quantidade de filhos indisponível.")
    
    # Correlação Tempo vs Violência
    if 'tempo_relacionamento' in df_feminicidio_filtrado.columns and 'bo_de_vd_contra_o_autor' in df_feminicidio_filtrado.columns:
        st.markdown("##### Relação: Tempo de Relacionamento vs. Violência Prévia")
        with st.expander("Análise de Correlação"):
             st.info("Este gráfico investiga se relacionamentos de longa duração apresentam maior frequência de denúncias prévias (BOs) comparado a relacionamentos recentes.")
        
        fig_corr = plot_correlacao_tempo_violencia(df_feminicidio_filtrado)
        if fig_corr:
            render_plotly_safe(fig_corr, use_container_width=True, key="fig_corr_tempo")
            
    st.markdown("---")
    

    st.subheader("Raio-X do Agressor")
    col_raiox1, col_raiox2 = st.columns(2)
    with col_raiox1:
        st.subheader("Dinâmica de Idade: Vítima vs. Agressor")
        with st.expander("Como interpretar este gráfico?"):
            st.info("""
            - **O que mostra:** A correlação entre a idade da vítima (eixo X) e a do agressor (eixo Y).
            - **Como ler:** Cada ponto é um caso. A linha tracejada vermelha representa onde a vítima e o agressor teriam a mesma idade.
            - **Pontos acima da linha:** Agressor mais velho que a vítima.
            - **Pontos abaixo da linha:** Agressor mais novo que a vítima.
            """)
        if not df_feminicidio_filtrado.empty and df_feminicidio_filtrado[
            ['idade_vitima', 'idade_autor']].notna().all(axis=1).any():
            fig_scatter_idade = plot_scatter_idade(df_feminicidio_filtrado)
            render_plotly_safe(fig_scatter_idade, use_container_width=True, key="scatter_idade_fem")
        else:
            st.info("Não há dados suficientes para exibir o gráfico de correlação de idades.")
    with col_raiox2:
    
        st.subheader("Histórico do Agressor")
        with st.expander("Como interpretar este gráfico?"):
            st.info("""
            - **O que mostra:** O fluxo do histórico criminal dos agressores.
            - **Como ler:** Siga as faixas da esquerda para a direita. O gráfico mostra, do total de agressores, quantos já tinham passagem policial e, destes, quantos tinham registros específicos de violência doméstica.
            """)
        if not df_feminicidio_filtrado.empty and 'passagem_policial' in df_feminicidio_filtrado.columns and 'passagem_por_violencia_domestica' in df_feminicidio_filtrado.columns:
            fig_sankey = plot_sankey_agressor(df_feminicidio_filtrado)
            if fig_sankey:
                render_plotly_safe(fig_sankey, use_container_width=True, key="sankey_fem")
            else:
                st.info("Não há dados para exibir o gráfico de histórico do agressor.")
        else:
            st.info(
                "Não há dados suficientes ou as colunas necessárias não existem para exibir o gráfico de histórico do agressor.")
    st.markdown("---")


    st.subheader("Análise Cruzada de Vítima e Agressor")
    with st.expander("Como interpretar este gráfico?"):
        st.info(
            """
            **Este mapa de calor cruza as faixas etárias de vítimas e agressores, revelando padrões de relacionamento etário nos crimes de feminicídio. Células mais escuras indicam uma maior concentração de casos.**
            - **O que mostra:** A concentração de casos de feminicídio no cruzamento entre a faixa etária da vítima (eixo Y) e a do agressor (eixo X).
            - **Como ler:** Células mais escuras indicam uma combinação de faixas etárias onde ocorreram mais crimes.
            """
        )
    df_heatmap_cruzado = df_feminicidio_filtrado.dropna(subset=['idade_vitima', 'idade_autor']).copy()

    if not df_heatmap_cruzado.empty:
        fig_heatmap_cruzado = plot_heatmap_cruzado(df_heatmap_cruzado)
        render_plotly_safe(fig_heatmap_cruzado, use_container_width=True, key="heatmap_cruzado_fem")
    else:
        st.info("Não há dados suficientes (com idade da vítima e do autor) para gerar a análise cruzada.")

    st.markdown("---")

    col_graf_fem5, col_graf_fem6 = st.columns(2)
    with col_graf_fem5:
    
        if 'meio_crime' in df_feminicidio_filtrado.columns:
            st.subheader("Meio Utilizado para o Crime")
            chart_type_meio = st.selectbox("Tipo de Gráfico", ("Barras", "Pizza"), key="chart_type_meio")
            if st.session_state.agrupamento_selecionado == "Consolidado":
                meio_crime = df_feminicidio_filtrado['meio_crime'].value_counts().reset_index()
                meio_crime.columns = ['meio_crime', 'Quantidade']
                color_param = None
            else:
                mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
                coluna_agrupamento = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
                meio_crime = df_feminicidio_filtrado.groupby(
                    ['meio_crime', coluna_agrupamento], observed=True).size().reset_index(
                    name='Quantidade')
                color_param = coluna_agrupamento

            fig_meio = plot_meio_crime(meio_crime, chart_type_meio, st.session_state.agrupamento_selecionado, color_param)
            render_plotly_safe(fig_meio, use_container_width=True, key="meio_fem")
        else:
            st.info("Dados de Meio do Crime não disponíveis.")

    with col_graf_fem6:
    
        if 'autor_preso' in df_feminicidio_filtrado.columns:
            st.subheader("Autor Foi Preso?")
            chart_type_preso = st.selectbox("Tipo de Gráfico", ("Pizza", "Barras"), key="chart_type_preso")
            autor_preso = df_feminicidio_filtrado['autor_preso'].value_counts().reset_index()
            autor_preso.columns = ['Resposta', 'Quantidade']

            fig_preso = plot_autor_preso(autor_preso, chart_type_preso)
            render_plotly_safe(fig_preso, use_container_width=True, key="preso_fem")
        else:
            st.info("Dados de Prisão do Autor não disponíveis.")
    st.markdown("---")

    st.markdown("---")

    col_graf_fem9, col_graf_fem10 = st.columns(2)
    with col_graf_fem9:
    
        st.subheader("Tipo de Local")
        
        if 'tipo_local' in df_feminicidio_filtrado.columns:
            fig_tipo_local = plot_tipo_local_detalhado(df_feminicidio_filtrado)
            render_plotly_safe(fig_tipo_local, use_container_width=True, key="fig_tipo_local_bar")
        else:
            st.info("Dado de Tipo de Local indisponível.")

    with col_graf_fem10:
        # Espaço vazio ou futuro gráfico
        st.write("")

    st.markdown("---")

    col_graf_fem7, col_graf_fem8 = st.columns(2)
    with col_graf_fem7:
    
        if 'passagem_policial' in df_feminicidio_filtrado.columns:
            st.subheader("Autor possuía registro de Boletim de Ocorrência por qualquer tipo de crime?")
            chart_type_autor_bo = st.selectbox("Tipo de Gráfico", ("Pizza", "Barras"), key="chart_type_autor_bo")
            autor_bo = df_feminicidio_filtrado['passagem_policial'].value_counts().reset_index()
            autor_bo.columns = ['Resposta', 'Quantidade']

            fig_autor_bo = plot_passagem_policial(autor_bo, chart_type_autor_bo, "Autor com Registro de B.O.?",
                                                  '#8e24aa')
            render_plotly_safe(fig_autor_bo, use_container_width=True, key="autor_bo_fem")
        else:
            st.info("Dados de Passagem Policial não disponíveis.")

    with col_graf_fem8:
    
        st.subheader("Autor possuía registro de Boletim de Ocorrência por Violência Doméstica?")
        if 'passagem_por_violencia_domestica' in df_feminicidio_filtrado.columns:
            chart_type_autor_bo_vd = st.selectbox("Tipo de Gráfico", ("Pizza", "Barras"),
                                                  key="chart_type_autor_bo_vd")
            autor_bo_vd = df_feminicidio_filtrado[
                'passagem_por_violencia_domestica'].value_counts().reset_index()
            autor_bo_vd.columns = ['Resposta', 'Quantidade']
            if not autor_bo_vd.empty:
                fig_autor_bo_vd = plot_passagem_policial(autor_bo_vd, chart_type_autor_bo_vd,
                                                         "Autor com B.O. por Violência Doméstica?", '#ab47bc')
                render_plotly_safe(fig_autor_bo_vd, use_container_width=True, key="autor_bo_vd_fem")
            else:
                st.info("Não há dados sobre B.O. por violência doméstica para os filtros selecionados.")
        else:
            st.warning("A coluna 'Passagem por Violência Doméstica' não foi encontrada na base de dados.")
    st.markdown("---")

    if st.session_state.agrupamento_selecionado != "Consolidado":
        mapa_agrupamento_tabela = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
        coluna_agrupamento_tabela = mapa_agrupamento_tabela.get(st.session_state.agrupamento_selecionado, "municipio")
        st.subheader(f"Tabela Consolidada de Feminicídios por {st.session_state.agrupamento_selecionado}")
        
        with st.expander("Como interpretar esta tabela?"):
            st.info(
                """
                - **O que mostra:** Um detalhamento anual do número de feminicídios por localidade.
                - **Colunas de Diferença:** Mostram a variação percentual de um ano para o outro.
                - **Tendência (% ao ano):** Indica a tendência de longo prazo calculada por regressão linear sobre todos os meses.
                """
            )
            
        if not df_feminicidio_filtrado.empty:
            tabela_feminicidio = criar_tabela_feminicidio_agrupado(df_feminicidio_filtrado,
                                                                   coluna_agrupamento_tabela,
                                                                   st.session_state.agrupamento_selecionado,
                                                                   df_original_filtrado=df_feminicidio_filtrado)
            if not tabela_feminicidio.empty:
                st.markdown("##### Exportar Dados da Tabela")
                col1_export_fem, col2_export_fem = st.columns(2)
                with col1_export_fem:
                    st.download_button(
                        label="📥 Exportar para CSV",
                        data=to_csv(tabela_feminicidio),
                        file_name=f'feminicidios_por_{st.session_state.agrupamento_selecionado}.csv',
                        mime='text/csv',
                        key='csv_consolidada_fem'
                    )
                with col2_export_fem:
                    st.download_button(
                        label="📥 Exportar para Excel",
                        data=to_excel(tabela_feminicidio),
                        file_name=f'feminicidios_por_{st.session_state.agrupamento_selecionado}.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        key='excel_consolidada_fem'
                    )

                colunas_evolucao = [col for col in tabela_feminicidio.columns if 'Diferença' in str(col)]
                format_dict = {col: formatar_seta_percentual for col in colunas_evolucao}

                ano_corrente_parcial = f'{pd.Timestamp.now().year} (Parcial)'
                colunas_de_anos = [col for col in tabela_feminicidio.columns if col.isdigit() and len(col) == 4]
                if ano_corrente_parcial in tabela_feminicidio.columns:
                    colunas_de_anos.append(ano_corrente_parcial)

                for col in colunas_de_anos:
                    format_dict[col] = format_int_br
                format_dict['total'] = format_int_br

                if 'Tendência (% ao ano)' in tabela_feminicidio.columns:
                    format_dict['Tendência (% ao ano)'] = '{:+.1f}%'

                colunas_para_colorir = colunas_evolucao[:]
                if 'Tendência (% ao ano)' in tabela_feminicidio.columns:
                    colunas_para_colorir.append('Tendência (% ao ano)')

                styler = tabela_feminicidio.style.map(colorir_percentual, subset=colunas_para_colorir).format(
                    format_dict)
                st.dataframe(styler, use_container_width=True, hide_index=True)
            else:
                st.warning("Não há dados para exibir na tabela de feminicídios com os filtros selecionados.")
        else:
            st.warning("Não há dados para exibir na tabela de feminicídios com os filtros selecionados.")

    else:
    
        st.subheader("Tabela Consolidada de Feminicídios (Total SC)")
        if not df_feminicidio_filtrado.empty:
            tabela_total = criar_tabela_total_feminicidio(df_feminicidio_filtrado,
                                                          df_original_filtrado=df_feminicidio_filtrado)
            
            if not tabela_total.empty:
                st.markdown("##### Exportar Dados da Tabela")
                col1_export_total, col2_export_total = st.columns(2)
                with col1_export_total:
                    st.download_button(
                        label="📥 Exportar para CSV",
                        data=to_csv(tabela_total),
                        file_name='feminicidios_total_sc.csv',
                        mime='text/csv',
                        key='csv_total_fem'
                    )
                with col2_export_total:
                    st.download_button(
                        label="📥 Exportar para Excel",
                        data=to_excel(tabela_total),
                        file_name='feminicidios_total_sc.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        key='excel_total_fem'
                    )

                colunas_evolucao = [col for col in tabela_total.columns if 'Diferença' in str(col)]
                format_dict = {col: formatar_seta_percentual for col in colunas_evolucao}

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
                st.warning("Não há dados para exibir na tabela total.")
        else:
             st.warning("Não há dados filtrados disponíveis.")

    st.markdown("---")

    st.header("Índice de Letalidade da Violência")
    st.markdown("""
    **Qual a probabilidade de uma denúncia de violência em um determinado município escalar para um feminicídio?**
    O índice é calculado como:

    `Índice = (Total de Feminicídios / (Total de Ocorrências de Violência + Total de Feminicídios)) * 100`

    Isso representa: *"Para cada 100 ocorrências de violência contra a mulher, X resultam em morte."*
    """)

    if st.session_state.agrupamento_selecionado == "Consolidado":
        st.warning(
            "Por favor, selecione um nível de agrupamento (Município, Mesorregião ou Associação de Municípios) para visualizar o Índice de Letalidade.")
    else:
        df_letalidade_calculado = calcular_indice_letalidade(df_geral_filtrado,
                                                                df_feminicidio_filtrado,
                                                                st.session_state.agrupamento_selecionado)

        if df_letalidade_calculado.empty:
            st.info("Não há dados suficientes para calcular o Índice de Letalidade com os filtros selecionados.")
        else:
            st.subheader(
                f"Mapa Coroplético do Índice de Letalidade por {st.session_state.agrupamento_selecionado}")
            with st.expander("Como interpretar este mapa?"):
                st.info(
                    """
                    - **O que mostra:** O risco de uma ocorrência de violência se tornar um feminicídio em cada localidade.
                    - **Como ler:** Tons mais escuros (vermelho/laranja) indicam uma maior letalidade, ou seja, uma maior proporção de casos que terminam em morte, mesmo que o número total de ocorrências seja baixo. É um indicador de falha na rede de proteção.
                    """
                )
            cols_regiao_let = df_regioes[['municipio_normalizado', 'municipio', 'mesoregiao', 'associacao']].drop_duplicates()
            if st.session_state.agrupamento_selecionado == "Município":
                map_df_letalidade = df_letalidade_calculado.rename(columns={'localidade': 'municipio_normalizado'})
                map_df_letalidade = pd.merge(map_df_letalidade, cols_regiao_let, on='municipio_normalizado', how='left')
            else:
                coluna_agrupamento = "mesoregiao" if st.session_state.agrupamento_selecionado == "Mesorregião" else "associacao"
                mapa_grupo = df_letalidade_calculado.set_index('localidade')
                municipios_no_filtro = df_geral_filtrado[
                    ['municipio_normalizado', coluna_agrupamento]].drop_duplicates()
                map_df_letalidade = pd.merge(municipios_no_filtro, mapa_grupo, left_on=coluna_agrupamento, right_index=True, how='left')
                map_df_letalidade = pd.merge(map_df_letalidade, cols_regiao_let, on='municipio_normalizado', how='left', suffixes=('', '_reg'))
                map_df_letalidade = map_df_letalidade.fillna(0)

            fig_mapa_letalidade = plot_mapa_letalidade(map_df_letalidade, geojson_sc, st.session_state.agrupamento_selecionado)
            render_plotly_safe(fig_mapa_letalidade, use_container_width=True, key="mapa_letalidade")
            st.markdown("---")

            st.subheader(f"Ranking do Índice de Letalidade por {st.session_state.agrupamento_selecionado}")
            st.markdown(
                "A tabela abaixo classifica as localidades com maior risco de letalidade. O índice alto, mesmo com poucas ocorrências, é um sinal de alerta.")
            df_ranking = df_letalidade_calculado.rename(
                columns={'localidade': st.session_state.agrupamento_selecionado,
                            'total_eventos': 'Total de Eventos (Ocorrências + Feminicídios)',
                            'total_ocorrencias': 'Ocorrências de Violência',
                            'total_feminicidios': 'Feminicídios',
                            'indice_letalidade': 'Índice de Letalidade'}).set_index(
                st.session_state.agrupamento_selecionado)
            st.dataframe(df_ranking.style.format(
                {'Índice de Letalidade': '{:.2f}', 'Total de Eventos (Ocorrências + Feminicídios)': '{:.0f}',
                    'Ocorrências de Violência': '{:.0f}', 'Feminicídios': '{:.0f}'}).background_gradient(
                cmap='OrRd', subset=['Índice de Letalidade']), use_container_width=True)
  except Exception as e:
        st.error(f"Ocorreu um erro ao renderizar a página de feminicídios: {e}")
        st.info("Tente ajustar os filtros na barra lateral ou recarregue a página.")