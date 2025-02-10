import streamlit as st
import pandas as pd
import os
import random

# Carica il database Excel automaticamente
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
            "Quotazione": "Quotazione",
            "Partite_Voto": "Partite_Voto"
        }

        df.rename(columns=column_mapping, inplace=True)

        # Controllo colonne mancanti
        expected_columns = list(column_mapping.values())
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV.")
            return None

        # Converti le colonne numeriche correggendo eventuali errori
        numeric_columns = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Converte i valori non numerici in NaN
        
        # Riempie i valori NaN con la media delle rispettive colonne
        for col in numeric_columns:
            df[col].fillna(df[col].mean(), inplace=True)

        # Assicura che la colonna "Ruolo" sia trattata come stringa senza NaN
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip().fillna("Sconosciuto")

        return df.to_dict(orient='records')
    
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None


def normalize_quotations(database, budget):
    original_budget = 500  # Le quotazioni originali sono basate su 500 crediti
    for player in database:
        player['Quotazione'] = max(round(player['Quotazione'] * (budget / original_budget), 2), 1)


def generate_team(database, budget=500, strategy="Equilibrata"):
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }

    normalize_quotations(database, budget)
    team = []
    attempts = 0
    max_attempts = 100  # Aumentato per migliorare la casualità

    while attempts < max_attempts:
        selected_team = []
        total_cost = 0

        for role, count in ROLES.items():
            players = sorted(
                [p for p in database if str(p['Ruolo']).strip() == role and p['Quotazione'] > 0],
                key=lambda x: (x['Quotazione'] * 0.4 + x['Partite_Voto'] * 0.3 + x['Fantamedia'] * 0.3),
                reverse=True
            )

            if strategy == "Equilibrata":
                selected = random.sample(players[:max(1, len(players) // 2)], min(count, len(players[:max(1, len(players) // 2)])))
            elif strategy == "Top Player Oriented":
                top_players = players[:max(1, len(players) // 3)]
                selected = random.sample(top_players, min(count, len(top_players)))
            elif strategy == "Modificatore di Difesa":
                if role in ["Portiere", "Difensore"]:
                    selected = random.sample(players[:max(1, len(players) // 3)], min(count, len(players[:max(1, len(players) // 3)])))
                else:
                    selected = random.sample(players[:max(1, len(players) // 2)], min(count, len(players[:max(1, len(players) // 2)])))
            else:
                selected = random.sample(players[:max(1, len(players) // 2)], min(count, len(players[:max(1, len(players) // 2)])))

            selected_team.extend(selected)
            total_cost += sum(p['Quotazione'] for p in selected)

        if total_cost >= budget * 0.95:
            return selected_team, total_cost

        attempts += 1

    return None, None


def export_to_csv(team):
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')


# Web App con Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
st.markdown("---")

# Selezione tipo di generazione
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (3 strategie)"])

budget = st.number_input("💰 Inserisci il budget", min_value=100, value=500, step=10)

# Selezione strategia di generazione
strategies = ["Equilibrata", "Top Player Oriented", "Modificatore di Difesa"]

if payment_type == "One Shot (1 strategia)":
    strategy = st.selectbox("🎯 Seleziona la strategia di generazione", strategies)
    strategy_list = [strategy]
else:
    strategy_list = strategies

database = load_database()
if database is None:
    st.stop()

if st.button("🛠️ Genera Squadra"):
    for strategy in strategy_list:
        team, total_cost = generate_team(database, budget, strategy)
        if team:
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost:.2f}")
            st.write("### Squadra generata:")
            st.write(pd.DataFrame(team))
            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso per formare una rosa completa.")
