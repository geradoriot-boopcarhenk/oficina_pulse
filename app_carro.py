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

def generar_recibo_impressao(nome_cliente, detalhes_os, nome_oficina, telefone_cliente, cpf_cliente):
    html_recibo = f"""
    <div style="padding: 20px; border: 2px solid #333; border-radius: 10px; font-family: sans-serif; background-color: white; color: black;">
        <h2 style="text-align: center; margin-bottom: 5px; color: #EA580C;">📋 RECIBO DE ORDEM DE SERVIÇO - {nome_oficina.upper()}</h2>
        <p style="text-align: center; font-size: 12px; color: #555; margin-top: 0;">Ecossistema Digital Pulse SaaS</p>
        <hr style="border: 1px solid #333;">
        <h4>👤 DADOS DO CLIENTE & VEÍCULO:</h4>
        <p><b>Nome / Veículo:</b> {nome_cliente}</p>
        <p><b>WhatsApp:</b> {telefone_cliente} | <b>CPF:</b> {cpf_cliente}</p>
        <hr style="border: 1px dashed #ccc;">
        <h4>🛠️ DETALHES DOS SERVIÇOS E PRODUTOS:</h4>
        <p style="font-size: 16px; background-color: #f9f9f9; padding: 15px; border-left: 5px solid #EA580C; border-radius: 4px;">{detalhes_os}</p>
        <br>
        <p style="text-align: center; font-size: 11px; color: #777;">Obrigado pela preferência! Volte sempre.</p>
    </div>
    """
    st.markdown(html_recibo, unsafe_allow_html=True)
    st.button("🖨️ Acionar Impressora / Salvar PDF", on_click=st.dialog("Instruções: Pressione Ctrl + P na sua tela para salvar como PDF instantaneamente!"))

if "oficina_autenticada" not in st.session_state:
    st.session_state["oficina_autenticada"] = None

if not st.session_state["oficina_autenticada"]:
    st.markdown("<h1 style='text-align: center; color: #EA580C;'>🚗 Oficina Pulse Automotiva - Portal de Assinantes</h1>", unsafe_allow_html=True)
    st.write("---")
    tab_login, tab_cadastro = st.tabs(["🔑 Acessar Sistema", "🏢 Cadastrar Nova Oficina"])
    with tab_login:
        usuario_input = st.text_input("Usuário Administrativo")
        senha_input = st.text_input("Senha Comercial", type="password")
        if st.button("Entrar no Painel", width="stretch"):
            oficina = db.autenticar_oficina(usuario_input, senha_input)
            if oficina:
                st.session_state["oficina_autenticada"] = oficina if isinstance(oficina, list) else oficina
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
                    st.success("✅ Oficina cadastrada com sucesso! Agora você pode fazer o login na aba ao lado.")
                else:
                    st.error("❌ Erro ao cadastrar. O usuário já pode estar em uso.")
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
menu = ["Painel Geral", "Clientes & Carros", "Estoque de Peças", "📋 Ordens de Serviço (OS)", "📜 Histórico de Clientes", "⚙️ Perfil da Oficina"]
escolha = st.sidebar.selectbox("Mapeamento do Sistema", menu)

if escolha == "Painel Geral":
    col1, col2 = st.columns(2)
    col1.metric("OS em Andamento", db.contar_os_por_status("Pendente"))
    faturamento_atual = db.obter_totais_financeiros()
    col2.metric("Faturamento Mensal", f"R$ {faturamento_atual:,.2f}")
    if faturamento_atual > 0:
        st.markdown("#### 📈 Desempenho Financeiro")
        df_grafico = pd.DataFrame([{"Mês": "Outubro", "Faturamento (R$)": faturamento_atual}])
        st.bar_chart(df_grafico, x="Mês", y="Faturamento (R$)")

elif escolha == "Clientes & Carros":
    st.markdown("### 📝 Cadastro de Cliente Proprietário e Veículo")
    with st.form("form_cliente_v3", clear_on_submit=True):
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
                nome_vinculado = f"{nome.strip().title()} ({marca_car.strip().title()} {modelo_car.strip().title()} | {placa_formatada} | {cor_car.strip().title()})"
                db.cadastrar_cliente(nome_vinculado, tel_formatado, cpf_formatado, oficina_id)
                st.success("🎉 Proprietário e Veículo cadastrados com sucesso!")
                st.rerun()
            else:
                st.error("⚠️ Por favor, preencha todos os campos obrigatórios!")
    st.markdown("### 📋 Seus Clientes Cadastrados")
    lista_c = db.listar_clientes(oficina_id)
    if lista_c:
        df_clientes = pd.DataFrame(lista_c)[['nome', 'telefone', 'cpf']]
        df_clientes.columns = ['Proprietário / Veículo Vinculado', 'WhatsApp', 'CPF']
        st.dataframe(df_clientes, width="stretch", hide_index=True)

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
    st.markdown("#### 📋 Almoxarifado de Peças Ativo")
    pecas = db.listar_pecas_estoque(oficina_id)
    if pecas:
        dados_tabela_estoque = []
        for p in pecas:
            nome_peca = p.get('nome_peça') or p.get('nome_peca') or "Sem Nome"
            qtd_atual = p.get('quantidade') or p.get('quantidade_atual') or 0
            dados_tabela_estoque.append({
                "Nome da Peça": nome_peca,
                "Qtd em Estoque": qtd_atual,
                "Preço de Custo": p.get('preco_custo', 0.0),
                "Preço de Venda": p.get('preco_venda', 0.0)
            })
        st.dataframe(pd.DataFrame(dados_tabela_estoque), width="stretch", hide_index=True)

elif escolha == "📋 Ordens de Serviço (OS)":
    st.markdown("### 📋 Módulo de Ordens de Serviço e Orçamentos Comerciais")
    st.write("---")
    lista_c = db.listar_clientes(oficina_id)
    pecas_estoque = db.listar_pecas_estoque(oficina_id)
    if not lista_c:
        st.warning("⚠️ Cadastre pelo menos um Cliente antes de abrir uma Ordem de Serviço.")
    else:
        st.markdown("#### 🛠️ Abrir Nova Ordem de Serviço com Peças")
        with st.form("form_os", clear_on_submit=True):
            dict_clientes = {c['nome']: c['id'] for c in lista_c}
            cliente_selecionado = st.selectbox("Selecione o Proprietário / Veículo", list(dict_clientes.keys()))
            descricao_problema = st.text_area("Descrição dos Serviços / Defeito")
            if pecas_estoque:
                dict_pecas = {}
                for p in pecas_estoque:
                    nome_chave = p.get('nome_peça') or p.get('nome_peca') or "Peça sem nome"
                    dict_pecas[nome_chave] = p
                peca_selecionada = st.selectbox("Vincular Peça do Estoque (Opcional)", ["Nenhuma"] + list(dict_pecas.keys()))
                qtd_peca = st.number_input("Quantidade da Peça utilizada", min_value=1, value=1)
            else:
                st.info("💡 Nenhum produto cadastrado no Estoque de Peças ainda.")
                peca_selecionada = "Nenhuma"
                qtd_peca = 0
            valor_mao_de_obra = st.number_input("Valor da Mão de Obra / Serviço (R$)", min_value=0.0, value=100.0)
            if st.form_submit_button("Gerar Nova OS"):
                if descricao_problema:
                    total_pecas_calculado = 0.0
                    detalhe_peca_texto = ""
                    if peca_selecionada != "Nenhuma":
                        p_dados = dict_pecas[peca_selecionada]
