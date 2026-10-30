# database_carro.py - Sincronizacao Definitiva Unificada de Carros
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
    # Cravada em definitivo a coluna correta "cliente_id" do banco de carros
    dados = {
        "cliente_id": cliente_id,
        "descricao_problema": f"{descricao} | Mão de Obra: R$ {valor_mao_de_obra:.2f}",
        "status": "Pendente"
    }
    res = requests.post(url, headers=HEADERS, json=dados)
    return res.status_code == 201

def listar_ordens_servico():
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?select=*,clientes(nome,telefone,cpf)"
    res = requests.get(url, headers=HEADERS)
    return res.json() if res.status_code == 200 else []

def atualizar_status_os(os_id, novo_status, oficina_id=None):
    url = f"{SUPABASE_URL}/rest/v1/ordens_servico?id=eq.{os_id}"
    dados = {"status": novo_status}
    requests.patch(url, headers=HEADERS, json=dados)
    
    if novo_status == 'Concluído':
        # Busca a descricao do problema para capturar o nome da peca utilizada
        url_os = f"{SUPABASE_URL}/rest/v1/ordens_servico?id=eq.{os_id}&select=descricao_problema"
        res_os = requests.get(url_os, headers=HEADERS)
        if res_os.status_code == 200 and len(res_os.json()) > 0:
            dados_os = res_os.json()
            texto = dados_os[0].get("descricao_problema", "") if isinstance(dados_os, list) else dados_os.get("descricao_problema", "")
            
            # Captura o padrão de peca gravado: "+ Peça: Nome da Peca (xQuantidade)"
            match = re.search(r'\+\s*Peça:\s*(.+?)\s*\(x(\d+)\)', texto, re.IGNORECASE)
            if match:
                nome_peca_usada = match.group(1).strip()
                qtd_usada = int(match.group(2))
                
                # Busca todas as pecas do estoque geral para localizar o produto correto
                url_pecas = f"{SUPABASE_URL}/rest/v1/estoque_pecas?select=*"
                res_p = requests.get(url_pecas, headers=HEADERS)
                if res_p.status_code == 200:
                    for p in res_p.json():
                        nome_banco = p.get('nome_peca') or p.get('nome_peça') or ""
                        if nome_banco.strip().lower() == nome_peca_usada.lower():
                            qtd_banco = p.get('quantidade') or p.get('quantidade_atual') or 0
                            nova_qtd = max(0, int(qtd_banco) - qtd_usada)
                            
                            # Executa a baixa automatica na coluna correta do banco de carros
                            url_update = f"{SUPABASE_URL}/rest/v1/estoque_pecas?id=eq.{p['id']}"
                            campo_qtd = 'quantidade' if 'quantidade' in p else 'quantidade_atual'
                            requests.patch(url_update, headers=HEADERS, json={campo_qtd: int(nova_qtd)})
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
