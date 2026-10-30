# database_carro.py
import requests
import pandas as pd
import re

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
        return res.json()
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

def listar_clientes(oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/clientes?oficina_id=eq.{oficina_id}&select=*"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def cadastrar_cliente(nome, telephone, cpf, oficina_id):
    url = f"{SUPABASE_URL}/rest/v1/clientes"
    dados = {"nome": nome, "telefone": telephone, "cpf": cpf, "oficina_id": oficina_id}
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def criar_ordem_servico(cliente_id, descricao, valor_mao_de_obra):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico"
    # Fiação calibrada mudando a chave para o padrão universal 'moto_id' aceito pelo banco de dados
    dados = {
        "moto_id": cliente_id,
        "descricao_problema": f"{descricao} | Mão de Obra: R$ {valor_mao_de_obra:.2f}",
        "status": "Pendente"
    }
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def listar_ordens_servico():
    # Ajustado o select para carregar o mapeamento unificado do relacionamento de clientes
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?select=*,clientes(nome,telefone,cpf)"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def atualizar_status_os(os_id, novo_status, oficina_id=None):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?id=eq.{os_id}"
    dados = {"status": novo_status}
    requests.patch(url, headers=HEADERS, json=dados)
    
    if novo_status == 'Concluído' and oficina_id:
        url_os = f"{SUPABASE_URL}/rest/v1/ordens_servico?id=eq.{os_id}&select=descricao_problema"
        res_os = requests.get(url_os, headers=HEADERS)
        if res_os.status_code == 200 and len(res_os.json()) > 0:
            texto = res_os.json().get("descricao_problema", "")
            match = re.search(r'\+\s*Peça:\s*(.+?)\s*\(x(\d+)\)', texto, re.IGNORECASE)
            if match:
                nome_peca_usada = match.group(1).strip()
                qtd_usada = int(match.group(2))
                
                pecas_totais = listar_pecas_estoque(oficina_id)
                for p in pecas_totais:
                    nome_banco = p.get('nome_peça') or p.get('nome_peca') or ""
                    if nome_banco.strip().lower() == nome_peca_usada.lower():
                        nova_qtd = max(0, int(p['quantidade_atual']) - qtd_usada)
                        url_update = f"{SUPABASE_URL}/rest/v1/estoque_pecas?id=eq.{p['id']}"
                        requests.patch(url_update, headers=HEADERS, json={"quantidade_atual": int(nova_qtd)})
                        break

def contar_os_por_status(status):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?status=eq.{status}&select=id"
    res = requests.get(url, headers=HEADERS)
    return len(res.json()) if res.status_code == 200 else 0

def obter_totais_financeiros():
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?status=eq.Concluído&select=descricao_problema"
    res = requests.get(url, headers=HEADERS)
    total = 0.0
    if res.status_code == 200:
        for os in res.json():
            texto = os.get("descricao_problema", "")
            match = re.search(r'Mão de Obra: R\$ ([\d.]+)', texto, re.IGNORECASE)
            if match:
                total += float(match.group(1))
    return total
