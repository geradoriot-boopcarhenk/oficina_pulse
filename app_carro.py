# app_carro.py
import streamlit as st
import database_carro as db
import pandas as pd
import base64
import re

st.set_page_config(page_title="Oficina Mecânica Automotiva", page_icon="🚗", layout="wide")

def formatar_cpf(cpf):
    nums = re.sub(r'\D', '', cpf)
    if len(nums) == 11:
        return f"{nums[:3]}.{nums[3:6]}.{nums[6:9]}-{nums[9:]}"
    return cpf

def formatar_telefone(tel):
    nums = re.sub(r'\D', '', tel)
    if len(nums) == 11:
        return f"({nums[:2]}) {nums[2:7]}-{nums[7:]}"
    elif len(nums) == 10:
        return f"({nums[:2]}) {nums[2:6]}-{nums[6:]}"
    return tel

def formatar_placa(placa):
    return placa.strip().upper()

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
    st.markdown("### 📝 Cadastro de Cliente Proprietário e Veículo")
    with st.form("form_cliente", clear_on_submit=True):
        st.markdown("#### 👤 Dados do Proprietário")
        nome = st.text_input("Nome do Proprietário")
        cpf_visual = st.text_input("CPF (Somente números)")
        tel_visual = st.text_input("WhatsApp de Contato (Com DDD)")
        
        st.markdown("#### 🚗 Dados do Veículo")
        col_car1, col_car2 = st.columns(2)
        marca_car = col_car1.text_input("Marca do Carro (Ex: Fiat, Chevrolet)")
        modelo_car = col_car2.text_input("Modelo do Carro (Ex: Uno, Onix)")
        placa_car = col_car1.text_input("Placa do Carro")
        cor_car = col_car2.text_input("Cor do Carro")
        
        if st.form_submit_button("Salvar Registro Completo"):
            if nome and cpf_visual and tel_visual and marca_car and modelo_car and placa_car:
                cpf_formatado = formatar_cpf(cpf_visual)
                tel_formatado = formatar_telefone(tel_visual)
                placa_formatada = formatar_placa(placa_car)
                
                # Monta a string do veiculo para guardar de forma limpa
                veiculo_completo = f"{marca_car.strip().title()} {modelo_car.strip().title()} - {cor_car.strip().title()}"
                
                # Envia para a tabela clientes
                db.cadastrar_cliente(nome, tel_formatado, cpf_formatado, oficina_id)
                
                st.success("🎉 Proprietário e Veículo cadastrados com sucesso!")
                st.rerun()
            else:
                st.error("⚠️ Por favor, preencha todos os campos obrigatórios!")
    
    st.markdown("### 📋 Seus Clientes e Carros Cadastrados")
    lista_c = db.listar_clientes(oficina_id)
    if lista_c:
        df_clientes = pd.DataFrame(lista_c)
        # Verifica quais colunas vieram para evitar quebras visuais
        colunas_exibir = []
        df_final = pd.DataFrame()
        
        if 'nome' in df_clientes.columns:
            df_final['Nome do Proprietário'] = df_clientes['nome']
        if 'telefone' in df_clientes.columns:
            df_final['WhatsApp'] = df_clientes['telefone']
        if 'cpf' in df_clientes.columns:
            df_final['CPF'] = df_clientes['cpf']
            
        st.dataframe(df_final, width="stretch", hide_index=True)

elif escolha == "Estoque de Peças":
    st.markdown("### 🗂️ Estoque de Peças Automotivas")
    with st.form("form_estoque", clear_on_submit=True):
        n_p = st.text_input("Nome da Peça")
        qtd = st.number_input("Quantidade em Estoque", min_value=0, value=5)
        c_u = st.number_input("Preço de Custo (R$)", min_value=0.0)
        v_u = st.number_input("Preço de Venda (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar no Almoxarifado") and n_p:
            db.cadastrar_peca_estoque(oficina_id, n_p, qtd, c_u, v_u)
            st.success(f"📦 {n_p} adicionada!")
            st.rerun()
    pecas = db.listar_pecas_estoque(oficina_id)
    if pecas: st.dataframe(pd.DataFrame(pecas)[['nome_peça', 'whitespace', 'preco_custo', 'preco_venda']], width="stretch", hide_index=True)

elif escolha == "⚙️ Perfil da Oficina":
    st.markdown("### ⚙️ Configurações da Oficina")
    uploaded_file = st.file_uploader("🖼️ Envie a Logomarca da sua Oficina", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        if st.button("💾 Salvar Logomarca", width="stretch"):
            if db.salvar_logomarca_oficina(oficina_id, base64_image):
                st.success("🎉 Logomarca atualizada!")
                st.rerun()
