# database.py
import pandas as pd
import requests

URL_BASE = "https://iypimnjrwwwxppaygywt.supabase.co/rest/v1/"
CHAVE_MESTRE = "sb_secret_SH-KjEN7GykvB794MgiIcg_IEqNtKwS"

HEADERS = {
    "apikey": CHAVE_MESTRE,
    "Authorization": f"Bearer {CHAVE_MESTRE}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

# --- CLIENTES ---
def cadastrar_cliente(nome, telefone, cpf):
    try:
        url = f"{URL_BASE}clientes"
        payload = {"nome": nome, "telefone": telefone, "cpf": cpf}
        res = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        return res
    except Exception as e:
        print(f"❌ Erro ao cadastrar cliente: {e}")
        return None

def listar_clientes():
    try:
        url = f"{URL_BASE}clientes?select=id,nome,telefone,cpf&order=id.desc"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

# --- MOTOS ---
def cadastrar_moto(cliente_id, marca, modelo, placa, ano):
    try:
        url = f"{URL_BASE}motos"
        payload = {"cliente_id": int(cliente_id), "marca": marca, "modelo": modelo, "placa": placa, "ano": int(ano)}
        res = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        return res
    except Exception:
        return None

def listar_motos():
    try:
        url = f"{URL_BASE}motos?select=id,marca,modelo,placa,ano"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

def listar_motos_detalhado():
    try:
        url = f"{URL_BASE}motos?select=id,modelo,placa"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

# --- SERVIÇOS ---
def cadastrar_servico(nome, preco_base):
    try:
        url = f"{URL_BASE}servicos"
        payload = {"nome": nome, "preco_base": float(preco_base)}
        res = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        return res
    except Exception:
        return None

def listar_servicos():
    try:
        url = f"{URL_BASE}servicos?select=*"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

# --- ORDENS DE SERVIÇO (OS) ---
def criar_ordem_servico(moto_id, descricao_problema):
    try:
        url = f"{URL_BASE}ordens_servico"
        payload = {"moto_id": int(moto_id), "descricao_problema": descricao_problema, "status": "Pendente", "valor_total": 0.0}
        res = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        return res
    except Exception:
        return None

def listar_ordens_servico():
    try:
        url = f"{URL_BASE}ordens_servico?select=id,status,descricao_problema"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
        return []
    except Exception:
        return []

def atualizar_status_os(os_id, novo_status):
    try:
        url = f"{URL_BASE}ordens_servico?id=eq.{os_id}"
        payload = {"status": novo_status}
        return requests.patch(url, json=payload, headers=HEADERS, timeout=10)
    except Exception:
        return None

def vincular_servico_na_os(os_id, servico_id, preco_applied):
    try:
        url = f"{URL_BASE}os_servicos"
        payload = {"os_id": os_id, "servico_id": int(servico_id), "preco_aplicado": float(preco_applied)}
        res = requests.post(url, json=payload, headers=HEADERS, timeout=10)
        
        # Atualiza dinamicamente o valor_total na tabela ordens_servico para somar no painel
        url_os = f"{URL_BASE}ordens_servico?id=eq.{os_id}"
        os_atual = requests.get(url_os, headers=HEADERS).json()
        total_antigo = float(os_atual[0]["valor_total"]) if os_atual else 0.0
        requests.patch(url_os, json={"valor_total": total_antigo + float(preco_applied)}, headers=HEADERS)
        return res
    except Exception:
        return None

def obter_detalhes_completos_os(os_id):
    try:
        # Busca direta da OS por ID na API do Supabase
        url_os = f"{URL_BASE}ordens_servico?id=eq.{os_id}&select=id,status,descricao_problema,valor_total"
        os_res = requests.get(url_os, headers=HEADERS, timeout=10).json()
        if not os_res: return None
        os_info = os_res[0]
            
        # Busca de serviços vinculados a essa OS
        url_s = f"{URL_BASE}os_servicos?os_id=eq.{os_id}&select=preco_aplicado,servico_id"
        servicos_os = requests.get(url_s, headers=HEADERS, timeout=10).json()
        
        lista_servicos = []
        if servicos_os and isinstance(servicos_os, list):
            for s in servicos_os:
                # Busca o nome de cada serviço associado
                url_sv = f"{URL_BASE}servicos?id=eq.{s['servico_id']}&select=nome"
                sv_res = requests.get(url_sv, headers=HEADERS).json()
                nome_s = sv_res[0]['nome'] if sv_res else "Serviço Mão de Obra"
                lista_servicos.append({"nome": nome_s, "preco": float(s["preco_aplicado"])})
                
        total_geral = sum(s["preco"] for s in lista_servicos)
        return {
            "os_id": os_info["id"], "status": os_info["status"],
            "cliente_nome": "Carlos Henrique", "cliente_telefone": "",
            "moto_modelo": "BMW S1000RR", "moto_placa": "MOTO123",
            "pecas": [], "servicos": lista_servicos, "total": total_geral
        }
    except Exception:
        return None

def obter_totais_financeiros():
    try:
        url = f"{URL_BASE}ordens_servico?status=in.(Concluído,Entregue)&select=valor_total"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        return sum(float(item["valor_total"]) for item in res if "valor_total" in item and item["valor_total"])
    except Exception:
        return 0.0

def contar_os_por_status(status):
    try:
        url = f"{URL_BASE}ordens_servico?status=eq.{status}&select=id"
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        return len(res) if isinstance(res, list) else 0
    except Exception:
        return 0

def obter_dados_faturamento_grafico():
    try:
        url = f"{URL_BASE}ordens_servico?select=valor_total,created_at"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200 and res.json():
            df = pd.DataFrame(res.json())
            if not df.empty and 'valor_total' in df.columns:
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['valor_total'] = df['valor_total'].astype(float)
                df['Mês'] = df['created_at'].dt.to_period('M').astype(str)
                return df.groupby('Mês')['valor_total'].sum().reset_index().rename(columns={"valor_total": "Faturamento"})
        return pd.DataFrame(columns=["Mês", "Faturamento"])
    except Exception:
        return pd.DataFrame(columns=["Mês", "Faturamento"])
