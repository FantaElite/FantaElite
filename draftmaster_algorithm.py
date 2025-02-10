import streamlit as st
import pandas as pd

# Carica il database Excel automaticamente
@st.cache_data
def load_database():
    # ... (codice caricamento database invariato)

def normalize_quotations(database, budget):
    # ... (codice normalizzazione quotazioni invariato)

def calculate_player_score(player):
    # Esempio di funzione che combina Fantamedia, Media Voto e Partite_Voto
    # Puoi aggiungere altri fattori e personalizzare i pesi
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

        for player in players:
            if len(selected) < count and player['Quotazione'] <= remaining_budget:
                selected.append(player)
                remaining_budget -= player['Quotazione']

            if len(selected) >= count:
                break

        if len(selected) < count:
            st.warning(f"⚠️ Attenzione: trovati solo {len(selected)} giocatori per il ruolo {role} (ne servono {count}). Verifica il budget o i giocatori disponibili.")
            return None, None

        team.extend(selected)

    total_cost = sum(p['Quotazione'] for p in team)
    return team, total_cost if total_cost <= budget else None

def export_to_csv(team):
    # ... (codice esportazione CSV invariato)

# Web App con Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
# ... (codice interfaccia Streamlit invariato)

if st.button("️ Genera Squadra"):
    for strategy in strategy_list:
        team, total_cost = generate_team(database, budget, strategy)
        if team:
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost:.2f}")
            # ... (codice visualizzazione squadra e download CSV invariato)
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso o non ci sono abbastanza giocatori disponibili.")