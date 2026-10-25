# app.py
import streamlit as st
import database_moto as db
import pandas as pd
import utils
import urllib.parse
import base64

st.set_page_config(page_title="Oficina de Motos", page_icon="🏍️", layout="wide")

if "oficina_autenticada" not in st.session_state:
    st.session_state["oficina_autenticada"] = None

if not st.session_state["oficina_autenticada"]:
    st.markdown("<h1 style='text-align: center; color: #F97316;'>🏍️ Oficina Pulse - Portal de Assinantes</h1>", unsafe_allow_html=True)
    st.write("---")
    tab_login, tab_cadastro = st.tabs(["🔑 Acessar Sistema", "🏢 Cadastrar Nova Oficina"])
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

st.title(f"🏍️ Gestão Integrada - {nome_oficina_ativa}")
menu = ["Painel Geral", "Clientes & Motos", "Estoque de Peças", "⚙️ Perfil da Oficina"]
escolha = st.sidebar.selectbox("Mapeamento do Sistema", menu)

if escolha == "Painel Geral":
    col1, col2 = st.columns(2)
    col1.metric("OS Ativas", db.contar_os_por_status("Pendente"))
    col2.metric("Faturamento Acumulado", "R$ 0,00")

elif escolha == "Clientes & Motos":
    st.markdown("### 📝 Cadastro de Cliente")
    with st.form("form_cliente"):
        nome = st.text_input("Nome Completo")
        cpf_visual = st.text_input("CPF")
        tel_visual = st.text_input("WhatsApp (Com DDD)")
        if st.form_submit_button("Salvar Registro") and nome and cpf_visual and tel_visual:
            db.cadastrar_cliente(nome, tel_visual, cpf_visual, oficina_id)
            st.success("🎉 Cliente cadastrado com sucesso!")
            st.rerun()
    lista_c = db.listar_clientes(oficina_id)
    if lista_c: st.dataframe(pd.DataFrame(lista_c)[['nome', 'telefone', 'cpf']], width="stretch", hide_index=True)

elif escolha == "Estoque de Peças":
    st.markdown("### 🗂️ Controle de Estoque de Motos")
    with st.form("form_estoque"):
        n_p = st.text_input("Nome da Peça")
        qtd = st.number_input("Quantidade Inicial", min_value=0, value=10)
        c_u = st.number_input("Preço de Custo (R$)", min_value=0.0)
        v_u = st.number_input("Preço de Venda (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar no Estoque") and n_p:
            db.cadastrar_peca_estoque(oficina_id, n_p, qtd, c_u, v_u)
            st.success(f"📦 {n_p} adicionada ao estoque!")
            st.rerun()
    pecas = db.listar_pecas_estoque(oficina_id)
    if pecas: st.dataframe(pd.DataFrame(pecas)[['nome_peca', 'quantidade_atual', 'preco_custo', 'preco_venda']], width="stretch", hide_index=True)

elif escolha == "⚙️ Perfil da Oficina":
    st.markdown("### ⚙️ Configurações da Oficina")
    uploaded_file = st.file_uploader("🖼️ Envie a Logomarca da sua Oficina", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        if st.button("💾 Salvar Logomarca", width="stretch"):
            if db.salvar_logomarca_oficina(oficina_id, base64_image):
                st.success("🎉 Logomarca salva com sucesso!")
                st.rerun()
