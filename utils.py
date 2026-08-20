import io
import re
import unicodedata

import numpy as np
import pandas as pd
import streamlit as st


def normalizar_nome(texto):
    """
    Limpa e padroniza uma string de texto para ser usada como
    chave de junção.
    """
    if not isinstance(texto, str):
        return ""

    texto = texto.lower()

    # --- 1. Mapa de Exceções (Hard-coded) ---
    mapa_excecoes = {
        'herval': 'herval d oeste',
        'luís alves': 'luiz alves',
        # (Mantemos a correção para o arquivo Geo)
    }
    if texto in mapa_excecoes:
        texto = mapa_excecoes[texto]

    # --- 2. Normalização de Acentos ---
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                    if unicodedata.category(c) != 'Mn')

    # --- 3. Normalização de Pontuação ---
    # Substitui qualquer coisa que NÃO seja (^) letra (a-z),
    # número (0-9) ou espaço (\s) por um espaço.
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)

    # --- 4. Normalização de Palavras ---
    # Remove artigos/preposições (agora cercados por espaços)
    texto = re.sub(r'\b(de|do|da|d)\b', ' ', texto)

    # --- 5. Limpeza Final ---
    # Remove espaços múltiplos (criados pelas substituições)
    texto = re.sub(r'\s+', ' ', texto).strip()

    return texto.upper()


def to_excel(df):
    """Converte um DataFrame para um arquivo Excel em memória."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados')
    processed_data = output.getvalue()
    return processed_data


def to_csv(df):
    """Converte um DataFrame para um arquivo CSV em memória."""
    return df.to_csv(index=False).encode('utf-8')


def colorir_percentual(val):
    """Retorna a cor para o valor percentual."""
    if pd.isna(val) or val == 0:
        return ''
    color = 'red' if val > 0 else 'green'
    return f'color: {color}'


def formatar_seta_percentual(val):
    """Formata o valor com seta e percentual."""
    if pd.isna(val):
        return '-'
    seta = '▲' if val > 0 else '▼' if val < 0 else ''
    if seta:
        return f'{seta} {abs(val):.2f}%'
    return f'{abs(val):.2f}%'


def calcular_tendencia_mensal_vetorizada(df, colunas_grupo, coluna_data='data_fato', min_meses=6):
    """
    Calcula a tendência anual (% ao ano) de múltiplos grupos de forma vetorizada via álgebra linear.
    Muito mais rápida que iterar grupos com groupby em Python (~30-50x mais rápida).
    
    Args:
        df: DataFrame com os dados filtrados.
        colunas_grupo: String ou lista de strings com a(s) coluna(s) de agrupamento.
        coluna_data: Nome da coluna de data.
        min_meses: Mínimo de meses com dados necessários para calcular a tendência.
        
    Returns:
        pd.Series: Tendência anual (% ao ano) indexada pelo grupo (ou MultiIndex se lista de colunas).
    """
    if df.empty:
        return pd.Series(dtype='float64')

    if isinstance(colunas_grupo, str):
        cols = [colunas_grupo]
    else:
        cols = list(colunas_grupo)

    cols_subset = cols + [coluna_data]
    df_temp = df[cols_subset].copy()
    df_temp['ano_mes'] = df_temp[coluna_data].dt.to_period('M')

    grouped = df_temp.groupby(cols + ['ano_mes'], observed=True).size()
    if grouped.empty:
        return pd.Series(dtype='float64')

    matrix = grouped.unstack('ano_mes', fill_value=0)

    n_cols = matrix.shape[1]
    if n_cols < min_meses:
        return pd.Series(np.nan, index=matrix.index, dtype='float64')

    Y = matrix.values.astype(float)
    x = np.arange(n_cols)
    x_mean = x.mean()
    denom = np.sum((x - x_mean) ** 2)

    if denom == 0:
        return pd.Series(np.nan, index=matrix.index, dtype='float64')

    Y_mean = Y.mean(axis=1)
    x_centered = x - x_mean
    slope = np.dot(Y, x_centered) / denom

    valid_mask = Y_mean > 0
    trend = np.full(len(Y), np.nan, dtype=float)
    trend[valid_mask] = (slope[valid_mask] * 12 / Y_mean[valid_mask]) * 100

    return pd.Series(trend, index=matrix.index, dtype='float64')


def calcular_tendencia_mensal(df, coluna_data='data_fato', coluna_grupo=None, min_meses=6):
    """
    Calcula a tendência anual (% ao ano) usando Regressão Linear sobre dados mensais.
    Usa TODOS os meses disponíveis, sem exclusão de dados atípicos.
    
    Args:
        df: DataFrame com os dados filtrados.
        coluna_data: Nome da coluna de data.
        coluna_grupo: Se fornecido, calcula a tendência por grupo (ex: 'municipio', 'fato_comunicado').
        min_meses: Mínimo de meses necessários para calcular a tendência (padrão: 6).
    
    Returns:
        float ou pd.Series: Tendência anual em percentual (% ao ano).
    """
    if df.empty:
        return np.nan if coluna_grupo is None else pd.Series(dtype='float64')

    if coluna_grupo is not None:
        return calcular_tendencia_mensal_vetorizada(df, coluna_grupo, coluna_data, min_meses)

    df_temp = df[[coluna_data]].copy()
    df_temp['ano_mes'] = df_temp[coluna_data].dt.to_period('M')

    contagem_mensal = df_temp.groupby('ano_mes').size().sort_index()

    if len(contagem_mensal) < min_meses:
        return np.nan

    x = np.arange(len(contagem_mensal))
    y = contagem_mensal.values.astype(float)
    media_y = y.mean()

    if media_y == 0:
        return np.nan

    n = len(x)
    sum_x = x.sum()
    sum_y = y.sum()
    sum_xy = (x * y).sum()
    sum_x2 = (x ** 2).sum()

    denominador = n * sum_x2 - sum_x ** 2
    if denominador == 0:
        return np.nan

    slope = (n * sum_xy - sum_x * sum_y) / denominador
    tendencia_anual = (slope * 12 / media_y) * 100
    return float(tendencia_anual)


def calcular_cagr(valor_inicial, valor_final, num_anos):
    """
    DEPRECADA: Mantida para compatibilidade. Use calcular_tendencia_mensal() para novos cálculos.
    Calcula a Taxa de Crescimento Anual Composta (CAGR).
    """
    if isinstance(valor_inicial, pd.Series):
        cagr = pd.Series(np.nan, index=valor_inicial.index, dtype='float64')
        if num_anos < 3:
            return cagr

        mask = (valor_inicial.notna()) & (valor_final.notna()) & (valor_inicial != 0)

        cagr.loc[mask] = ((valor_final[mask] / valor_inicial[mask]) ** (1 / (num_anos - 1)) - 1) * 100
        return cagr
    else:
        if pd.isna(valor_inicial) or pd.isna(valor_final) or valor_inicial == 0 or num_anos < 3:
            return np.nan
        return ((valor_final / valor_inicial) ** (1 / (num_anos - 1)) - 1) * 100


def format_number_br(val):
    """Formata números para o padrão brasileiro (milhar com ponto, decimal com vírgula)."""
    if pd.isna(val):
        return '-'
    if isinstance(val, (int, float)):
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return val


def format_int_br(val):
    """Formata inteiros para o padrão brasileiro (milhar com ponto)."""
    if pd.isna(val):
        return '-'
    return f"{val:,.0f}".replace(",", ".")


def render_plotly_safe(fig, key, use_container_width=True, **kwargs):
    """Renderiza um gráfico Plotly com tratamento de exceção para evitar crash total."""
    try:
        if 'width' in kwargs:
            kwargs.pop('width')
        st.plotly_chart(fig, use_container_width=use_container_width, key=key, **kwargs)
    except Exception as e:
        st.warning(f"Não foi possível gerar o gráfico: {e}")
