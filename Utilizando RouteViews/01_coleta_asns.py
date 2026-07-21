import os
import re
import time
import requests
import pandas as pd

COUNTRIES = ["IR", "IL", "SY", "IQ", "LB"]
CACHE_FILE = "asn_cache.json"

def get_json(url, params, retries=4, timeout=40):
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            time.sleep(wait)
    return None

def get_routed_asns(country):
    data = get_json("https://stat.ripe.net/data/country-asns/data.json", {"resource": country, "lod": 1})
    if not data: return []
    routed_str = data["data"]["countries"][0]["routed"]
    return [int(x) for x in re.findall(r"AsnSingle\((\d+)\)", routed_str)]

def get_as_info(asn):
    name, n_prefixes = "unknown", 0
    d1 = get_json("https://stat.ripe.net/data/as-overview/data.json", {"resource": f"AS{asn}"})
    if d1: name = d1["data"].get("holder", "unknown")
    d2 = get_json("https://stat.ripe.net/data/announced-prefixes/data.json", {"resource": f"AS{asn}"})
    if d2: n_prefixes = len(d2["data"].get("prefixes", []))
    return name, n_prefixes

def coletar_asns():
    if os.path.exists("5asns_por_pais.csv"):
        print("Arquivo '5asns_por_pais.csv' encontrado! Carregando dados locais...")
        df_asns = pd.read_csv("5asns_por_pais.csv")
    else:
        print("Coletando os 5 principais ASNs por país...")
        cache = {}
        for country in COUNTRIES:
            asns = get_routed_asns(country)
            for i, asn in enumerate(asns):
                name, n_prefixes = get_as_info(asn)
                cache[f"{country}-{asn}"] = {"country": country, "asn": asn, "name": name, "n_prefixes": n_prefixes}
                time.sleep(0.3)
                
        df_asns = pd.DataFrame(cache.values())
        df_asns = df_asns.sort_values(["country", "n_prefixes"], ascending=[True, False])
        df_asns = df_asns.groupby("country").head(5)
        df_asns.to_csv("5asns_por_pais.csv", index=False)

    # Remoção de ASNs em nuvem/segurança e adição de ASNs centrais para os bloqueios
    df_asns = df_asns[~df_asns["asn"].isin([198949, 13150])]
    extra = pd.DataFrame([
        {"country": "IR", "asn": 12880, "name": "TIC (gateway internacional)", "n_prefixes": None},
        {"country": "IL", "asn": 1680, "name": "Cellcom Fixed Line Communication L.P", "n_prefixes": None},
        {"country": "IL", "asn": 16116, "name": "Pelephone Communications Ltd.", "n_prefixes": None},
    ])
    df_asns = pd.concat([df_asns, extra], ignore_index=True)
    print(df_asns.head())
    return df_asns

if __name__ == "__main__":
    coletar_asns()
