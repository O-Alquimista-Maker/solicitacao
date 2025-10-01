# pages/2_Consultar_Solicitações.py

import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import psycopg2
import warnings
from PIL import Image

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable.*", category=UserWarning)

# --- FUNÇÕES DE BANCO DE DADOS E UTILITÁRIOS ---
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

# >>>>> NOVA FUNÇÃO DE EXCLUSÃO <<<<<
def delete_solicitacao(conn, id_para_excluir):
    if conn is None: return False
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM solicitacoes WHERE id = %s;", (id_para_excluir,))
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao excluir a solicitação: {e}")
        conn.rollback()
        return False

# ... (funções to_excel e gerar_excel_formulario permanecem inalteradas) ...
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
        header_format = workbook.add_format({'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        code_format = workbook.add_format({'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'border': 1})
        title_format = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'left', 'valign': 'vcenter'})
        data_format = workbook.add_format({'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'text_wrap': True})
        money_format = workbook.add_format({'num_format': 'R$ #,##0.00', 'font_size': 11, 'align': 'left', 'valign': 'vcenter', 'border': 1})

        worksheet.merge_range('A1:A2', '', header_format)
        try:
            largura_desejada_px, altura_desejada_px = 159, 57
            with Image.open("assets/logo.png") as img:
                largura_original_px, altura_original_px = img.size
            escala_x = largura_desejada_px / largura_original_px
            escala_y = altura_desejada_px / altura_original_px
            worksheet.insert_image('A1', 'assets/logo.png', {'x_scale': escala_x, 'y_scale': escala_y, 'object_position': 1})
        except FileNotFoundError:
            worksheet.write('A1', 'Logo')

        worksheet.merge_range('B1:C2', 'FORMULÁRIO DE ENVIO PARA ASSISTÊNCIA TÉCNICA', header_format)
        worksheet.write('D1', 'F00000', code_format)
        worksheet.write('D2', 'Ver:00', code_format)
        
        worksheet.set_row(0, 35)
        worksheet.set_row(1, 35)
        
        row = 2
        for campo, valor_dado in dados.items():
            worksheet.write(row, 0, campo, title_format)
            if campo == "Valor":
                worksheet.merge_range(row, 1, row, 3, valor_dado, money_format)
            else:
                worksheet.merge_range(row, 1, row, 3, str(valor_dado), data_format)
            worksheet.set_row(row, 30)
            row += 1
            
        worksheet.set_column('A:A', 30); worksheet.set_column('B:C', 25); worksheet.set_column('D:D', 10)
        
        row += 2
        worksheet.merge_range(row, 0, row, 3, '_________________________________________', workbook.add_format({'align': 'center'}))
        row += 1
        worksheet.merge_range(row, 0, row, 3, 'Assinatura do Solicitante', workbook.add_format({'align': 'center'}))
    return output.getvalue()

# --- LÓGICA DA PÁGINA ---
if not st.session_state.get("identificado", False):
    st.error("Por favor, faça a identificação na página principal para continuar."); st.stop()

st.set_page_config(layout="wide", page_title="Consultar Solicitações")
st.title("📊 Consultar Histórico de Solicitações")
st.markdown("---")

conn = init_connection()
if not conn:
    st.error("Conexão com o banco de dados falhou."); st.stop()

# --- MODAL DE CONFIRMAÇÃO DE EXCLUSÃO ---
# Inicializa o estado para controlar o modal
if 'solicitacao_para_excluir' not in st.session_state:
    st.session_state.solicitacao_para_excluir = None

# Se houver uma solicitação marcada para exclusão, mostra o modal
if st.session_state.solicitacao_para_excluir is not None:
    solicitacao = st.session_state.solicitacao_para_excluir
    
    # Usamos um st.expander como um modal improvisado
    with st.expander("🚨 **CONFIRMAR EXCLUSÃO** 🚨", expanded=True):
        st.warning(f"Você tem certeza que deseja excluir permanentemente a solicitação para o equipamento **{solicitacao['modelo_equipamento']}** (ID: {solicitacao['id']})?")
        st.write("**Esta ação não pode ser desfeita.**")
        
        col1, col2, _ = st.columns([1, 1, 4])
        with col1:
            if st.button("Sim, excluir", type="primary"):
                if delete_solicitacao(conn, solicitacao['id']):
                    st.success("Solicitação excluída com sucesso!")
                    st.session_state.solicitacao_para_excluir = None # Limpa o estado
                    st.rerun() # Recarrega a página
                else:
                    st.error("A exclusão falhou. Verifique o console para mais detalhes.")
        with col2:
            if st.button("Cancelar"):
                st.session_state.solicitacao_para_excluir = None # Limpa o estado
                st.rerun() # Recarrega a página

# --- LÓGICA PRINCIPAL DA PÁGINA (só executa se não houver modal aberto) ---
if st.session_state.solicitacao_para_excluir is None:
    df = fetch_all_solicitacoes(conn)
    if df.empty:
        st.warning("Nenhuma solicitação encontrada."); st.stop()

    # --- FILTROS ---
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

    # --- EXIBIÇÃO DA TABELA ---
    st.write(f"**Exibindo {len(df_filtrado)} de {len(df)} solicitações.**")
    colunas = st.columns((2, 2, 2, 1, 2)) # Ajusta a proporção para a nova coluna de ações
    campos = ["Data", "Solicitante", "Modelo", "Foto", "Ações"]
    for col, campo in zip(colunas, campos):
        col.markdown(f"**{campo}**")

    if 'download_info' not in st.session_state:
        st.session_state.download_info = None

    for index, row in df_filtrado.iterrows():
        col1, col2, col3, col4, col5 = st.columns((2, 2, 2, 1, 2))
        with col1: st.write(row['data_solicitacao'].strftime('%d/%m/%Y %H:%M'))
        with col2: st.write(row['solicitante'])
        with col3: st.write(row['modelo_equipamento'])
        with col4:
            if pd.notna(row['url_imagem']):
                st.markdown(f'<a href="{row["url_imagem"]}" target="_blank"><img src="{row["url_imagem"]}" width="70"></a>', unsafe_allow_html=True)
            else:
                st.write("N/A")
        with col5:
            # Coluna para os botões de ação
            action_col1, action_col2 = st.columns(2)
            with action_col1:
                if st.button("🖨️", key=f"form_{row['id']}", help="Gerar formulário Excel"):
                    # ... (lógica para gerar formulário)
                    dados_para_excel = {
                        "Data da Solicitação": row['data_solicitacao'].strftime('%d/%m/%Y %H:%M:%S'), "Solicitante": row['solicitante'],
                        "Setor/Cargo": row['setor_cargo'], "Modelo do Equipamento": row['modelo_equipamento'],
                        "Descrição do Equipamento": row['descricao_equipamento'] or "Não informado", "Código do Equipamento": row['codigo_equipamento'],
                        "Sistema Alocado": row['sistema_alocado'], "Quantidade": row['quantidade'], "Centro de Custo": row['centro_custo'] or "Não informado",
                        "Valor": row['valor'] or 0.0, "Motivo do Envio": row['motivo_envio']
                    }
                    excel_bytes = gerar_excel_formulario(dados_para_excel)
                    st.session_state.download_info = {
                        "data": excel_bytes,
                        "file_name": f"solicitacao_{row['solicitante'].split(' ')[0]}_{row['data_solicitacao'].strftime('%Y%m%d')}.xlsx"
                    }
                    st.rerun()
            with action_col2:
                if st.button("🗑️", key=f"delete_{row['id']}", help="Excluir solicitação"):
                    # Marca a solicitação para exclusão e recarrega para mostrar o modal
                    st.session_state.solicitacao_para_excluir = row
                    st.rerun()

    # --- LÓGICA DE DOWNLOAD E EXPORTAÇÃO ---
    if st.session_state.download_info:
        st.sidebar.markdown("---"); st.sidebar.subheader("Download Pronto")
        st.sidebar.download_button(
            label="📥 Baixar Formulário Gerado", data=st.session_state.download_info["data"],
            file_name=st.session_state.download_info["file_name"],
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.session_state.download_info = None

    st.markdown("---")
    if not df_filtrado.empty:
        excel_data = to_excel(df_filtrado)
        st.download_button(label="📊 Exportar Lista Filtrada para Excel", data=excel_data,
                           file_name=f"relatorio_solicitacoes_{datetime.now().strftime('%Y%m%d')}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.caption("Desenvolvido por 🧙‍♂️ Fabio Sena 🧙‍♂️ | Versão 1.3")

