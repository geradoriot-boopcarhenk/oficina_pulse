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
menu = ["Painel Geral", "Clientes & Carros", "Estoque de Peças", "📋 Ordens de Serviço (OS)", "⚙️ Perfil da Oficina"]
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
    st.markdown("### 📝 Cadastro de Cliente Proprietário")
    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome do Proprietário")
        cpf_visual = st.text_input("CPF (Somente números)")
        tel_visual = st.text_input("WhatsApp de Contato (Com DDD)")
        if st.form_submit_button("Salvar Registro Proprietário") and nome and cpf_visual and tel_visual:
            cpf_formatado = formatar_cpf(cpf_visual)
            tel_formatado = formatar_telefone(tel_visual)
            db.cadastrar_cliente(nome, tel_formatado, cpf_formatado, oficina_id)
            st.success("🎉 Cliente cadastrado com formatação profissional!")
            st.rerun()
    
    st.markdown("### 📋 Seus Clientes Cadastrados")
    lista_c = db.listar_clientes(oficina_id)
    if lista_c:
        df_clientes = pd.DataFrame(lista_c)[['nome', 'telefone', 'cpf']]
        df_clientes.columns = ['Nome do Proprietário', 'WhatsApp', 'CPF']
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
        df_p = pd.DataFrame(pecas)
        # Força mapeamento seguro idependente se veio com ou sem cedilha do banco
        if 'nome_peça' in df_p.columns:
            df_p = df_p.rename(columns={'nome_peça': 'nome_peca'})
        
        if 'nome_peca' in df_p.columns:
            df_final_p = df_p[['nome_peca', 'quantidade_atual', 'preco_custo', 'preco_venda']]
            df_final_p.columns = ['Nome da Peça', 'Qtd em Estoque', 'Preço de Custo', 'Preço de Venda']
            st.dataframe(df_final_p, width="stretch", hide_index=True)

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
            cliente_selecionado = st.selectbox("Selecione o Proprietário", list(dict_clientes.keys()))
            descricao_problema = st.text_area("Descrição dos Serviços / Defeito")
            
            if pecas_estoque:
                df_p_os = pd.DataFrame(pecas_estoque)
                if 'nome_peça' in df_p_os.columns:
                    df_p_os = df_p_os.rename(columns={'nome_peça': 'nome_peca'})
                
                dict_pecas = {p['nome_peca']: p for p in df_p_os.to_dict(orient='records')}
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
                        total_pecas_calculado = float(p_dados['preco_venda']) * qtd_peca
                        detalhe_peca_texto = f" + Peça: {peca_selecionada} (x{qtd_peca})"
                    
                    valor_total_os = valor_mao_de_obra + total_pecas_calculado
                    descricao_final = f"{descricao_problema}{detalhe_peca_texto}"
                    
                    db.criar_ordem_servico(dict_clientes[cliente_selecionado], descricao_final, valor_total_os)
                    st.success(f"✅ OS Registrada! Valor Total do Orçamento: R$ {valor_total_os:,.2f}")
                    st.rerun()
                else:
                    st.error("⚠️ Insira a descrição do problema!")
        
        st.write("---")
        st.markdown("#### 📋 Histórico de Ordens de Serviço Ativas")
        lista_os = db.listar_ordens_servico()
        if lista_os:
            for os_item in lista_os:
                c1, c2, c3 = st.columns()
                nome_c = os_item.get('clientes', {}).get('nome', 'Cliente') if os_item.get('clientes') else "Proprietário"
                c1.write(f"👤 **{nome_c}**")
                c2.write(f"📄 {os_item['descricao_problema']}")
                
                if os_item['status'] == 'Pendente':
                    if c3.button("🏁 Concluir Serviço", key=f"btn_{os_item['id']}"):
                        db.atualizar_status_os(os_item['id'], 'Concluído')
                        st.success("🎉 OS Concluída!")
                        st.rerun()
                else:
                    c3.markdown("🟢 **Concluído**")

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
