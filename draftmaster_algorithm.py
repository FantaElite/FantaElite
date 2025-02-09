import streamlit as st
import pandas as pd
import os
import random

# Carica il database Excel automaticamente
@st.cache
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

        # Assicura che tutte le colonne siano stringhe prima di operare su di esse
        df = df.astype(str)
        
        # Converti le colonne numeriche correggendo eventuali virgole nei decimali
        df["Quotazione"] = pd.to_numeric(df["Quotazione"].str.replace(",", ".", regex=True), errors="coerce")
        df["Fantamedia"] = pd.to_numeric(df["Fantamedia"].str.replace(",", ".", regex=True), errors="coerce")
        df["Media_Voto"] = pd.to_numeric(df["Media_Voto"].str.replace(",", ".", regex=True), errors="coerce")
        df["Partite_Voto"] = pd.to_numeric(df["Partite_Voto"].str.replace(",", ".", regex=True), errors="coerce")

        # Riempie solo i valori NaN in Quotazione con 0 per evitare problemi di visualizzazione
        df["Quotazione"].fillna(0, inplace=True)

        # Se Fantamedia è presente ma Media Voto è NaN, assegna Media Voto = Fantamedia
        df.loc[df["Media_Voto"].isna() & df["Fantamedia"].notna(), "Media_Voto"] = df["Fantamedia"]
        
        return df.to_dict(orient='records')
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

def generate_team(database, budget=500, strategy="Equilibrata"):
    # Calcola il rapporto percentuale tra il budget dell'utente e il valore massimo del mercato
    max_total_cost = sum(player['Quotazione'] for player in database if isinstance(player['Quotazione'], (int, float)))
    budget_ratio = budget / max_total_cost if max_total_cost > 0 else 1

    # Adatta le quotazioni dei giocatori in base al budget scelto
    for player in database:
        if isinstance(player['Quotazione'], (int, float)):
            player['Quotazione'] = round(player['Quotazione'] * budget_ratio, 1)
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }
    
    team = []
    total_cost = 0
    
    for role, count in ROLES.items():
        players = [p for p in database if p['Ruolo'].strip() == role]
        if not players:
            st.error(f"Errore: Nessun giocatore disponibile per il ruolo {role}")
            return None, None

        # Considerazione delle presenze per determinare la titolarità
        for p in players:
            if 'Partite_Voto' not in p or pd.isna(p['Partite_Voto']):
                p['Partite_Voto'] = 0  # Default a 0 se mancante
        
        # Ordinamento in base alla strategia scelta
        players = sorted(players, key=lambda x: (x['Fantamedia'], x['Media_Voto'], x['Partite_Voto']), reverse=True)
        
        try:
            selected = random.sample(players[:50], count)  # Assicura varietà
        except ValueError as e:
            st.error(f"Errore nella selezione dei giocatori per {role}: {e}")
            return None, None

        team.extend(selected)
        total_cost += sum(player['Quotazione'] for player in selected if isinstance(player['Quotazione'], (int, float)))
    
    if total_cost > budget:
        st.warning(f"Sforato il budget ({total_cost} > {budget}), rigenerando...")
        return generate_team(database, budget, strategy)
    
    return team, total_cost

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

budget = st.number_input("💰 Inserisci il budget", min_value=1, value=500, step=1)

# Selezione strategia di generazione
strategies = ["Equilibrata", "Top Player Oriented", "Squadra Diversificata", "Modificatore di Difesa"]

if payment_type == "One Shot (1 strategia)":
    strategy = st.selectbox("🎯 Seleziona la strategia di generazione", strategies)
    strategy_list = [strategy]
else:
    strategy_list = strategies  # Se è "Complete", genera tutte le strategie

database = load_database()
if database is None:
    st.stop()

if st.button("🛠️ Genera Squadra"):
    for strategy in strategy_list:
        team, total_cost = generate_team(database, budget, strategy)
        if team:
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost}")
            for player in team:
                st.write(f"{player['Ruolo']}: {player['Nome']} ({player['Squadra']}) - Cost: {player['Quotazione']} - Fantamedia: {player['Fantamedia']:.2f} - Media Voto: {player['Media_Voto']:.2f} - Presenze: {player['Partite_Voto']}")
            
            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}).")
