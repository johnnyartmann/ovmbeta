import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime
from data_loader import carregar_dados_processados
import header


def carregar_css(caminho_arquivo):
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            css = f.read()
        return f"<style>{css}</style>"
    except FileNotFoundError:
        st.error(f"Arquivo de estilo '{caminho_arquivo}' não encontrado.")
        return ""


st.set_page_config(
    page_title="Observatório da Violência Contra a Mulher - SC",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="auto"
)

css_personalizado = carregar_css("style.css")
st.markdown(css_personalizado, unsafe_allow_html=True)

dfs, geojson_data = carregar_dados_processados()

if dfs is not None and geojson_data is not None:
    df_geral = dfs.get('geral', pd.DataFrame())
    df_feminicidio = dfs.get('feminicidio', pd.DataFrame())
    df_populacao = dfs.get('populacao', pd.DataFrame())
    df_regioes = dfs.get('regioes', pd.DataFrame())
    df_calendario = dfs.get('calendario', pd.DataFrame())
    geojson_sc = geojson_data
else:
    st.error("Falha no carregamento dos dados processados.")
    st.warning("Execute o script 'preprocess_data.py' para gerar os arquivos de dados necessários.")
    st.stop()

if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "Análise Geral"
if 'reset_counter' not in st.session_state:
    st.session_state.reset_counter = 0
if 'agrupamento_selecionado' not in st.session_state:
    st.session_state.agrupamento_selecionado = "Consolidado"

_rc = st.session_state.reset_counter

st.sidebar.image("logo_ovm.png", use_container_width=True)

if not df_geral.empty:
    with st.sidebar:
        # --- PERIODO (fora do form para atualizacao reativa das opcoes) ---
        st.subheader("PERÍODO")
        min_date = df_geral['data_fato'].min().date()
        max_date = df_geral['data_fato'].max().date()

        st.session_state.data_inicial = st.date_input(
            "Data Inicial",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY",
            key=f"data_inicial_widget_{_rc}"
        )
        st.session_state.data_final = st.date_input(
            "Data Final",
            value=max_date,
            min_value=st.session_state.data_inicial,
            max_value=max_date,
            format="DD/MM/YYYY",
            key=f"data_final_widget_{_rc}"
        )

        df_geral_filtrado_por_data = df_geral[
            (df_geral['data_fato'].dt.date >= st.session_state.data_inicial) &
            (df_geral['data_fato'].dt.date <= st.session_state.data_final)
        ]

        # --- DEMAIS FILTROS (aplicados de forma reativa a cada clique) ---
        st.subheader("VISUALIZAR POR")
        st.session_state.agrupamento_selecionado = st.selectbox(
            "Agrupar por",
            options=["Consolidado", "Município", "Mesorregião", "Associação de Municípios"],
            index=0,
            key=f"agrupamento_selecionado_widget_{_rc}"
        )

        st.subheader("LOCALIZAÇÃO")
        municipios_disponiveis = sorted(df_geral_filtrado_por_data['municipio'].dropna().unique())
        todos_municipios = st.checkbox("Todos os municípios", value=True, key=f"todos_municipios_check_{_rc}")

        if todos_municipios:
            municipio_selecionado = municipios_disponiveis
        else:
            municipio_selecionado = st.multiselect(
                "Município(s) específico(s)",
                options=municipios_disponiveis,
                default=[],
                key=f"municipio_selecionado_multi_{_rc}"
            )
            if not municipio_selecionado:
                st.warning("Nenhum município selecionado. Exibindo dados de todos os municípios.")
                municipio_selecionado = municipios_disponiveis

        mesoregioes_disponiveis = sorted(df_geral_filtrado_por_data['mesoregiao'].unique())
        mesoregiao_selecionado = st.multiselect(
            "Mesorregião(ões)",
            options=mesoregioes_disponiveis,
            default=mesoregioes_disponiveis,
            key=f"mesoregiao_selecionado_multi_{_rc}"
        )

        associacoes_disponiveis = sorted(df_geral_filtrado_por_data['associacao'].dropna().unique())
        associacao_selecionado = st.multiselect(
            "Associação(ões) de Municípios",
            options=associacoes_disponiveis,
            default=associacoes_disponiveis,
            key=f"associacao_selecionado_multi_{_rc}"
        )

        st.subheader("TIPO DE CRIME")
        fatos_disponiveis = sorted(df_geral_filtrado_por_data['fato_comunicado'].unique())
        todos_crimes = st.checkbox("Todos os tipos", value=True, key=f"todos_crimes_check_{_rc}")

        if todos_crimes:
            fato_selecionado = fatos_disponiveis
        else:
            fato_selecionado = st.multiselect(
                "Tipo(s) de crime",
                options=fatos_disponiveis,
                default=[],
                key=f"fato_selecionado_multi_{_rc}"
            )
            if not fato_selecionado:
                st.warning("Nenhum tipo de crime selecionado. Exibindo todos os tipos.")
                fato_selecionado = fatos_disponiveis

        st.subheader("PERFIL DA VÍTIMA")
        idade_selecionada = st.slider(
            "Faixa Etária",
            min_value=0,
            max_value=100,
            value=(0, 100),
            key=f"idade_selecionada_slider_{_rc}"
        )
        idade_max_texto = "100+ anos" if idade_selecionada[1] == 100 else f"{idade_selecionada[1]} anos"
        st.caption(f"Idades: {idade_selecionada[0]} a {idade_max_texto}")

        crimes_por_municipio_para_filtro = df_geral_filtrado_por_data['municipio_normalizado'].value_counts().reset_index()
        crimes_por_municipio_para_filtro.columns = ['municipio_normalizado', 'total_fatos']

        df_populacional_metrics = pd.merge(df_populacao.copy(), crimes_por_municipio_para_filtro, on='municipio_normalizado', how='left')
        df_populacional_metrics['total_fatos'] = df_populacional_metrics['total_fatos'].fillna(0)

        anos_no_filtro = df_geral_filtrado_por_data['ano'].unique()
        num_anos = len(anos_no_filtro) if len(anos_no_filtro) > 0 else 1

        df_populacional_metrics['media_anual_fatos'] = df_populacional_metrics['total_fatos'] / num_anos
        df_populacional_metrics['taxa_por_mil_mulheres'] = (
            (df_populacional_metrics['media_anual_fatos'] / df_populacional_metrics['populacao_feminina'].replace(0, pd.NA)) * 1000
        ).fillna(0)
        df_populacional_metrics['percentual_mulheres_vitimas'] = (
            (df_populacional_metrics['media_anual_fatos'] / df_populacional_metrics['populacao_feminina'].replace(0, pd.NA)) * 100
        ).fillna(0)

        st.subheader("FILTROS POPULACIONAIS")

        date_dep_key = f"{st.session_state.data_inicial}_{st.session_state.data_final}_{_rc}"

        min_pop, max_pop = int(df_populacao['populacao_feminina'].min()), int(df_populacao['populacao_feminina'].max())
        pop_disabled = False
        if min_pop >= max_pop:
            max_pop = min_pop + 1
            pop_disabled = True
        pop_selecionada = st.slider("População Feminina", min_value=min_pop, max_value=max_pop, value=(min_pop, max_pop), disabled=pop_disabled, key=f"pop_selecionada_slider_{_rc}")

        min_media_fatos, max_media_fatos = float(df_populacional_metrics['media_anual_fatos'].min()), float(df_populacional_metrics['media_anual_fatos'].max())
        media_disabled = False
        if min_media_fatos >= max_media_fatos:
            max_media_fatos = min_media_fatos + 0.01
            media_disabled = True
        media_fatos_selecionada = st.slider("Média Anual de Fatos", min_value=min_media_fatos, max_value=max_media_fatos, value=(min_media_fatos, max_media_fatos), disabled=media_disabled, key=f"media_fatos_slider_{date_dep_key}")

        min_taxa, max_taxa = float(df_populacional_metrics['taxa_por_mil_mulheres'].min()), float(df_populacional_metrics['taxa_por_mil_mulheres'].max())
        taxa_disabled = False
        if min_taxa >= max_taxa:
            max_taxa = min_taxa + 0.01
            taxa_disabled = True
        taxa_selecionada = st.slider("Fatos por Mil Mulheres", min_value=min_taxa, max_value=max_taxa, value=(min_taxa, max_taxa), disabled=taxa_disabled, key=f"taxa_slider_{date_dep_key}")

        min_perc, max_perc = float(df_populacional_metrics['percentual_mulheres_vitimas'].min()), float(df_populacional_metrics['percentual_mulheres_vitimas'].max())
        perc_disabled = False
        if min_perc >= max_perc:
            max_perc = min_perc + 0.01
            perc_disabled = True
        perc_selecionado = st.slider("% de Mulheres Vítimas", min_value=min_perc, max_value=max_perc, value=(min_perc, max_perc), disabled=perc_disabled, key=f"perc_slider_{date_dep_key}")

    # --- LOGICA DE FILTRAGEM FINAL ---
    idade_max_filtro = float('inf') if idade_selecionada[1] == 100 else idade_selecionada[1]
    idade_total_selecionada = (idade_selecionada[0] == 0 and idade_selecionada[1] == 100)

    municipios_filtrados_populacao = df_populacional_metrics[
        (df_populacional_metrics['populacao_feminina'] >= pop_selecionada[0]) &
        (df_populacional_metrics['populacao_feminina'] <= pop_selecionada[1]) &
        (df_populacional_metrics['media_anual_fatos'] >= media_fatos_selecionada[0]) &
        (df_populacional_metrics['media_anual_fatos'] <= media_fatos_selecionada[1]) &
        (df_populacional_metrics['taxa_por_mil_mulheres'] >= taxa_selecionada[0]) &
        (df_populacional_metrics['taxa_por_mil_mulheres'] <= taxa_selecionada[1]) &
        (df_populacional_metrics['percentual_mulheres_vitimas'] >= perc_selecionado[0]) &
        (df_populacional_metrics['percentual_mulheres_vitimas'] <= perc_selecionado[1])
    ]['municipio_normalizado']

    mask_idade_geral = (
        (df_geral['idade_vitima'].isna()) | (df_geral['idade_vitima'].between(0, float('inf'), inclusive='both'))
    ) if idade_total_selecionada else (
        df_geral['idade_vitima'].between(idade_selecionada[0], idade_max_filtro, inclusive='both')
    )

    df_geral_filtrado = df_geral[
        (df_geral['data_fato'].dt.date >= st.session_state.data_inicial) &
        (df_geral['data_fato'].dt.date <= st.session_state.data_final) &
        (df_geral['fato_comunicado'].isin(fato_selecionado)) &
        (df_geral['municipio'].isin(municipio_selecionado)) &
        (df_geral['mesoregiao'].isin(mesoregiao_selecionado)) &
        (df_geral['associacao'].isin(associacao_selecionado)) &
        mask_idade_geral &
        (df_geral['municipio_normalizado'].isin(municipios_filtrados_populacao))
    ].copy()

    mask_idade_fem = (
        (df_feminicidio['idade_vitima'].isna()) | (df_feminicidio['idade_vitima'].between(0, float('inf'), inclusive='both'))
    ) if idade_total_selecionada else (
        df_feminicidio['idade_vitima'].between(idade_selecionada[0], idade_max_filtro, inclusive='both')
    )

    df_feminicidio_filtrado = df_feminicidio[
        (df_feminicidio['data_fato'].dt.date >= st.session_state.data_inicial) &
        (df_feminicidio['data_fato'].dt.date <= st.session_state.data_final) &
        (df_feminicidio['municipio'].isin(municipio_selecionado)) &
        (df_feminicidio['mesoregiao'].isin(mesoregiao_selecionado)) &
        (df_feminicidio['associacao'].isin(associacao_selecionado)) &
        mask_idade_fem &
        (df_feminicidio['municipio_normalizado'].isin(municipios_filtrados_populacao))
    ].copy()

    # Guarda no session_state para acesso em módulos
    st.session_state['df_geral_filtrado'] = df_geral_filtrado
    st.session_state['df_feminicidio_filtrado'] = df_feminicidio_filtrado
    st.session_state['df_populacao'] = df_populacao
    st.session_state['df_regioes'] = df_regioes
    st.session_state['df_calendario'] = df_calendario

    with st.sidebar:
        st.markdown("---")
        st.subheader("📄 RELATÓRIO OFICIAL")

        btn_gerar_label = "📄 Gerar Relatório PDF Completo (18 Páginas)"
        if st.button(btn_gerar_label, use_container_width=True, type="primary", key=f"btn_gerar_pdf_{_rc}"):
            with st.spinner("Gerando Relatório Executivo Completo (18 Páginas)..."):
                try:
                    from tabs.relatorio_pdf import gerar_relatorio_pdf
                    pdf_bytes = gerar_relatorio_pdf(
                        df_geral=df_geral_filtrado,
                        df_feminicidio=df_feminicidio_filtrado,
                        df_populacao=df_populacao,
                        df_regioes=df_regioes,
                        df_calendario=df_calendario,
                        agrupamento=st.session_state.agrupamento_selecionado,
                        data_inicial=st.session_state.data_inicial,
                        data_final=st.session_state.data_final,
                        idade_selecionada=idade_selecionada,
                        crimes_selecionados=fato_selecionado,
                        municipios_selecionados=municipio_selecionado,
                        mesorregioes_selecionadas=mesoregiao_selecionado,
                        associacoes_selecionadas=associacao_selecionado
                    )
                    st.session_state['pdf_gerado_bytes'] = pdf_bytes
                    st.session_state['pdf_gerado_ts'] = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.session_state['pdf_gerado_nome'] = f"Relatorio_OVM_SC_{datetime.now().strftime('%d-%m-%Y_%H-%M')}.pdf"
                except Exception as e:
                    st.error(f"Erro ao gerar relatório: {e}")

        if st.session_state.get('pdf_gerado_bytes'):
            st.download_button(
                label="⬇️ Baixar Relatório PDF (18 Págs)",
                data=st.session_state['pdf_gerado_bytes'],
                file_name=st.session_state.get('pdf_gerado_nome', 'Relatorio_OVM_SC.pdf'),
                mime="application/pdf",
                use_container_width=True,
                type="secondary",
                key=f"download_btn_pdf_{st.session_state.get('pdf_gerado_ts', 'default')}"
            )
            st.success("✅ Relatório pronto para download!")

        st.markdown("---")
        if st.button("🔄 Resetar Todos os Filtros", use_container_width=True, key=f"btn_reset_{_rc}"):
            st.session_state.reset_counter += 1
            if 'pdf_gerado_bytes' in st.session_state:
                del st.session_state['pdf_gerado_bytes']
            st.rerun()

    if st.session_state.active_tab == "Análise de Feminicídios":
        header.render_custom_header(df_feminicidio_filtrado, idade_selecionada=idade_selecionada)
    else:
        header.render_custom_header(df_geral_filtrado, idade_selecionada=idade_selecionada)
    header.render_tab_buttons()

    if st.session_state.active_tab == "Análise Geral":
        from tabs import analise_geral
        analise_geral.render(df_geral_filtrado, df_feminicidio_filtrado, df_populacao, df_regioes, df_calendario, geojson_sc)
    elif st.session_state.active_tab == "Análise de Feminicídios":
        from tabs import analise_feminicidios
        analise_feminicidios.render(df_geral_filtrado, df_feminicidio_filtrado, df_populacao, df_regioes, df_calendario, geojson_sc)
    elif st.session_state.active_tab == "Metodologia e Glossário":
        from tabs import glossario
        glossario.render()
    elif st.session_state.active_tab == "Download de Dados":
        from tabs import download
        download.render()

else:
    # Mesmo sem dados, renderiza o header e as abas de navegação
    header.render_custom_header(None)
    header.render_tab_buttons()

    if st.session_state.active_tab == "Metodologia e Glossário":
        from tabs import glossario
        glossario.render()
    elif st.session_state.active_tab == "Download de Dados":
        from tabs import download
        download.render()
    else:
        st.error("Nenhum dado para exibir.")
        st.warning("Verifique se os arquivos de dados foram carregados corretamente ou se os filtros aplicados não resultaram em uma seleção vazia.")
