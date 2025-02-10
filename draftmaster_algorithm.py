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

def generate_random_team(database, budget=500):
    ROLES = ["Attaccante", "Centrocampista", "Difensore", "Portiere"]
    normalize_quotations(database, budget)
    team = []
    remaining_budget = budget

    for role in ROLES:
        count = 8 if role in ["Centrocampista", "Difensore"] else 6 if role == "Attaccante" else 3
        role_players = [p for p in database if str(p['Ruolo']).strip() == role and p['Quotazione'] > 0]
        selected = []

        # Genera combinazioni casuali di giocatori per il ruolo corrente
        for _ in range(100):  # Prova 100 combinazioni casuali
            random.shuffle(role_players)  # Mescola l'ordine dei giocatori
            current_selection = []
            current_budget = remaining_budget

            for player in role_players:
                if len(current_selection) < count and player['Quotazione'] <= current_budget:
                    current_selection.append(player)
                    current_budget -= player['Quotazione']

            if len(current_selection) == count:  # Trovata una combinazione valida
                selected = current_selection
                remaining_budget = current_budget
                break  # Esce dal ciclo di combinazioni casuali

        if len(selected) < count:
            st.warning(f"⚠️ Attenzione: non è stato possibile selezionare abbastanza giocatori per il ruolo {role}. Budget insufficiente o giocatori non disponibili.")
            return None, None

        team.extend(selected)

    total_cost = sum(p['Quotazione'] for p in team)
    if total_cost <= budget:
        return team, total_cost
    else:
        return None, None

def generate_team(database, budget=500, strategy="Equilibrata"):
    if strategy == "Casuale":  # Usa la nuova funzione per la strategia casuale
        return generate_random_team(database, budget)
    elif strategy == "Equilibrata":
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
                return None, None

            team.extend(selected)

        total_cost = sum(p['Quotazione'] for p in team)
        if total_cost <= budget:
            return team, total_cost
        else:
            return None, None
    elif strategy == "Top Player Oriented":  # Esempio: "Top Player Oriented" strategy
        ROLES = ["Attaccante", "Centrocampista", "Difensore", "Portiere"]
        normalize_quotations(database, budget)
        team = []
        remaining_budget = budget

        # Ordina per Fantamedia, poi randomizza tra i migliori giocatori
        for role in ROLES:
            count = 8 if role in ["Centrocampista", "Difensore"] else 6 if role == "Attaccante" else 3
            players = sorted([p for p in database if str(p['Ruolo']).strip() == role and p['Quotazione'] > 0],
                           key=lambda x: (x['Fantamedia'], random.random()), reverse=True)  # Aggiungi random.random()
            selected = []

            for player in players:
                if len(selected) < count and player['Quotazione'] <= remaining_budget:
                    selected.append(player)
                    remaining_budget -= player['Quotazione']

            if len(selected) < count:
                st.warning(f"⚠️ Attenzione: non è stato possibile selezionare abbastanza giocatori per il ruolo {role}. Budget insufficiente o giocatori non disponibili.")
                return None, None

            team.extend(selected)

        total_cost = sum(p['Quotazione'] for p in team)
        if total_cost <= budget:
            return team, total_cost
        else:
            return None, None
    elif strategy == "Squadra Diversificata":  # Esempio: "Squadra Diversificata" strategy
        ROLES = ["Attaccante", "Centrocampista", "Difensore", "Portiere"]
        normalize_quotations(database, budget)
        team = []
        remaining_budget = budget
        squadre_selezionate = set()  # Set per tenere traccia delle squadre già selezionate

        for role in ROLES:
            count = 8 if role in ["Centrocampista", "Difensore"] else 6 if role ==