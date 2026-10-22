# app_carro.py
import streamlit as st
import database as db
import pandas as pd
import utils
import urllib.parse

st.set_page_config(page_title="Oficina Mecânica Automotiva", page_icon="🚗", layout="wide")

# --- GERENCIADOR DE LOGIN MULTI-EMPRESAS ---
if "oficina_autenticada" not in st.session_state:
    st.session_state["oficina_autenticada"] = None

# --- TELA DE ACESSO BLINDADA ---
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
                st.success(f"🎉 Bem-vindo!")
                st.rerun()
            else:
                st.error("❌ Credenciais incorretas ou assinatura inativa!")
                
    with tab_cadastro:
        st.markdown("### 📝 Crie sua conta para começar a gerenciar e vender")
        novo_nome = st.text_input("Nome da Oficina / Razão Social")
        novo_user = st.text_input("Escolha um Usuário único")
        nova_senha = st.text_input("Escolha uma Senha segura", type="password")
        if st.button("Finalizar Cadastro de Empresa", width="stretch"):
            if novo_nome and novo_user and nova_senha:
                if db.cadastrar_nova_oficina(novo_nome, novo_user, nova_senha):
                    st.success("✅ Oficina cadastrada! Faça login na aba ao lado.")
                else:
                    st.error("❌ Usuário já está em uso! Escolha outro.")
    st.stop()

oficina_id = st.session_state["oficina_autenticada"]["id"]
nome_oficina_ativa = st.session_state["oficina_autenticada"]["nome_oficina"]

# --- BARRA LATERAL ---
st.sidebar.markdown(f"### 🏢 {nome_oficina_ativa}")
if st.sidebar.button("🚪 Sair / Trocar de Conta"):
    st.session_state["oficina_autenticada"] = None
    st.rerun()

st.title(f"🚗 Gestão Integrada - {nome_oficina_ativa}")

menu = ["Painel Geral", "Clientes & Carros", "Estoque de Peças", "Serviços & Reparos", "Ordens de Serviço (OS)"]
escolha = st.sidebar.selectbox("Mapeamento do Sistema", menu)

if escolha == "Painel Geral":
    col1, col2 = st.columns(2)
    col1.metric("OS em Andamento", db.contar_os_por_status("Pendente") + db.contar_os_por_status("Em Andamento"))
    col2.metric("Faturamento Mensal", f"R$ {db.obter_totais_financeiros():,.2f}")
    
    df_grafico = db.obter_dados_faturamento_grafico()
    if not df_grafico.empty: 
        st.line_chart(df_grafico.set_index("Mês"), y="Faturamento", color="#EA580C")

elif escolha == "Clientes & Carros":
    tab1, tab2 = st.tabs(["Cadastro de Clientes", "Cadastro de Veículos (Carros)"])
    with tab1:
        st.markdown("### 📝 Novo Cliente")
        with st.form("form_cliente"):
            nome = st.text_input("Nome do Proprietário")
            cpf_visual = st.text_input("CPF")
            tel_visual = st.text_input("WhatsApp de Contato")
            if st.form_submit_button("Salvar Registro"):
                if nome and cpf_visual and tel_visual:
                    db.cadastrar_cliente(nome, tel_visual, cpf_visual, oficina_id)
                    st.success("🎉 Cliente cadastrado com sucesso!")
                    st.rerun()

        st.markdown("### 📋 Seus Clientes Cadastrados")
        lista_c = db.listar_clientes(oficina_id)
        if lista_c: st.dataframe(pd.DataFrame(lista_c)[['nome', 'telefone', 'cpf']], width="stretch", hide_index=True)
        
    with tab2:
        st.markdown("### 🚗 Vincular Carro ao Cliente")
        clientes = db.listar_clientes(oficina_id)
        if clientes:
            op_c = {cl['nome']: cl['id'] for cl in clientes}
            sel_c = st.selectbox("Selecione o Dono do Carro", list(op_c.keys()))
            with st.form("form_veiculo_carro"):
                ma = st.text_input("Montadora (Ex: Volkswagen, Chevrolet, Fiat)")
                mo = st.text_input("Modelo do Carro")
                pl = st.text_input("Placa do Carro")
                ano = st.number_input("Ano Fabricação/Modelo", min_value=1980, value=2026)
                if st.form_submit_button("Salvar Veículo"):
                    db.cadastrar_moto(op_c[sel_c], ma, mo, pl.upper(), ano)
                    st.success(f"✅ Veículo {mo} cadastrado!")
                    st.rerun()
        lista_m = db.listar_motos()
        if lista_m: st.dataframe(pd.DataFrame(lista_m), width="stretch")

elif escolha == "Estoque de Peças":
    st.markdown("### 🗂️ Estoque de Peças Automotivas (Pastilhas, Óleos, Amortecedores)")
    with st.form("form_estoque"):
        n_p = st.text_input("Nome da Peça")
        qtd = st.number_input("Quantidade em Estoque", min_value=0, value=5)
        c_u = st.number_input("Preço de Custo Distribuidor (R$)", min_value=0.0)
        v_u = st.number_input("Preço de Venda Cliente (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar no Almoxarifado") and n_p:
            db.cadastrar_peca_estoque(oficina_id, n_p, qtd, c_u, v_u)
            st.success(f"📦 {n_p} adicionada!")
            st.rerun()
            
    st.markdown("#### 📋 Almoxarifado de Peças Ativo")
    pecas = db.listar_pecas_estoque(oficina_id)
    if pecas: st.dataframe(pd.DataFrame(pecas)[['nome_peca', 'quantidade_atual', 'preco_custo', 'preco_venda']], width="stretch", hide_index=True)

elif escolha == "Serviços & Reparos":
    with st.form("s"):
        no = st.text_input("Descrição do Serviço Automotivo")
        pr = st.number_input("Preço Mão de Obra (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar Mão de Obra") and no:
            db.cadastrar_servico(no, pr, oficina_id)
            st.success("Serviço automotivo salvo!")
            st.rerun()
    lista_s = db.listar_servicos(oficina_id)
    if lista_s: st.dataframe(pd.DataFrame(lista_s)[['nome', 'preco_base']], width="stretch", hide_index=True)

elif escolha == "Ordens de Serviço (OS)":
    t1, t2 = st.tabs(["Check-in (Nova OS)", "Check-out & Orçamentos"])
    with t1:
        motos = db.listar_motos_detalhado()
        if motos:
            op_m = {f"{m['modelo']} - Placa: {m['placa']}": m['id'] for m in motos}
            sel_m = st.selectbox("Selecione o Veículo", list(op_m.keys()))
            prob = st.text_area("Relato de Defeito")
            if st.button("Abrir Ordem de Serviço Automotiva") and prob:
                db.criar_ordem_servico(op_m[sel_m], prob)
                st.success("⚙️ Ordem de Serviço aberta!")
                st.rerun()
                
    with t2:
        ordens = db.listar_ordens_servico()
        if ordens:
            op_os = {f"OS: {o['id'][:8]}...": o for o in ordens if o['status'] in ['Pendente', 'Em Andamento']}
            if op_os:
                sel_os = st.selectbox("Selecione a OS Ativa", list(op_os.keys()))
                os_obj = op_os[sel_os]
                dados_reais_os = db.obter_detalhes_completos_os(os_obj['id'])
                
                if dados_reais_os:
                    st.markdown("#### 🛠️ Lançar Serviços / Mão de Obra")
                    s_disp = db.listar_servicos(oficina_id)
                    if s_disp:
                        op_s = {f"{s['nome']} (R$ {s['preco_base']:.2f})": s for s in s_disp}
                        s_s = st.selectbox("Manutenção", list(op_s.keys()))
                        if st.button("Lançar Mão de Obra"):
                            db.vincular_servico_na_os(dados_reais_os['os_id'], op_s[s_s]['id'], op_s[s_s]['preco_base'])
                            st.rerun()
                    
                    st.markdown("#### 📦 Lançar Componentes e Peças Utilizadas")
                    p_disp = db.listar_pecas_estoque(oficina_id)
                    if p_disp:
                        op_p = {f"{p['nome_peca']} (Qtd: {p['quantidade_atual']} | R$ {p['preco_venda']:.2f})": p for p in p_disp if p['quantidade_atual'] > 0}
                        if op_p:
                            s_p = st.selectbox("Componente Aplicado", list(op_p.keys()))
                            qtd_p = st.number_input("Quantidade Instalada", min_value=1, max_value=op_p[s_p]['quantidade_atual'], value=1)
                            if st.button("Dar Baixa e Vincular Peça"):
                                db.vincular_peca_na_os(dados_reais_os['os_id'], op_p[s_p]['id'], qtd_p, op_p[s_p]['preco_venda'])
                                st.rerun()

                    st.markdown("### 📋 Resumo Consolidado")
                    if dados_reais_os['servicos']: st.dataframe(pd.DataFrame(dados_reais_os['servicos']), width="stretch")
                    if dados_reais_os['pecas']: st.dataframe(pd.DataFrame(dados_reais_os['pecas']), width="stretch")
                    st.markdown(f"## **Total do Orçamento: R$ {dados_reais_os['total']:.2f}**")
                    
                    st_list = ["Pendente", "Em Andamento", "Concluído", "Entregue"]
                    novo_st = st.selectbox("Status", st_list, index=st_list.index(dados_reais_os['status']))
                    if st.button("Confirmar Alteração"):
                        db.atualizar_status_os(dados_reais_os['os_id'], novo_st)
                        st.rerun()
                    
                    st.write("---")
                    col_pdf, col_wpp = st.columns(2)
                    with col_pdf:
                        if st.button("⬇️ Emitir Recibo Oficial PDF", width="stretch"):
                            path = utils.gerar_pdf_recibo(dados_reais_os["os_id"], "Cliente", "Carro", "PLACA", dados_reais_os["pecas"], dados_reais_os["servicos"], dados_reais_os["total"])
