import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

EVENTS = [
    {"country": "IR", "label": "guerra_ira_2026",        "start": "2026-06-10T00:00:00", "end": "2026-06-25T00:00:00"},
    {"country": "LB", "label": "conflito_hezbollah_2024", "start": "2024-09-15T00:00:00", "end": "2024-11-30T00:00:00"},
    {"country": "SY", "label": "protestos_primavera_arabe_2011", "start": "2011-03-10T00:00:00", "end": "2011-04-10T00:00:00"},
    {"country": "SY", "label": "apagao_nacional_2012",   "start": "2012-11-27T00:00:00", "end": "2012-12-05T00:00:00"},
    {"country": "SY", "label": "queda_assad_2024",       "start": "2024-11-25T00:00:00", "end": "2024-12-15T00:00:00"},
    {"country": "IL", "label": "guerra_ira_2026",        "start": "2026-06-10T00:00:00", "end": "2026-06-25T00:00:00"},
    {"country": "IQ", "label": "guerra_ira_2026",        "start": "2026-06-10T00:00:00", "end": "2026-06-25T00:00:00"},
    {"country": "SY", "label": "apagao_parcial_junho_2011","start": "2011-06-01T00:00:00","end": "2011-06-06T00:00:00"}
]

CSV_FILE = "bgp_updates_raw_completo.csv"
csv_lock = threading.Lock()

def fetch_bgp_updates(asn, start_time, end_time, event_label, retries=5):
    url = f"https://stat.ripe.net/data/bgp-updates/data.json?resource=AS{asn}&starttime={start_time}&endtime={end_time}"
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 429:
                time.sleep(2 ** attempt + 5)
                continue
            r.raise_for_status()
            data = r.json()
            if "data" in data and "updates" in data["data"]:
                updates = data["data"]["updates"]
                
                # OPTIMIZATION: To prevent memory crash and gigabytes of CSV data,
                # we only save ONE announcement ('A') per unique prefix.
                # We keep all Withdrawals ('W').
                unique_a_prefixes = set()
                rows = []
                
                for upd in updates:
                    u_type = upd.get("type")
                    prefix = upd.get("attrs", {}).get("target_prefix", "")
                    
                    if u_type == "A":
                        if prefix in unique_a_prefixes:
                            continue
                        unique_a_prefixes.add(prefix)
                        
                    rows.append({
                        "asn": asn,
                        "timestamp": upd.get("timestamp"),
                        "type": u_type,
                        "prefix": prefix,
                        "event": event_label
                    })
                return rows
            return []
        except requests.exceptions.RequestException as e:
            time.sleep(2 ** attempt + 2)
    print(f"Falha ao coletar AS{asn} para {start_time} - {end_time}")
    return []

def worker(task):
    asn, date_start, date_end, event_label = task
    rows = fetch_bgp_updates(asn, date_start.strftime("%Y-%m-%dT%H:%M:%S"), date_end.strftime("%Y-%m-%dT%H:%M:%S"), event_label)
    
    if rows:
        df = pd.DataFrame(rows)
        with csv_lock:
            df.to_csv(CSV_FILE, mode='a', header=not os.path.exists(CSV_FILE), index=False)
    return len(rows)

def extracao_completa():
    if not os.path.exists("5asns_por_pais.csv"):
        print("Erro: execute 01_coleta_asns.py primeiro.")
        return

    asns_df = pd.read_csv("5asns_por_pais.csv")
    
    # Se o arquivo já existe, limpa-o para evitar dados duplicados
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)

    tasks = []
    # Para cada evento, gerar chunks de 2 horas para evitar 502 Bad Gateway da RIPE em ASNs gigantes
    for event in EVENTS:
        start_date = datetime.strptime(event["start"], "%Y-%m-%dT%H:%M:%S")
        end_date = datetime.strptime(event["end"], "%Y-%m-%dT%H:%M:%S")
        
        # Filtra os ASNs pelo país do evento
        target_asns = asns_df[asns_df["country"] == event["country"]]["asn"].tolist()
        
        current_date = start_date
        while current_date < end_date:
            next_date = current_date + timedelta(hours=2)
            if next_date > end_date:
                next_date = end_date
            
            for asn in target_asns:
                tasks.append((asn, current_date, next_date, event["label"]))
            
            current_date = next_date

    print(f"Total de {len(tasks)} requisições (chunks de 2h) criadas. Iniciando download multithread...")
    
    total_records = 0
    completed = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(worker, task): task for task in tasks}
        for future in as_completed(futures):
            try:
                count = future.result()
                total_records += count
                completed += 1
                if completed % 10 == 0:
                    print(f"Progresso: {completed}/{len(tasks)} requisições concluídas. Total registros: {total_records}")
            except Exception as e:
                print(f"Erro em uma das threads: {e}")

    print(f"Extração concluída com sucesso! Total de {total_records} updates salvos em {CSV_FILE}.")

if __name__ == "__main__":
    extracao_completa()
