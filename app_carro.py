# app_carro.py - Versao Enterprise SaaS com Painel Mestre e Cobrancas
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

# Inicializacao de sessoes
if "oficina_autenticada" not in st.session_state:
    st.session_state["oficina_autenticada"] = None
if "modo_admin" not in st.session_state:
    st.session_state["modo_admin"] = False

# TELA DE AUTENTICACAO GERAL
if not st.session_state["oficina_autenticada"] and not st.session_state["modo_admin"]:
    st.markdown("<h1 style='text-align: center; color: #EA580C;'>🚗 Oficina Pulse Automotiva - Portal de Assinantes</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("### 🔑 Acessar Sistema Privado")
    usuario_input = st.text_input("Usuário Administrativo")
    senha_input = st.text_input("Senha Comercial", type="password")
    
    if st.button("Entrar no Painel", width="stretch"):
        # ROTA SECRETA DE ADMIN DO DONO DO SOFTWARE (CARLOS HENRIQUE)
        if usuario_input == "admin" and senha_input == "master123":
            st.session_state["modo_admin"] = True
            st.success("👑 Painel de Administrador Geral Ativado!")
            st.rerun()
        else:
            oficina = db.autenticar_oficina(usuario_input, senha_input)
            if oficina:
                st.session_state["oficina_autenticada"] = oficina if isinstance(oficina, list) else oficina
                st.success("🎉 Bem-vindo ao sistema!")
                st.rerun()
            else:
                st.error("❌ Credenciais incorretas!")
    st.stop()

# ----------------- TELA MESTRE DO ADMINISTRADOR -----------------
if st.session_state["modo_admin"]:
    st.title("👑 Central do Administrador Mestre - Pulse SaaS")
    st.write("Gerencie os acessos, inadimplências e status de pagamento das oficinas parceiras.")
    
    if st.sidebar.button("🚪 Sair do Modo Admin"):
        st.session_state["modo_admin"] = False
        st.rerun()
        
    st.write("---")
    st.markdown("### 🏢 Clientes / Oficinas Ativas no Banco")
    
    oficinas_cadastradas = db.listar_todas_oficinas()
    if oficinas_cadastradas:
        for ofi in oficinas_cadastradas:
            col_nome, col_user, col_status, col_acao = st.columns([2, 1.5, 1, 1.5])
            col_nome.write(f"🏢 **{ofi['nome_oficina']}**")
            col_user.write(f"👤 Usuário: `{ofi['usuario']}`")
            
            status_atual = ofi.get('status_pagamento') or ofi.get('status') or 'Ativo'
            if status_atual == 'Ativo':
                col_status.markdown("🟢 **Ativo**")
                if col_acao.button("🔴 Bloquear Acesso", key=f"bloq_{ofi['id']}"):
                    db.alterar_status_oficina(ofi['id'], 'Bloqueado')
                    st.toast(f"Oficina {ofi['nome_oficina']} Bloqueada!")
                    st.rerun()
            else:
                col_status.markdown("🔴 **Bloqueado**")
                if col_acao.button("🟢 Ativar Assinatura", key=f"ativ_{ofi['id']}"):
                    db.alterar_status_oficina(ofi['id'], 'Ativo')
                    st.toast(f"Oficina {ofi['nome_oficina']} Ativada!")
                    st.rerun()
    else:
        st.info("Nenhuma oficina registrada no banco de dados ainda.")
    st.stop()

# ----------------- FLUXO DO CLIENTE (OFICINA MECANICA) -----------------
oficina_crua = st.session_state["oficina_autenticada"]
oficina_dados = oficina_crua[0] if isinstance(oficina_crua, list) and len(oficina_crua) > 0 else oficina_crua

oficina_id = oficina_dados["id"]
nome_oficina_ativa = oficina_dados["nome_oficina"]
status_assinatura = db.obter_status_assinatura(oficina_id)

if status_assinatura == 'Bloqueado':
    st.markdown("<h1 style='text-align: center; color: #DC2626;'>🚨 Sistema Suspenso por Inadimplência</h1>", unsafe_allow_html=True)
    st.write("---")
    st.error(f"Prezado gestor da {nome_oficina_ativa}, identificamos que a assinatura mensal do seu Ecossistema ERP Pulse está atrasada.")
    
    st.markdown("### 💳 Regularize agora via PIX para liberação imediata:")
    col_pix1, col_pix2 = st.columns()
    col_pix1.image("https://r2.dev", width=200, caption="Escaneie para Pagar")
    col_pix2.markdown("""
    **Valor da Mensalidade:** R$ 149,00  
    **Chave PIX Copia e Cola:** `cobranca-pulse-saas-automotivo-master-key-payment-gateway`  
    
    *Após efetuar o pagamento, o sistema identificará a transação automaticamente e liberará todas as suas ordens de serviço e histórico em até 2 minutos.*
    """)
    
    if st.sidebar.button("🚪 Sair da Conta"):
        st.session_state["oficina_autenticada"] = None
        st.rerun()
    st.stop()

# SE PASSAR PELA TRAVA, ABRE O ERP OPERACIONAL INTEGRADO
try:
    logo_data = db.obter_logomarca_oficina(oficina_id)
except:
    logo_data = None

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
        marca_car = col_car1.text_input("Marca do Carro")
        modelo_car = col_car2.text_input("Modelo do Carro")
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
    st.markdown("### 📋 Módulo de Ordens de Serviço")
    lista_c = db.listar_clientes(oficina_id)
    pecas_estoque = db.listar_pecas_estoque(oficina_id)
    if not lista_c:
        st.warning("⚠️ Cadastre pelo menos um Cliente antes de abrir uma OS.")
    else:
        with st.form("form_os", clear_on_submit=True):
            dict_clientes = {c['nome']: c['id'] for c in lista_c}
