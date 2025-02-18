import streamlit as st
import pandas as pd
import random
import io
import zipfile

# Funzioni di caricamento e normalizzazione (rimangono invariate)
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

        # Assicura che la colonna "Ruolo" sia trattata come stringa senza NaN
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip().fillna("Sconosciuto")

        # Convertiamo la quotazione in percentuale rispetto a un budget di 500 crediti
        df["Quota_Percentuale"] = (df["Quota_Percentuale"] / 500.0) * 100  # Converte in percentuale

        return df.to_dict(orient='records')

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
        "Portiere": 0.08,
        "Difensore": 0.20,
        "Centrocampista": 0.23,
        "Attaccante": 0.49
    }
}

def generate_team(database, strategy="Equilibrata"):
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

    generated_teams = set() # Insieme per tenere traccia delle squadre generate (usando hash)

    budget_percentages = BUDGET_PERCENTAGES.get(strategy)
    if not budget_percentages:
        st.error(f"Strategia sconosciuta: {strategy}")
        return None, None

    target_budget_per_role = {}
    for role in ROLES:
        target_budget_per_role[role] = budget_percentages[role] * 100 # Usa le percentuali esatte

    while attempts < max_attempts:
        selected_team = []
        total_cost_percentage = 0

        for role, count in ROLES.items():
            role_budget = target_budget_per_role[role]

            players = sorted(
                [p for p in database if str(p['Ruolo']).strip() == role and p['Quota_Percentuale'] > 0],
                key=lambda x: (x['Quota_Percentuale'] * 0.33 + x['Partite_Voto'] * 0.33 + x['Fantamedia'] * 0.34),
                reverse=True
            )

            if not players or len(players) < count:
                break

            available_players = [p for p in players if p['Quota_Percentuale'] <= role_budget]
            if len(available_players) < count:
                break

            sample_size = min(len(available_players), count * 3)
            selected = random.sample(available_players[:sample_size], count)
            selected_team.extend(selected)
            total_cost_percentage += sum(p['Quota_Percentuale'] for p in selected)

        # Controllo di duplicati usando hash
        team_hash = hash(tuple(sorted([p['Nome'] for p in selected_team]))) # Ordina i nomi per coerenza
        if team_hash in generated_teams:
            attempts += 1
            continue # Salta al prossimo tentativo se la squadra è un duplicato

        generated_teams.add(team_hash) # Aggiungi l'hash della squadra all'insieme

        # Controllo e aggiustamento del budget (se necessario)
        while total_cost_percentage > 100:
            player_to_remove = random.choice(selected_team)
            selected_team.remove(player_to_remove)
            total_cost_percentage -= player_to_remove['Quota_Percentuale']

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

if st.button("️ Genera La Tua Squadra"):
    if payment_type == "Complete (2 strategie)":
        teams = {}
        csv_data = {}
        for strategy in strategies:  # strategies contiene ora entrambe le strategie
            team, total_cost_percentage = generate_team(database, strategy)
            print(f"DEBUG: Team (dopo generate_team - {strategy}): {team}")
            if team and total_cost_percentage >= 95 and len(team) == 25:
                teams[strategy] = team
                csv_data[strategy] = export_to_csv(team)
            else:
                st.error(f"Errore nella generazione della squadra ({strategy}).")
                break  # Interrompi il ciclo se una delle squadre non viene generata

        if len(teams) == 2:  # Verifica che entrambe le squadre siano state generate
            # Crea un archivio ZIP in memoria
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for strategy, data in csv_data.items():
                    filename = f"squadra_{strategy}.csv"
                    zipf.writestr(filename, data)

            st.download_button(
                label="⬇️ Scarica Squadre (Complete)",
                data=zip_buffer.getvalue(),
                file_name="squadre_complete.zip",
                mime="application/zip"
            )

            # Visualizza entrambe le squadre *correttamente*
            for strategy, team in teams.items():
                st.write(f"### Squadra {strategy}:")
                st.dataframe(pd.DataFrame(team))

    else:  # Modalità One Shot (rimane invariata)
        for strategy in strategy_list:
            team, total_cost_percentage = generate_team(database, strategy)
            print(f"DEBUG: Team (dopo generate_team - {strategy}): {team}")
            if team and total_cost_percentage >= 95 and len(team) == 25:
                st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost_percentage:.2f}% del budget")
                st.write("### Squadra generata:")
                # Visualizza la squadra *correttamente*
                st.dataframe(pd.DataFrame(team))

                csv_data = export_to_csv(team)
                print(f"DEBUG: csv_data ({strategy}): {csv_data}")

                st.download_button(
                    label=f"⬇️ Scarica Squadra ({strategy})",
                    data=csv_data,
                    file_name=f"squadra_{strategy}.csv",
                    mime="text/csv"
                )
            elif team is not None and len(team) < 25:
                st.error(f"❌ Errore nella generazione della squadra ({strategy}). Non è stato possibile completare tutti i ruoli.")
            else:
                st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo basso per formare una rosa completa.")