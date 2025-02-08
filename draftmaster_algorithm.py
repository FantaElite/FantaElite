import streamlit as st
import pandas as pd
import os
import random

# Carica il database Excel automaticamente
@st.cache
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')
        
        # Rimuove eventuali spazi prima e dopo i nomi delle colonne
        df.columns = df.columns.str.strip()
        
        # Mappa i nomi corretti senza modificare il testo originale
        expected_columns = [
            "Nome", "Squadra", "Ruolo", "Media Voto", "Fantamedia", "Quotazione", "Partite a Voto"
        ]
        
        # Controllo colonne mancanti con debug
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV. Ecco le colonne trovate: {df.columns.tolist()}")
            return None

        # Converti le colonne numeriche correggendo eventuali virgole nei decimali
        df["Quotazione"] = pd.to_numeric(df["Quotazione"].str.replace(",", "."), errors="coerce")
        df["Fantamedia"] = pd.to_numeric(df["Fantamedia"].str.replace(",", "."), errors="coerce")
        df["Media Voto"] = pd.to_numeric(df["Media Voto"].str.replace(",", "."), errors="coerce")
        df["Partite a Voto"] = pd.to_numeric(df["Partite a Voto"].str.replace(",", "."), errors="coerce")

        # Riempie solo i valori NaN in Quotazione con 0 per evitare problemi di visualizzazione
        df["Quotazione"].fillna(0, inplace=True)

        # Se Fantamedia è presente ma Media Voto è NaN, assegna Media Voto = Fantamedia
        df.loc[df["Media Voto"].isna() & df["Fantamedia"].notna(), "Media Voto"] = df["Fantamedia"]

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
        players = [p for p in database if p['Ruolo'] == role]
        if not players:
            st.error(f"Errore: Nessun giocatore disponibile per il ruolo {role}")
            return None, None

        # Considerazione delle presenze per determinare la titolarità
        for p in players:
            if 'Partite a Voto' not in p or pd.isna(p['Partite a Voto']):
                p['Partite a Voto'] = 0  # Default a 0 se mancante
        
        # Applicazione della strategia
        if strategy == "Top Player Oriented":
            players = sorted(players, key=lambda x: (x['Fantamedia'], x['Media Voto'], x['Partite a Voto']), reverse=True)
        elif strategy == "Squadra Diversificata":
            team_squadre = set([p['Squadra'] for p in team])
            players = [p for p in players if p['Squadra'] not in team_squadre]
        elif strategy == "Modificatore di Difesa":
            if role in ["Portiere", "Difensore"]:
                players = sorted(players, key=lambda x: (x['Media Voto'], x['Fantamedia'], x['Partite a Voto']), reverse=True)
            else:
                players = sorted(players, key=lambda x: (x['Fantamedia'], x['Partite a Voto']), reverse=True)
        else:  # Equilibrata
            players = sorted(players, key=lambda x: (x['Fantamedia'], x['Partite a Voto']), reverse=True)
        
        try:
            selected = random.sample(players[:20], count)  # Assicura varietà
        except ValueError as e:
            st.error(f"Errore nella selezione dei giocatori per {role}: {e}")
            return None, None

        team.extend(selected)
        total_cost += sum(player['Quotazione'] for player in selected if isinstance(player['Quotazione'], (int, float)))
    
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
            st.write(f"{player['Ruolo']}: {player['Nome']} ({player['Squadra']}) - Cost: {player['Quotazione']} - Fantamedia: {player['Fantamedia']:.2f} - Media Voto: {player['Media Voto']:.2f} - Presenze: {player['Partite a Voto']}")
        
        csv_data = export_to_csv(team)
        st.download_button("Scarica CSV", csv_data, file_name="squadra_fantacalcio.csv", mime="text/csv")