import os
import pandas as pd
import matplotlib.pyplot as plt

def gerar_grafico_withdrawals():
    if os.path.exists("withdrawals_por_dia.csv"):
        wd = pd.read_csv("withdrawals_por_dia.csv")
        if not wd.empty and "date" in wd.columns:
            wd["date"] = pd.to_datetime(wd["date"])
            eventos_wd = wd["event"].dropna().unique()

            for evento in eventos_wd:
                dados_evento = wd[wd["event"] == evento]
                
                fig, ax = plt.subplots(figsize=(10, 4))
                for country, grupo in dados_evento.groupby("country"):
                    grupo = grupo.sort_values("date")
                    ax.plot(grupo["date"], grupo["n_withdrawals"], marker="o", label=f"País: {country}")

                ax.set_title(f"Withdrawals BGP Diários ({evento.replace('_', ' ').title()})")
                ax.set_xlabel("Data")
                ax.set_ylabel("Quantidade de Withdrawals")
                ax.grid(True, linestyle="--", alpha=0.6)
                ax.legend(fontsize=9)
                fig.autofmt_xdate()
                plt.tight_layout()
                plt.savefig(f"grafico_withdrawals_{evento}.png", dpi=150)
                plt.close()
                print(f"Gráfico salvo: grafico_withdrawals_{evento}.png")
        else:
            print("Aviso: 'withdrawals_por_dia.csv' está vazio (nenhum withdrawal encontrado).")

def gerar_grafico_prefixos():
    if os.path.exists("prefixos_visiveis_por_evento.csv"):
        df_vis = pd.read_csv("prefixos_visiveis_por_evento.csv")
        if not df_vis.empty and "date" in df_vis.columns:
            df_vis["date"] = pd.to_datetime(df_vis["date"])
            eventos_vis = df_vis["event"].dropna().unique()

            for evento in eventos_vis:
                dados_evento = df_vis[df_vis["event"] == evento]
                
                fig, ax = plt.subplots(figsize=(10, 4))
                for country, grupo in dados_evento.groupby("country"):
                    grupo = grupo.sort_values("date")
                    ax.plot(grupo["date"], grupo["v4_prefixes_visiveis"], marker="s", label=f"País: {country}")

                ax.set_title(f"Prefixos Visíveis BGP ({evento.replace('_', ' ').title()})")
                ax.set_xlabel("Data")
                ax.set_ylabel("Qtd de Prefixos IPv4")
                ax.grid(True, linestyle="--", alpha=0.6)
                ax.legend(fontsize=9)
                fig.autofmt_xdate()
                plt.tight_layout()
                plt.savefig(f"grafico_prefixos_visiveis_{evento}.png", dpi=150)
                plt.close()
                print(f"Gráfico salvo: grafico_prefixos_visiveis_{evento}.png")

if __name__ == "__main__":
    gerar_grafico_withdrawals()
    gerar_grafico_prefixos()
