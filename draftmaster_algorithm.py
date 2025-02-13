import streamlit as st
import pandas as pd
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
            "Media_Voto": "Media_Voto",
            "Fantamedia": "Fantamedia",
            "Quotazione": "Quota_Percentuale",
            "Partite_Voto": "Partite_Voto"
        }

        df.rename(columns=column_mapping, inplace=True)

        # Converti le colonne numeriche correggendo eventuali errori
        numeric_columns = ["Quota_Percentuale", "Fantamedia", "Media_Voto", "Partite_Voto"]

        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")  # Converte i valori non numerici in NaN

        # Riempie solo i valori NaN con la media delle quotazioni esistenti
        df["Quota_Percentuale"].fillna(df["Quota_Percentuale"].mean(), inplace=True)

        # Assicura che la colonna "Ruolo" sia trattata come stringa senza NaN
        df["Ruolo"] = df["Ruolo"].astype(str).str.strip().fillna("Sconosciuto")

        return df.to_dict(orient='records')

    except Exception as e:
        st.error(f"Errore nel caricamento del database: {e}")
        return None

# Percentuali di budget per ogni strategia
BUDGET_ALLOCATION = {
    "Equilibrata": {
        "Portiere": (6, 8),
        "Difensore": (11, 15),
        "Centrocampista": (24, 27),
        "Attaccante": (50, 59)
    },
    "Modificatore di Difesa": {
        "Portiere": (7, 9),
        "Difensore": (18, 22),
        "Centrocampista": (22, 25),
        "Attaccante": (45, 53)
    }
}

# Definizione ruoli
ROLES = {
    "Portiere": 3,
    "Difensore": 8,
    "Centrocampista": 8,
    "Attaccante": 6
}

def generate_team(database, strategy="Equilibrata", attempts_limit=50):
    target_budget_min = 95
    target_budget_max = 100

    budget_ranges = BUDGET_ALLOCATION[strategy]

    attempts = 0
    best_team = None
    best_cost = 0

    while attempts < attempts_limit:
        selected_team = []
        total_cost_percentage = 0
        assigned_budget = {}

        # Genera un budget casuale per ogni ruolo rispettando il range
        for role in ROLES:
            assigned_budget[role] = random.uniform(*budget_ranges[role])

        # Normalizziamo il budget per fare in modo che la somma sia **esattamente 100%**
        total_budget_assigned = sum(assigned_budget.values())
        for role in assigned_budget:
            assigned_budget[role] = (assigned_budget[role] / total_budget_assigned) * 100

        # Selezione giocatori per ogni ruolo
        for role, count in ROLES.items():
            players = sorted(
                [p for p in database if role in str(p['Ruolo']).split(';') and p['Quota_Percentuale'] > 0],
                key=lambda x: (x['Quota_Percentuale'] * 0.4 + x['Partite_Voto'] * 0.3 + x['Fantamedia'] * 0.3),
                reverse=True
            )

            if not players or len(players) < count:
                continue  # Se non ci sono abbastanza giocatori, riprova

            # Seleziona casualmente i giocatori, ma evita il sovraccarico di giocatori costosi
            selected = random.sample(players[:max(count * 3, len(players))], count)

            selected_team.extend(selected)
            total_cost_percentage += sum(p['Quota_Percentuale'] for p in selected)

        # Se il budget supera il 100%, rimuoviamo il giocatore meno costoso fino a rientrare nel range
        while total_cost_percentage > target_budget_max and selected_team:
            selected_team = sorted(selected_team, key=lambda x: x['Quota_Percentuale'], reverse=True)
            removed_player = selected_team.pop()
            total_cost_percentage -= removed_player['Quota_Percentuale']

        # Fallback per aggiungere giocatori economici se il budget è troppo basso
        if total_cost_percentage < target_budget_min:
            cheap_players = sorted(database, key=lambda x: x['Quota_Percentuale'])
            for p in cheap_players:
                if p not in selected_team and total_cost_percentage + p['Quota_Percentuale'] <= target_budget_max:
                    selected_team.append(p)
                    total_cost_percentage += p['Quota_Percentuale']
                if total_cost_percentage >= target_budget_min:
                    break

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

# Selezione tipo di pagamento
payment_type = st.radio("Tipo di generazione", ["One Shot (1 strategia)", "Complete (2 strategie)"])

# Selezione strategia di generazione
strategies = ["Equilibrata", "Modificatore di Difesa"]

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
        team, total_cost_percentage = generate_team(database, strategy, attempts_limit=50)
        if team and len(team) == sum(ROLES.values()):
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost_percentage:.2f}% del budget")
            st.write("### Squadra generata:")
            st.write(pd.DataFrame(team))
            csv_data = export_to_csv(team)
            st.download_button(f"⬇️ Scarica Squadra ({strategy})", csv_data, file_name=f"squadra_{strategy}.csv", mime="text/csv")
        else:
            st.error(f"❌ Errore nella generazione della squadra ({strategy}). Il budget potrebbe essere troppo alto o troppo basso per formare una rosa completa.")
