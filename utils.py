# utils.py

import streamlit as st

def configurar_pagina(titulo_pagina):
    """
    Configura o layout da página, adicionando o logo, o título e a sidebar.
    """
    st.set_page_config(layout="wide", page_title=titulo_pagina)

    # --- CABEÇALHO COM LOGO E TÍTULO ---
    col1, col2 = st.columns([1, 4]) # Proporção das colunas
    with col1:
        try:
            st.image("assets/logo.png", width=150)
        except Exception as e:
            st.error(f"Erro ao carregar o logo: {e}")
    with col2:
        st.title(titulo_pagina)

    # --- BARRA LATERAL (SIDEBAR) ---
    if st.session_state.get("identificado", False):
        st.sidebar.markdown(f"Bem-vindo, **{st.session_state.nome.split(' ')[0]}**!")
        st.sidebar.markdown("---")
    
    # Adiciona a assinatura no final da sidebar para ficar em todas as páginas
    st.sidebar.caption("Desenvolvido por 🧙‍♂️ Fabio Sena 🧙‍♂️ | Versão 1.4")
