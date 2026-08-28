import base64
import os
from datetime import datetime
import streamlit as st
import textwrap


@st.cache_data
def get_logo_base64():
    """Carrega a logo da OVM para Base64 uma única vez em cache para impressão oficial."""
    caminhos = [
        os.path.join(os.path.dirname(__file__), 'logo_ovm.png'),
        'logo_ovm.png'
    ]
    for caminho in caminhos:
        if os.path.exists(caminho):
            try:
                with open(caminho, 'rb') as f:
                    return base64.b64encode(f.read()).decode('utf-8')
            except Exception:
                pass
    return ""


def build_institutional_print_header(df_filtrado=None, idade_selecionada=None):
    """
    Constrói o cabeçalho institucional formal com Logo OVM e Quadro de Filtros.
    Fica invisível na tela comum e é exibido automaticamente ao imprimir / salvar PDF (Ctrl+P).
    """
    active_tab = st.session_state.get('active_tab', 'Análise Geral')
    logo_b64 = get_logo_base64()
    logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" alt="Logo OVM/SC" class="print-logo" />' if logo_b64 else ''

    data_emissao = datetime.now().strftime("%d/%m/%Y às %H:%M")

    # Se estiver nas abas de análise e houver dados
    if df_filtrado is not None and not df_filtrado.empty and 'data_inicial' in st.session_state and 'data_final' in st.session_state:
        data_ini = st.session_state.data_inicial
        data_fim = st.session_state.data_final
        dias_totais = (data_fim - data_ini).days
        periodo_str = f'{data_ini.strftime("%d/%m/%Y")} a {data_fim.strftime("%d/%m/%Y")} ({dias_totais} dias)'

        # Mesorregiões
        mesos_no_filtro = [m for m in df_filtrado['mesoregiao'].unique() if m != 'Não informado']
        if len(mesos_no_filtro) >= 6:
            texto_meso = "Todo o Estado (SC)"
        elif len(mesos_no_filtro) <= 2:
            texto_meso = ", ".join(mesos_no_filtro)
        else:
            texto_meso = f"{len(mesos_no_filtro)} Mesorregiões ({', '.join(sorted(mesos_no_filtro))})"

        # Associações de Municípios
        assocs_no_filtro = [a for a in df_filtrado['associacao'].unique() if a != 'Não informado']
        if len(assocs_no_filtro) >= 20:
            texto_assoc = "Todas / Diversas Associações de Municípios"
        elif len(assocs_no_filtro) <= 3:
            texto_assoc = ", ".join(assocs_no_filtro) if assocs_no_filtro else "Todas"
        else:
            texto_assoc = f"{len(assocs_no_filtro)} Associações de Municípios ({', '.join(sorted(assocs_no_filtro))})"

        # Municípios
        muns_selecionados = df_filtrado['municipio'].unique()
        if len(muns_selecionados) >= 293:
            texto_mun = "Todos os 295 Municípios"
        elif len(muns_selecionados) <= 4:
            texto_mun = ", ".join(muns_selecionados)
        else:
            texto_mun = f"{len(muns_selecionados)} Municípios selecionados"

        # Crimes
        crimes_selecionados = df_filtrado['fato_comunicado'].unique()
        if len(crimes_selecionados) >= 5 or ('Feminicídio' in crimes_selecionados and len(crimes_selecionados) == 1):
            texto_crime = "Todos os crimes cadastrados" if len(crimes_selecionados) > 1 else "Feminicídio"
        else:
            texto_crime = ", ".join(crimes_selecionados)

        # Idade
        if idade_selecionada is not None and hasattr(idade_selecionada, '__getitem__') and len(idade_selecionada) == 2:
            if idade_selecionada[0] == 0 and idade_selecionada[1] == 100:
                texto_idade = "Todas as idades (0 a 100+ anos)"
            else:
                idade_max = f"{idade_selecionada[1]} anos" if idade_selecionada[1] < 100 else "100+ anos"
                texto_idade = f"{idade_selecionada[0]} a {idade_max}"
        else:
            texto_idade = "Todas as idades (0 a 100+ anos)"

        # Agrupamento
        agrup_sel = st.session_state.get('agrupamento_selecionado', 'Município')

        filtros_box = f"""<div class="print-filters-box">
<div class="print-filters-title">📋 FILTROS E PARÂMETROS APLICADOS NESTE RELATÓRIO:</div>
<div class="print-filters-grid">
<div class="print-filter-item"><strong>• Período:</strong> {periodo_str}</div>
<div class="print-filter-item"><strong>• Abrangência:</strong> {texto_meso}</div>
<div class="print-filter-item"><strong>• Municípios:</strong> {texto_mun}</div>
<div class="print-filter-item"><strong>• Associações de Municípios:</strong> {texto_assoc}</div>
<div class="print-filter-item"><strong>• Crimes:</strong> {texto_crime}</div>
<div class="print-filter-item"><strong>• Faixa Etária:</strong> {texto_idade}</div>
<div class="print-filter-item"><strong>• Visualização:</strong> Agrupado por {agrup_sel}</div>
</div>
</div>"""
    else:
        filtros_box = f"""<div class="print-filters-box">
<div class="print-filters-title">📋 SEÇÃO DO SISTEMA:</div>
<div class="print-filters-grid">
<div class="print-filter-item"><strong>• Módulo:</strong> {active_tab}</div>
<div class="print-filter-item"><strong>• Escopo:</strong> Informações e Dados Oficiais OVM/SC</div>
</div>
</div>"""

    html = f"""<div class="print-institutional-header">
<div class="print-header-top">
<div class="print-logo-box">
{logo_img_tag}
</div>
<div class="print-title-box">
<h1 class="print-main-title">OBSERVATÓRIO DA VIOLÊNCIA CONTRA A MULHER - SC</h1>
<div class="print-sub-title">Relatório Analítico Oficial • {active_tab}</div>
<div class="print-emission-time">Emitido em: {data_emissao}</div>
</div>
</div>
{filtros_box}
</div>"""
    return html


def render_custom_header(df_geral_filtrado=None, idade_selecionada=None):
    """
    Renderiza o cabeçalho customizado no topo da página e injeta o cabeçalho de impressão.
    
    Args:
        df_geral_filtrado: DataFrame com os dados filtrados para os cards de resumo.
        idade_selecionada: Faixa etária selecionada (tupla min, max).
    """
    
    # Verifica a aba ativa para determinar a visibilidade dos cards
    active_tab = st.session_state.get('active_tab', 'Análise Geral')
    show_info_cards = active_tab in ["Análise Geral", "Análise de Feminicídios"]

    # Injeta cabeçalho institucional para impressão (Ctrl+P)
    print_header_html = build_institutional_print_header(df_geral_filtrado, idade_selecionada)
    st.markdown(print_header_html, unsafe_allow_html=True)

    # --- CSS PARA HEADER E CARDS ---
    header_style = textwrap.dedent("""
    <style>
        /* RESET & Compatibilidade */
        header[data-testid="stHeader"] {
            visibility: visible !important;
            background: transparent !important;
            box-shadow: none !important;
            z-index: 1000 !important;
        }

        [data-testid="stSidebarCollapsedControl"] button,
        [data-testid="stToolbar"] button,
        header[data-testid="stHeader"] button {
            color: #4a148c !important;
            fill: #4a148c !important;
        }

        footer { visibility: hidden; }

        /* AJUSTES DE LAYOUT PRINCIPAL */
        .block-container {
            padding-top: 1.5rem !important;
            padding-bottom: 2rem !important;
            max-width: 95% !important;
        }

        /* BOTÕES DE NAVEGAÇÃO RESPONSIVOS SEM QUEBRA DE PALAVRAS */
        .stButton > button,
        button[data-testid="stBaseButton-primary"],
        button[data-testid="stBaseButton-secondary"] {
            white-space: nowrap !important;
            word-break: keep-all !important;
            overflow: hidden !important;
            text-overflow: ellipsis !important;
            min-height: 42px !important;
            height: auto !important;
            padding: 0.55rem 0.85rem !important;
            font-size: clamp(0.78rem, 0.9vw, 0.95rem) !important;
            font-weight: 700 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.35rem !important;
            border-radius: 8px !important;
        }

        [data-testid="stHorizontalBlock"]:has(button[key*="btn_"]),
        [data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-secondary"]),
        [data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-primary"]) {
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
            margin-bottom: 0.75rem !important;
        }

        [data-testid="stHorizontalBlock"]:has(button[key*="btn_"]) > div,
        [data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-secondary"]) > div,
        [data-testid="stHorizontalBlock"]:has([data-testid="stBaseButton-primary"]) > div {
            flex: 1 1 200px !important;
            min-width: 175px !important;
            max-width: 100% !important;
        }

        /* CONTAINER PAI FIXO / STICKY NO STREAMLIT */
        div[data-testid="stElementContainer"]:has(.custom-info-cards-wrapper),
        div.element-container:has(.custom-info-cards-wrapper),
        [data-testid="stVerticalBlock"] > div:has(.custom-info-cards-wrapper) {
            position: -webkit-sticky !important;
            position: sticky !important;
            top: 0px !important;
            z-index: 995 !important;
            width: 100% !important;
        }

        /* BANNER DE CARDS DE RESUMO FIXO / STICKY COM EFEITO VIDRO */
        .custom-info-cards-wrapper {
            position: -webkit-sticky !important;
            position: sticky !important;
            top: 0px !important;
            z-index: 995 !important;
            background: linear-gradient(135deg, rgba(46, 8, 84, 0.90) 0%, rgba(74, 20, 140, 0.90) 50%, rgba(106, 27, 154, 0.90) 100%) !important;
            border-radius: 12px !important;
            padding: 0.65rem 1rem !important;
            margin-bottom: 1.5rem !important;
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.25) !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 0.4rem !important;
            -webkit-backdrop-filter: blur(16px) !important;
            backdrop-filter: blur(16px) !important;
            border: 1px solid rgba(255, 255, 255, 0.22) !important;
        }

        .header-info-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.6rem;
            flex-wrap: wrap;
            width: 100%;
        }

        .info-container {
            display: flex;
            gap: 0.6rem;
            width: 100%;
            justify-content: center;
            align-items: stretch;
            flex-wrap: wrap;
        }

        .info-card {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: #ffffff !important;
            border-radius: 8px !important;
            padding: 0.45rem 0.75rem !important;
            flex: 1 1 140px;
            min-width: 130px;
            max-width: 210px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1) !important;
            border: 1px solid rgba(142, 36, 170, 0.25) !important;
            transition: all 0.2s ease;
        }

        .info-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.15) !important;
            border-color: #8e24aa !important;
        }

        .info-card h5 {
            margin: 0 0 0.15rem 0 !important;
            color: #666666 !important;
            font-size: 10.5px !important;
            text-transform: uppercase !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px !important;
            text-align: center;
        }

        .info-card p {
            margin: 0 !important;
            color: #1a1a1a !important;
            font-weight: 800 !important;
            font-size: 14px !important;
            text-align: center;
            line-height: 1.2;
        }

        .info-card span {
            font-size: 10.5px !important;
            color: #7b1fa2 !important;
            font-weight: 600 !important;
            text-align: center;
            margin-top: 0.15rem !important;
        }

        /* EXPANDER HTML NO HEADER */
        .header-expander {
            margin-top: 0.25rem;
            padding: 0.4rem 0.8rem;
            background: white;
            border: 1px solid rgba(142, 36, 170, 0.3);
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.08);
            width: fit-content;
            margin-left: auto;
            margin-right: auto;
            color: #4a148c;
        }

        .header-expander:hover {
            background: #faf7fc;
            border-color: #8e24aa;
        }

        .header-expander summary {
            font-weight: 600;
            color: #4a148c;
            font-size: 12px;
            outline: none;
            user-select: none;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            justify-content: center;
        }

        .header-expander[open] summary {
            color: #6a1b9a;
            margin-bottom: 0.4rem;
            border-bottom: 1px solid rgba(0, 0, 0, 0.08);
            padding-bottom: 0.2rem;
        }

        .expander-content {
            font-size: 12px;
            color: #333;
            line-height: 1.4;
            text-align: center;
        }

        .expander-content p {
            margin: 0.2rem 0;
            word-break: break-word;
        }

        .expander-content strong {
            color: #4a148c;
            font-weight: 700;
        }

        /* Oculta o header de resumo de filtros no celular */
        @media (max-width: 768px) {
            .custom-info-cards-wrapper,
            div[data-testid="stElementContainer"]:has(.custom-info-cards-wrapper),
            div.element-container:has(.custom-info-cards-wrapper),
            [data-testid="stVerticalBlock"] > div:has(.custom-info-cards-wrapper) {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                max-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }
        }

        @media print {
            .block-container,
            .main,
            [data-testid="stMain"],
            [data-testid="stMainBlockContainer"] {
                padding-top: 0 !important;
                margin-top: 0 !important;
            }

            [data-testid="stHeader"],
            header[data-testid="stHeader"],
            .custom-info-cards-wrapper,
            [data-testid="stElementContainer"]:has(button),
            [data-testid="stHorizontalBlock"]:has(button),
            div.element-container:has(button),
            div[data-testid="stElementContainer"]:has(.custom-info-cards-wrapper),
            div.element-container:has(.custom-info-cards-wrapper),
            [data-testid="stVerticalBlock"] > div:has(.custom-info-cards-wrapper) {
                display: none !important;
                visibility: hidden !important;
                height: 0 !important;
                max-height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
            }

            .print-institutional-header {
                display: block !important;
                width: 100% !important;
                margin-top: 0 !important;
                padding-top: 0 !important;
            }
        }
    </style>
    """)

    # --- INJETAR CSS ---
    st.markdown(header_style, unsafe_allow_html=True)

    # --- CONSTRUIR INFO CARDS HTML ---
    def build_info_html(df_filtrado):
        """Constrói os cards de informação dos filtros"""
        if 'data_inicial' not in st.session_state or 'data_final' not in st.session_state or df_filtrado is None or df_filtrado.empty:
            return ""

        data_ini = st.session_state.data_inicial
        data_fim = st.session_state.data_final
        dias_totais = (data_fim - data_ini).days

        # --- MESORREGIÕES ---
        mesos_no_filtro = df_filtrado['mesoregiao'].unique()
        mesos_reais = [m for m in mesos_no_filtro if m != 'Não informado']
        qtd_mesos = len(mesos_reais)

        if qtd_mesos >= 6:
            texto_meso = "Todo o Estado (SC)"
            detalhe_meso = None
        elif qtd_mesos <= 2:
            texto_meso = ", ".join(mesos_reais[:2])
            detalhe_meso = ", ".join(sorted(mesos_reais))
        else:
            texto_meso = f"{qtd_mesos} Mesorregiões"
            detalhe_meso = ", ".join(sorted(mesos_reais))

        # --- ASSOCIAÇÕES DE MUNICÍPIOS ---
        assocs_no_filtro = df_filtrado['associacao'].unique()
        assocs_reais = [a for a in assocs_no_filtro if a != 'Não informado']
        qtd_assocs = len(assocs_reais)

        if qtd_assocs >= 20:
            texto_assoc = "Diversas Associações de Municípios"
            detalhe_assoc = None
        elif qtd_assocs <= 1:
            texto_assoc = assocs_reais[0] if assocs_reais else "Nenhuma"
            detalhe_assoc = None
        elif qtd_assocs <= 3:
            texto_assoc = ", ".join(assocs_reais[:3])
            detalhe_assoc = ", ".join(sorted(assocs_reais))
        else:
            texto_assoc = f"{qtd_assocs} Associações de Municípios"
            detalhe_assoc = ", ".join(sorted(assocs_reais))

        # --- MUNICÍPIOS ---
        muns_selecionados = df_filtrado['municipio'].unique()
        qtd_mun = len(muns_selecionados)

        if qtd_mun >= 293:
            texto_mun = "Todos os 295 Municípios"
            mostrar_expander_mun = False
        elif qtd_mun == 1:
            texto_mun = muns_selecionados[0]
            mostrar_expander_mun = False
        else:
            texto_mun = f"{qtd_mun} Municípios"
            mostrar_expander_mun = True

        # --- TIPOS DE CRIME ---
        crimes_selecionados = df_filtrado['fato_comunicado'].unique()
        qtd_crimes = len(crimes_selecionados)
        
        if qtd_crimes <= 2:
            texto_crime = ", ".join(crimes_selecionados)
            detalhe_crime = None
        else:
            texto_crime = f"{qtd_crimes} Tipos de Crime"
            detalhe_crime = ", ".join(sorted(crimes_selecionados))

        # Monta HTML do expander se necessário
        expander_html = ""
        tem_detalhe = any([detalhe_meso, detalhe_assoc, mostrar_expander_mun, detalhe_crime])
        
        if tem_detalhe:
            corpo_expander = ""
            if detalhe_meso: corpo_expander += f"<p><strong>Mesorregiões:</strong> {detalhe_meso}</p>"
            if detalhe_assoc: corpo_expander += f"<p><strong>Associações de Municípios:</strong> {detalhe_assoc}</p>"
            if mostrar_expander_mun: 
                lista_mun = ", ".join(sorted(muns_selecionados))
                corpo_expander += f"<p><strong>Municípios:</strong> {lista_mun}</p>"
            if detalhe_crime: corpo_expander += f"<p><strong>Crimes:</strong> {detalhe_crime}</p>"

            expander_html = f'<details class="header-expander"><summary>🔎 Ver detalhes selecionados</summary><div class="expander-content">{corpo_expander}</div></details>'

        info_html = f"""
<div class="header-info-row">
<div class="info-container">
<div class="info-card">
<h5>📅 Período</h5>
<p>{data_ini.strftime("%d/%m/%Y")} - {data_fim.strftime("%d/%m/%Y")}</p>
<span>{dias_totais} dias</span>
</div>
<div class="info-card">
<h5>🗺️ Abrangência</h5>
<p>{texto_meso}</p>
<span>Mesorregiões</span>
</div>
<div class="info-card">
<h5>🏢 Associações de Municípios</h5>
<p>{texto_assoc}</p>
<span>Selecionadas</span>
</div>
<div class="info-card">
<h5>📍 Municípios</h5>
<p>{texto_mun}</p>
<span>Selecionados</span>
</div>
<div class="info-card">
<h5>⚖️ Crimes</h5>
<p>{texto_crime}</p>
<span>Tipos</span>
</div>
</div>
{expander_html}
</div>
"""
        return info_html

    # Renderiza os cards de info APENAS se a aba permitir
    if show_info_cards:
        info_html = build_info_html(df_geral_filtrado)
        if info_html:
            st.markdown(f'''
<div class="custom-info-cards-wrapper">
{info_html}
</div>
''', unsafe_allow_html=True)


def render_tab_buttons():
    """
    Renderiza os botões de navegação das abas e o botão de atalho para impressão.
    """

    # Callbacks para mudar de aba
    def mudar_aba(nome_aba):
        st.session_state.active_tab = nome_aba

    # Cria os botões de abas em colunas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tipo = "primary" if st.session_state.get('active_tab') == "Análise Geral" else "secondary"
        st.button(
            "📊 Análise Geral",
            key="btn_analise_geral",
            on_click=mudar_aba,
            args=("Análise Geral",),
            type=tipo,
            use_container_width=True
        )

    with col2:
        tipo = "primary" if st.session_state.get('active_tab') == "Análise de Feminicídios" else "secondary"
        st.button(
            "🚨 Análise de Feminicídios",
            key="btn_feminicidios",
            on_click=mudar_aba,
            args=("Análise de Feminicídios",),
            type=tipo,
            use_container_width=True
        )

    with col3:
        tipo = "primary" if st.session_state.get('active_tab') == "Metodologia e Glossário" else "secondary"
        st.button(
            "📖 Metodologia e Glossário",
            key="btn_metodologia",
            on_click=mudar_aba,
            args=("Metodologia e Glossário",),
            type=tipo,
            use_container_width=True
        )

    with col4:
        tipo = "primary" if st.session_state.get('active_tab') == "Download de Dados" else "secondary"
        st.button(
            "📥 Download de Dados",
            key="btn_download",
            on_click=mudar_aba,
            args=("Download de Dados",),
            type=tipo,
            use_container_width=True
        )
