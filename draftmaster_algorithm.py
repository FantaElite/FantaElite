import streamlit as st
import pandas as pd
import random

# 🔴 Forza il reset della cache per evitare problemi di memoria 🔴
st.cache_data.clear()

# 🔹 Caricamento database con pulizia dati
@st.cache_data
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';')
        
        # 🔸 Rimuove eventuali spazi nei nomi delle colonne
        df.columns = df.columns.str.strip()
        
        # 🔸 Rinomina le colonne per assicurare coerenza
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

        # 🔹 Controllo che tutte le colonne attese siano presenti
        expected_columns = list(column_mapping.values())
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Errore: Mancano le colonne {missing_columns} nel file CSV. Ecco le colonne trovate: {df.columns.tolist()}")
            return None

        # 🔸 Forza "Ruolo" a essere sempre stringa
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip()

        # 🔹 Convertiamo i numeri da stringa con virgola a float con punto decimale
        numeric_columns = ["Quotazione", "Fantamedia", "Media_Voto", "Partite_Voto"]
        for col in numeric_columns:
            df[col] = df[col].astype(str).str.replace(",", ".")  # Converte eventuali virgole in punti
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Converte i valori in numerici

        # 🔹 Riempie eventuali NaN nei numeri
        df.fillna({"Quotazione": df["Quotazione"].mean(), "Fantamedia": 0, "Media_Voto": 0, "Partite_Voto": 0}, inplace=True)

        # 🔹 Verifica che il caricamento sia corretto
        st.write("📌 Anteprima Database Caricato:", df.head())

        return df.to_dict(orient='records')
    
    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

# 🔹 Funzione per proporzionare le quotazioni in base al budget selezionato
def normalize_quotations(database, budget):
    max_quot = max(player['Quotazione'] for player in database if player['Quotazione'] > 0)
    scale_factor = budget / max_quot if max_quot > 0 else 1
    for player in database:
        player['Quotazione'] = max(round(player['Quotazione'] * scale_factor, 2), 1)  # Assicura che nessun giocatore abbia quota 0

# 🔹 Funzione per generare la squadra in base al budget e alla strategia scelta
def generate_team(database, budget=500, strategy="Equilibrata"):
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }

    # 🔹 Proporziona le quotazioni in base al budget
    normalize_quotations(database, budget)
    
    team = []
    remaining_budget = budget
    
    for role, count in ROLES.items():
        players = sorted(
            [p for p in database if p['Ruolo'].strip() == role and p['Quotazione'] > 0], 
            key=lambda x: x['Fantamedia'], reverse=True
        )
        selected = []
        
        for player in players:
            if len(selected) < count and player['Quotazione'] <= remaining_budget:
                selected.append(player)
                remaining_budget -= player['Quotazione']
                
            if len(selected) >= count:
                break
        
        if len(selected) < count:
            st.warning(f"⚠️ Non è stato possibile selezionare abbastanza giocatori per il ruolo {role}. Budget insufficiente.")
            return None, None
        
        team.extend(selected)
    
    total_cost = sum(p['Quotazione'] for p in team)
    return team, total_cost if total_cost <= budget else None

# 🔹 Esporta la squadra in CSV
def export_to_csv(team):
    df = pd.DataFrame(team)
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')

# 🔹 UI con Streamlit
st.title("⚽ FantaElite - Generatore di Rose Fantacalcio ⚽")
st.markdown("""---
### Scegli il tuo metodo di acquisto
""")

# 🔹 Selezione tipo di pagamento
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (4 strategie)"])

# 🔹 Selezione del budget
budget = st.number_input("💰 Inserisci il budget", min_value=1, value=500, step=1)

# 🔹 Scelta della strategia
strategies = ["Equilibrata", "Top Player Oriented", "Squadra Diversificata", "Modificatore di Difesa"]
if payment_type == "One Shot (1 strategia)":
    strategy = st.selectbox("🎯 Seleziona la strategia di generazione", strategies)
    strategy_list = [strategy]
else:
    strategy_list = strategies

# 🔹 Caricamento database
database = load_database()
if database is None:
    st.stop()

# 🔹 Pulsante per generare la squadra
if st.button("🛠️ Genera Squadra"):
    for strategy in strategy_list:
        team, total_cost = generate_team(database, budget, strategy)
        if team:
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost:.2f}")
            st.write("### Squadra generata:")
            for player in team:
                st.write(f"{player['Ruolo']}: {player['Nome']} ({player['Squadra']}) - Cost: {player['Quotazione']:.2f} - Fantamedia: {player['Fantamedia']:.2f} - Media Voto: {player['Media_Voto']:.2f} - Presenze: {player['Partite_Voto']}")
            
            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso per formare una rosa completa.")
