import streamlit as st
import pandas as pd
import random

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
    df = pd.DataFrame(team).reset_index(drop=True)  # Correzione: reset_index() aggiunto
    return df.to_csv(index=False, sep=';', decimal=',', encoding='utf-8').encode('utf-8')


BUDGET_PERCENTAGES = {
    "Equilibrata": {
        "Portiere": (0.06, 0.08),  # 6-8%
        "Difensore": (0.11, 0.15),  # 11-15%
        "Centrocampista": (0.24, 0.27),  # 24-27%
        "Attaccante": (0.50, 0.59)  # 50-59%
    },
    "Modificatore di Difesa": {
        "Portiere": (0.07, 0.09),  # 7-9%
        "Difensore": (0.18, 0.22),  # 18-22%
        "Centrocampista": (0.22, 0.25),  # 22-25%
        "Attaccante": (0.45, 0.53)  # 45-53%
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
    target_budget = 95

    budget_percentages = BUDGET_PERCENTAGES.get(strategy)
    if not budget_percentages:
        st.error(f"Strategia sconosciuta: {strategy}")
        return None, None

    while attempts < max_attempts:
        selected_team = []
        total_cost_percentage = 0

        for role, count in ROLES.items():
            min_percentage, max_percentage = budget_percentages[role]
            role_budget_percentage = random.uniform(min_percentage, max_percentage)
            role_budget = role_budget_percentage * 100  # Budgeto per ruolo in percentuale

            players = sorted(
                [p for p in database if str(p['Ruolo']).strip() == role and p['Quota_Percentuale'] > 0],
                key=lambda x: (x['Quota_Percentuale'] * 0.33 + x['Partite_Voto'] * 0.33 + x['Fantamedia'] * 0.34),
                reverse=True
            )

            if not players or len(players) < count:
                break

            available_players = [p for p in players if p['Quota_Percentuale'] <= role_budget]
            if len(available_players) < count:
                break  # Non ci sono abbastanza giocatori disponibili con quel budget

            sample_size = min(len(available_players), count * 3)  # Limita il sample ai giocatori disponibili
            selected = random.sample(available_players[:sample_size], count)
            selected_team.extend(selected)
            total_cost_percentage += sum(p['Quota_Percentuale'] for p in selected)

        # Aggiustamento finale (rimane invariato)
        if total_cost_percentage < target_budget:
            sorted_players = sorted(database, key=lambda x: x['Quota_Percentuale'], reverse=True)
            for p in sorted_players:
                if p not in selected_team and total_cost_percentage + p['Quota_Percentuale'] <= 100:
                    selected_team.append(p)
                    total_cost_percentage += p['Quota_Percentuale']
                if total_cost_percentage >= target_budget:
                    break

        if total_cost_percentage >= target_budget and total_cost_percentage <= 100 and len(selected_team) == 25:
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
    for strategy in strategy_list:
        team, total_cost_percentage = generate_team(database, strategy)
        if team and total_cost_percentage >= 95 and len(team) == 25:
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost_percentage:.2f}% del budget")
            st.write("### Squadra generata:")
            st.write(pd.DataFrame(team))
            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})",)