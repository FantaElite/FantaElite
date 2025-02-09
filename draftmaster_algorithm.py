import streamlit as st
import pandas as pd
import random

# Carica il database Excel automaticamente
@st.cache
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')
        df.columns = df.columns.str.strip()  # Pulisce gli spazi nei nomi colonne
        
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

        # Controllo delle colonne essenziali
        expected_columns = list(column_mapping.values())
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV.")
            return None

        # Conversione dei dati numerici
        for col in ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ".", regex=True), errors="coerce")

        df["Quotazione"].fillna(1, inplace=True)  # Evita divisioni per zero

        return df.to_dict(orient='records')
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None


def normalize_quotations(database, budget):
    """
    Normalizza le quotazioni in modo che il massimo valore presente nel database
    sia equivalente al budget massimo, mantenendo le proporzioni relative.
    """
    max_quot = max(player['Quotazione'] for player in database if player['Quotazione'] > 0)
    if max_quot > 0:
        scale_factor = budget / max_quot
        for player in database:
            player['Quotazione'] = max(1, round(player['Quotazione'] * scale_factor, 2))  # Assicura un costo minimo di 1


def generate_team(database, budget=500, strategy="Equilibrata"):
    """
    Genera una squadra in base alla strategia scelta, evitando il loop infinito e
    garantendo un budget sempre rispettato.
    """
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }

    normalize_quotations(database, budget)  # Applica la riproporzione del budget

    team = []
    remaining_budget = budget

    for role, count in ROLES.items():
        players = [p for p in database if p['Ruolo'].strip() == role]

        if strategy == "Equilibrata":
            players = sorted(players, key=lambda x: x['Fantamedia'], reverse=True)
        elif strategy == "Top Player Oriented":
            players = sorted(players, key=lambda x: (x['Fantamedia'] * 1.5) - x['Quotazione'], reverse=True)
        elif strategy == "Squadra Diversificata":
            random.shuffle(players)
        elif strategy == "Modificatore di Difesa":
            if role == "Difensore":
                players = sorted(players, key=lambda x: x['Fantamedia'], reverse=True)
            else:
                random.shuffle(players)

        selected = []
        for player in players:
            if len(selected) < count and player['Quotazione'] <= remaining_budget:
                selected.append(player)
                remaining_budget -= player['Quotazione']

        if len(selected) < count:
            st.warning(f"⚠️ Budget troppo basso per selezionare abbastanza {role}.")
            return None, None

        team.extend(selected)

    total_cost = sum(p['Quotazione'] for p in team)
    return team, total_cost if total_cost <= budget else None


def export_to_csv(team):
    """
    Esporta la squadra in un file CSV scaricabile.
    """
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')


# Web App con Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
st.markdown("---\n### Scegli il tuo metodo di acquisto\n")

# Selezione tipo di pagamento
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (4 strategie)"])
budget = st.number_input("💰 Inserisci il budget", min_value=100, value=500, step=50)

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
                st.write(f"{player['Ruolo']}: {player['Nome']} ({player['Squadra']}) - Cost: {player['Quotazione']:.2f} - Fantamedia: {player['Fantamedia']:.2f}")

            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso per formare una rosa completa.")
