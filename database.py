# database.py
import requests
import pandas as pd

SUPABASE_URL = "https://iypimnjrwwwxppaygywt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Iml5cGltbmpyd3d3eHBwYXlneXd0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAxNTMwOTEsImV4cCI6MjA1NTc1OTA5MX0.gHAnp9ePZl4DId43z6M4Z1b1Z1b1Z1b1Z1b1Z1b1Z1b1"

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
        return res.json()[0].get('logomarca_base64')
    return None

def listar_pecas_estoque(oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/estoque_pecas?oficina_id=eq.{oficina_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def cadastrar_peca_estoque(oficina_id, nome, qtd, custo, venda):
    url = f"{SUPABASE_URL}/rest/v1/estoque_pecas"
    dados = {
        "oficina_id": oficina_id,
        "nome_peca": nome,
        "quantidade_atual": int(qtd),
        "preco_custo": float(custo),
        "preco_venda": float(venda)
    }
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def listar_clientes(oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/clientes?oficina_id=eq.{oficina_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def cadastrar_cliente(nome, telefone, cpf, oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/clientes"
    dados = {"nome": nome, "telefone": telefone, "cpf": cpf, "oficina_id": oficina_id}
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def contar_os_por_status(status):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?status=eq.{status}&select=id"
    res = requests.get(url, headers=HEADERS)
    return len(res.json()) if res.status_code == 200 else 0

def obter_totais_financeiros():
    return 0.0

def obter_dados_faturamento_grafico():
    return pd.DataFrame()

def listar_motos():
    return []

def cadastrar_moto(cliente_id, marca, modelo, placa, ano):
    pass

def listar_motos_detalhado():
    return []

def listar_ordens_servico():
    return []

def criar_ordem_servico(moto_id, descricao):
    pass

def obter_detalhes_completos_os(os_id):
    return None

def listar_servicos(oficina_id):
    return []

def cadastrar_servico(nome, preco, oficina_id):
    return False

def atualizar_status_os(os_id, novo_status):
    pass
