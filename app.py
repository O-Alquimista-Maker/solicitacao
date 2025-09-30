# app.py (versão com redirecionamento automático)

import streamlit as st
from streamlit.errors import StreamlitAPIException

# --- CONFIGURAÇÃO INICIAL E ESTADO DA SESSÃO ---
# st.set_page_config deve ser o primeiro comando Streamlit
st.set_page_config(layout="wide", page_title="Sistema de Manutenção")

# Inicializa o estado da sessão
if 'nome' not in st.session_state: st.session_state.nome = ""
if 'setor_cargo' not in st.session_state: st.session_state.setor_cargo = ""
if 'identificado' not in st.session_state: st.session_state.identificado = False

# --- FUNÇÃO DE IDENTIFICAÇÃO (MODIFICADA) ---
def tela_identificacao():
    st.title("Sistema de Solicitação de Manutenção")
    st.header("Identificação do Usuário")
    
    # Etapa 1: Solicitar o nome
    if st.session_state.nome == "":
        nome_input = st.text_input("Por favor, digite seu nome completo:")
        if st.button("Confirmar Nome"):
            if nome_input:
                st.session_state.nome = nome_input
                st.rerun() # Re-executa para passar para a próxima etapa
            else:
                st.warning("O nome é obrigatório.")

    # Etapa 2: Solicitar Setor/Cargo e redirecionar
    elif st.session_state.setor_cargo == "":
        st.write(f"### Bem-vindo, {st.session_state.nome}!")
        setor_cargo_input = st.text_input("Agora, preencha seu Setor/Cargo:")
        
        if st.button("Entrar e Iniciar Solicitação"):
            if setor_cargo_input:
                st.session_state.setor_cargo = setor_cargo_input
                st.session_state.identificado = True
                
                # --- MÁGICA DO REDIRECIONAMENTO AQUI ---
                try:
                    st.switch_page("pages/1_Nova_Solicitação.py")
                except StreamlitAPIException:
                    # Fallback para versões mais antigas do Streamlit ou se a página não for encontrada
                    st.error("Não foi possível redirecionar para a página de solicitação.")
                    st.info("Por favor, selecione 'Nova Solicitação' no menu à esquerda.")
                    st.rerun() # Apenas atualiza a página para mostrar o menu
            else:
                st.warning("O Setor/Cargo é obrigatório.")

# --- LÓGICA PRINCIPAL ---
# Se o usuário já estiver identificado, mas estiver na página principal,
# mostre o menu e uma mensagem de boas-vindas.
if st.session_state.identificado:
    st.sidebar.markdown(f"Bem-vindo, **{st.session_state.nome.split(' ')[0]}**!")
    st.sidebar.markdown("---")
    st.header("Bem-vindo ao Sistema!")
    st.write("Use o menu à esquerda para navegar entre as funcionalidades.")
    st.info("⬅️ Você pode criar uma nova solicitação ou consultar o histórico a qualquer momento.")
# Se não estiver identificado, execute o processo de login.
else:
    tela_identificacao()
