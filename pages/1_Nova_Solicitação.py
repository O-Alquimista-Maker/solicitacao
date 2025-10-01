# pages/1_Nova_Solicitação.py

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import base64
from io import BytesIO
import psycopg2
import warnings
from PIL import Image

warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy connectable.*", category=UserWarning)

# --- FUNÇÕES DE BANCO DE DADOS E UTILITÁRIOS ---
def init_connection():
    try: return psycopg2.connect(**st.secrets["database"])
    except: return None

def insert_solicitacao(conn, dados):
    if conn is None: return False
    insert_query = """
    INSERT INTO solicitacoes (data_solicitacao, solicitante, setor_cargo, modelo_equipamento, descricao_equipamento, 
                              codigo_equipamento, sistema_alocado, quantidade, centro_custo, valor, motivo_envio)
    VALUES (%(data_solicitacao)s, %(solicitante)s, %(setor_cargo)s, %(modelo_equipamento)s, %(descricao_equipamento)s,
            %(codigo_equipamento)s, %(sistema_alocado)s, %(quantidade)s, %(centro_custo)s, %(valor)s, %(motivo_envio)s);
    """
    try:
        with conn.cursor() as cur:
            cur.execute(insert_query, dados)
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir dados no banco: {e}"); conn.rollback(); return False

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
        altura_linha_pt = (altura_desejada_px * 0.75) / 2
        worksheet.set_row(0, altura_linha_pt)
        worksheet.set_row(1, altura_linha_pt)
        
        row = 2
        for campo, valor_dado in dados.items():
            worksheet.write(row, 0, campo, title_format)
            if campo == "Valor":
                worksheet.merge_range(row, 1, row, 3, valor_dado, money_format)
            else:
                worksheet.merge_range(row, 1, row, 3, str(valor_dado), data_format)
            worksheet.set_row(row, 30)
            row += 1
            
        worksheet.set_column('A:A', 30); worksheet.set_column('B:C', 50); worksheet.set_column('D:D', 10)
        row += 2
        worksheet.merge_range(row, 0, row, 3, '_________________________________________', workbook.add_format({'align': 'center'}))
        row += 1
        worksheet.merge_range(row, 0, row, 3, 'Assinatura do Solicitante', workbook.add_format({'align': 'center'}))
    return output.getvalue()

# --- LÓGICA DA PÁGINA ---
if not st.session_state.get("identificado", False):
    st.error("Por favor, faça a identificação na página principal para continuar."); st.stop()

st.set_page_config(layout="wide", page_title="Nova Solicitação")
st.title("📝 FORMULÁRIO DE ENVIO DE EQUIPAMENTOS")
st.info(f"Solicitante: **{st.session_state.nome}** | Setor/Cargo: **{st.session_state.setor_cargo}**")
st.markdown("---")

conn = init_connection()
if not conn:
    st.error("Conexão com o banco de dados falhou."); st.stop()

with st.form(key="formulario_envio", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        modelo = st.text_input("Modelo do Equipamento*"); descricao = st.text_input("Descrição do Equipamento (Opcional)")
        codigo = st.text_input("Código do Equipamento (Nº de Série)*"); sistema = st.text_input("Sistema Alocado*")
    with col2:
        quantidade = st.number_input("Quantidade*", min_value=1, step=1); centro_custo = st.text_input("Centro de Custo (Opcional)")
        valor = st.number_input("Valor (Opcional)", min_value=0.0, format="%.2f"); motivo = st.text_area("Motivo do Envio*", height=155)
    submit_button = st.form_submit_button(label="✔️ Enviar Solicitação e Gerar Formulário")

if submit_button:
    if not all([modelo, codigo, sistema, motivo]):
        st.error("Por favor, preencha todos os campos obrigatórios marcados com *."); st.stop()
    
    fuso_horario_sp = pytz.timezone('America/Sao_Paulo')
    data_solicitacao_obj = datetime.now(fuso_horario_sp)
    dados_para_bd = {
        "data_solicitacao": data_solicitacao_obj, "solicitante": st.session_state.nome, "setor_cargo": st.session_state.setor_cargo,
        "modelo_equipamento": modelo, "descricao_equipamento": descricao or None, "codigo_equipamento": codigo,
        "sistema_alocado": sistema, "quantidade": quantidade, "centro_custo": centro_custo or None, "valor": valor or None, "motivo_envio": motivo
    }
    if insert_solicitacao(conn, dados_para_bd):
        st.success("Solicitação salva no banco de dados e formulário gerado com sucesso!")
        dados_para_excel = {
            "Data da Solicitação": data_solicitacao_obj.strftime('%d/%m/%Y %H:%M:%S'), "Solicitante": st.session_state.nome,
            "Setor/Cargo": st.session_state.setor_cargo, "Modelo do Equipamento": modelo, "Descrição do Equipamento": descricao or "Não informado",
            "Código do Equipamento": codigo, "Sistema Alocado": sistema, "Quantidade": quantidade, "Centro de Custo": centro_custo or "Não informado",
            "Valor": valor or 0.0, "Motivo do Envio": motivo
        }
        dados_excel_bytes = gerar_excel_formulario(dados_para_excel)
        st.download_button(
            label="📥 Baixar Formulário de Solicitação (Excel)", data=dados_excel_bytes,
            file_name=f"solicitacao_{st.session_state.nome.split(' ')[0]}_{data_solicitacao_obj.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Falha ao salvar a solicitação. O formulário Excel não foi gerado.")

st.caption("Desenvolvido por 🧙‍♂️ Fabio Sena 🧙‍♂️ | Versão 1.3")
