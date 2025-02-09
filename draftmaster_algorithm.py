import streamlit as st
import pandas as pd
import random

# Carica il database Excel automaticamente
@st.cache
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

        # Controllo che tutte le colonne attese siano presenti
        expected_columns = list(column_mapping.values())
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV. Colonne trovate: {df.columns.tolist()}")
            return None

        # Convertire le colonne testuali in stringhe per evitare problemi di tipo
        text_columns = ["Nome", "Squadra", "Ruolo"]
        for col in text_columns:
            df[col] = df[col].astype(str).str.strip()

        # Convertire le colonne numeriche e gestire i NaN
        numeric_columns = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Convertire i non numerici in NaN
            df[col].fillna(0, inplace=True)  # Sostituire NaN con 0

        # Debug: Mostra i primi valori per verificare la correttezza del caricamento
        st.write("✅ Database caricato con successo! Esempio di dati:", df.head())

        return df.to_dict(orient='records')

    except Exception as e:
        st.error(f"❌ Errore nel caricamento del database: {e}")
        return None


def normalize_quotations(database, budget):
    """
    Normalizza le quotazioni in base al budget, mantenendo le proporzioni.
    """
    max_quot = max(player['Quotazione'] for player in database if player['Quotazione'] > 0)
    scale_factor = budget / max_quot if max_quot > 0 else 1
    for player in database:
        player['Quotazione'] = max(round(player['Quotazione'] * scale_factor, 2), 1)


def generate_team(database, budget=500, strategy="Equilibrata"):
    """
    Genera una rosa equilibrata rispettando il budget e la strategia scelta.
    """
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
        players = sorted(
            [p for p in database if p['Ruolo'].strip() == role and p['Quotazione'] > 0],
            key=lambda x: x['Fantamedia'],
            reverse=True
        )
        selected = []

        for player in players:
            if len(selected) < count and player['Quotazione'] <= remaining_budget:
                selected.append(player)
                remaining_budget -= player['Quotazione']

            if len(selected) >= count:
                break

        if len(selected) < count:
            st.warning(f"⚠️ Attenzione: non abbastanza giocatori per il ruolo {role}. Budget insufficiente.")
            return None, None

        team.extend(selected)

    total_cost = sum(p['Quotazione'] for p in team)
    return team, total_cost if total_cost <= budget else None


def export_to_csv(team):
    """
    Esporta la rosa generata in formato CSV.
    """
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')


# Web App con Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
st.markdown("### Scegli il tuo metodo di acquisto")

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
                st.write(f"{player['Ruolo']}: {player['Nome']} ({player['Squadra']}) - Costo: {player['Quotazione']:.2f} - Fantamedia: {player['Fantamedia']:.2f}")

            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Budget insufficiente.")
