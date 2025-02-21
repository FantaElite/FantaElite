import streamlit as st
import pandas as pd
import random
import io
import zipfile
import cProfile

# Funzioni di caricamento e normalizzazione (rimangono invariate, ma usa pandas)
@st.cache_data
def load_database():
    url = "https://raw.githubusercontent.com/FantaElite/FantaElite/main/database_fantacalcio_v2.csv"
    try:
        df = pd.read_csv(url, encoding="utf-8", delimiter=';', dtype={
            "Nome": str,
            "Squadra": str,
            "Ruolo": str,
            "Media_Voto": float,
            "Fantamedia": float,
            "Quotazione": float,
            "Partite_Voto": int
        })  # Specifica i tipi di dato

        # Rimuove eventuali spazi prima e dopo i nomi delle colonne
        df.columns = df.columns.str.strip()

        # Mappa i nuovi nomi delle colonne corretti
        column_mapping = {
            "Nome": "Nome",
            "Squadra": "Squadra",
            "Ruolo": "Ruolo",
            "Media_Voto": "Media_Voto",
            "Fantamedia": "Fantamedia",
            "Quotazione": "Quota_Percentuale",
            "Partite_Voto": "Partite_Voto"
        }

        df.rename(columns=column_mapping, inplace=True)

        # Riempie solo i valori NaN con la media delle quotazioni esistenti
        df["Quota_Percentuale"].fillna(df["Quota_Percentuale"].mean(), inplace=True)

        # Convertiamo la quotazione in percentuale rispetto a un budget di 500 crediti
        df["Quota_Percentuale"] = (df["Quota_Percentuale"] / 500.0) * 100  # Converte in percentuale

        return df

    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None


def export_to_csv(team):
    df = pd.DataFrame(team).reset_index(drop=True)
    csv_data = df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8')  # Codifica la stringa CSV
    return csv_data.encode('utf-8') #Codifica per download

BUDGET_PERCENTAGES = {
    "Equilibrata": {
        "Portiere": 0.07,
        "Difensore": 0.13,
        "Centrocampista": 0.25,
        "Attaccante": 0.55
    },
    "Modificatore di Difesa": {
        "Portiere": 0.09,
        "Difensore": 0.21,
        "Centrocampista": 0.23,
        "Attaccante": 0.47
    }
}

def valuta_giocatore(giocatore):
    quotazione = giocatore['Quota_Percentuale']
    partite_voto = giocatore['Partite_Voto']
    media_voto = giocatore['Media_Voto']
    fanta_media = giocatore['Fantamedia']

    if partite_voto == 0 and media_voto == 0 and fanta_media == 0:
        # Caso giocatore nuovo: valutazione basata principalmente sulla quotazione
        valutazione = quotazione * 4.5  # Puoi sperimentare con questo moltiplicatore
    else:
        # Caso giocatore con statistiche: valutazione "standard"
        valutazione = (quotazione * 0.3) + (partite_voto * 0.33) + (media_voto * 0.34)  # Pesi leggermente modificati

    # print(f"Giocatore: {giocatore['Nome']}, Quotazione: {quotazione}, Valutazione: {valutazione}")  # Commenta o rimuovi questa riga

    return valutazione

def generate_team(df, strategy="Equilibrata"): # Riceve il DataFrame 'df'
    ROLES = {
        "Portiere": 3,
        "Difensore": 8,
        "Centrocampista": 8,
        "Attaccante": 6
    }

    attempts = 0
    max_attempts = 50
    best_team = None
    best_cost = 0

    generated_teams = set()

    budget_percentages = BUDGET_PERCENTAGES.get(strategy)
    if not budget_percentages:
        st.error(f"Strategia sconosciuta: {strategy}")
        return None, None

    target_budget_per_role = {}
    for role in ROLES:
        target_budget_per_role[role] = budget_percentages[role] * 100

    while attempts < max_attempts:
        selected_team = []
        total_cost_percentage = 0

        for role, count in ROLES.items():
            role_budget = target_budget_per_role[role]

            # Filtraggio efficiente con pandas
            role_df = df[(df["Ruolo"] == role) & (df["Quota_Percentuale"] > 0)]

          # *** INSERISCI QUI IL CODICE CORRETTO ***
    players = role_df.copy()
    players['Valutazione'] = players.apply(lambda row: valuta_giocatore(row.to_dict()), axis=1)
    players = players.sort_values(by='Valutazione', ascending=False)
    # *** FINE DEL CODICE DA INSERIRE ***

            if players.empty or len(players) < count:
                break

            available_players = players[players["Quota_Percentuale"] <= role_budget]

            if len(available_players) < count:
                break

            sample_size = min(len(available_players), count * 3)
            available_players_sorted = available_players.sort_values(by=lambda x: x.apply(valuta_giocatore), ascending=False) # Ordina i giocatori disponibili
            selected = available_players_sorted.iloc[:sample_size].sample(count).to_dict(orient='records') # Usa .iloc e .sample()

            selected_team.extend(selected)
            total_cost_percentage += sum(p['Quota_Percentuale'] for p in selected)

        if total_cost_percentage >= 95 and total_cost_percentage <= 100 and len(selected_team) == 25:
            return selected_team, total_cost_percentage

        if total_cost_percentage > best_cost and len(selected_team) == 25:
            best_team = selected_team
            best_cost = total_cost_percentage

        attempts += 1

    return best_team, best_cost


# Web App con Streamlit
st.title("⚽ FantaElite - Team Gen ⚽")
st.markdown("""---
### Scegli il tuo metodo di acquisto
""")

# Selezione tipo di pagamento
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (2 strategie)"])

# Selezione strategia di generazione
strategies = ["Equilibrata", "Modificatore di Difesa"]

if payment_type == "One Shot (1 strategia)":
    strategy = st.selectbox(" Seleziona la strategia di generazione", strategies)
    strategy_list = [strategy]
else:
    strategy_list = strategies

database = load_database()
if database is None:
    st.stop()

teams = {}  # Dizionario per memorizzare le squadre (anche per "One Shot")
csv_data = {}  # Dizionario per i dati CSV (anche per "One Shot")

if st.button("️ Genera La Tua Squadra"):
    if payment_type == "Complete (2 strategie)":
        for strategy in strategies:
            team, total_cost_percentage = generate_team(database, strategy)
            print(f"DEBUG: Team (dopo generate_team - {strategy}): {team}")
            if team and total_cost_percentage >= 95 and len(team) == 25:
                teams[strategy] = team
                csv_data[strategy] = export_to_csv(team)
            else:
                st.error(f"Errore nella generazione della squadra ({strategy}).")
                break

        if len(teams) == 2:  # Verifica che entrambe le squadre siano state generate
            for strategy, team in teams.items():
                st.write(f"### Squadra {strategy}:")
                if team:
                    df = pd.DataFrame(team)
                    if not df.empty:
                        st.dataframe(df)
                    else:
                        st.write("Nessun giocatore trovato per questa strategia.")
                else:
                    st.write("Nessun giocatore trovato per questa strategia.")
    else:  # Modalità "One Shot"
        for strategy in strategy_list:
            team, total_cost_percentage = generate_team(database, strategy)
            print(f"DEBUG: Team (dopo generate_team - {strategy}): {team}")
            if team and total_cost_percentage >= 95 and len(team) == 25:
                teams[strategy] = team
                csv_data[strategy] = export_to_csv(team)
                st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost_percentage:.2f}% del budget")
                st.write("### Squadra generata:")
                if team:
                    df = pd.DataFrame(team)
                    if not df.empty:
                        st.dataframe(df)
                    else:
                        st.write("Nessun giocatore trovato per questa strategia.")
                else:
                    st.write("Nessun giocatore trovato per questa strategia.")
            elif team is not None and len(team) < 25:
                st.error(f"❌ Errore nella generazione della squadra ({strategy}). Non è stato possibile completare tutti i ruoli.")
            else:
                st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso per formare una rosa completa.")

    # Creazione dell'archivio ZIP *fuori* dai blocchi if
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for strategy, data in csv_data.items():
            filename = f"squadra_{strategy}.csv"
            zipf.writestr(filename, data)

    # Bottone di download *unico*, *fuori* dai blocchi if
    st.download_button(
        label="⬇️ Scarica Squadre",  # Etichetta generica
        data=zip_buffer.getvalue(),
        file_name="squadre.zip" if payment_type == "Complete (2 strategie)" else "squadra.csv",  # Nome file dinamico
        mime="application/zip" if payment_type == "Complete (2 strategie)" else "text/csv"  # MIME type dinamico
    )

if st.button("Esegui Profiling"):
    profiler = cProfile.Profile()
    profiler.enable()

    for strategy in strategy_list:  # Esegui il profiling per ogni strategia selezionata
        generate_team(database, strategy)

    profiler.disable()
    profiler.print_stats(sort='time')