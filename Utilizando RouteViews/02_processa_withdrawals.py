import os
import pandas as pd

def processar_withdrawals():
    if os.path.exists("withdrawals_por_dia.csv"):
        print("Arquivo 'withdrawals_por_dia.csv' encontrado! Lendo dados processados...")
        withdrawals_by_day = pd.read_csv("withdrawals_por_dia.csv", parse_dates=["date"])
        print(withdrawals_by_day.head())
        return withdrawals_by_day
    
    print("Processando BGP Updates para calcular withdrawals...")
    if not os.path.exists("bgp_updates_raw_completo.csv"):
        print("Erro: Arquivo 'bgp_updates_raw_completo.csv' não encontrado.")
        return None
        
    df_updates = pd.read_csv("bgp_updates_raw_completo.csv")
    df_updates["date"] = pd.to_datetime(df_updates["timestamp"]).dt.normalize()
    
    # Precisamos do mapeamento ASN -> País
    if os.path.exists("5asns_por_pais.csv"):
        df_asns = pd.read_csv("5asns_por_pais.csv")
        df_updates = df_updates.merge(df_asns[["asn", "country"]], on="asn", how="left")
    else:
        print("Aviso: '5asns_por_pais.csv' não encontrado. Use o script 01 primeiro.")
        return None
        
    withdrawals_by_day = (
        df_updates[df_updates["type"] == "W"]
        .groupby(["event", "country", "date"])
        .size()
        .reset_index(name="n_withdrawals")
    )
    
    withdrawals_by_day.to_csv("withdrawals_por_dia.csv", index=False)
    print("Withdrawals calculados e salvos em 'withdrawals_por_dia.csv'.")
    print(withdrawals_by_day.head())
    return withdrawals_by_day

if __name__ == "__main__":
    processar_withdrawals()
