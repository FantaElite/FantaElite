import streamlit as st
import pandas as pd
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

        # Riempie solo i valori NaN con la media delle quotazioni esistenti
        df["Quotazione"].fillna(df["Quotazione"].mean(), inplace=True)

        # Assicura che la colonna "Ruolo" sia trattata come stringa senza NaN
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip().fillna("Sconosciuto")

        return df.to_dict(orient='records')

    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

def normalize_quotations(database, budget):
    for player in database:
        original_quotazione = player['Quotazione']
        player['Quotazione'] = max(round(original_quotazione * (budget / 500), 2), 1)

def calculate_player_score(player):
    fantamedia_weight = 0.5
    media_voto_weight = 0.3
    partite_voto_weight = 0.2
    return (player['Fantamedia'] * fantamedia_weight + 
            player['Media_Voto'] * media_voto_weight + 
            player['Partite_Voto'] * partite_voto_weight)

def generate_team(database, budget=500, strategy="Equilibrata"):
    ROLES = ["Attaccante", "Centrocampista", "Difensore", "Portiere"]  # Ordine di priorità

    normalize_quotations(database, budget)
    team = []
    remaining_budget = budget

    for role in ROLES:
        count = 8 if role in ["Centrocampista", "Difensore"] else 6 if role == "Attaccante" else 3
        players = sorted([p for p in database if str(p['Ruolo']).strip() == role and p['Quotazione'] > 0], 
                       key=calculate_player_score, reverse=True)
        selected = []

        for _ in range(count):
            eligible_players = [p for p in players if p['Quotazione'] <= remaining_budget]
            if not eligible_players:
                break

            scored_players = sorted(eligible_players, key=lambda x: (calculate_player_score(x), random.random()), reverse=True)
            if scored_players:
                selected_player = scored_players[0]
                selected.append(selected_player)
                remaining_budget -= selected_player['Quotazione']
                players.remove(selected_player)

        if len(selected) < count:
            st.warning(f"⚠️ Attenzione: non è stato possibile selezionare abbastanza giocatori per il ruolo {role}. Budget insufficiente o giocatori non disponibili.")
            st.write(f"Giocatori trovati: {len(selected)}, necessari: {count}")
            return None, None

        team.extend(selected)

    total_cost = sum(p['Quotazione'] for p in team)
    if total_cost <= budget:
        return team, total_cost
    else:
        return None, None

def export_to_csv(team):
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')

# Web App con Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
st.markdown("""---
### Scegli il tuo metodo di acquisto
""")

# Selezione tipo di pagamento
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (4 strategie)"])

budget = st.number_input(" Inserisci il budget", min_value=100, value=500, step=1)  # Budget da 100 in su

# Selezione strategia di generazione
strategies = ["Equilibrata", "Top Player Oriented", "Squadra Diversificata", "Modificatore di Difesa"]

if payment_type == "One Shot (1 strategia)":
    strategy = st.selectbox(" Seleziona la strategia di generazione", strategies)
    strategy_list = [strategy]
else:
    strategy_list = strategies

database = load_database()
if database is None:
    st.stop()

if st.button("️ Genera Squadra"):
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
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso o non ci sono abbastanza giocatori disponibili.")