# app_carro.py - Sincronizacao Definitiva de OS

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
    
    st.markdown("### 🔑 Acessar Sistema Privado")
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
    st.stop()

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

# Adicionados os desempacotadores planos nas variáveis de sessão globais
oficina_dados = st.session_state["oficina_autenticada"]
oficina_id = oficina_dados[0]["id"] if isinstance(oficina_dados, list) else oficina_dados["id"]
nome_oficina_ativa = oficina_dados[0]["nome_oficina"] if isinstance(oficina_dados, list) else oficina_dados["nome_oficina"]

# Trava de segurança mestre adicionada para evitar travamentos de resposta da logo
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
                        total_pecas_calculado = float(p_dados.get('preco_venda', 0.0)) * qtd_peca
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
        if "visualizar_recibo" not in st.session_state: st.session_state["visualizar_recibo"] = None
        lista_os = db.listar_ordens_servico()
        if lista_os:
            for os_item in lista_os:
                c1, c2, c3, c4 = st.columns([1.5, 2, 1, 1])
                cliente_obj = os_item.get('clientes', {}) or {}
                nome_c = cliente_obj.get('nome', 'Cliente')
                tel_c = cliente_obj.get('telefone', 'Não Informado')
                cpf_c = cliente_obj.get('cpf', 'Não Informado')
                
                c1.write(f"👤 **{nome_c}**")
                c2.write(f"📄 {os_item['descricao_problema']}")
                if os_item['status'] == 'Pendente':
                    if c3.button("🏁 Concluir Serviço", key=f"btn_{os_item['id']}"):
                        db.atualizar_status_os(os_item['id'], 'Concluído', oficina_id=oficina_id)
                        st.success("🎉 OS Concluída!")
                        st.rerun()
                else:
                    c3.markdown("🟢 **Concluído**")
                    if c4.button("📄 Recibo", key=f"rec_{os_item['id']}"):
                        st.session_state["visualizar_recibo"] = {"nome": nome_c, "desc": os_item['descricao_problema'], "tel": tel_c, "cpf": cpf_c}
            if st.session_state["visualizar_recibo"]:
                st.write("---")
                r = st.session_state["visualizar_recibo"]
                gerar_recibo_impressao(r["nome"], r["desc"], nome_oficina_ativa, r["tel"], r["cpf"])
                if st.button("❌ Fechar Visualização de Recibo"):
                    st.session_state["visualizar_recibo"] = None
                    st.rerun()

elif escolha == "📜 Histórico de Clientes":
    st.markdown("### 📜 Histórico de Serviços Realizados por Cliente")
    st.write("---")
    lista_c = db.listar_clientes(oficina_id)
    lista_os = db.listar_ordens_servico()
    if not lista_c:
        st.info("💡 Nenhum cliente cadastrado no sistema ainda.")
    else:
        dict_clientes = {c['nome']: c['id'] for c in lista_c}
        cliente_selecionado = st.selectbox("Selecione o Cliente / Veículo para puxar a ficha:", list(dict_clientes.keys()))
        id_cliente_busca = dict_clientes[cliente_selecionado]
        os_filtradas = [os for os in lista_os if os.get('cliente_id') == id_cliente_busca and os.get('status') == 'Concluído']
        if os_filtradas:
            st.markdown(f"#### 🛠️ Ficha de Serviços de: **{cliente_selecionado}**")
            dados_tabela = []
            for item in os_filtradas:
                texto_problema = item['descricao_problema']
                match_valor = re.search(r'Mão de Obra: R\$ ([\d.]+)', texto_problema, re.IGNORECASE)
                valor_exibicao = f"R$ {float(match_valor.group(1)):,.2f}" if match_valor else "Não informado"
                dados_tabela.append({"Ordem de Serviço / Defeito Relatado": texto_problema, "Valor Total": valor_exibicao})
            st.dataframe(pd.DataFrame(dados_tabela), width="stretch", hide_index=True)
        else:
            st.warning(f"⚠️ Nenhuma Ordem de Serviço concluída foi encontrada para {cliente_selecionado} ainda.")

elif "Perfil" in escolha:
    st.markdown("### ⚙️ Configurações da Oficina")
    uploaded_file = st.file_uploader("🖼️ Envie a Logomarca da sua Oficina", type=["png", "jpg", "jpeg"])
    if uploaded_file is not None:
        bytes_data = uploaded_file.read()
        base64_image = base64.b64encode(bytes_data).decode('utf-8')
        if st.button("💾 Salvar Logomarca", width="stretch"):
            if db.salvar_logomarca_oficina(oficina_id, base64_image):
                st.success("🎉 Logomarca updated!")
                st.rerun()
