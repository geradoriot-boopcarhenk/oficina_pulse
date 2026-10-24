# database.py
import requests
import pandas as pd

SUPABASE_URL = "https://iypimnjrwwwxppaygywt.supabase.co"
SUPABASE_KEY = "sb_publishable_nrVu4x2XZmss8FliB6yZ3738SgscwXjT6Hj9pA9qDhc8b5VbY7H8m1N2"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def autenticar_oficina(usuario, senha):
    url = f"{SUPABASE_URL}/rest/v1/oficinas?usuario=eq.{usuario}&senha=eq.{senha}"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200 and len(res.json()) > 0:
        return res.json()[0]
    return None

def cadastrar_nova_oficina(nome, usuario, senha):
    url = f"{SUPABASE_URL}/rest/v1/oficinas"
    dados = {"nome_oficina": nome, "usuario": usuario, "senha": senha}
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def salvar_logomarca_oficina(oficina_id, imagem_base64):
    url = f"{SUPABASE_URL}/rest/v1/oficinas?id=eq.{oficina_id}"
    dados = {"logomarca_base64": imagem_base64}
    res = requests.patch(url, headers=HEADERS, json=dados)
    return res.status_code == 200

def obter_logomarca_oficina(oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/oficinas?id=eq.{oficina_id}&select=logomarca_base64"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200 and len(res.json()) > 0:
        return res.json().get('logomarca_base64')
    return None

def listar_pecas_estoque(oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/estoque_pecas?oficina_id=eq.{oficina_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def cadastrar_peca_estoque(oficina_id, nome, qtd, custo, venda):
    url = f"{SUPABASE_URL}/rest/v1/estoque_pecas"
    dados = {
        "oficina_id": oficina_id,
        "nome_peça": nome,
        "quantidade_atual": int(qtd),
        "preco_custo": float(custo),
        "preco_venda": float(venda)
    }
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def atualizar_quantidade_peca(peca_id, nova_qtd):
    url = f"{SUPABASE_URL}/rest/v1/estoque_pecas?id=eq.{peca_id}"
    dados = {"quantidade_atual": int(nova_qtd)}
    requests.patch(url, headers=HEADERS, json=dados)

def vincular_peca_na_os(os_id, peca_id, qtd, preco_venda):
    url = f"{SUPABASE_URL}/rest/v1/os_pecas"
    dados = {
        "os_id": os_id,
        "peca_id": peca_id,
        "quantidade": int(qtd),
        "preco_venda_aplicado": float(preco_venda)
    }
    res = requests.post(url, headers=HEADERS, json=dados)
    if res.status_code == 201:
        url_p = f"{SUPABASE_URL}/rest/v1/estoque_pecas?id=eq.{peca_id}&select=quantidade_atual"
        res_p = requests.get(url_p, headers=HEADERS)
        if res_p.status_code == 200 and len(res_p.json()) > 0:
            qtd_atual = res_p.json()['quantidade_atual']
            atualizar_quantidade_peca(peca_id, max(0, qtd_atual - int(qtd)))
        return True
    return False

def listar_pecas_da_os(os_id):
    url = f"{SUPABASE_URL}/rest/v1/os_pecas?os_id=eq.{os_id}&select=*,estoque_pecas(nome_peça)"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        dados = []
        for item in res.json():
            dados.append({
                "Peça": item['estoque_pecas']['nome_peça'] if item.get('estoque_pecas') else "Peça Removida",
                "Quantidade": item['quantidade'],
                "Preço Unitário": item['preco_venda_aplicado'],
                "Subtotal": item['quantidade'] * item['preco_venda_aplicado']
            })
        return dados
    return []

def listar_clientes(oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/clientes?oficina_id=eq.{oficina_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def cadastrar_cliente(nome, telefone, cpf, oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/clientes"
    dados = {"nome": nome, "telefone": telefone, "cpf": cpf, "oficina_id": oficina_id}
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def listar_servicos(oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/servicos?oficina_id=eq.{oficina_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def cadastrar_servico(nome, preco, oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/servicos"
    dados = {"nome": nome, "preco_base": float(preco), "oficina_id": oficina_id}
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def contar_os_por_status(status):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?status=eq.{status}&select=id"
    res = requests.get(url, headers=HEADERS)
    return len(res.json()) if res.status_code == 200 else 0

def obter_totais_financeiros():
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?status=eq.Concluído&select=id"
    res = requests.get(url, headers=HEADERS)
    return len(res.json()) * 150.00

def obter_dados_faturamento_grafico():
    return pd.DataFrame([{"Mês": "Março", "Faturamento": obter_totais_financeiros()}])

def listar_motos():
    url = f"{SUPABASE_URL}/rest/v1/motos?select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def cadastrar_moto(cliente_id, marca, modelo, placa, ano):
    url = f"{SUPABASE_URL}/rest/v1/motos"
    dados = {"cliente_id": cliente_id, "marca": marca, "modelo": modelo, "placa": placa, "ano": int(ano)}
    requests.post(url, headers=HEADERS, json=dados)

def listar_motos_detalhado():
    url = f"{SUPABASE_URL}/rest/v1/motos?select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def listar_ordens_servico():
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def criar_ordem_servico(moto_id, descricao):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico"
    dados = {"moto_id": moto_id, "descricao_problema": descricao, "status": "Pendente"}
    requests.post(url, headers=HEADERS, json=dados)

def obter_detalhes_completos_os(os_id):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?id=eq.{os_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200 and len(res.json()) > 0:
        os_data = res.json()
        servicos_da_os = listar_servicos_da_os(os_id)
        total_servicos = sum(s['Preço Aplicado'] for s in servicos_da_os)
        pecas_da_os = listar_pecas_da_os(os_id)
        total_pecas = sum(p['Subtotal'] for p in pecas_da_os)
        
        return {
            "os_id": os_data['id'],
            "status": os_data['status'],
            "descricao_problema": os_data['descricao_problema'],
            "servicos": servicos_da_os,
            "pecas": pecas_da_os,
            "total": total_servicos + total_pecas
        }
    return None

def listar_servicos_da_os(os_id):
    url = f"{SUPABASE_URL}/rest/v1/os_servicos?os_id=eq.{os_id}&select=*,servicos(nome)"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        dados = []
        for item in res.json():
            dados.append({
                "Serviço": item['servicos']['nome'] if item.get('servicos') else "Mão de Obra",
                "Preço Aplicado": item['preco_aplicado']
            })
        return dados
    return []

def vincular_servico_na_os(os_id, servico_id, preco):
    url = f"{SUPABASE_URL}/rest/v1/os_servicos"
    dados = {"os_id": os_id, "servico_id": servico_id, "preco_aplicado": float(preco)}
    requests.post(url, headers=HEADERS, json=dados)

def atualizar_status_os(os_id, novo_status):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?id=eq.{os_id}"
    dados = {"status": novo_status}
    requests.patch(url, headers=HEADERS, json=dados)
