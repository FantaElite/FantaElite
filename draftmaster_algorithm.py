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
    df = pd.DataFrame(team).reset_index(drop=True)  # Correzione: reset_index() aggiunto
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')


BUDGET_PERCENTAGES = {
    "Equilibrata": {
        "Portiere": (0.05, 0.10),  # Percentuali leggermente più ampie
        "Difensore": (0.10, 0.18),
        "Centrocampista": (0.20, 0.30),
        "Attaccante": (0.45, 0.65)
    },
    "Modificatore di Difesa": {
        "Portiere": (0.06, 0.12),
        "Difensore": (0.15, 0.25),
        "Centrocampista": (0.20, 0.30),
        "Attaccante": (0.40, 0.60)
    }
}

def generate_team(database, strategy="Equilibrata"):
    # ... (Codice iniziale come prima)

    while attempts < max_attempts:
        # ... (Selezione giocatori per ruolo come prima)

        # Aggiustamento finale (più "intelligente" e flessibile)
        remaining_budget = 100 - total_cost_percentage

        # Calcola il budget *effettivo* per ruolo, tenendo conto dello sforamento
        actual_budget_per_role = {}
        for role in ROLES:
            target_percentage = target_budget_per_role[role] / 100  # Converti in frazione
            ideal_cost = target_percentage * 100  # Costo "ideale"
            actual_budget_per_role[role] = min(ideal_cost + remaining_budget / len(ROLES), budget_percentages[strategy][role][1] * 100) # Massimo il limite superiore + quota parte budget rimanente

        # Aggiungi giocatori mancanti, considerando il budget *effettivo*
        for role, count in ROLES.items():
            players_in_role = [p for p in selected_team if p['Ruolo'] == role]
            missing_players = count - len(players_in_role)

            if missing_players > 0:
                available_players = sorted(
                    [p for p in database if p['Ruolo'] == role and p not in selected_team and p['Quota_Percentuale'] <= actual_budget_per_role[role]],
                    key=lambda x: (x['Quota_Percentuale'] * 0.33 + x['Partite_Voto'] * 0.33 + x['Fantamedia'] * 0.34),
                    reverse=True
                )
                
                players_to_add = available_players[:min(missing_players, len(available_players))]
                selected_team.extend(players_to_add)
                total_cost_percentage += sum(p['Quota_Percentuale'] for p in players_to_add)
                remaining_budget -= sum(p['Quota_Percentuale'] for p in players_to_add)

        if total_cost_percentage >= 95 and total_cost_percentage <= 100 and len(selected_team) == 25:
            return selected_team, total_cost_percentage

        attempts += 1

    return best_team, best_cost


# Web App con Streamlit
st.title("⚽ FantaElite - Team Gen ⚽")
st.markdown("""---
### Scegli il tuo metodo di acquisto
""")

# Selezione tipo di pagamento
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (2 strategie)"])

# Selezione strategia di generazione
strategies = ["Equilibrata", "Modificatore di Difesa"]

if payment_type == "One Shot (1 strategia)":
    strategy = st.selectbox(" Seleziona la strategia di generazione", strategies)
    strategy_list = [strategy]
else:
    strategy_list = strategies

database = load_database()
if database is None:
    st.stop()

if st.button("️ Genera La Tua Squadra"):
    for strategy in strategy_list:
        team, total_cost_percentage = generate_team(database, strategy)
        if team and total_cost_percentage >= 95 and len(team) == 25:  # Aggiunti i due punti
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost_percentage:.2f}% del budget")
            st.write("### Squadra generata:")
            st.write(pd.DataFrame(team))
            csv_data = export_to_csv(team)
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