import streamlit as st
import pandas as pd
import os
import random
import io

# Carica il database Excel automaticamente
@st.cache_data  # Corretto in st.cache_data in Streamlit 1.12+
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
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV. Ecco le colonne trovate: {df.columns.tolist()}")
            return None

        # Converte le colonne numeriche e gestisce le virgole
        numeric_cols = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce")

        # Riempie i valori NaN in Quotazione con 0
        df["Quotazione"].fillna(0, inplace=True)

        # Se Fantamedia è presente ma Media Voto è NaN, assegna Media Voto = Fantamedia
        df.loc[df["Media_Voto"].isna() & df["Fantamedia"].notna(), "Media_Voto"] = df["Fantamedia"]

        # Validazione dei dati (esempio: controllo valori positivi per Quotazione)
        if not df["Quotazione"].ge(0).all():
            st.error("Errore: La colonna 'Quotazione' contiene valori negativi.")
            return None

        return df.to_dict(orient='records')
    except FileNotFoundError:
        st.error(f"Errore: File non trovato all'URL specificato: {url}")
        return None
    except pd.errors.ParserError:
        st.error("Errore: Errore nel parsing del file CSV. Controlla il formato.")
        return None
    except requests.exceptions.RequestException as e:  # Gestione errore di richiesta HTTP
        st.error(f"Errore nella richiesta del file CSV: {e}")
        return None
    except Exception as e:
        st.error(f"Errore generico nel caricamento del database: {e}")
        return None

def generate_team(database, budget=500, strategy="Equilibrata", max_attempts=10):  # Aggiunto limite tentativi
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
