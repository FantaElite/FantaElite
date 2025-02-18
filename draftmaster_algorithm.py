import streamlit as st
import pandas as pd
import random

# Funzioni di caricamento e normalizzazione (rimangono invariate)
@st.cache_data
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')

        # Rimuove eventuali spazi prima e dopo i nomi delle colonne
        df.columns = df.columns.str.strip()

        # Mappa i nuovi nomi delle colonne corretti
        column_mapping = {
            "Nome": "Nome",
            "Squadra": "Squadra",
            "Ruolo": "Ruolo",
            "Media_Voto": "Media_Voto",
            "Fantamedia": "Fantamedia",
            "Quotazione": "Quota_Percentuale",
            "Partite_Voto": "Partite_Voto"
        }

        df.rename(columns=column_mapping, inplace=True)

        # Controllo colonne mancanti
        expected_columns = list(column_mapping.values())
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV. Ecco le colonne trovate: {df.columns.tolist()}")
            return None

        # Converti le colonne numeriche correggendo eventuali errori
        numeric_columns = ["Quota_Percentuale", "Fantamedia", "Media_Voto", "Partite_Voto"]

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Converte i valori non numerici in NaN

        # Riempie solo i valori NaN con la media delle quotazioni esistenti
        df["Quota_Percentuale"].fillna(df["Quota_Percentuale"].mean(), inplace=True)

        # Assicura che la colonna "Ruolo" sia trattata come stringa senza NaN
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip().fillna("Sconosciuto")

        # Convertiamo la quotazione in percentuale rispetto a un budget di 500 crediti
        df["Quota_Percentuale"] = (df["Quota_Percentuale"] / 500.0) * 100  # Converte in percentuale

        return df.to_dict(orient='records')

    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None


def export_to_csv(team):
    df = pd.DataFrame(team).reset_index(drop=True)
    csv_data = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8')  # Codifica la stringa CSV
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
        team, total_cost_percentage = generate_team(database, strategy)  # Corretto!

        print(f"DEBUG: Team (dopo generate_team): {team}") # Stampa 'team' per debug

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