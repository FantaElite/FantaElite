import streamlit as st
import pandas as pd
import random

# Carica il database Excel automaticamente
@st.cache
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')

        # Pulizia delle colonne
        df.columns = df.columns.str.strip()

        # Mappatura colonne per evitare errori di lettura
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
            st.error(f"Errore: Mancano colonne {missing_columns} nel file CSV. Trovate: {df.columns.tolist()}")
            return None

        # Conversione delle colonne numeriche
        numeric_columns = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Riempie solo i valori NaN con la media delle quotazioni esistenti
        df["Quotazione"].fillna(df["Quotazione"].mean(), inplace=True)

        # Assicura che la colonna "Ruolo" sia trattata come stringa e senza NaN
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip().fillna("Sconosciuto")

        return df.to_dict(orient='records')

    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None


def normalize_quotations(database, budget):
    """ Riproporziona le quotazioni in base al budget scelto. """
    max_quot = max(player['Quotazione'] for player in database if player['Quotazione'] > 0)
    if max_quot > 0:
        scale_factor = budget / max_quot
        for player in database:
            player['Quotazione'] = max(round(player['Quotazione'] * scale_factor, 2), 1)  # Minimo 1 credito


def generate_team(database, budget=500, strategy="Equilibrata"):
    """ Genera una squadra in base al budget e alla strategia. """
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }

    normalize_quotations(database, budget)
    team = []
    remaining_budget = budget

    for role, count in ROLES.items():
        # Filtra i giocatori per ruolo e con quotazione valida
        players = [p for p in database if p['Ruolo'] == role and p['Quotazione'] > 0]

        # Ordinamento per strategia
        if strategy == "Equilibrata":
            players = sorted(players, key=lambda x: x["Fantamedia"], reverse=True)
        elif strategy == "Top Player Oriented":
            players = sorted(players, key=lambda x: (x["Quotazione"], x["Fantamedia"]), reverse=True)
        elif strategy == "Squadra Diversificata":
            random.shuffle(players)
        elif strategy == "Modificatore di Difesa":
            if role == "Difensore":
                players = sorted(players, key=lambda x: x["Media_Voto"], reverse=True)
            else:
                players = sorted(players, key=lambda x: x["Fantamedia"], reverse=True)

        selected = []
        for player in players:
            if len(selected) < count and player["Quotazione"] <= remaining_budget:
                selected.append(player)
                remaining_budget -= player["Quotazione"]

            if len(selected) >= count:
                break

        # Se non riusciamo a completare il ruolo, restituiamo errore
        if len(selected) < count:
            st.warning(f"⚠️ Budget insufficiente per completare il ruolo {role}.")
            return None, None

        team.extend(selected)

    total_cost = sum(p["Quotazione"] for p in team)
    return team, total_cost if total_cost <= budget else None


def export_to_csv(team):
    """ Esporta la squadra generata in un CSV. """
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')


# 🌍 Interfaccia Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
st.markdown("### 📌 Scegli il tuo metodo di generazione")

payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (4 strategie)"])
budget = st.number_input("💰 Inserisci il budget", min_value=1, value=500, step=1)

# Selezione strategia
strategies = ["Equilibrata", "Top Player Oriented", "Squadra Diversificata", "Modificatore di Difesa"]
if payment_type == "One Shot (1 strategia)":
    strategy = st.selectbox("🎯 Seleziona la strategia di generazione", strategies)
    strategy_list = [strategy]
else:
    strategy_list = strategies

# Carica il database
database = load_database()
if database is None:
    st.stop()

if st.button("🛠️ Genera Squadra"):
    for strategy in strategy_list:
        team, total_cost = generate_team(database, budget, strategy)
        if team:
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost:.2f}")
            st.write("### 📜 Squadra selezionata:")
            for player in team:
                st.write(f"{player['Ruolo']}: {player['Nome']} ({player['Squadra']}) - Cost: {player['Quotazione']:.2f} - Fantamedia: {player['Fantamedia']:.2f}")

            # Esporta in CSV
            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore: Budget troppo basso per formare una rosa completa con la strategia '{strategy}'.")

