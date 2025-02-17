import streamlit as st
import pandas as pd
import random

# ... (Funzioni load_database, export_to_csv, BUDGET_PERCENTAGES e generate_team rimangono invariate)

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
        if team and total_cost_percentage >= 95 and len(team) == 25:  # Aggiunti i due punti
            st.success(f"✅ Squadra generata con successo ({strategy})! Costo totale: {total_cost_percentage:.2f}% del budget")
            st.write("### Squadra generata:")
            st.write(pd.DataFrame(team))
            csv_data = export_to_csv(team)
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