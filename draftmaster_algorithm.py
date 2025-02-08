import streamlit as st
import pandas as pd
import os
import random

# Carica il database Excel automaticamente
@st.cache
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';', dtype=str).apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        
        # Mappa i nomi corretti
        column_map = {
            "Nome": "name",
            "Squadra": "team",
            "Ruolo": "role",
            "Media Voto": "media_voto",
            "Fantamedia": "fantamedia",
            "Quotazione": "cost",
            "Partite a Voto": "appearances"
        }
        
        df = df.rename(columns=lambda x: column_map.get(x, x))

        # Converti cost, media_voto, fantamedia e presenze in numeri correggendo eventuali virgole nei decimali
        df["cost"] = pd.to_numeric(df["cost"].str.replace(",", "."), errors="coerce")
        df["fantamedia"] = pd.to_numeric(df["fantamedia"].str.replace(",", "."), errors="coerce")
        df["media_voto"] = pd.to_numeric(df["media_voto"].str.replace(",", "."), errors="coerce")
        df["appearances"] = pd.to_numeric(df["appearances"].str.replace(",", "."), errors="coerce")

        # Riempie solo i valori NaN in cost con 0 per evitare problemi di visualizzazione
        df["cost"].fillna(0, inplace=True)

        # Se fantamedia è presente ma media voto è NaN, assegna media_voto = fantamedia
        df.loc[df["media_voto"].isna() & df["fantamedia"].notna(), "media_voto"] = df["fantamedia"]

        # Controllo colonne mancanti
        missing_columns = [col for col in column_map.values() if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV. Controlla il file e riprova.")
            return None

        return df.to_dict(orient='records')
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

def generate_team(database, budget=500, strategy="Equilibrata"):
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

        # Considerazione delle presenze per determinare la titolarità
        for p in players:
            if 'appearances' not in p or pd.isna(p['appearances']):
                p['appearances'] = 0  # Default a 0 se mancante
        
        # Applicazione della strategia
        if strategy == "Top Player Oriented":
            players = sorted(players, key=lambda x: (x['fantamedia'], x['media_voto'], x['appearances']), reverse=True)
        elif strategy == "Squadra Diversificata":
            team_squadre = set([p['team'] for p in team])
            players = [p for p in players if p['team'] not in team_squadre]
        elif strategy == "Modificatore di Difesa":
            if role in ["Portiere", "Difensore"]:
                players = sorted(players, key=lambda x: (x['media_voto'], x['fantamedia'], x['appearances']), reverse=True)
            else:
                players = sorted(players, key=lambda x: (x['fantamedia'], x['appearances']), reverse=True)
        else:  # Equilibrata
            players = sorted(players, key=lambda x: (x['fantamedia'], x['appearances']), reverse=True)
        
        try:
            selected = random.sample(players[:20], count)  # Assicura varietà
        except ValueError as e:
            st.error(f"Errore nella selezione dei giocatori per {role}: {e}")
            return None, None

        team.extend(selected)
        total_cost += sum(player['cost'] for player in selected if isinstance(player['cost'], (int, float)))
    
    if total_cost > budget:
        st.warning(f"Sforato il budget ({total_cost} > {budget}), rigenerando...")
        return generate_team(database, budget, strategy)  # Riprova se sfora il budget
    
    return team, total_cost

def export_to_csv(team):
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')

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
            st.write(f"{player['role']}: {player['name']} ({player['team']}) - Cost: {player['cost']} - Fantamedia: {player['fantamedia']:.2f} - Media Voto: {player['media_voto']:.2f} - Presenze: {player['appearances']}")
        
        csv_data = export_to_csv(team)
        st.download_button("Scarica CSV", csv_data, file_name="squadra_fantacalcio.csv", mime="text/csv")