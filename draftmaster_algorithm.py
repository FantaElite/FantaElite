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
        "Portiere": 0.07,  # 7%
        "Difensore": 0.13,  # 13%
        "Centrocampista": 0.25,  # 25%
        "Attaccante": 0.55   # 55%
    },
    "Modificatore di Difesa": {
        "Portiere": 0.08,
        "Difensore": 0.20,
        "Centrocampista": 0.23,
        "Attaccante": 0.49
    }
}

def generate_team(database, strategy="Equilibrata"):
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }

    attempts = 0
    max_attempts = 50
    best_team = None
    best_cost = 0
    target_budget = 95

    budget_percentages = BUDGET_PERCENTAGES.get(strategy)
    if not budget_percentages:
        st.error(f"Strategia sconosciuta: {strategy}")
        return None, None

    # Calcola il budget target per ruolo (usando le percentuali esatte)
    target_budget_per_role = {}
    for role in ROLES:
        target_budget_per_role[role] = budget_percentages[role] * 100  # Usa la percentuale esatta

    while attempts < max_attempts:
        selected_team = []
        total_cost_percentage = 0

        for role, count in ROLES.items():
            role_budget = target_budget_per_role[role]

            players = sorted(
                [p for p in database if str(p['Ruolo']).strip() == role and p['Quota_Percentuale'] > 0],
                key=lambda x: (x['Quota_Percentuale'] * 0.33 + x['Partite_Voto'] * 0.33 + x['Fantamedia'] * 0.34),
                reverse=True
            )

            if not players or len(players) < count:
                break

            available_players = [p for p in players if p['Quota_Percentuale'] <= role_budget]
            if len(available_players) < count:
                break  # Non ci sono abbastanza giocatori disponibili con quel budget

            sample_size = min(len(available_players), count * 3)  # Limita il sample ai giocatori disponibili
            selected = random.sample(available_players[:sample_size], count)
            selected_team.extend(selected)
            total_cost_percentage += sum(p['Quota_Percentuale'] for p in selected)

        # Aggiustamento finale (con percentuali esatte)
        remaining_budget = 100 - total_cost_percentage

        # Aggiungi giocatori mancanti, usando il budget calcolato con le percentuali esatte
        for role, count in ROLES.items():
            players_in_role = [p for p in selected_team if p['Ruolo'] == role]
            missing_players = count - len(players_in_role)

            if missing_players > 0:
                available_players = sorted(
                    [p for p in database if p['Ruolo'] == role and p not in selected_team and p['Quota_Percentuale'] <= target_budget_per_role[role]], # Usa il budget calcolato con le percentuali esatte
                    key=lambda x: (x['Quota_Percentuale'] * 0.33 + x['Partite_Voto'] * 0.33 + x['Fantamedia'] * 0.34),
                    reverse=True
                )
                
                players_to_add = available_players[:min(missing_players, len(available_players))]
                selected_team.extend(players_to_add)
                total_cost_percentage += sum(p['Quota_Percentuale'] for p in players_to_add)
                remaining_budget -= sum(p['Quota_Percentuale'] for p in players_to_add)

        if total_cost_percentage >= 95 and total_cost_percentage <= 100 and len(selected_team) == 25:
            return selected_team, total_cost_percentage

        if total_cost_percentage > best_cost and len(selected_team) == 25:
            best_team = selected_team
            best_cost = total_cost_percentage

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
        if team and total_cost_percentage >= 95 and len(team) == 25:
            st.success(f"✅ Squadra generata con successo