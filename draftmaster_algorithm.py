import streamlit as st
import pandas as pd
import io
import requests
import random

@st.cache_data
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')

        # 1. Pulizia dei nomi delle colonne
        df.columns = df.columns.str.strip()

        # 2. Mappatura delle colonne (assicura la coerenza)
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

        # 3. Conversione FORZATA al tipo stringa (per le colonne testuali)
        for col in ["Nome", "Squadra", "Ruolo"]:
            if col in df.columns:
                df[col] = df[col].astype(str)

        # 4. Conversione FORZATA al tipo numerico (con gestione errori)
        for col in ["Media_Voto", "Fantamedia", "Quotazione", "Partite_Voto"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors='coerce')

        # 5. Gestione dei valori mancanti (NaN)
        df["Quotazione"].fillna(0, inplace=True)
        df.loc[df["Media_Voto"].isna() & df["Fantamedia"].notna(), "Media_Voto"] = df["Fantamedia"]

        # 6. Validazione dei dati (controllo valori positivi)
        if "Quotazione" in df.columns and not df["Quotazione"].ge(0).all():
            st.error("Errore: La colonna 'Quotazione' contiene valori negativi.")
            return None

        return df.to_dict(orient='records')

    except FileNotFoundError:
        st.error(f"Errore: File non trovato all'URL specificato.")
        return None
    except pd.errors.ParserError:
        st.error("Errore: Errore nel parsing del file CSV. Controlla il formato.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Errore nella richiesta del file CSV: {e}")
        return None
    except Exception as e:
        st.error(f"Errore generico nel caricamento del database: {e}")
        return None

def generate_team(database, budget=500, strategy="Equilibrata", max_attempts=10):
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }

    team = []
    total_cost = 0
    attempts = 0

    for role, count in ROLES.items():
        players = [p for p in database if p['Ruolo'] == role]
        if not players:
            st.error(f"Errore: Nessun giocatore disponibile per il ruolo {role}")
            return None, None

        # Considerazione delle presenze per determinare la titolarità
        for p in players:
            if 'Partite_Voto' not in p or pd.isna(p['Partite_Voto']):
                p['Partite_Voto'] = 0  # Default a 0 se mancante

        # Ordinamento giocatori per strategia
        players = sort_players(players, strategy, role)

        # Mescola i giocatori prima della selezione per garantire varietà
        random.shuffle(players)

        try:
            selected = random.sample(players[:20], count)  # Assicura varietà
        except ValueError as e:
            st.error(f"Errore nella selezione dei giocatori per {role}: {e}. Sono disponibili {len(players)} giocatori.")
            return None, None

        team.extend(selected)
        total_cost += sum(player['Quotazione'] for player in selected if isinstance(player['Quotazione'], (int, float)))

    while total_cost > budget and attempts < max_attempts:  # Loop con limite di tentativi
        st.warning(f"Sforato il budget ({total_cost} > {budget}), rigenerando (tentativo {attempts + 1}/{max_attempts})...")
        team, total_cost = generate_team(database, budget, strategy, max_attempts) # Richiama se stesso con il nuovo team
        attempts +=1

    if total_cost > budget:
        st.error(f"Impossibile generare una squadra con budget di {budget} dopo {max_attempts} tentativi.")
        return None, None

    return team, total_cost

def sort_players(players, strategy, role):
    if strategy == "Top Player Oriented":
        return sorted(players, key=lambda x: (x['Fantamedia'], x['Media_Voto'], x['Partite_Voto']), reverse=True)
    elif strategy == "Squadra Diversificata":
        # Implementa la logica per diversificare le squadre (da implementare)
        return sorted(players, key=lambda x: (x['Fantamedia'], x['Partite_Voto']), reverse=True) # Ordine di default
    elif strategy == "Modificatore di Difesa":
        if role in ["Portiere", "Difensore"]:
            return sorted(players, key=lambda x: (x['Media_Voto'], x['Fantamedia'], x['Partite_Voto']), reverse=True)
        else:
            return sorted(players, key=lambda x: (x['Fantamedia'], x['Partite_Voto']), reverse=True)
    else:  # Equilibrata
        return sorted(players, key=lambda x: (x['Fantamedia'], x['Partite_Voto']), reverse=True)

def export_to_csv(team):
    df = pd.DataFrame(team)
    csv_file = io.StringIO()  # Usa StringIO per evitare di scrivere su disco
    df.to_csv(csv_file, index=False, sep=';', decimal=',', encoding='utf-8')
    csv_data = csv_file.getvalue().encode('utf-8')  # Ottieni i dati dal buffer
    return csv_data

# Web App con Streamlit
st.title("FantaElite - Generatore di Rose Fantacalcio")

database = load_database()
if database is None:
    st.stop()

budget = st.number_input("Inserisci il budget", min_value=100, max_value=1000, value=500, step=10)

# Menu a tendina per selezionare la strategia
strategy = st.selectbox("Seleziona la strategia di generazione", ["Equilibrata", "Top Player Oriented", "Squadra Diversificata", "Modificatore di Difesa"])

if st.button("Genera Squadra"):
    team, total_cost = generate_team(database, budget, strategy)

    if team is None:
        st.error("Errore nella generazione della squadra.")
    else:
        st.success(f"Squadra generata con successo! Costo totale: {total_cost}")
        for player in team:
            st.write(f"{player['Ruolo']}: {player['Nome']} ({player['Squadra']}) - Cost: {player['Quotazione']} - Fantamedia: {player['Fantamedia']:.2f} - Media Voto: {player['Media_Voto']:.2f} - Presenze: {player['Partite_Voto']}")

        csv_data = export_to_csv(team)
        st.download_button("Scarica CSV", csv_data, file_name="squadra_fantacalcio.csv", mime="text/csv")