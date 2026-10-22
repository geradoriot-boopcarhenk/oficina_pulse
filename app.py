# app.py
import streamlit as st
import database as db
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

# --- RENDERIZADOR DA LOGOMARCA RENDERIZADA ---
logo_data = db.obter_logomarca_oficina(oficina_id)
if logo_data:
    st.sidebar.image(f"data:image/png;base64,{logo_data}", use_container_width=True)
else:
    st.sidebar.markdown(f"### 🏢 {nome_oficina_ativa}")

if st.sidebar.button("🚪 Sair / Trocar de Conta"):
    st.session_state["oficina_autenticada"] = None
    st.rerun()

st.title(f"🏍️ Gestão Integrada - {nome_oficina_ativa}")
menu = ["Painel Geral", "Clientes & Motos", "Estoque de Peças", "Serviços", "Ordens de Serviço (OS)", "⚙️ Perfil da Oficina"]
escolha = st.sidebar.selectbox("Mapeamento do Sistema", menu)

if escolha == "Painel Geral":
    col1, col2 = st.columns(2)
    col1.metric("OS Ativas", db.contar_os_por_status("Pendente") + db.contar_os_por_status("Em Andamento"))
    col2.metric("Faturamento Acumulado", f"R$ {db.obter_totais_financeiros():,.2f}")
    df_grafico = db.obter_dados_faturamento_grafico()
    if not df_grafico.empty: 
        st.line_chart(df_grafico.set_index("Mês"), y="Faturamento", color="#F97316")

elif escolha == "Clientes & Motos":
    tab1, tab2 = st.tabs(["Clientes", "Veículos"])
    with tab1:
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
    with tab2:
        st.markdown("### 🏍️ Cadastro de Moto")
        clientes = db.listar_clientes(oficina_id)
        if clientes:
            op_c = {cl['nome']: cl['id'] for cl in clientes}
            sel_c = st.selectbox("Selecione o Cliente", list(op_c.keys()))
            with st.form("form_moto"):
                ma = st.text_input("Marca")
                mo = st.text_input("Modelo")
                pl = st.text_input("Placa")
                ano = st.number_input("Ano", min_value=1980, value=2026)
                if st.form_submit_button("Vincular Moto"):
                    db.cadastrar_moto(op_c[sel_c], ma, mo, pl.upper(), ano)
                    st.success("✅ Moto vinculada!")
                    st.rerun()
        lista_m = db.listar_motos()
        if lista_m: st.dataframe(pd.DataFrame(lista_m), width="stretch")

elif escolha == "Estoque de Peças":
    st.markdown("### 🗂️ Controle de Estoque")
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

elif escolha == "Serviços":
    with st.form("s"):
        no = st.text_input("Descrição da Mão de Obra")
        pr = st.number_input("Preço Base (R$)", min_value=0.0)
        if st.form_submit_button("Salvar Serviço") and no:
            db.cadastrar_servico(no, pr, oficina_id)
            st.success("Serviço salvo!")
            st.rerun()
    lista_s = db.listar_servicos(oficina_id)
    if lista_s: st.dataframe(pd.DataFrame(lista_s)[['nome', 'preco_base']], width="stretch", hide_index=True)

elif escolha == "Ordens de Serviço (OS)":
    t1, t2 = st.tabs(["Abrir Chamado", "Gerenciamento de OS"])
    with t1:
        motos = db.listar_motos_detalhado()
        if motos:
            op_m = {f"{m['modelo']} ({m['placa']})": m['id'] for m in motos}
            sel_m = st.selectbox("Selecione o Veículo", list(op_m.keys()))
            prob = st.text_area("Problema Relatado")
            if st.button("Abrir OS") and prob:
                db.criar_ordem_servico(op_m[sel_m], prob)
                st.success("OS Criada!")
                st.rerun()
    with t2:
        ordens = db.listar_ordens_servico()
        if ordens:
            op_os = {f"OS ID: {o['id'][:8]}...": o for o in ordens if o['status'] in ['Pendente', 'Em Andamento']}
            if op_os:
                sel_os = st.selectbox("Selecione a OS Ativa", list(op_os.keys()))
                os_obj = op_os[sel_os]
                dados_reais_os = db.obter_detalhes_completos_os(os_obj['id'])
                if dados_reais_os:
                    st.markdown("#### 🛠️ Lançar Serviços")
                    s_disp = db.listar_servicos(oficina_id)
                    if s_disp:
                        op_s = {f"{s['nome']} (R$ {s['preco_base']:.2f})": s for s in s_disp}
                        s_s = st.selectbox("Mão de Obra", list(op_s.keys()))
                        if st.button("Lançar Mão de Obra"):
                            db.vincular_servico_na_os(dados_reais_os['os_id'], op_s[s_s]['id'], op_s[s_s]['preco_base'])
                            st.rerun()
                    st.markdown("#### 📦 Lançar Peças do Estoque")
                    p_disp = db.listar_pecas_estoque(oficina_id)
                    if p_disp:
                        op_p = {f"{p['nome_peca']} (Qtd: {p['quantidade_atual']} | R$ {p['preco_venda']:.2f})": p for p in p_disp if p['quantidade_atual'] > 0}
                        if op_p:
                            s_p = st.selectbox("Selecione a Peça", list(op_p.keys()))
                            qtd_p = st.number_input("Quantidade", min_value=1, max_value=op_p[s_p]['quantidade_atual'], value=1)
                            if st.button("Adicionar Peça na OS"):
                                db.vincular_peca_na_os(dados_reais_os['os_id'], op_p[s_p]['id'], qtd_p, op_p[s_p]['preco_venda'])
                                st.rerun()
                    st.markdown("### 📋 Resumo Financeiro")
                    if dados_reais_os['servicos']: st.dataframe(pd.DataFrame(dados_reais_os['servicos']), width="stretch")
                    if dados_reais_os['pecas']: st.dataframe(pd.DataFrame(dados_reais_os['pecas']), width="stretch")
                    st.markdown(f"## **Total Geral: R$ {dados_reais_os['total']:.2f}**")
                    st_list = ["Pendente", "Em Andamento", "Concluído", "Entregue"]
                    novo_st = st.selectbox("Status", st_list, index=st_list.index(dados_reais_os['status']))
                    if st.button("Confirmar Atualização"):
                        db.atualizar_status_os(dados_reais_os['os_id'], novo_st)
                        st.rerun()
                    st.write("---")
                    col_pdf, col_wpp = st.columns(2)
                    with col_pdf:
                        if st.button("⬇️ Gerar Recibo PDF", width="stretch"):
                            path = utils.gerar_pdf_recibo(dados_reais_os['os_id'], "Cliente", "Veículo", "PLACA", dados_reais_os['pecas'], dados_reais_os['servicos'], dados_reais_os['total'])
                            with open(path, "rb") as f:
                                st.download_button("Baixar PDF", f, file_name="recibo.pdf", mime="application/pdf")
                    with col_wpp:
                        texto_wpp = f"Ola! O veiculo cadastrado na OS {dados_reais_os['os_id'][:8]} esta pronto!\n\n💰 *Valor Total: R$ {dados_reais_os['total']:.2f}*"
                        texto_encoded = urllib.parse.quote(texto_wpp)
                        link_wpp = f"https://whatsapp.com{texto_encoded}"
