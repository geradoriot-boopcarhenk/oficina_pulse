# app_carro.py
import streamlit as st
import database as db
import pandas as pd
import utils
import urllib.parse
import base64

st.set_page_config(page_title="Oficina Mecânica Automotiva", page_icon="🚗", layout="wide")

if "oficina_autenticada" not in st.session_state:
    st.session_state["oficina_autenticada"] = None

if not st.session_state["oficina_autenticada"]:
    st.markdown("<h1 style='text-align: center; color: #EA580C;'>🚗 Oficina Pulse Automotiva - Portal de Assinantes</h1>", unsafe_allow_html=True)
    st.write("---")
    tab_login, tab_cadastro = st.tabs(["🔑 Acessar Painel", "🏢 Cadastrar Nova Oficina"])
    with tab_login:
        usuario_input = st.text_input("Usuário Administrativo")
        senha_input = st.text_input("Senha Comercial", type="password")
        if st.button("Entrar no Painel", width="stretch"):
            oficina = db.autenticar_oficina(usuario_input, senha_input)
            if oficina:
                st.session_state["oficina_autenticada"] = oficina
                st.success("🎉 Bem-vindo!")
                st.rerun()
            else:
                st.error("❌ Credenciais incorretas!")
    with tab_cadastro:
        st.markdown("### 📝 Crie sua conta")
        novo_nome = st.text_input("Nome da Oficina / Razão Social")
        novo_user = st.text_input("Escolha um Usuário único")
        nova_senha = st.text_input("Escolha uma Senha segura", type="password")
        if st.button("Finalizar Cadastro de Empresa", width="stretch"):
            if novo_nome and novo_user and nova_senha:
                if db.cadastrar_nova_oficina(novo_nome, novo_user, nova_senha):
                    st.success("✅ Oficina cadastrada! Faça login na aba ao lado.")
                else:
                    st.error("❌ Usuário já está em uso!")
    st.stop()

oficina_id = st.session_state["oficina_autenticada"]["id"]
nome_oficina_ativa = st.session_state["oficina_autenticada"]["nome_oficina"]

logo_data = db.obter_logomarca_oficina(oficina_id)
if logo_data:
    st.sidebar.image(f"data:image/png;base64,{logo_data}", use_container_width=True)
else:
    st.sidebar.markdown(f"### 🏢 {nome_oficina_ativa}")

if st.sidebar.button("🚪 Sair / Trocar de Conta"):
    st.session_state["oficina_autenticada"] = None
    st.rerun()

st.title(f"🚗 Gestão Integrada - {nome_oficina_ativa}")
menu = ["Painel Geral", "Clientes & Carros", "Estoque de Peças", "⚙️ Perfil da Oficina"]
escolha = st.sidebar.selectbox("Mapeamento do Sistema", menu)

if escolha == "Painel Geral":
    col1, col2 = st.columns(2)
    col1.metric("OS em Andamento", db.contar_os_por_status("Pendente"))
    col2.metric("Faturamento Mensal", "R$ 0,00")

elif escolha == "Clientes & Carros":
    st.markdown("### 📝 Cadastro de Cliente Proprietário")
    with st.form("form_cliente"):
        nome = st.text_input("Nome do Proprietário")
        cpf_visual = st.text_input("CPF")
        tel_visual = st.text_input("WhatsApp de Contato")
        if st.form_submit_button("Salvar Registro Proprietário") and nome and cpf_visual and tel_visual:
            db.cadastrar_cliente(nome, tel_visual, cpf_visual, oficina_id)
            st.success("🎉 Cliente cadastrado com sucesso!")
            st.rerun()
    
    st.markdown("### 📋 Seus Clientes Cadastrados")
    lista_c = db.listar_clientes(oficina_id)
    if lista_c: st.dataframe(pd.DataFrame(lista_c)[['nome', 'telefone', 'cpf']], width="stretch", hide_index=True)

elif escolha == "Estoque de Peças":
    st.markdown("### 🗂️ Estoque de Peças Automotivas")
    with st.form("form_estoque"):
        n_p = st.text_input("Nome da Peça")
        qtd = st.number_input("Quantidade em Estoque", min_value=0, value=5)
        c_u = st.number_input("Preço de Custo (R$)", min_value=0.0)
        v_u = st.number_input("Preço de Venda (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar no Almoxarifado") and n_p:
            db.cadastrar_peca_estoque(oficina_id, n_p, qtd, c_u, v_u)
            st.success(f"📦 {n_p} adicionada!")
            st.rerun()
            
    st.markdown("#### 📋 Almoxarifado de Peças Ativo")
    pecas = db.listar_pecas_estoque(oficina_id)
    if pecas: st.dataframe(pd.DataFrame(pecas)[['nome_peca', 'quantidade_atual', 'preco_custo', 'preco_venda']], width="stretch", hide_index=True)

elif escolha == "⚙️ Perfil da Oficina":
    st.markdown("### ⚙️ Configurações da Oficina")
    st.write("---")
    uploaded_file = st.file_uploader("🖼️ Envie a Logomarca da sua Oficina (.png ou .jpg)", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        if st.button("💾 Salvar Logomarca no Sistema", width="stretch"):
            if db.salvar_logomarca_oficina(oficina_id, base64_image):
                st.success("🎉 Logomarca atualizada com sucesso! Atualize a página.")
                st.rerun()
