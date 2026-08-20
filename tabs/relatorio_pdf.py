"""
Módulo para geração de relatório PDF oficial do Observatório da Violência Contra a Mulher - SC.
Gera um documento PDF executivo unificado (Análise Geral + Análise de Feminicídios),
com layout A4 padrão, cabeçalho institucional em todas as páginas, 1 seção temática por página,
gráficos em alta resolução e tabelas totalmente preenchidas e formatadas.
"""

import io
import os
import tempfile
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.io as pio
from fpdf import FPDF
from fpdf.enums import XPos, YPos

from tabs.analise_geral import (
    criar_tabela_consolidada,
    criar_tabela_total_consolidada,
    criar_tabela_populacional_agrupada,
)
from tabs.analise_feminicidios import (
    criar_tabela_feminicidio_agrupado,
    criar_tabela_total_feminicidio,
    calcular_indice_letalidade,
)
from plotting import (
    plot_serie_temporal,
    plot_dia_semana,
    plot_por_ano,
    plot_por_mes,
    plot_faixa_etaria,
    plot_tipo_crime,
    plot_barras_vulnerabilidade,
    plot_feminicidio_serie_temporal,
    plot_feminicidio_por_ano,
    plot_vinculo_autor,
    plot_meio_crime,
    plot_autor_preso,
    plot_bo_contra_autor,
)
from utils import calcular_tendencia_mensal


# ============================================================================
# CONSTANTES DE CORES E LAYOUT
# ============================================================================
ROXO_ESCURO = (74, 20, 140)       # #4a148c
ROXO_MEDIO = (142, 36, 170)       # #8e24aa
ROXO_CLARO = (206, 147, 216)      # #ce93d8
ROXO_BG = (248, 244, 251)         # #f8f4fb
ROXO_BORDER = (209, 196, 233)     # #d1c4e9
BRANCO = (255, 255, 255)
CINZA_TEXTO = (45, 45, 45)
CINZA_SUAVE = (100, 100, 100)
CINZA_LINHA = (225, 225, 225)
CINZA_BG = (248, 249, 250)


# ============================================================================
# CLASSE DO PDF PERSONALIZADO COM CABEÇALHO OFICIAL EM TODAS AS PÁGINAS
# ============================================================================
class RelatorioOVMCompletoPDF(FPDF):
    """
    Documento PDF Profissional Oficial do Observatório da Violência Contra a Mulher - SC.
    Reproduz o cabeçalho institucional em 100% das páginas com layout A4 Portrait.
    """

    def __init__(self, logo_path=None, filtros_info=None):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.logo_path = logo_path
        self.filtros_info = filtros_info or {}

        # Suporte a fontes Unicode cross-platform (Windows, Linux Debian/Ubuntu/Streamlit Cloud, macOS)
        self.font_family_name = 'Helvetica'
        font_candidates = []

        # 1. Matplotlib bundled fonts (100% garantido em qualquer ambiente onde matplotlib estiver instalado)
        try:
            import matplotlib
            mpl_ttf_dir = os.path.join(matplotlib.get_data_path(), 'fonts', 'ttf')
            font_candidates.append((
                os.path.join(mpl_ttf_dir, 'DejaVuSans.ttf'),
                os.path.join(mpl_ttf_dir, 'DejaVuSans-Bold.ttf'),
                os.path.join(mpl_ttf_dir, 'DejaVuSans-Oblique.ttf'),
                os.path.join(mpl_ttf_dir, 'DejaVuSans-BoldOblique.ttf'),
            ))
        except Exception:
            pass

        # 2. Windows (Arial)
        windir = os.environ.get('WINDIR', 'C:/Windows')
        font_candidates.append((
            os.path.join(windir, 'Fonts', 'arial.ttf'),
            os.path.join(windir, 'Fonts', 'arialbd.ttf'),
            os.path.join(windir, 'Fonts', 'ariali.ttf'),
            os.path.join(windir, 'Fonts', 'arialbi.ttf'),
        ))

        # 3. Linux Debian / Ubuntu / Streamlit Cloud
        font_candidates.extend([
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'),
            ('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
             '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
             '/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf',
             '/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf'),
            ('/usr/share/fonts/truetype/freefont/FreeSans.ttf',
             '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
             '/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf',
             '/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf'),
        ])

        # 4. macOS
        font_candidates.extend([
            ('/Library/Fonts/Arial.ttf',
             '/Library/Fonts/Arial Bold.ttf',
             '/Library/Fonts/Arial Italic.ttf',
             '/Library/Fonts/Arial Bold Italic.ttf'),
            ('/Library/Fonts/DejaVuSans.ttf',
             '/Library/Fonts/DejaVuSans-Bold.ttf',
             '/Library/Fonts/DejaVuSans-Oblique.ttf',
             '/Library/Fonts/DejaVuSans-BoldOblique.ttf'),
        ])

        for reg, bld, itl, bi in font_candidates:
            if reg and os.path.exists(reg.replace('\\', '/')):
                reg_clean = reg.replace('\\', '/')
                try:
                    self.add_font('CustomUnicodeFont', '', reg_clean)
                    if bld and os.path.exists(bld.replace('\\', '/')):
                        self.add_font('CustomUnicodeFont', 'B', bld.replace('\\', '/'))
                    if itl and os.path.exists(itl.replace('\\', '/')):
                        self.add_font('CustomUnicodeFont', 'I', itl.replace('\\', '/'))
                    if bi and os.path.exists(bi.replace('\\', '/')):
                        self.add_font('CustomUnicodeFont', 'BI', bi.replace('\\', '/'))
                    self.font_family_name = 'CustomUnicodeFont'
                    break
                except Exception:
                    continue

        self.set_auto_page_break(auto=True, margin=14)
        self.set_margins(left=10, top=10, right=10)

    def _sanitize_text(self, txt):
        """Sanitiza strings para evitar erro de codificação caso a fonte seja Helvetica (Latin-1)."""
        if txt is None:
            return ''
        txt = str(txt)
        if self.font_family_name == 'Helvetica':
            replacements = {
                '•': '-',
                'Δ': 'Dif.',
                '—': '-',
                '–': '-',
                '“': '"',
                '”': '"',
                '‘': "'",
                '’': "'",
                '…': '...',
                '≤': '<=',
                '≥': '>=',
                '≠': '!=',
                '≈': '~',
            }
            for k, v in replacements.items():
                txt = txt.replace(k, v)
            try:
                txt = txt.encode('latin-1', errors='replace').decode('latin-1')
            except Exception:
                pass
        return txt

    def cell(self, *args, **kwargs):
        """Sobrescreve cell garantindo sanitização de caracteres incompatíveis."""
        if len(args) >= 3:
            args = list(args)
            args[2] = self._sanitize_text(args[2])
            args = tuple(args)
        elif 'text' in kwargs:
            kwargs['text'] = self._sanitize_text(kwargs['text'])
        elif 'txt' in kwargs:
            kwargs['txt'] = self._sanitize_text(kwargs['txt'])
        return super().cell(*args, **kwargs)

    def multi_cell(self, *args, **kwargs):
        """Sobrescreve multi_cell garantindo sanitização de caracteres incompatíveis."""
        if len(args) >= 3:
            args = list(args)
            args[2] = self._sanitize_text(args[2])
            args = tuple(args)
        elif 'text' in kwargs:
            kwargs['text'] = self._sanitize_text(kwargs['text'])
        elif 'txt' in kwargs:
            kwargs['txt'] = self._sanitize_text(kwargs['txt'])
        return super().multi_cell(*args, **kwargs)

    def header(self):
        """Cabeçalho Institucional Oficial no topo de CADA página."""
        top_y = 6
        self.set_xy(10, top_y)

        # 1. Faixa decorativa superior
        self.set_fill_color(*ROXO_ESCURO)
        self.rect(10, top_y, 190, 1.2, 'F')

        # 2. Logo OVM à esquerda
        logo_w = 20
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, x=10, y=top_y + 2.2, w=logo_w)
            except Exception:
                pass

        # 3. Título e Subtítulos
        text_x = 10 + logo_w + 3
        self.set_xy(text_x, top_y + 2.0)
        self.set_font(self.font_family_name, 'B', 10)
        self.set_text_color(*ROXO_ESCURO)
        self.cell(190 - text_x + 10, 4.2, 'OBSERVATÓRIO DA VIOLÊNCIA CONTRA A MULHER - SC', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        bullet = '•' if self.font_family_name != 'Helvetica' else '-'
        self.set_x(text_x)
        self.set_font(self.font_family_name, 'B', 7.8)
        self.set_text_color(*ROXO_MEDIO)
        self.cell(190 - text_x + 10, 3.8, f'Relatório Analítico Oficial {bullet} Análise Geral e Feminicídios', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        self.set_x(text_x)
        self.set_font(self.font_family_name, '', 6.6)
        self.set_text_color(*CINZA_SUAVE)
        data_emissao = self.filtros_info.get('data_emissao', datetime.now().strftime('%d/%m/%Y às %H:%M'))
        self.cell(190 - text_x + 10, 3.2, f'Emitido em: {data_emissao}', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # 4. Caixa de Filtros Aplicados
        box_y = top_y + 14.5
        box_h = 18
        box_w = 190

        # Fundo e borda externa da caixa de filtros
        self.set_fill_color(*ROXO_BG)
        self.set_draw_color(*ROXO_BORDER)
        self.set_line_width(0.3)
        self.rect(10, box_y, box_w, box_h, 'DF')

        # Barra lateral roxa na caixa de filtros
        self.set_fill_color(*ROXO_ESCURO)
        self.rect(10, box_y, 1.8, box_h, 'F')

        # Título interno da caixa
        self.set_xy(13, box_y + 1.0)
        self.set_font(self.font_family_name, 'B', 6.4)
        self.set_text_color(*ROXO_ESCURO)
        self.cell(box_w - 6, 3.2, 'FILTROS E PARÂMETROS APLICADOS NESTE RELATÓRIO:', new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Itens de Filtro em 2 colunas
        col1_x = 13
        col2_x = 108
        line_h = 3.0
        curr_y = box_y + 4.5

        periodo_str = self.filtros_info.get('periodo', 'Todos os dados disponíveis')
        abrangencia_str = self.filtros_info.get('abrangencia', 'Todo o Estado (SC)')
        municipios_str = self.filtros_info.get('municipios', 'Todos os 295 Municípios')
        assocs_str = self.filtros_info.get('associacoes', 'Todas / Diversas Associações de Municípios')
        crimes_str = self.filtros_info.get('crimes', 'Todos os crimes cadastrados')
        faixa_str = self.filtros_info.get('faixa_etaria', 'Todas as idades (0 a 100+ anos)')
        vis_str = self.filtros_info.get('visualizacao', 'Agrupado por Consolidado')

        bullet_item = '• ' if self.font_family_name != 'Helvetica' else '- '

        # Linha 1
        self._render_filter_item(col1_x, curr_y, f'{bullet_item}Período: ', periodo_str, 92)
        self._render_filter_item(col2_x, curr_y, f'{bullet_item}Abrangência: ', abrangencia_str, 90)
        curr_y += line_h

        # Linha 2
        self._render_filter_item(col1_x, curr_y, f'{bullet_item}Municípios: ', municipios_str, 92)
        self._render_filter_item(col2_x, curr_y, f'{bullet_item}Associações de Municípios: ', assocs_str, 90)
        curr_y += line_h

        # Linha 3
        self._render_filter_item(col1_x, curr_y, f'{bullet_item}Crimes: ', crimes_str, 92)
        self._render_filter_item(col2_x, curr_y, f'{bullet_item}Faixa Etária: ', faixa_str, 90)
        curr_y += line_h

        # Linha 4
        self._render_filter_item(col1_x, curr_y, f'{bullet_item}Visualização: ', vis_str, 92)

        # 5. Linha divisória roxa
        sep_y = box_y + box_h + 1.8
        self.set_draw_color(*ROXO_ESCURO)
        self.set_line_width(0.5)
        self.line(10, sep_y, 200, sep_y)

        # Posiciona o cursor logo abaixo para o conteúdo da página
        self.set_xy(10, sep_y + 3)

    def _render_filter_item(self, x, y, label, value, max_w):
        self.set_xy(x, y)
        self.set_font(self.font_family_name, 'B', 5.9)
        self.set_text_color(*ROXO_ESCURO)
        label_w = self.get_string_width(label) + 0.5
        self.cell(label_w, 2.8, label)

        self.set_font(self.font_family_name, '', 5.9)
        self.set_text_color(*CINZA_TEXTO)
        val_w = max_w - label_w
        val_txt = str(value)
        if self.get_string_width(val_txt) > val_w:
            while self.get_string_width(val_txt + '..') > val_w and len(val_txt) > 3:
                val_txt = val_txt[:-1]
            val_txt += '..'
        self.cell(val_w, 2.8, val_txt)

    def footer(self):
        """Rodapé formal em cada página."""
        self.set_y(-11)
        self.set_draw_color(*CINZA_LINHA)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())

        bullet = '•' if self.font_family_name != 'Helvetica' else '-'
        self.set_y(-9)
        self.set_font(self.font_family_name, 'I', 6.8)
        self.set_text_color(*CINZA_SUAVE)
        self.cell(100, 5, f'Observatório da Violência Contra a Mulher - SC {bullet} Relatório Oficial', align='L')
        self.cell(90, 5, f'Página {self.page_no()} de {{nb}}', align='R')


# ============================================================================
# FUNÇÕES DE APOIO AO LAYOUT
# ============================================================================
def _fig_to_image(fig, width=900, height=450):
    """Converte uma figura Plotly em bytes PNG de alta definição sem menus."""
    if fig is None:
        return None
    try:
        fig.update_layout(
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Arial, sans-serif", size=11, color="#333333"),
            margin=dict(l=45, r=25, t=35, b=45),
            autosize=True
        )
        return pio.to_image(fig, format='png', width=width, height=height, scale=2)
    except Exception:
        return None


def add_section_header(pdf, titulo, subtitulo=None):
    """Renderiza título da seção/página."""
    pdf.set_font(pdf.font_family_name, 'B', 11.5)
    pdf.set_text_color(*ROXO_ESCURO)
    pdf.cell(0, 5.2, titulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    if subtitulo:
        pdf.set_font(pdf.font_family_name, '', 7.5)
        pdf.set_text_color(*CINZA_SUAVE)
        pdf.cell(0, 3.6, subtitulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    y = pdf.get_y() + 1
    pdf.set_draw_color(*ROXO_MEDIO)
    pdf.set_line_width(0.6)
    pdf.line(10, y, 75, y)
    pdf.set_y(y + 3)


def add_kpis(pdf, kpis):
    """Adiciona cards de KPI responsivos e centralizados."""
    n = len(kpis)
    if n == 0:
        return
    total_w = 190
    gap = 2.5
    card_w = (total_w - (n - 1) * gap) / n
    card_h = 16
    y = pdf.get_y()

    for i, kpi in enumerate(kpis):
        x = 10 + i * (card_w + gap)
        pdf.set_fill_color(*ROXO_BG)
        pdf.set_draw_color(*ROXO_CLARO)
        pdf.set_line_width(0.3)
        pdf.rect(x, y, card_w, card_h, 'DF')

        pdf.set_font(pdf.font_family_name, 'B', 6.0)
        pdf.set_text_color(*ROXO_MEDIO)
        pdf.set_xy(x + 1, y + 1.5)
        pdf.cell(card_w - 2, 3.2, kpi['label'].upper(), align='C')

        pdf.set_font(pdf.font_family_name, 'B', 10.5)
        pdf.set_text_color(*ROXO_ESCURO)
        pdf.set_xy(x + 1, y + 5.2)
        pdf.cell(card_w - 2, 6.0, str(kpi['value']), align='C')

        if 'sub' in kpi and kpi['sub']:
            pdf.set_font(pdf.font_family_name, '', 5.5)
            pdf.set_text_color(*CINZA_SUAVE)
            pdf.set_xy(x + 1, y + 11.2)
            pdf.cell(card_w - 2, 3, str(kpi['sub']), align='C')

    pdf.set_y(y + card_h + 4)


def add_image_box(pdf, img_bytes, w=190, max_h=190, title=None):
    """Adiciona um gráfico Plotly convertido perfeitamente dimensionado."""
    if img_bytes is None:
        return

    if title:
        pdf.set_font(pdf.font_family_name, 'B', 8.5)
        pdf.set_text_color(*ROXO_MEDIO)
        pdf.cell(0, 4.0, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        tmp.write(img_bytes)
        tmp_path = tmp.name

    try:
        from PIL import Image as PILImage
        with PILImage.open(tmp_path) as img:
            orig_w, orig_h = img.size

        calc_h = w * orig_h / orig_w
        if calc_h > max_h:
            calc_h = max_h
            w = calc_h * orig_w / orig_h

        x = 10 + (190 - w) / 2
        y = pdf.get_y()
        pdf.image(tmp_path, x=x, y=y, w=w, h=calc_h)
        pdf.set_y(y + calc_h + 3)
    except Exception:
        pass
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def add_two_images(pdf, img1_bytes, img2_bytes, title1=None, title2=None, max_h=95):
    """Adiciona 2 gráficos empilhados verticalmente na mesma página."""
    if img1_bytes is not None:
        add_image_box(pdf, img1_bytes, w=190, max_h=max_h, title=title1)
    if img2_bytes is not None:
        add_image_box(pdf, img2_bytes, w=190, max_h=max_h, title=title2)


def add_table(pdf, df, col_widths=None, max_rows=55, title=None):
    """Renderiza tabela formatada com suporte a quebra automática de página."""
    if df is None or df.empty:
        pdf.set_font(pdf.font_family_name, 'I', 7.5)
        pdf.set_text_color(*CINZA_SUAVE)
        pdf.cell(0, 5, 'Nenhum dado disponível para exibição.', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        return

    if title:
        pdf.set_font(pdf.font_family_name, 'B', 8.5)
        pdf.set_text_color(*ROXO_MEDIO)
        pdf.cell(0, 4.2, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

    df_display = df.head(max_rows).copy()

    # Simplifica cabeçalhos longos para o PDF
    rename_dict = {}
    delta_symbol = "Δ" if pdf.font_family_name != 'Helvetica' else "Dif."
    for c in df_display.columns:
        c_str = str(c)
        if 'Diferença' in c_str:
            anos = [p for p in c_str.split() if '-' in p]
            if anos:
                ano_part = anos[0].replace('20', '')
                rename_dict[c] = f"{delta_symbol} {ano_part}"
            else:
                rename_dict[c] = "Dif.%"
        elif 'Tendência' in c_str:
            rename_dict[c] = "Tend. a.a."
        elif '(Parcial)' in c_str:
            rename_dict[c] = c_str.replace('(Parcial)', '*').strip()
        elif c_str.lower() == 'total':
            rename_dict[c] = 'Total'
        elif 'Letalidade' in c_str:
            rename_dict[c] = 'Ind. Letalidade'
        elif 'Ocorrências Gerais' in c_str:
            rename_dict[c] = 'Ocorrências'

    if rename_dict:
        df_display = df_display.rename(columns=rename_dict)

    columns = list(df_display.columns)
    n_cols = len(columns)
    usable_w = 190

    if col_widths is None:
        if n_cols > 6:
            w_first = 28
            w_other = (usable_w - w_first) / (n_cols - 1)
            col_widths = [w_first] + [w_other] * (n_cols - 1)
        else:
            col_widths = [usable_w / n_cols] * n_cols
    else:
        tot = sum(col_widths)
        if abs(tot - usable_w) > 0.1:
            col_widths = [w * (usable_w / tot) for w in col_widths]

    row_h = 4.8
    header_h = 5.4

    # Cabeçalho da tabela
    pdf.set_font(pdf.font_family_name, 'B', 6.0 if n_cols > 8 else 6.5)
    pdf.set_fill_color(*ROXO_ESCURO)
    pdf.set_text_color(*BRANCO)
    pdf.set_draw_color(*ROXO_ESCURO)

    x_start = 10
    curr_x = x_start
    for i, col in enumerate(columns):
        col_name = str(col)
        if len(col_name) > 22:
            col_name = col_name[:20] + '..'
        pdf.set_xy(curr_x, pdf.get_y())
        pdf.cell(col_widths[i], header_h, col_name, border=1, align='C', fill=True)
        curr_x += col_widths[i]
    pdf.ln(header_h)

    # Linhas de dados
    pdf.set_font(pdf.font_family_name, '', 5.8 if n_cols > 8 else 6.2)
    for idx, row in df_display.iterrows():
        # Quebra automática se ultrapassar a página
        if pdf.get_y() + row_h > pdf.h - 14:
            pdf.add_page()
            # Re-renderiza cabeçalho da tabela
            pdf.set_font(pdf.font_family_name, 'B', 6.0 if n_cols > 8 else 6.5)
            pdf.set_fill_color(*ROXO_ESCURO)
            pdf.set_text_color(*BRANCO)
            curr_x = x_start
            for i, col in enumerate(columns):
                col_name = str(col)
                if len(col_name) > 22:
                    col_name = col_name[:20] + '..'
                pdf.set_xy(curr_x, pdf.get_y())
                pdf.cell(col_widths[i], header_h, col_name, border=1, align='C', fill=True)
                curr_x += col_widths[i]
            pdf.ln(header_h)
            pdf.set_font(pdf.font_family_name, '', 5.8 if n_cols > 8 else 6.2)

        is_even = (list(df_display.index).index(idx) % 2 == 0)
        pdf.set_fill_color(*(CINZA_BG if is_even else BRANCO))
        pdf.set_draw_color(*CINZA_LINHA)

        y_row = pdf.get_y()
        curr_x = x_start
        for i, col in enumerate(columns):
            val = row[col]
            val_str = str(val) if pd.notna(val) else '-'
            if isinstance(val, float):
                val_str = f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            elif isinstance(val, (int, np.integer)):
                val_str = f"{val:,}".replace(",", ".")

            align = 'L' if i == 0 else 'R'
            col_str = str(col)
            if 'Δ' in col_str or 'Dif' in col_str or 'Tend' in col_str:
                try:
                    num_val = float(val) if not pd.isna(val) else 0
                    if num_val > 0:
                        pdf.set_text_color(200, 30, 30)
                    elif num_val < 0:
                        pdf.set_text_color(30, 140, 30)
                    else:
                        pdf.set_text_color(*CINZA_TEXTO)
                except (ValueError, TypeError):
                    pdf.set_text_color(*CINZA_TEXTO)
            else:
                pdf.set_text_color(*CINZA_TEXTO)

            pdf.set_xy(curr_x, y_row)
            pdf.cell(col_widths[i], row_h, val_str, border=1, align=align, fill=True)
            curr_x += col_widths[i]

        pdf.ln(row_h)

    pdf.ln(2)
    if len(df) > max_rows:
        pdf.set_font(pdf.font_family_name, 'I', 6.0)
        pdf.set_text_color(*CINZA_SUAVE)
        pdf.cell(0, 3.5, f'* Exibindo as primeiras {max_rows} de {len(df)} linhas.', new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ============================================================================
# GERADOR OFICIAL DO RELATÓRIO COMPLETO UNIFICADO (12 PÁGINAS)
# ============================================================================
def gerar_relatorio_pdf(
    df_geral=None,
    df_feminicidio=None,
    df_populacao=None,
    df_regioes=None,
    df_calendario=None,
    agrupamento="Consolidado",
    data_inicial=None,
    data_final=None,
    idade_selecionada=None,
    crimes_selecionados=None,
    municipios_selecionados=None,
    mesorregioes_selecionadas=None,
    associacoes_selecionadas=None,
):
    """
    Gera o relatório PDF completo com todas as 12 seções temáticas unificadas
    (Análise Geral + Análise de Feminicídios), com o cabeçalho oficial em todas as páginas.
    """
    import streamlit as st

    # Recupera do session_state caso parâmetros não sejam passados diretamente
    try:
        if df_geral is None:
            df_geral = st.session_state.get('df_geral_filtrado', pd.DataFrame())
        if df_feminicidio is None:
            df_feminicidio = st.session_state.get('df_feminicidio_filtrado', pd.DataFrame())
        if df_populacao is None:
            df_populacao = st.session_state.get('df_populacao', pd.DataFrame())
        if df_regioes is None:
            df_regioes = st.session_state.get('df_regioes', pd.DataFrame())
        if df_calendario is None:
            df_calendario = st.session_state.get('df_calendario', pd.DataFrame())

        if agrupamento is None or agrupamento == "Consolidado":
            agrupamento = st.session_state.get('agrupamento_selecionado', agrupamento)
        if data_inicial is None:
            data_inicial = st.session_state.get('data_inicial')
        if data_final is None:
            data_final = st.session_state.get('data_final')
    except Exception:
        pass

    if df_geral is None:
        df_geral = pd.DataFrame()
    if df_feminicidio is None:
        df_feminicidio = pd.DataFrame()
    if df_populacao is None:
        df_populacao = pd.DataFrame()
    if df_regioes is None:
        df_regioes = pd.DataFrame()
    if df_calendario is None:
        df_calendario = pd.DataFrame()
    if agrupamento is None:
        agrupamento = "Consolidado"

    # Monta textos descritivos dos filtros
    if data_inicial and data_final:
        dias_totais = (data_final - data_inicial).days + 1
        periodo_str = f"{data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')} ({dias_totais} dias)"
    else:
        dias_totais = 1
        periodo_str = "Todos os dados disponíveis"

    # Abrangência / Mesorregiões
    mesos = [m for m in df_geral['mesoregiao'].unique() if m != 'Não informado'] if not df_geral.empty else []
    if len(mesos) >= 6:
        abrangencia_str = "Todo o Estado (SC)"
    elif len(mesos) <= 2 and mesos:
        abrangencia_str = ", ".join(mesos)
    elif mesos:
        abrangencia_str = f"{len(mesos)} Mesorregiões"
    else:
        abrangencia_str = "Todo o Estado (SC)"

    # Municípios
    muns = df_geral['municipio'].unique() if not df_geral.empty else []
    if len(muns) >= 293:
        muns_str = "Todos os 295 Municípios"
    elif len(muns) == 1:
        muns_str = muns[0]
    elif len(muns) <= 3 and len(muns) > 0:
        muns_str = ", ".join(muns)
    elif len(muns) > 0:
        muns_str = f"{len(muns)} Municípios Selecionados"
    else:
        muns_str = "Todos os 295 Municípios"

    # Associações de Municípios
    assocs = [a for a in df_geral['associacao'].unique() if a != 'Não informado'] if not df_geral.empty else []
    if len(assocs) >= 20:
        assocs_str = "Todas / Diversas Associações de Municípios"
    elif len(assocs) <= 2 and assocs:
        assocs_str = ", ".join(assocs)
    elif assocs:
        assocs_str = f"{len(assocs)} Associações de Municípios"
    else:
        assocs_str = "Todas / Diversas Associações de Municípios"

    # Crimes
    crimes = df_geral['fato_comunicado'].unique() if not df_geral.empty else []
    if len(crimes) >= 5 or len(crimes) == 0:
        crimes_str = "Todos os crimes cadastrados"
    elif len(crimes) == 1:
        crimes_str = crimes[0]
    else:
        crimes_str = f"{len(crimes)} Crimes Selecionados"

    # Faixa Etária
    if idade_selecionada is not None and hasattr(idade_selecionada, '__getitem__') and len(idade_selecionada) == 2:
        if idade_selecionada[0] == 0 and idade_selecionada[1] == 100:
            faixa_str = "Todas as idades (0 a 100+ anos)"
        else:
            idade_max = f"{idade_selecionada[1]} anos" if idade_selecionada[1] < 100 else "100+ anos"
            faixa_str = f"{idade_selecionada[0]} a {idade_max}"
    else:
        faixa_str = "Todas as idades (0 a 100+ anos)"

    filtros_info = {
        'periodo': periodo_str,
        'abrangencia': abrangencia_str,
        'municipios': muns_str,
        'associacoes': assocs_str,
        'crimes': crimes_str,
        'faixa_etaria': faixa_str,
        'visualizacao': f"Agrupado por {agrupamento}",
        'data_emissao': datetime.now().strftime('%d/%m/%Y às %H:%M')
    }

    # Logo
    logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo_ovm.png')
    if not os.path.exists(logo_path):
        logo_path = None

    # Inicializa o PDF
    pdf = RelatorioOVMCompletoPDF(logo_path=logo_path, filtros_info=filtros_info)
    pdf.alias_nb_pages()

    # =========================================================================
    # PÁGINA 1: RESUMO EXECUTIVO - ANÁLISE GERAL
    # =========================================================================
    pdf.add_page()
    add_section_header(
        pdf,
        "Resumo Executivo — Análise Geral de Ocorrências",
        "Panorama dos registros de violência contra a mulher no Estado de Santa Catarina"
    )

    total_registros = len(df_geral)
    crimes_por_dia = total_registros / dias_totais if dias_totais > 0 else 0
    crimes_por_hora = total_registros / (dias_totais * 24) if dias_totais > 0 else 0

    media_idade = 0.0
    if not df_geral.empty and df_geral['idade_vitima'].notna().any():
        media_idade = df_geral['idade_vitima'].mean()

    pct_fds = 0.0
    if not df_geral.empty:
        ocorr_fds = df_geral[df_geral['data_fato'].dt.dayofweek.isin([5, 6])].shape[0]
        pct_fds = (ocorr_fds / total_registros * 100) if total_registros > 0 else 0.0

    tendencia = calcular_tendencia_mensal(df_geral)
    tend_texto = f"{tendencia:+.1f}% a.a." if pd.notna(tendencia) else "N/A"

    add_kpis(pdf, [
        {'label': 'Total Registros', 'value': f"{total_registros:,}".replace(',', '.')},
        {'label': 'Média / Dia', 'value': f"{crimes_por_dia:.1f}"},
        {'label': 'Média / Hora', 'value': f"{crimes_por_hora:.2f}"},
        {'label': 'Tendência', 'value': tend_texto},
        {'label': 'Idade Média', 'value': f"{media_idade:.1f} anos"},
        {'label': 'Fins de Semana', 'value': f"{pct_fds:.1f}%"},
    ])

    pdf.set_font(pdf.font_family_name, '', 7.8)
    pdf.set_text_color(*CINZA_TEXTO)
    data_ini_str = data_inicial.strftime('%d/%m/%Y') if data_inicial else 'Início'
    data_fim_str = data_final.strftime('%d/%m/%Y') if data_final else 'Fim'
    pdf.multi_cell(
        190, 4.2,
        f"Este documento apresenta o consolidado dos registros oficiais de violência doméstica e familiar "
        f"contra a mulher em Santa Catarina entre {data_ini_str} e {data_fim_str}. "
        f"No período analisado foram contabilizadas {total_registros:,}".replace(',', '.') + f" ocorrências. "
        f"A idade média das vítimas é de {media_idade:.1f} anos, com {pct_fds:.1f}% das infrações ocorrendo aos finais de semana."
    )
    pdf.ln(3)

    if not df_geral.empty:
        top_crimes = df_geral['fato_comunicado'].value_counts().head(5).reset_index()
        top_crimes.columns = ['Natureza do Crime', 'Total']
        top_crimes['% do Total'] = (top_crimes['Total'] / total_registros * 100).apply(lambda x: f"{x:.1f}%")
        add_table(pdf, top_crimes, title="Principais Fatos Comunicados (Top 5)")

    # =========================================================================
    # PÁGINA 2: SÉRIE HISTÓRICA MENSAL
    # =========================================================================
    pdf.add_page()
    add_section_header(
        pdf,
        "Série Histórica Mensal de Ocorrências",
        "Evolução temporal das ocorrências registradas mês a mês no período"
    )
    if not df_geral.empty:
        df_temporal = df_geral.copy()
        df_temporal['ano_mes'] = df_temporal['data_fato'].dt.to_period('M').astype(str)
        if agrupamento == "Consolidado":
            registros_por_mes_ano = df_temporal.groupby('ano_mes').size().reset_index(name='quantidade').sort_values('ano_mes')
            color_p = None
        else:
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            registros_por_mes_ano = df_temporal.groupby(['ano_mes', col_agrup], observed=True).size().reset_index(name='quantidade').sort_values('ano_mes')
            color_p = col_agrup

        fig_temporal = plot_serie_temporal(registros_por_mes_ano, "Linha", agrupamento, color_p)
        img_temporal = _fig_to_image(fig_temporal, width=1050, height=520)
        add_image_box(pdf, img_temporal, w=190, max_h=190)

    # =========================================================================
    # PÁGINA 3: OCORRÊNCIAS POR ANO E POR MÊS
    # =========================================================================
    pdf.add_page()
    add_section_header(
        pdf,
        "Distribuição Temporal — Anos e Meses",
        "Comparativo de volume anual e padrão de sazonalidade mensal"
    )
    if not df_geral.empty:
        ano_corrente = pd.Timestamp.now().year
        if agrupamento == "Consolidado":
            registros_por_ano = df_geral['ano'].value_counts().sort_index().reset_index()
            registros_por_ano.columns = ['ano', 'Quantidade']
            color_p = None
        else:
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            registros_por_ano = df_geral.groupby(['ano', col_agrup], observed=True).size().reset_index(name='Quantidade')
            color_p = col_agrup

        if not registros_por_ano.empty:
            registros_por_ano['ano'] = registros_por_ano['ano'].apply(lambda x: f'{x} (Parcial)' if x == ano_corrente else str(x))
        fig_ano = plot_por_ano(registros_por_ano, "Barras", agrupamento, color_p)
        img_ano = _fig_to_image(fig_ano, width=900, height=380)

        meses_ordem = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        nomes_meses_pt = {'January': 'Jan', 'February': 'Fev', 'March': 'Mar', 'April': 'Abr', 'May': 'Mai', 'June': 'Jun', 'July': 'Jul', 'August': 'Ago', 'September': 'Set', 'October': 'Out', 'November': 'Nov', 'December': 'Dez'}
        df_geral_temp = df_geral.copy()
        df_geral_temp['mes_cat'] = pd.Categorical(df_geral_temp['mes'], categories=meses_ordem, ordered=True)
        registros_por_mes = df_geral_temp['mes_cat'].value_counts().sort_index().reset_index()
        registros_por_mes.columns = ['Mês', 'Quantidade']
        registros_por_mes['Mês'] = registros_por_mes['Mês'].map(nomes_meses_pt)
        fig_mes = plot_por_mes(registros_por_mes, "Barras")
        img_mes = _fig_to_image(fig_mes, width=900, height=380)

        add_two_images(pdf, img_ano, img_mes, title1="Total de Ocorrências por Ano", title2="Sazonalidade Mensal Acumulada", max_h=92)

    # =========================================================================
    # PÁGINA 4: DIA DA SEMANA E FAIXA ETÁRIA
    # =========================================================================
    pdf.add_page()
    add_section_header(
        pdf,
        "Distribuição por Dia da Semana e Faixa Etária",
        "Concentração das ocorrências nos dias da semana e perfil etário das vítimas"
    )
    if not df_geral.empty:
        df_geral_temp = df_geral.copy()
        df_geral_temp['dia_semana'] = df_geral_temp['data_fato'].dt.day_name()
        dias_ordem = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        nomes_dias_pt = {'Sunday': 'Dom', 'Monday': 'Seg', 'Tuesday': 'Ter', 'Wednesday': 'Qua', 'Thursday': 'Qui', 'Friday': 'Sex', 'Saturday': 'Sáb'}
        df_geral_temp['dia_semana_cat'] = pd.Categorical(df_geral_temp['dia_semana'], categories=dias_ordem, ordered=True)
        registros_por_dia = df_geral_temp['dia_semana_cat'].value_counts().sort_index().reset_index()
        registros_por_dia.columns = ['Dia da Semana', 'Quantidade']
        registros_por_dia['Dia da Semana'] = registros_por_dia['Dia da Semana'].map(nomes_dias_pt)
        fig_dia = plot_dia_semana(registros_por_dia, "Barras")
        img_dia = _fig_to_image(fig_dia, width=900, height=380)

        df_faixa = df_geral.dropna(subset=['idade_vitima']).copy()
        bins = [0, 12, 17, 29, 40, 50, 60, 70, 79, 120]
        labels = ['0-12', '13-17', '18-29', '30-40', '41-50', '51-60', '61-70', '71-79', '80+']
        df_faixa['faixa_etaria'] = pd.cut(df_faixa['idade_vitima'], bins=bins, labels=labels, right=True)
        registros_por_faixa = df_faixa['faixa_etaria'].value_counts().sort_index().reset_index()
        registros_por_faixa.columns = ['Faixa Etária', 'Quantidade']
        fig_faixa = plot_faixa_etaria(registros_por_faixa, "Barras")
        img_faixa = _fig_to_image(fig_faixa, width=900, height=380)

        add_two_images(pdf, img_dia, img_faixa, title1="Volume de Crimes por Dia da Semana", title2="Distribuição por Faixa Etária da Vítima", max_h=92)

    # =========================================================================
    # PÁGINA 5: NATUREZA DOS CRIMES E VULNERABILIDADE
    # =========================================================================
    pdf.add_page()
    add_section_header(
        pdf,
        "Natureza das Ocorrências e Vulnerabilidade",
        "Crimes mais frequentes e distribuição percentual de tipos de crime por idade"
    )
    if not df_geral.empty:
        if agrupamento == "Consolidado":
            registros_por_fato = df_geral['fato_comunicado'].value_counts().reset_index()
            registros_por_fato.columns = ['fato_comunicado', 'Quantidade']
            color_p = None
        else:
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            registros_por_fato = df_geral.groupby(['fato_comunicado', col_agrup], observed=True).size().reset_index(name='Quantidade')
            color_p = col_agrup

        fig_fato = plot_tipo_crime(registros_por_fato, "Barras", agrupamento, color_p)
        img_fato = _fig_to_image(fig_fato, width=900, height=380)

        df_vuln = df_geral.dropna(subset=['idade_vitima']).copy()
        bins = [0, 12, 17, 29, 40, 50, 60, 70, 79, 120]
        labels = ['0-12', '13-17', '18-29', '30-40', '41-50', '51-60', '61-70', '71-79', '80+']
        df_vuln['faixa_etaria'] = pd.cut(df_vuln['idade_vitima'], bins=bins, labels=labels, right=True)
        crime_counts = df_vuln.groupby(['faixa_etaria', 'fato_comunicado'], observed=False).size().unstack(fill_value=0)
        crime_pct = crime_counts.div(crime_counts.sum(axis=1), axis=0) * 100
        crime_pct = crime_pct.reset_index()
        df_plot = crime_pct.melt(id_vars='faixa_etaria', var_name='fato_comunicado', value_name='percentual')
        fig_vuln = plot_barras_vulnerabilidade(df_plot)
        img_vuln = _fig_to_image(fig_vuln, width=900, height=380)

        add_two_images(pdf, img_fato, img_vuln, title1="Fatos Comunicados Mais Frequentes", title2="Composição Percentual de Crimes por Faixa Etária", max_h=92)

    # =========================================================================
    # PÁGINA 6: TABELA CONSOLIDADA DE OCORRÊNCIAS
    # =========================================================================
    pdf.add_page()
    add_section_header(
        pdf,
        "Tabela Consolidada de Ocorrências",
        "Histórico anual por tipologia penal e evolução temporal"
    )
    if not df_geral.empty:
        if agrupamento != "Consolidado":
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            tabela_cons = criar_tabela_consolidada(df_geral, col_agrup, agrupamento, df_original_filtrado=df_geral)
        else:
            tabela_cons = criar_tabela_total_consolidada(df_geral, df_original_filtrado=df_geral)

        if tabela_cons is not None and not tabela_cons.empty:
            add_table(pdf, tabela_cons, max_rows=40)

    # =========================================================================
    # PÁGINA 7: TAXA POPULACIONAL
    # =========================================================================
    pdf.add_page()
    add_section_header(
        pdf,
        "Taxa de Ocorrências por População Feminina",
        "Indicadores proporcionais por 1.000 habitantes mulheres"
    )
    if not df_geral.empty and not df_populacao.empty:
        anos_no_filtro = df_geral['ano'].unique()
        num_anos = len(anos_no_filtro) if len(anos_no_filtro) > 0 else 1
        tabela_pop = criar_tabela_populacional_agrupada(df_geral, df_populacao, df_regioes, agrupamento, num_anos)
        if tabela_pop is not None and not tabela_pop.empty:
            add_table(pdf, tabela_pop.reset_index(), max_rows=35)

    # =========================================================================
    # PÁGINA 8: RESUMO EXECUTIVO - FEMINICÍDIOS
    # =========================================================================
    pdf.add_page()
    add_section_header(
        pdf,
        "Resumo Executivo — Análise de Feminicídios",
        "Indicadores críticos de letalidade e fatores de risco em Santa Catarina"
    )
    total_fem = len(df_feminicidio)
    if total_fem > 0:
        vitimas_bo = df_feminicidio[df_feminicidio['bo_de_vd_contra_o_autor'].astype(str).str.upper() == 'SIM'].shape[0]
        pct_bo = (vitimas_bo / total_fem * 100) if total_fem > 0 else 0.0

        autores_hist = 0
        if 'passagem_por_violencia_domestica' in df_feminicidio.columns:
            autores_hist = df_feminicidio[df_feminicidio['passagem_por_violencia_domestica'].astype(str).str.upper() == 'SIM'].shape[0]
        pct_hist = (autores_hist / total_fem * 100) if total_fem > 0 else 0.0

        add_kpis(pdf, [
            {'label': 'Total de Feminicídios', 'value': str(total_fem)},
            {'label': '% Vítimas c/ BO Anterior', 'value': f"{pct_bo:.1f}%"},
            {'label': '% Autores c/ Histórico VD', 'value': f"{pct_hist:.1f}%"},
        ])

        pdf.set_font(pdf.font_family_name, '', 7.8)
        pdf.set_text_color(*CINZA_TEXTO)
        pdf.multi_cell(
            190, 4.2,
            f"A análise de feminicídios investiga as mortes consumadas de mulheres por razões da condição de sexo feminino. "
            f"No período foram registrados {total_fem} feminicídios em Santa Catarina. "
            f"Em {pct_bo:.1f}% dos casos a vítima já possuía Boletim de Ocorrência anterior registrado contra o autor, "
            f"e em {pct_hist:.1f}% dos casos o agressor já tinha passagens policiais prévias por violência doméstica."
        )
        pdf.ln(4)

        top_mun_fem = df_feminicidio['municipio'].value_counts().head(8).reset_index()
        top_mun_fem.columns = ['Município', 'Feminicídios']
        top_mun_fem['% do Estado'] = (top_mun_fem['Feminicídios'] / total_fem * 100).apply(lambda x: f"{x:.1f}%")
        add_table(pdf, top_mun_fem, title="Municípios com Maior Registro de Feminicídios (Top 8)")
    else:
        pdf.set_font(pdf.font_family_name, 'I', 9)
        pdf.set_text_color(*CINZA_SUAVE)
        pdf.cell(0, 10, 'Nenhum registro de feminicídio encontrado para os filtros selecionados.', ln=True)

    # =========================================================================
    # PÁGINA 9: EVOLUÇÃO TEMPORAL DE FEMINICÍDIOS
    # =========================================================================
    if total_fem > 0:
        pdf.add_page()
        add_section_header(
            pdf,
            "Evolução Histórica de Feminicídios",
            "Série temporal mensal e distribuição de mortes por ano"
        )
        df_fem_temp = df_feminicidio.copy()
        df_fem_temp['ano_mes'] = df_fem_temp['data_fato'].dt.to_period('M').astype(str)
        if agrupamento == "Consolidado":
            fem_por_mes = df_fem_temp.groupby('ano_mes').size().reset_index(name='Quantidade')
            color_p = None
        else:
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            fem_por_mes = df_fem_temp.groupby(['ano_mes', col_agrup], observed=True).size().reset_index(name='Quantidade')
            color_p = col_agrup
        fem_por_mes.rename(columns={'ano_mes': 'Mês/Ano'}, inplace=True)
        fig_fem_serie = plot_feminicidio_serie_temporal(fem_por_mes, "Barras", agrupamento, color_p)
        img_fem_serie = _fig_to_image(fig_fem_serie, width=900, height=380)

        ano_corrente = pd.Timestamp.now().year
        if agrupamento == "Consolidado":
            fem_por_ano = df_feminicidio['ano'].value_counts().sort_index().reset_index()
            fem_por_ano.columns = ['ano', 'Quantidade']
            color_p = None
        else:
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            fem_por_ano = df_feminicidio.groupby(['ano', col_agrup], observed=True).size().reset_index(name='Quantidade')
            color_p = col_agrup

        if not fem_por_ano.empty:
            fem_por_ano['ano'] = fem_por_ano['ano'].apply(lambda x: f'{x} (Parcial)' if x == ano_corrente else str(x))
        fig_fem_ano = plot_feminicidio_por_ano(fem_por_ano, "Barras", agrupamento, color_p)
        img_fem_ano = _fig_to_image(fig_fem_ano, width=900, height=380)

        add_two_images(pdf, img_fem_serie, img_fem_ano, title1="Série Temporal de Feminicídios", title2="Feminicídios por Ano", max_h=92)

    # =========================================================================
    # PÁGINA 10: PERFIL DO FEMINICÍDIO (VÍNCULO, MEIO, AUTOR)
    # =========================================================================
    if total_fem > 0:
        pdf.add_page()
        add_section_header(
            pdf,
            "Perfil do Feminicídio — Relação, Meio e Autor",
            "Vínculo da vítima com o agressor, instrumento utilizado e situação penal"
        )
        if agrupamento == "Consolidado":
            vinculo = df_feminicidio['relacao_autor'].value_counts().reset_index()
            vinculo.columns = ['relacao_autor', 'Quantidade']
            color_p = None
        else:
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            vinculo = df_feminicidio.groupby(['relacao_autor', col_agrup], observed=True).size().reset_index(name='Quantidade')
            color_p = col_agrup

        fig_vinculo = plot_vinculo_autor(vinculo, "Barras", agrupamento, color_p)
        img_vinculo = _fig_to_image(fig_vinculo, width=900, height=380)

        if agrupamento == "Consolidado":
            meio = df_feminicidio['meio_crime'].value_counts().reset_index()
            meio.columns = ['meio_crime', 'Quantidade']
            color_p = None
        else:
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            meio = df_feminicidio.groupby(['meio_crime', col_agrup], observed=True).size().reset_index(name='Quantidade')
            color_p = col_agrup

        fig_meio = plot_meio_crime(meio, "Barras", agrupamento, color_p)
        img_meio = _fig_to_image(fig_meio, width=900, height=380)

        add_two_images(pdf, img_vinculo, img_meio, title1="Vínculo / Relação da Vítima com o Autor", title2="Meio Empregado no Feminicídio", max_h=92)

    # =========================================================================
    # PÁGINA 11: TABELA CONSOLIDADA DE FEMINICÍDIOS
    # =========================================================================
    if total_fem > 0:
        pdf.add_page()
        add_section_header(
            pdf,
            "Tabela Consolidada de Feminicídios",
            "Detalhamento anual de ocorrências consumadas"
        )
        if agrupamento != "Consolidado":
            mapa_agrup = {"Município": "municipio", "Mesorregião": "mesoregiao", "Associação": "associacao", "Associação de Municípios": "associacao"}
            col_agrup = mapa_agrup.get(agrupamento, 'municipio')
            tabela_fem = criar_tabela_feminicidio_agrupado(df_feminicidio, col_agrup, agrupamento, df_original_filtrado=df_feminicidio)
        else:
            tabela_fem = criar_tabela_total_feminicidio(df_feminicidio, df_original_filtrado=df_feminicidio)

        if tabela_fem is not None and not tabela_fem.empty:
            add_table(pdf, tabela_fem, max_rows=35)

    # =========================================================================
    # PÁGINA 12: ÍNDICE DE LETALIDADE
    # =========================================================================
    if not df_geral.empty and not df_feminicidio.empty:
        pdf.add_page()
        add_section_header(
            pdf,
            "Índice de Letalidade da Violência Contra a Mulher",
            "Relação percentual entre ocorrências violentas e desfecho fatal"
        )
        pdf.set_font(pdf.font_family_name, '', 7.6)
        pdf.set_text_color(*CINZA_TEXTO)
        pdf.multi_cell(
            190, 4.0,
            'O Índice de Letalidade expressa a proporção: "A cada 100 ocorrências de violência contra a mulher registradas, '
            'quantas resultaram em feminicídio consumado?" Regiões com índice elevado merecem atenção redobrada das forças de segurança e da rede de proteção.'
        )
        pdf.ln(3)

        agrup_let = agrupamento if agrupamento != "Consolidado" else "Mesorregião"
        df_letalidade = calcular_indice_letalidade(df_geral, df_feminicidio, agrup_let)
        if df_letalidade is not None and not df_letalidade.empty:
            df_ranking = df_letalidade.rename(columns={
                'localidade': agrup_let,
                'total_eventos': 'Total Eventos',
                'total_ocorrencias': 'Ocorrências Gerais',
                'total_feminicidios': 'Feminicídios',
                'indice_letalidade': 'Índice de Letalidade (%)'
            })
            add_table(pdf, df_ranking, max_rows=20, title=f"Ranking de Letalidade por {agrup_let}")

    # Exporta para bytes
    pdf_bytes = bytes(pdf.output())

    # Libera imediatamente da memória RAM todos os objetos temporários
    del pdf
    import gc
    gc.collect()

    return pdf_bytes
