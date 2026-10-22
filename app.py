# app.py
import streamlit as st
import database as db
import pandas as pd
import utils

st.set_page_config(page_title="Oficina de Motos", page_icon="🏍️", layout="wide")

# --- GERENCIADOR DE LOGIN COM SEGURANÇA ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = False

def autenticar(usuario, senha):
    # LOGIN COMERCIAL PADRÃO (Você pode mudar estes dados quando quiser!)
    USUARIO_CORRETO = "admin"
    SENHA_CORRETA = "pulse2026"
    
    if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
        st.session_state["usuario_logado"] = True
        return True
    return False

# --- SE NÃO ESTIVER LOGADO, EXIBE A TELA DE ACESSO BLINDADA ---
if not st.session_state["usuario_logado"]:
    st.markdown("<h1 style='text-align: center; color: #F97316;'>🏍️ Oficina Pulse - Área Restrita</h1>", unsafe_margin=True)
    st.write("---")
    
    col_login, _ = st.columns([1, 2])
    with col_login:
        st.markdown("### 🔑 Faça login para acessar o sistema")
        usuario_input = st.text_input("Usuário de Acesso")
        senha_input = st.text_input("Senha Comercial", type="password")
        
        if st.button("Entrar no Painel", width="stretch"):
            if autenticar(usuario_input, senha_input):
                st.success("Acesso concedido com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos! Verifique os dados.")
    st.stop() # Bloqueia o carregamento do restante da página se não logar

# --- BOTÃO DE LOGOUT NA BARRA LATERAL SE ESTIVER LOGADO ---
if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state["usuario_logado"] = False
    st.rerun()

# --- CONTINUAÇÃO NORMAL DO APLICATIVO APÓS LOGIN AUTORIZADO ---
st.title("🏍️ Sistema de Gestão - Oficina de Motos")

menu = ["Painel Geral", "Clientes & Motos", "Serviços", "Ordens de Serviço (OS)"]
escolha = st.sidebar.selectbox("Navegação", menu)

if escolha == "Painel Geral":
    col1, col2 = st.columns(2)
    col1.metric("OS Ativas", db.contar_os_por_status("Pendente") + db.contar_os_por_status("Em Andamento"))
    col2.metric("Faturamento Acumulado", f"R$ {db.obter_totais_financeiros():,.2f}")
    
    df_grafico = db.obter_dados_faturamento_grafico()
    if not df_grafico.empty: 
        st.line_chart(df_grafico.set_index("Mês"), y="Faturamento", color="#F97316")

elif escolha == "Clientes & Motos":
    tab1, tab2 = st.tabs(["Clientes", "Motos"])
    with tab1:
        st.markdown("### 📝 Cadastro de Novo Cliente")
        with st.form("form_cliente_definitivo"):
            nome = st.text_input("Nome", value="Carlos Henrique")
            cpf_visual = st.text_input("CPF", value="617.923.303-91")
            tel_visual = st.text_input("Telefone com DDD", value="(85) 99282-4395")
            botao_salvar = st.form_submit_button("Salvar Registro de Cliente", width="stretch")
            
        if botao_salvar:
            if nome and cpf_visual and tel_visual:
                db.cadastrar_cliente(nome, tel_visual, cpf_visual)
                st.success(f"🎉 Cliente {nome} cadastrado com sucesso!")
                st.rerun()

        st.markdown("### 📋 Lista de Clientes Registrados")
        lista_c = db.listar_clientes()
        if lista_c and len(lista_c) > 0:
            df_clientes = pd.DataFrame(lista_c)
            if 'created_at' in df_clientes.columns: df_clientes = df_clientes.drop(columns=['created_at'])
            df_clientes = df_clientes[['id', 'nome', 'telefone', 'cpf']]
            st.dataframe(df_clientes, width="stretch", hide_index=True)
        else:
            st.info("Nenhum cliente listado na tabela ainda.")
        
    with tab2:
        st.markdown("### 🏍️ Cadastro de Nova Moto")
        clientes = db.listar_clientes()
        if clientes and len(clientes) > 0:
            op_c = {f"{cl['nome']}": cl['id'] for cl in clientes}
            sel_c = st.selectbox("Selecione o Dono do Veículo", list(op_c.keys()))
            cliente_id_final = op_c[sel_c]
        else:
            st.warning("⚠️ Atenção: Nenhum cliente cadastrado no sistema ainda.")
            cliente_id_final = None

        with st.form("form_moto_definitivo"):
            ma = st.text_input("Marca", value="BMW")
            mo = st.text_input("Modelo", value="S1000RR")
            pl = st.text_input("Placa", value="MOTO123")
            ano = st.number_input("Ano", min_value=1980, value=2026)
            
            if st.form_submit_button("Salvar Registro de Moto", width="stretch"):
                if cliente_id_final and ma and mo and pl:
                    db.cadastrar_moto(cliente_id_final, ma, mo, pl.upper(), ano)
                    st.success(f"✅ Moto {mo} vinculada com sucesso!")
                    st.rerun()
                    
        st.markdown("### 📋 Lista de Motos Registradas")
        lista_m = db.listar_motos()
        if lista_m: st.dataframe(pd.DataFrame(lista_m), width="stretch")
        else: st.info("Nenhuma moto cadastrada ainda.")

elif escolha == "Serviços":
    with st.form("s"):
        no = st.text_input("Nome do Serviço")
        pr = st.number_input("Preço Mão de Obra", min_value=0.0)
        if st.form_submit_button("Salvar Serviço") and no:
            db.cadastrar_servico(no, pr)
            st.success("Serviço salvo com sucesso!")
            st.rerun()
            
    st.markdown("### 📋 Serviços Cadastrados")
    lista_s = db.listar_servicos()
    if lista_s and len(lista_s) > 0:
        df_servicos = pd.DataFrame(lista_s)
        if 'created_at' in df_servicos.columns: df_servicos = df_servicos.drop(columns=['created_at'])
        st.dataframe(df_servicos, width="stretch", hide_index=True)
    else:
        st.info("Nenhum serviço cadastrado ainda.")

elif escolha == "Ordens de Serviço (OS)":
    t1, t2, t3 = st.tabs(["Nova OS", "Lançar Itens / Alterar Status", "Histórico"])
    with t1:
        motos = db.listar_motos_detalhado()
        if motos:
            op_m = {f"{m['modelo']} ({m['placa']})": m['id'] for m in motos}
            sel_m = st.selectbox("Moto", list(op_m.keys()))
            prob = st.text_area("Problema")
            if st.button("Abrir OS") and prob:
                db.criar_ordem_servico(op_m[sel_m], prob)
                st.success("OS Criada com sucesso!")
                st.rerun()
                
    with t2:
        ordens = db.listar_ordens_servico()
        if ordens:
            op_os = {f"OS ID: {o['id'][:8]}... | Problema: {o['descricao_problema'][:40]}...": o for o in ordens if o['status'] in ['Pendente', 'Em Andamento']}
            if op_os:
                sel_os = st.selectbox("Selecione a OS", list(op_os.keys()))
                os_obj = op_os[sel_os]
                dados_reais_os = db.obter_detalhes_completos_os(os_obj['id'])
                
                if dados_reais_os:
                    st.markdown("#### 🛠️ Lançamento de Mão de Obra")
                    s_disp = db.listar_servicos()
                    if s_disp:
                        op_s = {f"{s['nome']} (R$ {s['preco_base']:.2f})": s for s in s_disp}
                        s_s = st.selectbox("Selecione o Serviço Prestado", list(op_s.keys()))
                        if st.button("Adicionar Serviço na OS", width="stretch"):
                            db.vincular_servico_na_os(dados_reais_os['os_id'], op_s[s_s]['id'], op_s[s_s]['preco_base'])
                            st.success("✅ Mão de obra vinculada com sucesso!")
                            st.rerun()
                    
                    if dados_reais_os['servicos']:
                        st.markdown("##### 📋 Serviços Lançados nesta OS")
                        st.dataframe(pd.DataFrame(dados_reais_os['servicos']), width="stretch")
                    
                    st.write("---")
                    st.markdown("#### 📈 Atualizar Situação")
                    st_list = ["Pendente", "Em Andamento", "Concluído", "Entregue"]
                    novo_st = st.selectbox("Status Atual da OS", st_list, index=st_list.index(dados_reais_os['status']))
                    if st.button("Confirmar Atualização de Status", width="stretch"):
                        db.atualizar_status_os(dados_reais_os['os_id'], novo_st)
                        st.success(f"Status updated to {novo_st}!")
                        st.rerun()
                    
                    if st.button("⬇️ Gerar Recibo da OS (PDF)", width="stretch"):
                        path = utils.gerar_pdf_recibo(dados_reais_os['os_id'], "Carlos Henrique", "BMW S1000RR", "MOTO123", [], dados_reais_os['servicos'], dados_reais_os['total'])
                        with open(path, "rb") as f:
                            st.download_button("Clique aqui para baixar o PDF", f, file_name=f"recibo_{dados_reais_os['os_id'][:8]}.pdf", mime="application/pdf")
    with t3:
        st.dataframe(db.listar_ordens_servico(), width="stretch")
