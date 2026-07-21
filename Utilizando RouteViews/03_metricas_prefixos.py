import os
import pandas as pd

def calcular_prefixos_visiveis():
    if os.path.exists("prefixos_visiveis_por_evento.csv"):
        print("Arquivo 'prefixos_visiveis_por_evento.csv' encontrado! Lendo dados processados...")
        df_visibility = pd.read_csv("prefixos_visiveis_por_evento.csv", parse_dates=["date"])
        print(df_visibility.head())
        return df_visibility
    
    print("Processando BGP Updates para estimar prefixos visíveis (A)...")
    if not os.path.exists("bgp_updates_raw_completo.csv"):
        print("Erro: Arquivo 'bgp_updates_raw_completo.csv' não encontrado.")
        return None
        
    df_updates = pd.read_csv("bgp_updates_raw_completo.csv")
    df_updates["date"] = pd.to_datetime(df_updates["timestamp"]).dt.normalize()
    
    if os.path.exists("5asns_por_pais.csv"):
        df_asns = pd.read_csv("5asns_por_pais.csv")
        df_updates = df_updates.merge(df_asns[["asn", "country"]], on="asn", how="left")
    else:
        print("Aviso: '5asns_por_pais.csv' não encontrado. Use o script 01 primeiro.")
        return None

    # Contagem de prefixos únicos anunciados por dia por país/evento
    df_visibility = (
        df_updates[df_updates["type"] == "A"]
        .groupby(["event", "country", "date"])
        .agg(v4_prefixes_visiveis=("prefix", "nunique"), asns_visiveis=("asn", "nunique"))
        .reset_index()
    )
    
    df_visibility.to_csv("prefixos_visiveis_por_evento.csv", index=False)
    print("Prefixos visíveis calculados e salvos em 'prefixos_visiveis_por_evento.csv'.")
    print(df_visibility.head())
    return df_visibility

if __name__ == "__main__":
    calcular_prefixos_visiveis()
