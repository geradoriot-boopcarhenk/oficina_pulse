# database_carro.py
import requests
import pandas as pd

SUPABASE_URL = "https://rhzrammhslouwuuragop.supabase.co"
SUPABASE_KEY = "sb_publishable_q_jv6ihPC2AjJtMedXcawQ_XiDOf0mH"

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

def obtener_logomarca_oficina(oficina_id):
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
        "nome_peça": nome,
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

def cadastrar_cliente(nome, telephone, cpf, oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/clientes"
    dados = {"nome": nome, "telefone": telephone, "cpf": cpf, "oficina_id": oficina_id}
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def contar_os_por_status(status):
    return 0
