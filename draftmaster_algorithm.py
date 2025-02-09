import streamlit as st
import pandas as pd
import random

# Carica il database Excel automaticamente
@st.cache
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')

        # Rimuove eventuali spazi nei nomi delle colonne
        df.columns = df.columns.str.strip()

        # Rinomina le colonne per essere sicuri che siano standardizzate
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

        # Verifica che tutte le colonne siano presenti
        expected_columns = list(column_mapping.values())
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV.")
            return None

        # Conversione delle colonne numeriche con gestione degli errori
        numeric_columns = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Converte eventuali valori errati in NaN

        # Riempiamo eventuali NaN con valori di default
        df["Quotazione"].fillna(df["Quotazione"].mean(), inplace=True)

        # Assicura che "Ruolo" sia trattato come stringa e non contenga NaN
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip().fillna("Sconosciuto")

        return df.to_dict(orient='records')

    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None


def normalize_quotations(database, budget):
    """ Normalizza solo la colonna 'Quotazione' in base al budget. """
    max_quot = max(player['Quotazione'] for player in database if player['Quotazione'] > 0)
    scale_factor = budget / max_quot if max_quot > 0 else 1
    for player in database:
        player['Quotazione'] = max(round(player['Quotazione'] * scale_factor, 2), 1)  # Assicura che nessuno abbia quota 0


def generate_team(database, budget=500, strategy="Equilibrata"):
    """ Genera una squadra in base alla strategia scelta e al budget. """
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
        players = [p for p in database if p['Ruolo'] == role and p['Quotazione'] > 0]

        # Applica la strategia scelta
        if strategy == "Equilibrata":
            players = sorted(players, key=lambda x: x['Fantamedia'], reverse=True)
        elif strategy == "Top Player Oriented":
            players = sorted(players, key=lambda x: (x['Quotazione'], x['Fantamedia']), reverse=True)
        elif strategy == "Squadra Diversificata":
            random.shuffle(players)
        elif strategy == "Modificatore di Difesa":
            if role == "Difensore":
                players = sorted(players, key=lambda x: x['Media_Voto'], reverse=True)
            else:
                players = sorted(players, key=lambda x: x['Fantamedia'], reverse=True)

        selected = []

        for player in players:
            if len(selected) < count and player['Quotazione'] <= remaining_budget:
                selected.append(player)
                remaining_budget -= player['Quotazione']

            if len(selected) >= count:
                break

        if len(selected) < count:
            st.warning(f"⚠️ Non è stato possibile selezionare abbastanza giocatori per il ruolo {role}. Verifica il budget.")
            return None, None

        team.extend(selected)

    total_cost = sum(p['Quotazione'] for p in team)
    return team, total_cost if total_cost <= budget else None


def export_to_csv(team):
    """ Esporta la squadra in un file CSV scaricabile. """
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')


# Interfaccia Web con Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
st.markdown("""---
### Scegli il tuo metodo di acquisto
""")

# Selezione tipo di pagamento
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (4 strategie)"])

budget = st.number_input("💰 Inserisci il budget", min_value=1, value=500, step=1)

# Selezione strategia di generazione
strategies = ["Equilibrata", "Top Player Oriented", "Squadra Diversificata", "Modificatore di Difesa"]

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
            for player in team:
                st.write(f"{player['Ruolo']}: {player['Nome']} ({player['Squadra']}) - Cost: {player['Quotazione']:.2f} - Fantamedia: {player['Fantamedia']:.2f} - Media Voto: {player['Media_Voto']:.2f} - Presenze: {player['Partite_Voto']}")

            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso per formare una rosa completa.")
