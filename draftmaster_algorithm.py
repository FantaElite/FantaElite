import streamlit as st
import pandas as pd
import random

# Funzioni di caricamento e normalizzazione (rimangono invariate)
@st.cache_data
def load_database():
    # ... (Codice invariato)

def export_to_csv(team):
    df = pd.DataFrame(team).reset_index(drop=True)
    csv_data = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8')  # Corretto: encoding applicato alla stringa
    return csv_data.encode('utf-8') #Codifica per download

BUDGET_PERCENTAGES = {
    "Equilibrata": {
        "Portiere": 0.07,
        "Difensore": 0.13,
        "Centrocampista": 0.25,
        "Attaccante": 0.55
    },
    "Modificatore di Difesa": {
        "Portiere": 0.08,
        "Difensore": 0.20,
        "Centrocampista": 0.23,
        "Attaccante": 0.49
    }
}

def generate_team(database, strategy="Equilibrata"):
    # ... (Codice generazione squadra, invariato)

# Web App con Streamlit
st.title("⚽ FantaElite - Team Gen ⚽")
# ... (Codice Streamlit invariato)

if st.button("️ Genera La Tua Squadra"):
    for strategy in strategy_list:
        team, total_cost_percentage = generate_team(database, strategy)

        print(f"DEBUG: Team (dopo generate_team): {team}")  # Stampa 'team' per debug

        if team and total_cost_percentage >= 95 and len(team) == 25:
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost_percentage:.2f}% del budget")
            st.write("### Squadra generata:")
            st.write(pd.DataFrame(team))  # Visualizza la squadra

            csv_data = export_to_csv(team)
            print(f"DEBUG: csv_data: {csv_data}")  # Stampa 'csv_data' per debug

            st.download_button(
                label=f"⬇️ Scarica Squadra ({strategy})",
                data=csv_data,
                file_name=f"squadra_{strategy}.csv",
                mime="text/csv"
            )
        elif team is not None and len(team) < 25:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Non è stato possibile completare tutti i ruoli.")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso per formare una rosa completa.")