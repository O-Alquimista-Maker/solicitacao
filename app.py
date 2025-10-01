# app.py

import streamlit as st
from streamlit.errors import StreamlitAPIException
from utils import configurar_pagina # Importa a nova função

# --- CONFIGURAÇÃO DA PÁGINA ---
# A função agora cuida do st.set_page_config e do título
# O título aqui é o que aparece na aba do navegador
configurar_pagina(titulo_pagina="Sistema de Manutenção")

# --- ESTADO DA SESSÃO (sem alterações) ---
if 'nome' not in st.session_state: st.session_state.nome = ""
if 'setor_cargo' not in st.session_state: st.session_state.setor_cargo = ""
if 'identificado' not in st.session_state: st.session_state.identificado = False

# --- FUNÇÃO DE IDENTIFICAÇÃO ---
def tela_identificacao():
    # O título principal já foi adicionado pela função configurar_pagina
    st.header("Identificação do Usuário")
    
    if st.session_state.nome == "":
        nome_input = st.text_input("Por favor, digite seu nome completo:")
        if st.button("Confirmar Nome"):
            if nome_input:
                st.session_state.nome = nome_input; st.rerun()
            else:
                st.warning("O nome é obrigatório.")

    elif st.session_state.setor_cargo == "":
        st.write(f"### Bem-vindo, {st.session_state.nome}!")
        setor_cargo_input = st.text_input("Agora, preencha seu Setor/Cargo:")
        
        if st.button("Entrar e Iniciar Solicitação"):
            if setor_cargo_input:
                st.session_state.setor_cargo = setor_cargo_input
                st.session_state.identificado = True
                try:
                    st.switch_page("pages/1_Nova_Solicitação.py")
                except StreamlitAPIException:
                    st.error("Não foi possível redirecionar."); st.rerun()
            else:
                st.warning("O Setor/Cargo é obrigatório.")

# --- LÓGICA PRINCIPAL ---
if st.session_state.identificado:
    st.write("Use o menu à esquerda para navegar entre as funcionalidades.")
    st.info("⬅️ Você pode criar uma nova solicitação ou consultar o histórico a qualquer momento.")
else:
    tela_identificacao()

# A assinatura foi movida para a função configurar_pagina na sidebar
