# app.py - Versao Enterprise SaaS Motos com Painel Mestre e Cobrancas
import streamlit as st
import database as db
import pandas as pd
import base64
import re

st.set_page_config(page_title="Oficina Mecânica de Motos", page_icon="🏍️", layout="wide")

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
    st.markdown("<h1 style='text-align: center; color: #EA580C;'>🏍️ Oficina Pulse - Portal de Assinantes</h1>", unsafe_allow_html=True)
    st.write("---")
    
    st.markdown("### 🔑 Acessar Sistema Privado")
    usuario_input = st.text_input("Usuário Administrativo")
    senha_input = st.text_input("Senha Comercial", type="password")
    
    if st.button("Entrar no Painel", width="stretch"):
        # ROTA SECRETA DE ADMIN MESTRE INTEGRADA
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
    st.title("👑 Central do Administrador Mestre - Pulse SaaS Motos")
    st.write("Gerencie os acessos, inadimplências e status de pagamento das oficinas parceiras.")
    
    if st.sidebar.button("🚪 Sair do Modo Admin"):
        st.session_state["modo_admin"] = False
        st.rerun()
        
    st.write("---")
    st.markdown("### ➕ Cadastrar Nova Oficina Cliente")
    with st.form("form_nova_oficina_admin", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)
        novo_nome_ofi = col_f1.text_input("Nome da Oficina")
        novo_user_ofi = col_f2.text_input("Usuário de Acesso")
        nova_senha_ofi = col_f3.text_input("Senha Inicial", type="password")
        
        if st.form_submit_button("Cadastrar Oficina", width="stretch"):
            if novo_nome_ofi and novo_user_ofi and nova_senha_ofi:
                if db.cadastrar_nova_oficina(novo_nome_ofi.strip(), novo_user_ofi.strip().lower(), nova_senha_ofi.strip()):
                    st.success(f"✅ Oficina '{novo_nome_ofi}' cadastrada com senha criptografada!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao cadastrar oficina no Supabase. Verifique se o usuário já existe.")
            else:
                st.warning("⚠️ Preencha todos os campos para criar a oficina.")
    st.write("---")

    st.markdown("### 🏢 Clientes / Oficinas de Motos Ativas no Banco")
    
    oficinas_cadastradas = db.listar_todas_oficinas()
    if oficinas_cadastradas:
        with st.expander("🖼️ Atualizar Logomarca de uma Oficina"):
            dict_ofis = {f"{o['nome_oficina']} ({o['usuario']})": o['id'] for o in oficinas_cadastradas}
            ofi_sel = st.selectbox("Selecione a Oficina", list(dict_ofis.keys()))
            arq_logo_adm = st.file_uploader("Envie a logo (PNG/JPG)", type=["png", "jpg", "jpeg"], key="up_logo_adm")
            if arq_logo_adm and st.button("Salvar Logomarca da Oficina"):
                img_b64 = base64.b64encode(arq_logo_adm.read()).decode("utf-8")
                if db.salvar_logomarca_oficina(dict_ofis[ofi_sel], img_b64):
                    st.success("✅ Logomarca atualizada com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar logomarca no Supabase.")
        for ofi in oficinas_cadastradas:
            col_nome, col_user, col_status, col_acao = st.columns([2, 1.5, 1, 1.5])
            col_nome.write(f"🏢 **{ofi['nome_oficina']}**")
            col_user.write(f"👤 Usuário: `{ofi['usuario']}`")
            
            status_atual = ofi.get('status') or ofi.get('status_pagamento') or 'Ativo'
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

# ----------------- FLUXO DO CLIENTE (OFICINA DE MOTOS) -----------------
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
    **Chave PIX Copia e Cola:** `cobranca-pulse-saas-motos-master-key-payment-gateway`  
    """)
    if st.sidebar.button("🚪 Sair da Conta"):
        st.session_state["oficina_autenticada"] = None
        st.rerun()
    st.stop()

try:
    logo_data = db.obter_logomarca_oficina(oficina_id)
except:
    logo_data = None

if logo_data:
    st.sidebar.image(f"data:image/png;base64,{logo_data}", use_container_width=True)
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), url("data:image/png;base64,{logo_data}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.markdown(f"### 🏢 {nome_oficina_ativa}")


if st.sidebar.button("🚪 Sair / Trocar de Conta"):
    st.session_state["oficina_autenticada"] = None
    st.rerun()

st.title(f"🏍️ Gestão Integrada - {nome_oficina_ativa}")
menu = ["Painel Geral", "Clientes & Motos", "Estoque de Peças", "📋 Ordens de Serviço (OS)", "📜 Histórico de Clientes"]
escolha = st.sidebar.selectbox("Mapeamento do Sistema", menu)

if escolha == "Painel Geral":
    col1, col2 = st.columns(2)
    col1.metric("OS em Andamento", db.contar_os_por_status("Pendente"))
    faturamento_atual = db.obter_totais_financeiros()
    col2.metric("Faturamento Mensal", f"R$ {faturamento_atual:,.2f}")

elif escolha == "Clientes & Motos":
    st.markdown("### 📝 Cadastro de Cliente Proprietário e Moto")
    with st.form("form_cliente", clear_on_submit=True):
        nome = st.text_input("Nome do Proprietário")
        cpf_visual = st.text_input("CPF")
        tel_visual = st.text_input("WhatsApp")
        marca_moto = st.text_input("Marca da Moto")
        modelo_moto = st.text_input("Modelo da Moto")
        placa_moto = st.text_input("Placa da Moto")
        if st.form_submit_button("Salvar Registro Completo"):
            if nome and cpf_visual and tel_visual and marca_moto and modelo_moto and placa_moto:
                cpf_formatado = formatar_cpf(cpf_visual)
                tel_formatado = formatar_telefone(tel_visual)
                placa_formatada = formatar_placa(placa_moto)
                nome_vinculado = f"{nome.strip().title()} ({marca_moto.strip().title()} {modelo_moto.strip().title()} | {placa_formatada})"
                db.cadastrar_cliente(nome_vinculado, tel_formatado, cpf_formatado, oficina_id)
                st.success("🎉 Proprietário e Moto cadastrados!")
                st.rerun()
                
    st.write("---")
    st.markdown("### 📋 Clientes & Motos Cadastrados")
    clientes_salvos = db.listar_clientes(oficina_id)
    if clientes_salvos:
        df_clientes = pd.DataFrame(clientes_salvos)[["nome", "cpf", "telefone"]]
        df_clientes.columns = ["Cliente / Moto / Placa", "CPF", "WhatsApp"]
        st.dataframe(df_clientes, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum cliente cadastrado ainda.")

elif escolha == "Estoque de Peças":
    st.markdown("### 🗂️ Estoque de Peças")
    with st.form("form_estoque", clear_on_submit=True):
        n_p = st.text_input("Nome da Peça")
        qtd = st.number_input("Quantidade", min_value=0, value=5)
        c_u = st.number_input("Preço de Custo (R$)", min_value=0.0)
        v_u = st.number_input("Preço de Venda (R$)", min_value=0.0)
        if st.form_submit_button("Cadastrar") and n_p:
            if db.cadastrar_peca_estoque(oficina_id, n_p, qtd, c_u, v_u):
                st.success(f"📦 {n_p} adicionada!")
                st.rerun()
                
    st.write("---")
    st.markdown("### 📦 Peças em Estoque")
    pecas_salvas = db.listar_pecas_estoque(oficina_id)
    if pecas_salvas:
        st.dataframe(pd.DataFrame(pecas_salvas), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma peça cadastrada no estoque ainda.")

elif escolha == "📋 Ordens de Serviço (OS)":
    st.markdown("### 📋 Ordens de Serviço")
    lista_c = db.listar_clientes(oficina_id)
    if not lista_c:
        st.warning("⚠️ Cadastre um cliente primeiro.")
    else:
        with st.form("form_os", clear_on_submit=True):
            dict_clientes = {c['nome']: c['id'] for c in lista_c}
            cliente_selecionado = st.selectbox("Selecione o Cliente / Moto", list(dict_clientes.keys()))
            descricao_problema = st.text_area("Descrição")
            
            pecas_disp = db.listar_pecas_estoque(oficina_id)
            opcoes_pecas = {"Nenhuma peça utilizada": None}
            for p_item in pecas_disp:
                nome_p = p_item.get("nome_peca") or p_item.get("nome_peça") or "Peça"
                qtd_p = p_item.get("quantidade") if "quantidade" in p_item else p_item.get("quantidade_atual", 0)
                preco_v = float(p_item.get("preco_venda") or 0.0)
                if int(qtd_p) > 0:
                    opcoes_pecas[f"{nome_p} (Estoque: {qtd_p} | R$ {preco_v:.2f})"] = (nome_p, preco_v, int(qtd_p))
            
            col_p1, col_p2 = st.columns((3, 1))
            peca_esc = col_p1.selectbox("Adicionar Peça do Estoque (Opcional)", list(opcoes_pecas.keys()))
            qtd_esc = col_p2.number_input("Qtd", min_value=1, value=1, step=1)
            
            valor_mao_de_obra = st.number_input("Valor Mão de Obra (R$)", min_value=0.0, value=100.0)
            if st.form_submit_button("Gerar Nova OS"):
                if descricao_problema:
                    desc_final = descricao_problema.strip()
                    valor_total = float(valor_mao_de_obra)
                    if opcoes_pecas[peca_esc] is not None:
                        nome_p, preco_v, qtd_max = opcoes_pecas[peca_esc]
                        qtd_usar = min(int(qtd_esc), qtd_max)
                        desc_final += f" + Peça: {nome_p} (x{qtd_usar})"
                        valor_total += (preco_v * qtd_usar)
                    if db.criar_ordem_servico(dict_clientes[cliente_selecionado], desc_final, valor_total):
                        st.success(f"✅ OS Registrada! Valor Total: R$ {valor_total:.2f}")
                        st.rerun()
                        
    st.write("---")
    st.markdown("### 🔧 Ordens de Serviço Registradas")
    lista_os = db.listar_ordens_servico()
    if lista_os:
        for os_item in lista_os:
            c1, c2, c3 = st.columns([3, 1, 1])
            cliente_info = os_item.get("clientes") or {}
            nome_cli = cliente_info.get("nome", "Cliente") if isinstance(cliente_info, dict) else "Cliente"
            c1.write(f"**{nome_cli}** — {os_item.get('descricao_problema', '')}")
            c2.write(f"Status: **{os_item.get('status', 'Pendente')}**")
            if os_item.get("status") != "Concluído":
                if c3.button("✅ Concluir", key=f"conc_{os_item['id']}"):
                    db.atualizar_status_os(os_item["id"], "Concluído", oficina_id)
                    st.rerun()
    else:
        st.info("Nenhuma Ordem de Serviço registrada ainda.")

elif escolha == "📜 Histórico de Clientes":
    st.markdown("### 📜 Histórico de Serviços por Cliente / Moto")
    clientes_hist = db.listar_clientes(oficina_id)
    todas_os = db.listar_ordens_servico()

    if not clientes_hist:
        st.info("Nenhum cliente cadastrado ainda.")
    else:
        mapa_cli = {c["nome"]: c for c in clientes_hist}
        selecionado = st.selectbox("Selecione o Cliente / Moto para consultar", list(mapa_cli.keys()))
        dados_cli = mapa_cli[selecionado]

        col_d1, col_d2 = st.columns(2)
        col_d1.write(f"**📱 WhatsApp:** {dados_cli.get('telefone', 'Não informado')}")
        col_d2.write(f"**🪪 CPF:** {dados_cli.get('cpf', 'Não informado')}")
        st.write("---")

        os_do_cliente = [
            o for o in todas_os
            if (o.get("moto_id") == dados_cli["id"] or o.get("cliente_id") == dados_cli["id"])
        ]

        if os_do_cliente:
            st.markdown(f"**Total de atendimentos registrados:** {len(os_do_cliente)}")
            df_hist = pd.DataFrame([
                {
                    "Serviço / Descrição": o.get("descricao_problema", ""),
                    "Status": o.get("status", "Pendente")
                }
                for o in os_do_cliente
            ])
            st.dataframe(df_hist, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhuma Ordem de Serviço registrada para este cliente até o momento.")
