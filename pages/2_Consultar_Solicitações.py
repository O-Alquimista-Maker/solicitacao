# pages/2_Consultar_Solicitações.py

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import psycopg2
import warnings

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable.*", category=UserWarning)

# --- FUNÇÕES DE BANCO DE DADOS E UTILITÁRIOS (sem alterações) ---
def init_connection():
    try: return psycopg2.connect(**st.secrets["database"])
    except: return None

def fetch_all_solicitacoes(conn):
    if conn is None: return pd.DataFrame()
    try:
        query = "SELECT * FROM solicitacoes ORDER BY data_solicitacao DESC;"
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}"); return pd.DataFrame()

def to_excel(df):
    output = BytesIO()
    df_copy = df.copy()
    if 'data_solicitacao' in df_copy.columns:
        df_copy['data_solicitacao'] = df_copy['data_solicitacao'].dt.tz_localize(None)
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_copy.to_excel(writer, index=False, sheet_name='RelatorioSolicitacoes')
        worksheet = writer.sheets['RelatorioSolicitacoes']
        for i, col in enumerate(df_copy.columns):
            column_len = max(df_copy[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
    return output.getvalue()

def gerar_excel_formulario(dados):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook  = writer.book
        worksheet = workbook.add_worksheet('Solicitacao')
        header_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center', 'valign': 'vcenter', 'bg_color': '#D9D9D9', 'border': 1})
        title_format = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'left', 'valign': 'vcenter'})
        data_format = workbook.add_format({'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00', 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': 1})
        worksheet.insert_image('A1', 'assets/logo.png', {'x_scale': 0.5, 'y_scale': 0.5})
        worksheet.set_row(0, 60)
        worksheet.merge_range('B1:D1', 'FORMULÁRIO DE ENVIO PARA ASSISTÊNCIA TÉCNICA', header_format)
        row = 2
        for campo, valor_dado in dados.items():
            worksheet.write(row, 0, campo, title_format)
            if campo == "Valor":
                worksheet.merge_range(row, 1, row, 3, valor_dado, money_format)
            else:
                worksheet.merge_range(row, 1, row, 3, str(valor_dado), data_format)
            worksheet.set_row(row, 30)
            row += 1
        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:D', 25)
        row += 2
        worksheet.merge_range(row, 0, row, 3, '_________________________________________', workbook.add_format({'align': 'center'}))
        row += 1
        worksheet.merge_range(row, 0, row, 3, 'Assinatura do Solicitante', workbook.add_format({'align': 'center'}))
    return output.getvalue()

# --- LÓGICA DA PÁGINA ---
if not st.session_state.get("identificado", False):
    st.error("Por favor, faça a identificação na página principal para continuar."); st.stop()

st.set_page_config(layout="wide", page_title="Consultar Solicitações")
st.title("Consultar Histórico de Solicitações")
st.markdown("---")

conn = init_connection()
if not conn:
    st.error("Conexão com o banco de dados falhou."); st.stop()

df = fetch_all_solicitacoes(conn)
if df.empty:
    st.warning("Nenhuma solicitação encontrada."); st.stop()

# --- FILTROS (sem alterações) ---
st.sidebar.markdown("---"); st.sidebar.header("Filtros da Consulta")
search_term = st.sidebar.text_input("Buscar por Solicitante, Modelo ou Código:")
min_date, max_date = df['data_solicitacao'].min().date(), df['data_solicitacao'].max().date()
date_range = st.sidebar.date_input("Filtrar por Data:", value=(min_date, max_date), min_value=min_date, max_value=max_date)
df_filtrado = df.copy()
if search_term:
    df_filtrado = df_filtrado[df_filtrado.apply(lambda row: search_term.lower() in str(row['solicitante']).lower() or \
                                                          search_term.lower() in str(row['modelo_equipamento']).lower() or \
                                                          search_term.lower() in str(row['codigo_equipamento']).lower(), axis=1)]
if len(date_range) == 2:
    start_date, end_date = pd.to_datetime(date_range[0]).date(), pd.to_datetime(date_range[1]).date()
    df_filtrado = df_filtrado[df_filtrado['data_solicitacao'].dt.date.between(start_date, end_date)]

# --- EXIBIÇÃO DA TABELA COM BOTÕES (GRANDE MUDANÇA AQUI) ---
st.write(f"**Exibindo {len(df_filtrado)} de {len(df)} solicitações.**")

# Cabeçalho da tabela
colunas = st.columns((2, 2, 2, 1)) # Ajuste as proporções conforme necessário
campos = ["Data da Solicitação", "Solicitante", "Modelo do Equipamento", "Ações"]
for col, campo in zip(colunas, campos):
    col.markdown(f"**{campo}**")

# Inicializa o estado para o download
if 'download_info' not in st.session_state:
    st.session_state.download_info = None

# Itera sobre as linhas do DataFrame filtrado para criar a tabela
for index, row in df_filtrado.iterrows():
    col1, col2, col3, col4 = st.columns((2, 2, 2, 1))
    
    with col1:
        st.write(row['data_solicitacao'].strftime('%d/%m/%Y %H:%M'))
    with col2:
        st.write(row['solicitante'])
    with col3:
        st.write(row['modelo_equipamento'])
    with col4:
        # O 'key' do botão é único para cada linha, usando o ID da solicitação
        if st.button("Gerar Formulário", key=f"form_{row['id']}"):
            # Prepara os dados para a função que gera o Excel
            dados_para_excel = {
                "Data da Solicitação": row['data_solicitacao'].strftime('%d/%m/%Y %H:%M:%S'),
                "Solicitante": row['solicitante'],
                "Setor/Cargo": row['setor_cargo'],
                "Modelo do Equipamento": row['modelo_equipamento'],
                "Descrição do Equipamento": row['descricao_equipamento'] or "Não informado",
                "Código do Equipamento": row['codigo_equipamento'],
                "Sistema Alocado": row['sistema_alocado'],
                "Quantidade": row['quantidade'],
                "Centro de Custo": row['centro_custo'] or "Não informado",
                "Valor": row['valor'] or 0.0,
                "Motivo do Envio": row['motivo_envio']
            }
            
            # Gera os bytes do Excel
            excel_bytes = gerar_excel_formulario(dados_para_excel)
            
            # Armazena as informações para o download no session_state
            st.session_state.download_info = {
                "data": excel_bytes,
                "file_name": f"solicitacao_{row['solicitante'].split(' ')[0]}_{row['data_solicitacao'].strftime('%Y%m%d')}.xlsx"
            }
            # st.rerun() é crucial para atualizar a tela e mostrar o botão de download
            st.rerun()

# --- LÓGICA DE DOWNLOAD ---
# Verifica se há um arquivo pronto para ser baixado no session_state
if st.session_state.download_info:
    st.sidebar.markdown("---")
    st.sidebar.subheader("Download Pronto")
    st.sidebar.download_button(
        label="📥 Baixar Formulário Gerado",
        data=st.session_state.download_info["data"],
        file_name=st.session_state.download_info["file_name"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    # Limpa o estado após oferecer o download para não mostrar o botão para sempre
    st.session_state.download_info = None

st.markdown("---")
# Botão para exportar o relatório completo (a lista)
if not df_filtrado.empty:
    excel_data = to_excel(df_filtrado)
    st.download_button(label="📊 Exportar Lista Filtrada para Excel", data=excel_data,
                       file_name=f"relatorio_solicitacoes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
