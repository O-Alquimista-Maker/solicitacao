# app.py (versão com Senha Mestre)

import streamlit as st
from streamlit.errors import StreamlitAPIException
from utils import configurar_pagina

# --- CONFIGURAÇÃO DA PÁGINA ---
configurar_pagina(titulo_pagina="Sistema de Manutenção")

# --- ESTADO DA SESSÃO ---
# Adicionamos 'autenticado' para controlar o acesso com a senha mestre
if 'autenticado' not in st.session_state: st.session_state.autenticado = False
if 'nome' not in st.session_state: st.session_state.nome = ""
if 'setor_cargo' not in st.session_state: st.session_state.setor_cargo = ""
if 'identificado' not in st.session_state: st.session_state.identificado = False

# --- FUNÇÕES DE AUTENTICAÇÃO E IDENTIFICAÇÃO ---
def tela_de_senha():
    st.header("Acesso Restrito")
    senha_digitada = st.text_input("Por favor, digite a senha mestre para acessar o sistema:", type="password")
    
    if st.button("Entrar"):
        # Compara a senha digitada com a senha no secrets.toml
        if senha_digitada == st.secrets["auth"]["master_password"]:
            st.session_state.autenticado = True
            st.rerun() # Recarrega a página para liberar o acesso
        else:
            st.error("Senha incorreta. Tente novamente.")

def tela_identificacao():
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

# --- LÓGICA PRINCIPAL DE ROTEAMENTO ---
# 1. Verifica se o usuário passou pela tela de senha
if not st.session_state.autenticado:
    tela_de_senha()

# 2. Se passou pela senha, mas não se identificou, mostra a tela de identificação
elif not st.session_state.identificado:
    tela_identificacao()

# 3. Se já está autenticado e identificado, mostra a tela de boas-vindas
else:
    st.write("Use o menu à esquerda para navegar entre as funcionalidades.")
    st.info("⬅️ Você pode criar uma nova solicitação ou consultar o histórico a qualquer momento.")

# A assinatura foi movida para a função configurar_pagina na sidebar
