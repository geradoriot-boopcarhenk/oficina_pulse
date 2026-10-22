# app_carro.py
import streamlit as st
import database as db
import pandas as pd
import utils

st.set_page_config(page_title="Oficina Mecânica Automotiva", page_icon="🚗", layout="wide")

# --- GERENCIADOR DE LOGIN COM SEGURANÇA ---
if "usuario_logado" not in st.session_state:
    st.session_state["usuario_logado"] = False

def autenticar(usuario, senha):
    USUARIO_CORRETO = "admin"
    SENHA_CORRETA = "pulse2026"
    
    if usuario == USUARIO_CORRETO and senha == SENHA_CORRETA:
        st.session_state["usuario_logado"] = True
        return True
    return False

# --- TELA DE ACESSO RESTRETA ---
if not st.session_state["usuario_logado"]:
    st.markdown("<h1 style='text-align: center; color: #EA580C;'>🚗 Oficina Pulse Automotiva - Área Restrita</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col_login, _ = st.columns([1, 2])
    with col_login:
        st.markdown("### 🔑 Controle de Acesso")
        usuario_input = st.text_input("Usuário de Acesso")
        senha_input = st.text_input("Senha Comercial", type="password")
        
        if st.button("Entrar no Painel", width="stretch"):
            if autenticar(usuario_input, senha_input):
                st.success("Acesso concedido com sucesso!")
                st.rerun()
            else:
                st.error("❌ Usuário ou senha incorretos!")
    st.stop()

if st.sidebar.button("🚪 Sair do Sistema"):
    st.session_state["usuario_logado"] = False
    st.rerun()

st.title("🚗 Sistema de Gestão - Oficina Mecânica Automotiva")

menu = ["Painel Geral", "Clientes & Carros", "Serviços & Manutenção", "Ordens de Serviço (OS)"]
escolha = st.sidebar.selectbox("Navegação", menu)

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
        with st.form("form_cliente_carro"):
            nome = st.text_input("Nome do Proprietário", value="Carlos Henrique")
            cpf_visual = st.text_input("CPF", value="617.923.303-91")
            tel_visual = st.text_input("WhatsApp de Contato", value="(85) 99282-4395")
            botao_salvar = st.form_submit_button("Salvar Registro de Cliente", width="stretch")
            
        if botao_salvar and nome and cpf_visual and tel_visual:
            db.cadastrar_cliente(nome, tel_visual, cpf_visual)
            st.success(f"🎉 Cliente {nome} cadastrado com sucesso!")
            st.rerun()

        st.markdown("### 📋 Clientes Cadastrados")
        lista_c = db.listar_clientes()
        if lista_c and len(lista_c) > 0:
            df_clientes = pd.DataFrame(lista_c)[['id', 'nome', 'telefone', 'cpf']]
            st.dataframe(df_clientes, width="stretch", hide_index=True)
        
    with tab2:
        st.markdown("### 🚗 Vincular Carro ao Cliente")
        clientes = db.listar_clientes()
        if clientes and len(clientes) > 0:
            op_c = {f"{cl['nome']}": cl['id'] for cl in clientes}
            sel_c = st.selectbox("Selecione o Dono do Carro", list(op_c.keys()))
            cliente_id_final = op_c[sel_c]
        else:
            st.warning("⚠️ Nenhum cliente cadastrado ainda.")
            cliente_id_final = None

        with st.form("form_veiculo_carro"):
            ma = st.text_input("Montadora (Ex: Volkswagen, Chevrolet, Fiat)", value="Chevrolet")
            mo = st.text_input("Modelo do Carro (Ex: Onix, Civic, Corolla)", value="Onix Hatch")
            pl = st.text_input("Placa do Carro", value="CAR8899")
            ano = st.number_input("Ano Fabricação/Modelo", min_value=1980, value=2026)
            
            if st.form_submit_button("Salvar Veículo", width="stretch") and cliente_id_final and ma and mo and pl:
                db.cadastrar_moto(cliente_id_final, ma, mo, pl.upper(), ano) # Reaproveita a tabela estrutural de veículos
                st.success(f"✅ Veículo {mo} cadastrado com sucesso!")
                st.rerun()
                    
        st.markdown("### 📋 Frota de Carros Registrada")
        lista_m = db.listar_motos()
        if lista_m: st.dataframe(pd.DataFrame(lista_m), width="stretch")

elif escolha == "Serviços & Manutenção":
    with st.form("s"):
        no = st.text_input("Descrição do Serviço Automotivo (Ex: Alinhamento, Troca de Pastilha)")
        pr = st.number_input("Preço de Mão de Obra (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar Tabela de Preço") and no:
            db.cadastrar_servico(no, pr)
            st.success("Serviço automotivo salvo!")
            st.rerun()
            
    st.markdown("### 📋 Serviços Disponíveis")
    lista_s = db.listar_servicos()
    if lista_s and len(lista_s) > 0:
        df_servicos = pd.DataFrame(lista_s)
        if 'created_at' in df_servicos.columns: df_servicos = df_servicos.drop(columns=['created_at'])
        st.dataframe(df_servicos, width="stretch", hide_index=True)

elif escolha == "Ordens de Serviço (OS)":
    t1, t2, t3 = st.tabs(["Abrir Nova OS", "Check-in de Serviços / Status", "Histórico de Diagnósticos"])
    with t1:
        motos = db.listar_motos_detalhado()
        if motos:
            op_m = {f"{m['modelo']} - Placa: {m['placa']}": m['id'] for m in motos}
            sel_m = st.selectbox("Selecione o Carro do Cliente", list(op_m.keys()))
            prob = st.text_area("Relato de Defeito / Diagnóstico Inicial")
            if st.button("Abrir Ordem de Serviço Automotiva") and prob:
                db.criar_ordem_servico(op_m[sel_m], prob)
                st.success("⚙️ Ordem de Serviço aberta com sucesso!")
                st.rerun()
                
    with t2:
        ordens = db.listar_ordens_servico()
        if ordens:
            op_os = {f"OS: {o['id'][:8]}... | Diagnóstico: {o['descricao_problema'][:40]}...": o for o in ordens if o['status'] in ['Pendente', 'Em Andamento']}
            if op_os:
                sel_os = st.selectbox("Selecione a OS Ativa", list(op_os.keys()))
                os_obj = op_os[sel_os]
                dados_reais_os = db.obter_detalhes_completos_os(os_obj['id'])
                
                if dados_reais_os:
                    st.markdown("#### 🛠️ Adicionar Mão de Obra / Peças")
                    s_disp = db.listar_servicos()
                    if s_disp:
                        op_s = {f"{s['nome']} (R$ {s['preco_base']:.2f})": s for s in s_disp}
                        s_s = st.selectbox("Selecione a Manutenção Realizada", list(op_s.keys()))
                        if st.button("Lançar Serviço no Orçamento", width="stretch"):
                            db.vincular_servico_na_os(dados_reais_os['os_id'], op_s[s_s]['id'], op_s[s_s]['preco_base'])
                            st.success("✅ Serviço adicionado!")
                            st.rerun()
                    
                    if dados_reais_os['servicos']:
                        st.dataframe(pd.DataFrame(dados_reais_os['servicos']), width="stretch")
                    
                    st.write("---")
                    st.markdown("#### 📈 Alterar Situação da Oficina")
                    st_list = ["Pendente", "Em Andamento", "Concluído", "Entregue"]
                    novo_st = st.selectbox("Status do Carro", st_list, index=st_list.index(dados_reais_os['status']))
                    if st.button("Atualizar Status do Veículo", width="stretch"):
                        db.atualizar_status_os(dados_reais_os['os_id'], novo_st)
                        st.success(f"Status atualizado!")
                        st.rerun()
                    
                    if st.button("⬇️ Emitir Recibo do Cliente (PDF)", width="stretch"):
                        path = utils.gerar_pdf_recibo(dados_reais_os['os_id'], "Carlos Henrique", "Chevrolet Onix", "CAR8899", [], dados_reais_os['servicos'], dados_reais_os['total'])
                        with open(path, "rb") as f:
                            st.download_button("Clique aqui para baixar o PDF", f, file_name=f"recibo_carro_{dados_reais_os['os_id'][:8]}.pdf", mime="application/pdf")
    with t3:
        st.dataframe(db.listar_ordens_servico(), width="stretch")
