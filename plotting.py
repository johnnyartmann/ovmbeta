import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def plot_mapa_geral(map_df, geojson_sc, color_col, label_text, agrupamento_selecionado):
    """Gera o mapa coroplético para a análise geral."""
    
    # Configuração dos rótulos (labels) para aparecerem bonitos no tooltip
    hover_labels = {
        'municipio_normalizado': 'Município',
        'mesoregiao': 'Mesorregião',
        'associacao': 'Associação de Municípios',
        color_col: label_text
    }
    
    # Configuração do que aparece no hover
    # True = aparece, False = esconde (útil para o ID que já está no título)
    hover_data_config = {
        'municipio_normalizado': False, 
        'mesoregiao': True, 
        'associacao': True,
        color_col: True
    }

    fig_mapa = px.choropleth_mapbox(
        map_df, 
        geojson=geojson_sc, 
        locations='municipio_normalizado',
        featureidkey="properties.NM_MUN_NORMALIZADO",
        color=color_col, 
        color_continuous_scale="Reds", 
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": -27.59, "lon": -50.52}, 
        opacity=0.7,
        labels=hover_labels,
        hover_name='municipio_normalizado', # Define o título da caixa como o nome do município
        hover_data=hover_data_config
    )
    
    fig_mapa.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0}, 
        coloraxis_showscale=True,
        coloraxis_colorbar=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
        separators=",."
    )
    return fig_mapa


def formatar_ano_mes(val):
    if not isinstance(val, str) or '-' not in val:
        return val
    try:
        parts = val.split('-')
        if len(parts) >= 2:
            ano, mes = parts[0], parts[1]
            nomes_meses = {
                '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
                '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
                '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
            }
            return f"{nomes_meses.get(mes, mes)}/{ano}"
        return val
    except Exception:
        return val


def plot_serie_temporal(registros_por_mes_ano, chart_type, agrupamento_selecionado, color_param_temporal):
    """Gera o gráfico de série temporal."""
    df_temp = registros_por_mes_ano.copy()
    df_temp['ano_mes'] = df_temp['ano_mes'].apply(formatar_ano_mes)
    
    if chart_type == "Barras":
        fig = px.bar(df_temp, x='ano_mes', y='quantidade', color=color_param_temporal,
                     labels={'ano_mes': 'Mês/Ano', 'quantidade': 'Quantidade de Registros'}, template='plotly_white')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(marker_color='#8A2BE2')
    elif chart_type == "Área":
        fig = px.area(df_temp, x='ano_mes', y='quantidade', color=color_param_temporal,
                      labels={'ano_mes': 'Mês/Ano', 'quantidade': 'Quantidade de Registros'}, template='plotly_white')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(line_color='#8A2BE2')
    else:  # Linha
        fig = px.line(df_temp, x='ano_mes', y='quantidade', color=color_param_temporal,
                      labels={'ano_mes': 'Mês/Ano', 'quantidade': 'Quantidade de Registros'}, template='plotly_white',
                      markers=True)
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(line_color='#8A2BE2')
    fig.update_layout(separators=",.")
    fig.update_xaxes(type='category')
    return fig


def plot_dia_semana(registros_por_dia, chart_type):
    """Gera o gráfico de distribuição por dia da semana."""
    if chart_type == "Barras":
        fig = px.bar(registros_por_dia, x='Dia da Semana', y='Quantidade',
                     labels={'x': 'Dia da Semana', 'y': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        fig.update_traces(marker_color='#8A2BE2', textposition='outside')
    elif chart_type == "Linha":
        fig = px.line(registros_por_dia, x='Dia da Semana', y='Quantidade',
                      labels={'x': 'Dia da Semana', 'y': 'Quantidade'},
                      template='plotly_white', markers=True)
        fig.update_traces(line_color='#8A2BE2')
    elif chart_type == "Área":
        fig = px.area(registros_por_dia, x='Dia da Semana', y='Quantidade',
                      labels={'x': 'Dia da Semana', 'y': 'Quantidade'},
                      template='plotly_white')
        fig.update_traces(line_color='#8A2BE2')
    else:  # Pizza
        fig = px.pie(registros_por_dia, names='Dia da Semana', values='Quantidade', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_traces(textinfo='percent+label', textposition='outside')
    fig.update_layout(separators=",.")
    return fig


def plot_por_ano(registros_por_ano, chart_type, agrupamento_selecionado, color_param):
    """Gera o gráfico de ocorrências por ano."""
    if chart_type == "Barras":
        fig = px.bar(registros_por_ano, x='ano', y='Quantidade', color=color_param,
                     labels={'ano': 'Ano', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(marker_color='#8A2BE2')
        fig.update_traces(textposition='outside')
    elif chart_type == "Linha":
        fig = px.line(registros_por_ano, x='ano', y='Quantidade', color=color_param,
                      labels={'ano': 'Ano', 'Quantidade': 'Quantidade'},
                      template='plotly_white', markers=True)
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(line_color='#8A2BE2')
    elif chart_type == "Área":
        fig = px.area(registros_por_ano, x='ano', y='Quantidade', color=color_param,
                      labels={'ano': 'Ano', 'Quantidade': 'Quantidade'},
                      template='plotly_white')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(line_color='#8A2BE2')
    else:  # Pizza
        fig = px.pie(registros_por_ano, names='ano', values='Quantidade', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_traces(textinfo='percent+label', textposition='outside')
    fig.update_layout(separators=",.")
    return fig


def plot_por_mes(registros_por_mes, chart_type):
    """Gera o gráfico de ocorrências por mês."""
    if chart_type == "Barras":
        fig = px.bar(registros_por_mes, x='Mês', y='Quantidade', labels={'x': 'Mês', 'y': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        fig.update_traces(marker_color='#9370DB', textposition='outside')
    elif chart_type == "Linha":
        fig = px.line(registros_por_mes, x='Mês', y='Quantidade', labels={'x': 'Mês', 'y': 'Quantidade'},
                      template='plotly_white', markers=True)
        fig.update_traces(line_color='#9370DB')
    elif chart_type == "Área":
        fig = px.area(registros_por_mes, x='Mês', y='Quantidade', labels={'x': 'Mês', 'y': 'Quantidade'},
                      template='plotly_white')
        fig.update_traces(line_color='#9370DB')
    else:
        fig = px.pie(registros_por_mes, names='Mês', values='Quantidade', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_traces(textinfo='percent+label', textposition='outside', sort=False)
    fig.update_layout(separators=",.")
    return fig


def plot_faixa_etaria(registros_por_faixa, chart_type):
    """Gera o gráfico de distribuição por faixa etária."""
    if chart_type == "Barras":
        fig = px.bar(registros_por_faixa, x='Faixa Etária', y='Quantidade',
                     labels={'x': 'Faixa Etária', 'y': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        fig.update_traces(marker_color='#9370DB', textposition='outside')
    else:  # Pizza
        fig = px.pie(registros_por_faixa, names='Faixa Etária', values='Quantidade', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_traces(textinfo='percent+label', textposition='outside')
    fig.update_layout(separators=",.")
    return fig


def plot_tipo_crime(registros_por_fato, chart_type, agrupamento_selecionado, color_param):
    """Gera o gráfico de tipos de crimes mais frequentes."""
    if chart_type == "Barras":
        fig = px.bar(registros_por_fato, x='Quantidade', y='fato_comunicado', color=color_param, orientation='h',
                     labels={'fato_comunicado': 'Tipo de Crime', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(marker_color='#9370DB')
        fig.update_traces(textposition='auto')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    else:  # Pizza
        fig = px.pie(registros_por_fato, names='fato_comunicado', values='Quantidade', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_traces(textinfo='percent+label', textposition='outside')
        fig.update_layout(separators=",.")
    return fig


def plot_mapa_feminicidio(map_df_fem, geojson_sc, agrupamento_selecionado):
    """Gera o mapa coroplético de feminicídios."""
    
    label_qtd = f'Total de Feminicídios ({agrupamento_selecionado})'
    
    hover_labels = {
        'municipio_normalizado': 'Município',
        'mesoregiao': 'Mesorregião',
        'associacao': 'Associação de Municípios',
        'quantidade': label_qtd
    }
    
    hover_data_config = {
        'municipio_normalizado': False,
        'mesoregiao': True,
        'associacao': True,
        'quantidade': True
    }

    fig = px.choropleth_mapbox(
        map_df_fem, 
        geojson=geojson_sc, 
        locations='municipio_normalizado',
        featureidkey="properties.NM_MUN_NORMALIZADO",
        color='quantidade', 
        color_continuous_scale="Reds", 
        mapbox_style="carto-positron", 
        zoom=6,
        center={"lat": -27.59, "lon": -50.52}, 
        opacity=0.7,
        labels=hover_labels,
        hover_name='municipio_normalizado',
        hover_data=hover_data_config
    )
    
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, coloraxis_showscale=True,
                      coloraxis_colorbar=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
                      separators=",.")
    return fig


def plot_feminicidio_serie_temporal(feminicidios_por_mes, chart_type, agrupamento_selecionado, color_param):
    """Gera o gráfico de série temporal de feminicídios."""
    df_temp = feminicidios_por_mes.copy()
    df_temp['Mês/Ano'] = df_temp['Mês/Ano'].apply(formatar_ano_mes)
    
    if chart_type == "Linha":
        fig = px.line(df_temp, x='Mês/Ano', y='Quantidade', color=color_param,
                      labels={'Mês/Ano': 'Mês/Ano', 'Quantidade': 'Quantidade'},
                      template='plotly_white', markers=True)
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(line_color='#8A2BE2')
    elif chart_type == "Área":
        fig = px.area(df_temp, x='Mês/Ano', y='Quantidade', color=color_param,
                      labels={'Mês/Ano': 'Mês/Ano', 'Quantidade': 'Quantidade'},
                      template='plotly_white')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(line_color='#8A2BE2')
    else:  # Barras
        fig = px.bar(df_temp, x='Mês/Ano', y='Quantidade', color=color_param,
                     labels={'Mês/Ano': 'Mês/Ano', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(marker_color='#8A2BE2')
        fig.update_traces(textposition='outside')
    fig.update_layout(separators=",.")
    fig.update_xaxes(type='category')
    return fig


def plot_feminicidio_por_ano(feminicidios_por_ano, chart_type, agrupamento_selecionado, color_param):
    """Gera o gráfico de feminicídios por ano."""
    if chart_type == "Linha":
        fig = px.line(feminicidios_por_ano, x='ano', y='Quantidade', color=color_param,
                      labels={'ano': 'Ano', 'Quantidade': 'Quantidade'},
                      template='plotly_white', markers=True)
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(line_color='#6a1b9a')
    elif chart_type == "Área":
        fig = px.area(feminicidios_por_ano, x='ano', y='Quantidade', color=color_param,
                      labels={'ano': 'Ano', 'Quantidade': 'Quantidade'},
                      template='plotly_white')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(line_color='#6a1b9a')
    else:  # Barras
        fig = px.bar(feminicidios_por_ano, x='ano', y='Quantidade', color=color_param,
                     labels={'ano': 'Ano', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(marker_color='#6a1b9a')
        fig.update_traces(textposition='outside')
    fig.update_layout(separators=",.")
    return fig


def plot_vinculo_autor(vinculo_autor, chart_type, agrupamento_selecionado, color_param):
    """Gera o gráfico de vínculo entre vítima e autor."""
    if chart_type == "Barras":
        fig = px.bar(vinculo_autor, x='Quantidade', y='relacao_autor', color=color_param, orientation='h',
                     labels={'relacao_autor': 'Vínculo com o Autor', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(marker_color='#8A2BE2')
        fig.update_traces(textposition='auto')
        fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    else:  # Pizza
        fig = px.pie(vinculo_autor, names='relacao_autor', values='Quantidade', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_traces(textinfo='percent+label', textposition='outside')
        fig.update_layout(separators=",.")
    return fig


def plot_bo_contra_autor(bo_contra_autor, chart_type):
    """Gera o gráfico de B.O. da vítima contra o autor."""
    if chart_type == "Barras":
        fig = px.bar(bo_contra_autor, x='Resposta', y='Quantidade',
                     labels={'Resposta': 'Resposta', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        fig.update_traces(marker_color='#8e24aa', textposition='outside')
    else:  # Pizza
        fig = px.pie(bo_contra_autor, names='Resposta', values='Quantidade', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
    fig.update_layout(separators=",.")
    return fig


def plot_distribuicao_idade(df_idade, column_name, chart_type, x_axis_label, color):
    """Gera o gráfico de distribuição de idade."""
    if chart_type == "Histograma":
        fig = px.histogram(df_idade, x=column_name, nbins=20,
                           labels={column_name: x_axis_label, 'count': 'Quantidade'},
                           template='plotly_white', color_discrete_sequence=[color])
    else: 
        fig = px.violin(df_idade, y=column_name,
                        labels={column_name: x_axis_label},
                        template='plotly_white', color_discrete_sequence=[color], box=True, points="all")
    fig.update_layout(separators=",.")
    return fig


def plot_scatter_idade(df_feminicidio_filtrado):
    """Gera o gráfico de dispersão de idades (vítima vs. autor)."""
    fig = px.scatter(df_feminicidio_filtrado.dropna(subset=['idade_vitima', 'idade_autor']),
                     x='idade_vitima', y='idade_autor',
                     labels={'idade_vitima': 'Idade da Vítima', 'idade_autor': 'Idade do Autor'},
                     color_discrete_sequence=['#8e24aa'],
                     hover_data=['municipio', 'relacao_autor', 'meio_crime'])
    max_idade = max(df_feminicidio_filtrado['idade_vitima'].max(), df_feminicidio_filtrado['idade_autor'].max())
    fig.add_shape(type='line', x0=0, y0=0, x1=max_idade, y1=max_idade,
                  line=dict(color='rgba(255, 0, 0, 0.5)', width=2, dash='dash'), name='Idade Igual')
    fig.update_layout(xaxis_title="Idade da Vítima", yaxis_title="Idade do Autor", legend_title="Legenda", separators=",.")
    return fig


def plot_sankey_agressor(df_feminicidio_filtrado):
    """Gera o gráfico de Sankey para o histórico do agressor."""
    total_agressores = len(df_feminicidio_filtrado)
    
    # Tratamento para garantir que 'SIM' seja contado corretamente independente da capitalização
    passagem_col = df_feminicidio_filtrado['passagem_policial'].astype(str).str.upper()
    com_passagem = passagem_col.value_counts().get('SIM', 0)
    
    sem_passagem = total_agressores - com_passagem
    
    # Filtro para violência doméstica (também garantindo uppercase)
    com_bo_vd = len(df_feminicidio_filtrado[
                        (passagem_col == 'SIM') & 
                        (df_feminicidio_filtrado['passagem_por_violencia_domestica'].astype(str).str.upper() == 'SIM')])
    
    com_bo_outros = com_passagem - com_bo_vd

    if total_agressores > 0:
        fig = go.Figure(data=[go.Sankey(
            node=dict(pad=20, thickness=25, line=dict(color="white", width=2),
                      label=["Total de Agressores", "Com Passagem Policial", "Sem Passagem Policial",
                             "Com B.O. por Violência Doméstica", "Com B.O. por Outros Crimes"],
                      color=["#4a148c", "#d32f2f", "#757575", "#e91e63", "#ff6f00"]),
            link=dict(source=[0, 0, 1, 1], target=[1, 2, 3, 4],
                      value=[com_passagem, sem_passagem, com_bo_vd, com_bo_outros],
                      color=["rgba(211, 47, 47, 0.4)", "rgba(117, 117, 117, 0.3)", "rgba(233, 30, 99, 0.5)",
                             "rgba(255, 111, 0, 0.4)"]),
            textfont=dict(family="Inter, sans-serif", size=14, color="white"))])
        
        fig.update_layout(
            font=dict(size=13, family="Inter, sans-serif"), 
            plot_bgcolor='white', 
            paper_bgcolor='white',
            margin=dict(t=0, b=20, l=10, r=10),
            separators=",."
        )
        
        return fig
    return go.Figure().add_annotation(text="Dados do histórico do agressor indisponíveis para os filtros atuais.",
                                       showarrow=False, font=dict(size=14))


def plot_heatmap_cruzado(df_heatmap_cruzado):
    """Gera o heatmap de análise cruzada (vítima vs. agressor)."""
    df_heatmap_cruzado = df_heatmap_cruzado.copy()
    bins = [0, 17, 29, 40, 50, 60, 120]
    labels = ['0-17 anos', '18-29 anos', '30-40 anos', '41-50 anos', '51-60 anos', '60+ anos']

    df_heatmap_cruzado['faixa_etaria_vitima'] = pd.cut(df_heatmap_cruzado['idade_vitima'], bins=bins, labels=labels,
                                                      right=True)
    df_heatmap_cruzado['faixa_etaria_autor'] = pd.cut(df_heatmap_cruzado['idade_autor'], bins=bins, labels=labels,
                                                     right=True)

    df_heatmap_cruzado['faixa_etaria_vitima'] = pd.Categorical(df_heatmap_cruzado['faixa_etaria_vitima'],
                                                              categories=labels, ordered=True)
    df_heatmap_cruzado['faixa_etaria_autor'] = pd.Categorical(df_heatmap_cruzado['faixa_etaria_autor'],
                                                             categories=labels, ordered=True)

    heatmap_data = df_heatmap_cruzado.groupby(['faixa_etaria_vitima', 'faixa_etaria_autor'],
                                              observed=False).size().unstack(fill_value=0)

    heatmap_data = heatmap_data.reindex(index=labels, columns=labels, fill_value=0)

    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_data.columns,
        y=heatmap_data.index,
        colorscale='Purples',
        hoverongaps=False,
        text=heatmap_data.values,
        texttemplate="%{text}"
    ))

    fig.update_layout(
        xaxis_title="Faixa Etária do Agressor",
        yaxis_title="Faixa Etária da Vítima",
        margin=dict(t=0, b=50, l=0, r=0),
        separators=",."
    )
    return fig


def plot_meio_crime(meio_crime, chart_type, agrupamento_selecionado, color_param):
    """Gera o gráfico de meio utilizado para o crime."""
    if chart_type == "Barras":
        fig = px.bar(meio_crime, x='meio_crime', y='Quantidade', color=color_param,
                     labels={'meio_crime': 'Meio Utilizado', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(marker_color='#8A2BE2')
        fig.update_traces(textposition='outside')
    else:  # Pizza
        fig = px.pie(meio_crime, names='meio_crime', values='Quantidade', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_traces(textinfo='percent+label', textposition='outside')
    fig.update_layout(separators=",.")
    return fig


def plot_autor_preso(autor_preso, chart_type):
    """Gera o gráfico se o autor foi preso."""
    if chart_type == "Barras":
        fig = px.bar(autor_preso, x='Resposta', y='Quantidade',
                     labels={'Resposta': 'Resposta', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        fig.update_traces(marker_color='#ab47bc', textposition='outside')
    else:  # Pizza
        fig = px.pie(autor_preso, names='Resposta', values='Quantidade', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
    fig.update_layout(separators=",.")
    return fig


def plot_passagem_policial(autor_bo, chart_type, title, color):
    """Gera o gráfico de passagem policial do autor."""
    if chart_type == "Barras":
        fig = px.bar(autor_bo, x='Resposta', y='Quantidade',
                     labels={'Resposta': 'Resposta', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        fig.update_traces(marker_color=color, textposition='outside')
    else:  # Pizza
        fig = px.pie(autor_bo, names='Resposta', values='Quantidade', hole=0.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
    fig.update_layout(separators=",.")
    return fig


def plot_localidade_crime(localidade_crime, chart_type, agrupamento_selecionado, color_param):
    """Gera o gráfico de localidade do crime."""
    if chart_type == "Barras":
        fig = px.bar(localidade_crime, x='localidade', y='Quantidade', color=color_param,
                     labels={'localidade': 'Localidade', 'Quantidade': 'Quantidade'},
                     template='plotly_white', text='Quantidade')
        if agrupamento_selecionado == "Consolidado":
            fig.update_traces(marker_color='#8A2BE2')
        fig.update_traces(textposition='outside')
    else:  # Pizza
        fig = px.pie(localidade_crime, names='localidade', values='Quantidade', hole=.4,
                     color_discrete_sequence=px.colors.sequential.Purples_r)
        fig.update_traces(textinfo='percent+label', textposition='outside')
    fig.update_layout(separators=",.")
    return fig


def plot_mapa_letalidade(map_df_letalidade, geojson_sc, agrupamento_selecionado="Município"):
    """Gera o mapa coroplético do índice de letalidade com tooltips formatados."""
    hover_labels = {
        'municipio': 'Município',
        'municipio_normalizado': 'Município',
        'mesoregiao': 'Mesorregião',
        'associacao': 'Associação de Municípios',
        'total_eventos': 'Total de Eventos',
        'total_ocorrencias': 'Ocorrências de Violência',
        'total_feminicidios': 'Feminicídios',
        'indice_letalidade': 'Índice de Letalidade (%)'
    }

    hover_data_config = {
        'municipio_normalizado': False,
        'mesoregiao': True if 'mesoregiao' in map_df_letalidade.columns else False,
        'associacao': True if 'associacao' in map_df_letalidade.columns else False,
        'total_feminicidios': ':.0f' if 'total_feminicidios' in map_df_letalidade.columns else False,
        'total_ocorrencias': ':.0f' if 'total_ocorrencias' in map_df_letalidade.columns else False,
        'indice_letalidade': ':.2f'
    }

    hover_name_col = 'municipio' if 'municipio' in map_df_letalidade.columns and map_df_letalidade['municipio'].notna().any() else 'municipio_normalizado'

    fig = px.choropleth_mapbox(
        map_df_letalidade,
        geojson=geojson_sc,
        locations='municipio_normalizado',
        featureidkey="properties.NM_MUN_NORMALIZADO",
        color='indice_letalidade',
        color_continuous_scale="Reds",
        mapbox_style="carto-positron",
        zoom=6,
        center={"lat": -27.59, "lon": -50.52},
        opacity=0.7,
        labels=hover_labels,
        hover_name=hover_name_col,
        hover_data=hover_data_config
    )
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        coloraxis_showscale=True,
        coloraxis_colorbar=dict(
            title="Letalidade (%)",
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5
        ),
        separators=",."
    )
    return fig


def plot_barras_vulnerabilidade(df_plot):
    """Gera o gráfico de barras de vulnerabilidade."""
    fig = px.bar(df_plot, x='faixa_etaria', y='percentual', color='fato_comunicado',
                 title="Distribuição Percentual de Tipos de Crime por Faixa Etária",
                 labels={'faixa_etaria': 'Faixa Etária da Vítima', 'percentual': 'Percentual de Ocorrências (%)',
                         'fato_comunicado': 'Tipo de Crime'},
                 template='plotly_white', color_discrete_sequence=px.colors.sequential.Purples_r)
    fig.update_layout(barmode='stack', yaxis_ticksuffix='%', separators=",.")
    return fig


def plot_heatmap_vulnerabilidade(crime_counts_heatmap):
    """Gera o heatmap de vulnerabilidade com normalização por coluna (tipo de crime)."""
    # Normaliza cada coluna dividindo pelo valor máximo daquela coluna
    df_normalized = crime_counts_heatmap.div(crime_counts_heatmap.max(axis=0), axis=1).fillna(0)

    fig = go.Figure(data=go.Heatmap(
        z=df_normalized.values,
        x=crime_counts_heatmap.columns,
        y=crime_counts_heatmap.index,
        colorscale='Purples',
        hoverongaps=False,
        customdata=crime_counts_heatmap.values,
        hovertemplate='<b>%{x}</b><br>%{y}<br>Ocorrências: %{customdata}<extra></extra>'
    ))
    fig.update_layout(title="Concentração de Crimes por Faixa Etária",
                      xaxis_title="Tipo de Crime", yaxis_title="Faixa Etária da Vítima",
                      separators=",.")
    return fig


def plot_efetividade_denuncia(df_efetividade):
    """Gera o gráfico de dispersão para a efetividade da denúncia."""
    fig = px.scatter(df_efetividade, x='taxa_crimes_leves', y='taxa_crimes_graves', hover_name='municipio',
                     hover_data={'total_crimes_leves': ':.0f', 'total_crimes_graves': ':.0f',
                                 'populacao_feminina': ':.0f', 'municipio': False},
                     labels={'taxa_crimes_leves': 'Taxa de Crimes Leves (por 1.000 mulheres)',
                             'taxa_crimes_graves': 'Taxa de Crimes Graves (por 1.000 mulheres)'},
                     title="Efetividade da Denúncia: Crimes Leves vs. Graves por Município")
    fig.update_traces(marker=dict(size=10, opacity=0.7, color='#8e24aa'))

    # Linha de tendência manual (sem statsmodels)
    import numpy as np
    x = df_efetividade['taxa_crimes_leves'].dropna().values
    y = df_efetividade['taxa_crimes_graves'].dropna().values
    if len(x) > 1 and len(x) == len(y):
        coeffs = np.polynomial.polynomial.polyfit(x, y, 1)
        x_sorted = np.sort(x)
        y_trend = np.polynomial.polynomial.polyval(x_sorted, coeffs)
        fig.add_trace(go.Scatter(x=x_sorted, y=y_trend, mode='lines',
                                 line=dict(dash='dash', color='rgba(142,36,170,0.5)', width=2),
                                 name='Tendência', showlegend=False))

    fig.update_layout(separators=",.")
    return fig


def plot_barras_sazonal(df_medias):
    """Gera o gráfico de barras para a análise sazonal."""
    fig = px.bar(df_medias, x='Tipo de Dia', y='Média Diária de Ocorrências', text='Média Diária de Ocorrências',
                 labels={'Média Diária de Ocorrências': 'Média de Ocorrências por Dia', 'Tipo de Dia': ''},
                 template='plotly_white')
    fig.update_traces(marker_color='#8e24aa', texttemplate='%{text:.2f}', textposition='outside')
    fig.update_layout(margin=dict(t=0, b=20, l=10, r=10), separators=",.")
    return fig


def plot_heatmap_sazonal(heatmap_pivot):
    """Gera o heatmap para a análise sazonal."""
    fig = go.Figure(data=go.Heatmap(z=heatmap_pivot.values, x=heatmap_pivot.columns, y=heatmap_pivot.index,
                                    colorscale='Purples', hoverongaps=False, text=heatmap_pivot.values,
                                    texttemplate="%{text:.2f}"))
    fig.update_layout(title="Concentração Média de Ocorrências por Mês e Dia da Semana",
                      xaxis_title="Dia da Semana", yaxis_title="Mês",
                      xaxis={'type': 'category'},
                      yaxis={'type': 'category', 'categoryorder': 'array',
                             'categoryarray': list(heatmap_pivot.index)},
                      separators=",.")
    return fig


def plot_barras_feriados(df_feriados):
    """Gera o gráfico de barras para os feriados com mais ocorrências."""
    fig = px.bar(df_feriados, x='nome_feriado', y='total_ocorrencias',
                 labels={'nome_feriado': 'Feriado', 'total_ocorrencias': 'Quantidade de Ocorrências'},
                 template='plotly_white', text='total_ocorrencias')
    fig.update_traces(marker_color='#8e24aa', textposition='outside')
    fig.update_layout(xaxis={'categoryorder': 'total descending'},
                      margin=dict(t=0, b=20, l=10, r=10),
                      separators=",.")
    return fig

def plot_perfil_racial(df_feminicidio):
    """
    Gera um gráfico de barras comparando a raça/cor da vítima e do autor.
    """
    # Preparar dados: Contagem para Vítima
    df_vitima = df_feminicidio['etnia_vitima'].value_counts().reset_index()
    df_vitima.columns = ['Raça/Cor', 'Quantidade']
    df_vitima['Tipo'] = 'Vítima'

    # Preparar dados: Contagem para Autor
    df_autor = df_feminicidio['etnia_autor'].value_counts().reset_index()
    df_autor.columns = ['Raça/Cor', 'Quantidade']
    df_autor['Tipo'] = 'Autor'

    # Unir os dados
    df_final = pd.concat([df_vitima, df_autor])

    # Plotar
    fig = px.bar(df_final, x='Raça/Cor', y='Quantidade', color='Tipo',
                 barmode='group',
                 color_discrete_map={'Vítima': '#8e24aa', 'Autor': '#424242'}, # Roxo para vítima, Cinza para autor
                 template='plotly_white', text='Quantidade')
    
    fig.update_traces(textposition='outside')
    fig.update_layout(separators=",.")
    
    return fig

def plot_distribuicao_horaria(df_feminicidio):
    """
    Gera um gráfico de distribuição dos crimes por hora do dia.
    """
    df_temp = df_feminicidio.dropna(subset=['hora_fato']).copy()
    
    try:
        df_temp['hora_temp'] = pd.to_datetime(df_temp['hora_fato'].astype(str), format='%H:%M:%S', errors='coerce').dt.hour
        if df_temp['hora_temp'].isnull().all() and pd.api.types.is_numeric_dtype(df_temp['hora_fato']):
             df_temp['hora_temp'] = df_temp['hora_fato'].astype(int)
    except Exception:
        return go.Figure().add_annotation(text="Dados de horário indisponíveis para os filtros atuais.",
                                           showarrow=False, font=dict(size=14))

    df_contagem = df_temp['hora_temp'].value_counts().sort_index().reset_index()
    df_contagem.columns = ['Hora do Dia', 'Quantidade']
    
    df_completo = pd.DataFrame({'Hora do Dia': range(24)})
    df_final = pd.merge(df_completo, df_contagem, on='Hora do Dia', how='left').fillna(0)

    fig = px.bar(df_final, x='Hora do Dia', y='Quantidade',
                 labels={'Hora do Dia': 'Hora do Dia (0h - 23h)', 'Quantidade': 'Ocorrências'},
                 template='plotly_white', text='Quantidade')
    
    fig.update_traces(marker_color='#d81b60', textposition='outside')
    fig.update_xaxes(tickmode='linear', dtick=1)
    fig.update_layout(separators=",.")
    
    return fig

def plot_tempo_relacionamento(df_feminicidio):
    """
    Gera gráfico de distribuição do tempo de relacionamento.
    """
    # Tratamento simples para garantir consistência
    df_temp = df_feminicidio['tempo_relacionamento'].value_counts().reset_index()
    df_temp.columns = ['Tempo de Relacionamento', 'Quantidade']
    
    # Função auxiliar para ordenação (mesma lógica do gráfico de correlação)
    def extrair_valor_sort(x):
        try:
            x = str(x).upper().strip()
            if x == 'NÃO INFORMADO':
                return 999999 # Fica pro final
            
            # Remove "S" no final de ANOS/MESES para facilitar
            if x.endswith('S'):
                x = x[:-1]
                
            parts = x.split(' ')
            if not parts:
                return 9999
            
            valor = int(parts[0])
            unidade = parts[1] if len(parts) > 1 else ''
            
            if 'MES' in unidade:
                return valor # Meses vem primeiro (1 a 11)
            elif 'ANO' in unidade:
                return valor * 12 + 1000 # Anos vem depois, o +1000 garante que 1 ANO > 11 MESES
            else:
                return 9999 # Outros casos
        except Exception:
            return 9999

    df_temp['sort_key'] = df_temp['Tempo de Relacionamento'].apply(extrair_valor_sort)
    df_temp.sort_values('sort_key', ascending=False, inplace=True) # Ascending=False para ficar de cima para baixo no gráfico invertido (eixo y)?
    # No gráfico de barras horizontal do plotly, a ordem padrão é de baixo para cima.
    # Se quisermos 1 ano no topo, precisamos ordenar inversamente se categoryorder não for usado, ou definir categoryorder.
    # Vamos criar a lista ordenada e passar para o plotly.
    
    # Ordenando do menor para o maior (1 mes ... 10 anos ... nao informado)
    df_temp.sort_values('sort_key', ascending=True, inplace=True)
    order_list = df_temp['Tempo de Relacionamento'].tolist()
    
    # Para o eixo Y ficar de cima (menor tempo) para baixo (maior tempo), geralmente passamos a ordem invertida ou configuramos o eixo.
    # Mas o usuário pediu "primeiro meses... sequencia anos...". Num gráfico de barras horizontal, o "primeiro" visualmente costuma ser o topo.
    
    fig = px.bar(df_temp, x='Quantidade', y='Tempo de Relacionamento', orientation='h',
                 title='Tempo de Relacionamento',
                 template='plotly_white', text='Quantidade')
    
    fig.update_traces(marker_color='#8e24aa', textposition='outside')
    # Force the order. Note that for Y axis in horizontal bar, the bottom is usually index 0.
    # To have "1 Month" at the top, we might need to reverse the order list for the category array??
    # Let's try categoryorder='array' with categoryarray=order_list.
    # Plotly 'category ascending' usually puts index 0 at bottom. 'category descending' puts index 0 at top.
    
    fig.update_layout(yaxis={'categoryorder':'array', 'categoryarray': order_list[::-1]}, separators=",.")
    return fig

def plot_filhos_com_autor(df_feminicidio):
    """
    Gera dois gráficos: 
    1. Pizza/Donut sobre se tinha filhos com o autor.
    2. Barras com a quantidade de filhos (se existir a coluna numérica).
    """
    figs = {}
    
    # Gráfico 1: Sim/Não
    if 'filhos_com_autor' in df_feminicidio.columns:
        df_sim_nao = df_feminicidio['filhos_com_autor'].value_counts().reset_index()
        df_sim_nao.columns = ['Tem Filhos?', 'Quantidade']
        
        fig1 = px.pie(df_sim_nao, names='Tem Filhos?', values='Quantidade', hole=0.4,
                      title='Vítima tinha filhos com o Autor?',
                      color_discrete_sequence=px.colors.sequential.Purples_r)
        fig1.update_traces(textinfo='percent+label', textposition='outside')
        figs['existencia'] = fig1
        
    # Gráfico 2: Quantidade numérica
    if 'num_filhos_com_autor' in df_feminicidio.columns:
        df_qtd = df_feminicidio['num_filhos_com_autor'].dropna().astype(int).value_counts().sort_index().reset_index()
        df_qtd.columns = ['Número de Filhos', 'Quantidade']
        # Forçar num de filhos como categoria para eixo x discreto
        df_qtd['Número de Filhos'] = df_qtd['Número de Filhos'].astype(str)
        
        fig2 = px.bar(df_qtd, x='Número de Filhos', y='Quantidade',
                      title='Quantidade de Filhos em Comum',
                      template='plotly_white', text='Quantidade')
        fig2.update_traces(marker_color='#ab47bc', textposition='outside')
        fig2.update_layout(separators=",.")
        figs['quantidade'] = fig2
        
    return figs

def plot_tipo_local_detalhado(df_feminicidio):
    """
    Visualização do tipo de local (Gráfico de Barras com opção de seleção).
    """
    df_counts = df_feminicidio['tipo_local'].value_counts().reset_index()
    df_counts.columns = ['Tipo de Local', 'Quantidade']
    
    fig = px.bar(df_counts, x='Quantidade', y='Tipo de Local', orientation='h',
                 title='Tipo de Local',
                 template='plotly_white', text='Quantidade')
    
    fig.update_traces(marker_color='#8e24aa', textposition='outside')
    fig.update_layout(yaxis={'categoryorder':'total ascending'}, separators=",.")
    return fig

def plot_matriz_risco_local_meio(df_feminicidio):
    """
    Heatmap: Tipo de Local vs Meio do Crime.
    """
    if 'tipo_local' not in df_feminicidio.columns or 'meio_crime' not in df_feminicidio.columns:
        return go.Figure().add_annotation(text="Dados de tipo de local ou meio do crime indisponíveis.",
                                           showarrow=False, font=dict(size=14))
        
    df_pivot = df_feminicidio.groupby(['tipo_local', 'meio_crime']).size().unstack(fill_value=0)
    
    fig = go.Figure(data=go.Heatmap(
        z=df_pivot.values,
        x=df_pivot.columns,
        y=df_pivot.index,
        colorscale='Reds',
        text=df_pivot.values,
        texttemplate="%{text}"
    ))
    
    fig.update_layout(
        title="Matriz de Risco: Local vs Meio Utilizado",
        xaxis_title="Meio do Crime",
        yaxis_title="Local Específico",
        separators=",."
    )
    return fig

def plot_correlacao_tempo_violencia(df_feminicidio):
    """
    Analisa se há relação entre tempo de relacionamento e histórico de violência.
    Usa 'bo_de_vd_contra_o_autor' como proxy de violência prévia.
    """
    # Filtra colunas necessárias
    cols = ['tempo_relacionamento', 'bo_de_vd_contra_o_autor']
    if not all(c in df_feminicidio.columns for c in cols):
        return go.Figure().add_annotation(text="Dados de tempo de relacionamento ou BO indisponíveis.",
                                           showarrow=False, font=dict(size=14))
        
    df_plot = df_feminicidio[cols].copy().dropna()
    
    # Função auxiliar para ordenação
    def extrair_valor_sort(x):
        try:
            x = str(x).upper().strip()
            if x == 'NÃO INFORMADO':
                return 999999 # Fica pro final
            
            # Remove "S" no final de ANOS/MESES para facilitar
            if x.endswith('S'):
                x = x[:-1]
                
            parts = x.split(' ')
            if not parts:
                return 9999
            
            valor = int(parts[0])
            unidade = parts[1] if len(parts) > 1 else ''
            
            if 'MES' in unidade:
                return valor # Meses vem primeiro (1 a 11)
            elif 'ANO' in unidade:
                return valor * 12 + 1000 # Anos vem depois, o +1000 garante que 1 ANO > 11 MESES
            else:
                return 9999 # Outros casos
        except Exception:
            return 9999

    df_plot['sort_key'] = df_plot['tempo_relacionamento'].apply(extrair_valor_sort)
    df_plot.sort_values('sort_key', inplace=True)
    
    # Como 'tempo_relacionamento' é texto (frequencia), vamos ver a distribuição de BOs para cada tempo.
    # Stacked Bar Chart 100%
    
    # É importante manter a ordem no groupby ou reordenar depois
    order_list = df_plot['tempo_relacionamento'].unique().tolist()
    
    df_grouped = df_plot.groupby(['tempo_relacionamento', 'bo_de_vd_contra_o_autor'], sort=False).size().reset_index(name='Qtd')
    
    # Calcula percentuais dentro de cada tempo de relacionamento
    df_grouped['Total'] = df_grouped.groupby('tempo_relacionamento')['Qtd'].transform('sum')
    df_grouped['Percentual'] = (df_grouped['Qtd'] / df_grouped['Total']) * 100
    
    fig = px.bar(df_grouped, x='tempo_relacionamento', y='Percentual', color='bo_de_vd_contra_o_autor',
                 title="Histórico de Violência por Duração do Relacionamento",
                 labels={'tempo_relacionamento': 'Duração da Relação', 'bo_de_vd_contra_o_autor': 'Tinha BO Prévio?'},
                 # Usando tons de roxo do painel
                 color_discrete_map={'SIM': '#8e24aa', 'NÃO': '#e1bee7', 'Não informado': '#f3e5f5'},
                 category_orders={'tempo_relacionamento': order_list},
                 template='plotly_white')
                 
    fig.update_layout(barmode='stack', yaxis_ticksuffix='%', separators=",.")
    return fig
