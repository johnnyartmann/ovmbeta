import pandas as pd
import holidays
from datetime import date, timedelta
from dateutil.easter import easter

def criar_base_calendario_brasil(start_year=2020, end_year=2040):
    """
    Cria uma base de dados completa com todos os dias do período especificado,
    enriquecida com informações sobre feriados nacionais brasileiros e outras
    datas importantes para análise de sazonalidade.

    Args:
        start_year (int): O ano de início do período.
        end_year (int): O ano de fim do período.

    Returns:
        pd.DataFrame: Um DataFrame com o calendário completo e as flags de eventos.
    """
    print(f"Gerando calendário de {start_year} a {end_year}...")

    # 1. Obter todos os feriados nacionais do período usando a biblioteca holidays
    br_holidays = holidays.Brazil(years=range(start_year, end_year + 1))
    
    # Adicionar feriados móveis e específicos solicitados
    for year in range(start_year, end_year + 1):
        easter_date = easter(year)
        
        # Carnaval (Sábado a Terça-feira)
        br_holidays[easter_date - timedelta(days=50)] = "Sábado de Carnaval"
        br_holidays[easter_date - timedelta(days=49)] = "Domingo de Carnaval"
        br_holidays[easter_date - timedelta(days=48)] = "Segunda-feira de Carnaval"
        br_holidays[easter_date - timedelta(days=47)] = "Terça-feira de Carnaval"
        
        # Quarta-feira de Cinzas
        br_holidays[easter_date - timedelta(days=46)] = "Quarta-feira de Cinzas"
        
        # Páscoa
        br_holidays[easter_date] = "Páscoa"
        
        # Corpus Christi (60 dias após a Páscoa)
        br_holidays[easter_date + timedelta(days=60)] = "Corpus Christi"
        
        # Véspera de Natal
        br_holidays[date(year, 12, 24)] = "Véspera de Natal"

    # Converter para um formato mais fácil de usar (DataFrame)
    df_feriados = pd.DataFrame(list(br_holidays.items()), columns=['data', 'nome_feriado'])
    df_feriados['data'] = pd.to_datetime(df_feriados['data'])
    print(f"Total de {len(df_feriados)} feriados nacionais encontrados.")

    # 2. Criar um DataFrame com TODOS os dias do período
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    
    df_calendario = pd.DataFrame({
        'data': pd.to_datetime(pd.date_range(start_date, end_date, freq='D'))
    })

    # 3. Juntar as informações de feriados ao calendário completo
    df_completo = pd.merge(df_calendario, df_feriados, on='data', how='left')

    # 4. Criar as colunas de análise (flags)
    
    # Flag para identificar se o dia é um feriado
    df_completo['is_feriado'] = df_completo['nome_feriado'].notna()

    # Flags para identificar fins de semana
    df_completo['dia_semana_num'] = df_completo['data'].dt.dayofweek # Segunda=0, Domingo=6
    df_completo['dia_semana_nome'] = df_completo['data'].dt.day_name()
    df_completo['is_fim_de_semana'] = df_completo['dia_semana_num'].isin([5, 6]) # Sábado ou Domingo

    # Flag para identificar a véspera de feriado (dia útil)
    # Usamos shift(-1) para "olhar" o dia seguinte
    df_completo['is_vespera_feriado'] = (
        (df_completo['is_feriado'].shift(-1) == True) & 
        (df_completo['is_fim_de_semana'] == False)
    ).fillna(False)

    # Flag para identificar o dia pós-feriado (útil para analisar "enforcamentos")
    # Usamos shift(1) para "olhar" o dia anterior
    df_completo['is_pos_feriado'] = (
        (df_completo['is_feriado'].shift(1) == True) &
        (df_completo['is_fim_de_semana'] == False)
    ).fillna(False)

    # Mapear nomes dos dias da semana para português
    nomes_dias_pt = {
        'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    df_completo['dia_semana_nome'] = df_completo['dia_semana_nome'].map(nomes_dias_pt)

    print("Colunas de análise criadas com sucesso.")
    return df_completo

if __name__ == "__main__":
    # --- CONFIGURAÇÕES ---
    ANO_INICIO = 2020
    ANO_FIM = 2040
    NOME_ARQUIVO_EXCEL = "data/base_calendario_feriados.xlsx"
    NOME_ARQUIVO_CSV = "data/base_calendario_feriados.csv"
    
    # Gera o DataFrame
    calendario_brasil = criar_base_calendario_brasil(ANO_INICIO, ANO_FIM)
    
    # --- SALVAR O ARQUIVO ---
    # Salvar em formato Excel (recomendado)
    try:
        calendario_brasil.to_excel(NOME_ARQUIVO_EXCEL, index=False, engine='openpyxl')
        print(f"\nBase de dados salva com sucesso em: '{NOME_ARQUIVO_EXCEL}'")
    except Exception as e:
        print(f"\nErro ao salvar o arquivo Excel: {e}")

    # Opcional: Salvar em formato CSV
    # try:
    #     calendario_brasil.to_csv(NOME_ARQUIVO_CSV, index=False, encoding='utf-8-sig')
    #     print(f"Base de dados salva com sucesso em: '{NOME_ARQUIVO_CSV}'")
    # except Exception as e:
    #     print(f"Erro ao salvar o arquivo CSV: {e}")
        
    print("\nVisualização das 5 primeiras linhas do arquivo gerado:")
    print(calendario_brasil.head())
    print("\nExemplo de um feriado (Ano Novo):")
    print(calendario_brasil[calendario_brasil['data'].dt.dayofyear <= 2])
    print("\nExemplo de um feriado móvel (Carnaval 2025):")
    print(calendario_brasil[(calendario_brasil['data'] >= '2025-03-01') & (calendario_brasil['data'] <= '2025-03-05')])