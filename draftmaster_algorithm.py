import streamlit as st
import pandas as pd
import random

# Funzioni di caricamento e normalizzazione (rimangono invariate)
@st.cache_data
def load_database():
    # ... (codice caricamento database invariato)

def normalize_quotations(database, budget):
    # ... (codice normalizzazione invariato)

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
        if role in ["Centrocampista", "Difensore"]:
            count = 8
        elif role == "Attaccante":
            count = 6
        else:  # Portiere
            count = 3
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
    if strategy == "Casuale":
        return generate_random_team(database, budget)
    elif strategy == "Equilibrata":
        ROLES = ["Attaccante", "Centrocampista", "Difensore", "Portiere"]
        normalize_quotations(database, budget)
        team = []
        remaining_budget = budget

        for role in ROLES:
            if role in ["Centrocampista", "Difensore"]:
                count = 8
            elif role == "Attaccante":
                count = 6
            else:  # Portiere
                count = 3
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
    elif strategy == "Top Player Oriented":
        ROLES = ["Attaccante", "Centrocampista", "Difensore", "Portiere"]
        normalize_quotations(database, budget)
        team = []
        remaining_budget = budget

        for role in ROLES:
            if role in ["Centrocampista", "Difensore"]:
                count = 8
            elif role == "Attaccante":
                count = 6
            else:  # Portiere
                count = 3
            players = sorted([p for p in database if str(p['Ruolo']).strip() == role and p['Quotazione'] > 0],
                           key=lambda x: (x['Fantamedia'], random.random()), reverse=True)
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
    elif strategy == "Squadra Diversificata":
        ROLES = ["Attaccante", "Centrocampista", "Difensore", "Portiere"]
        normalize_quotations(database, budget)
        team = []
        remaining_budget = budget
        squadre_selezionate = set()

        for role in ROLES:
            if role in ["Centrocampista", "Difensore"]:
                count = 8
            elif role == "Attaccante":
                count = 6
            else:  # Portiere
                count = 3
            players = sorted([p for p in database if str(p['Ruolo']).strip() == role and p['Quotazione'] > 0],
                           key=lambda x: (x['Fantamedia'], random.random()), reverse=True)
            selected = []

            for player in players:
                if len(selected) < count and player['Quotazione'] <= remaining_budget and player['Squadra'] not in squadre_selezionate:
                    selected.append(player)
                    remaining_budget -= player['Quotazione']
                    squadre_selezionate.add(player['Squadra'])


            if len(selected) < count:
                st.warning(f"⚠️ Attenzione: non è stato possibile selezionare abbastanza giocatori per il ruolo {role}. Budget insufficiente o giocatori non disponibili.")
                return None, None

            team.extend(selected)

        total_cost = sum(p['Quotazione'] for p in team)
        if total_cost <= budget:
            return team, total_cost
        else:
            return None, None
    elif strategy == "Modificatore di Difesa":
        ROLES = ["Difensore", "Portiere", "Centrocampista", "Attaccante"]
        normalize_quotations(database, budget)
        team = []
        remaining_budget = budget

        for role in ROLES:
            if role in ["Centrocampista", "Difensore"]:
                count = 8
            elif role == "Attaccante":
                count = 6
            else:  # Portiere
                count = 3
            players = sorted([p for p in database if str(p['Ruolo']).strip() == role and p['Quotazione'] > 0],
                           key=lambda x: (x['Fantamedia'], random.random()), reverse=True)
            selected = []

            for player in players:
                if len(selected) < count and player['Quotazione'] <= remaining_budget:
                    selected.append(player)
                    remaining_budget -= player['Quotazione']

            if len(selected) < count:
                st.warning(f"⚠️