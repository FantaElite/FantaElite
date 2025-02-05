import streamlit as st
import pandas as pd
import os
import random

# Carica il database Excel automaticamente
@st.cache
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio.csv"  # Cambia con il tuo link
    df = pd.read_csv(url, encoding="utf-8", errors="replace")
    return df.to_dict(orient='records')

def generate_team(database, budget=500):
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }
    
    team = []
    total_cost = 0
    
    for role, count in ROLES.items():
        players = [p for p in database if p['role'] == role]
        if not players:
            st.error(f"Errore: Nessun giocatore disponibile per il ruolo {role}")
            return None, None

        players = sorted(players, key=lambda x: x['fantamedia'], reverse=True)
        try:
            selected = random.sample(players[:20], count)  # Assicura varietà
        except ValueError as e:
            st.error(f"Errore nella selezione dei giocatori per {role}: {e}")
            return None, None

        team.extend(selected)
        total_cost += sum(player['cost'] for player in selected)
    
    if total_cost > budget:
        st.warning(f"Sforato il budget ({total_cost} > {budget}), rigenerando...")
        return generate_team(database, budget)  # Riprova se sfora il budget
    
    return team, total_cost

def export_to_csv(team):
    df = pd.DataFrame(team)
    return df.to_csv(index=False).encode('utf-8')

# Web App con Streamlit
st.title("FantaElite - Generatore di Rose Fantacalcio")

database = load_database()
if database is None:
    st.stop()

budget = st.number_input("Inserisci il budget", min_value=100, max_value=1000, value=500, step=10)

if st.button("Genera Squadra"):
    team, total_cost = generate_team(database, budget)
    
    if team is None:
        st.error("Errore nella generazione della squadra.")
    else:
        st.success(f"Squadra generata con successo! Costo totale: {total_cost}")
        for player in team:
            st.write(f"{player['role']}: {player['name']} ({player['team']}) - Cost: {player['cost']} - Fantamedia: {player['fantamedia']:.2f}")
        
        csv_data = export_to_csv(team)
        st.download_button("Scarica CSV", csv_data, file_name="squadra_fantacalcio.csv", mime="text/csv")