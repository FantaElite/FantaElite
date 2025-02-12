import streamlit as st
import pandas as pd
import os
import random

# Carica il database Excel automaticamente
@st.cache_data(ttl=0)
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
            "Ruolo_Mantra": "Ruolo_Mantra",
            "Media_Voto": "Media_Voto",
            "Fantamedia": "Fantamedia",
            "Quotazione": "Quota_Percentuale",
            "Partite_Voto": "Partite_Voto"
        }
        
        df.rename(columns=column_mapping, inplace=True)
        
        # Controllo colonne mancanti
        expected_columns = list(column_mapping.values())
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV. Ecco le colonne trovate: {df.columns.tolist()}")
            return None

        # Converti le colonne numeriche correggendo eventuali errori
        numeric_columns = ["Quota_Percentuale", "Fantamedia", "Media_Voto", "Partite_Voto"]
        
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Converte i valori non numerici in NaN
        
        # Riempie solo i valori NaN con la media delle quotazioni esistenti
        df["Quota_Percentuale"].fillna(df["Quota_Percentuale"].mean(), inplace=True)
        
        # Assicura che la colonna "Ruolo" e "Ruolo_Mantra" siano trattate come stringa senza NaN
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip().fillna("Sconosciuto")
        df["Ruolo_Mantra"] = df["Ruolo_Mantra"].astype(str).str.strip().fillna("Sconosciuto")
        
        return df.to_dict(orient='records')
    
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

def generate_team(database, strategy="Equilibrata", mode="Classic"):
    target_budget_min = 95
    target_budget_max = 100
    
    if mode == "Classic":
        ROLES = {
            "Portiere": 3,
            "Difensore": 8,
            "Centrocampista": 8,
            "Attaccante": 6
        }
    else:
        ROLES = {
            "Por": 3, "Dc": 4, "Dd": 2, "Ds": 2, "M": 2, "C": 4,
            "T": 2, "E": 2, "A": 2, "Pc": 2
        }
    
    attempts = 0
    max_attempts = 100
    best_team = None
    best_cost = 0
    
    while attempts < max_attempts:
        selected_team = []
        total_cost_percentage = 0
        
        for role, count in ROLES.items():
            players = sorted(
                [p for p in database if (role in str(p['Ruolo']).split(';') if mode == "Classic" else role in str(p['Ruolo_Mantra']).split(';')) and p['Quota_Percentuale'] > 0],
                key=lambda x: (x['Quota_Percentuale'] * 0.4 + x['Partite_Voto'] * 0.3 + x['Fantamedia'] * 0.3),
                reverse=True
            )
            
            if not players or len(players) < count:
                break  # Se non ci sono abbastanza giocatori, si interrompe
            
            selected = random.sample(players[:count * 3], count)
            
            selected_team.extend(selected)
            total_cost_percentage += sum(p['Quota_Percentuale'] for p in selected)
        
        if target_budget_min <= total_cost_percentage <= target_budget_max and len(selected_team) == sum(ROLES.values()):
            return selected_team, total_cost_percentage
        
        if total_cost_percentage > best_cost and len(selected_team) == sum(ROLES.values()):
            best_team = selected_team
            best_cost = total_cost_percentage
        
        attempts += 1
    
    return best_team, best_cost

def export_to_csv(team):
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')

# Web App con Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
st.markdown("""---
### Scegli il tuo metodo di acquisto
""")

# Selezione modalità di gioco
mode = st.selectbox("⚙️ Seleziona la modalità di gioco", ["Classic", "Mantra"])

# Selezione tipo di pagamento
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (3 strategie)"])

# Selezione strategia di generazione
strategies = ["Equilibrata", "Top Player Oriented", "Modificatore di Difesa"]

if payment_type == "One Shot (1 strategia)":
    strategy = st.selectbox("🎯 Seleziona la strategia di generazione", strategies)
    strategy_list = [strategy]
else:
    strategy_list = strategies

database = load_database()
if database is None:
    st.stop()

if st.button("🛠️ Genera Squadra"):
    for strategy in strategy_list:
        team, total_cost_percentage = generate_team(database, strategy, mode)
        if team and target_budget_min <= total_cost_percentage <= target_budget_max and len(team) == sum(ROLES.values()):
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost_percentage:.2f}% del budget")
            st.write("### Squadra generata:")
            st.write(pd.DataFrame(team))
            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo alto o troppo basso per formare una rosa completa.")
