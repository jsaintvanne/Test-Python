import streamlit as st
import pandas as pd
from datetime import date
from utils.sidebar import render_sidebar
from utils.config import apply_compact_layout

st.set_page_config(page_title="Suivi des prêts", layout="wide")
apply_compact_layout()

# Navigation visible en permanence
render_sidebar()

st.title("🏦 Suivi des prêts")

# Protection du contenu
if not st.session_state.get("logged_in", False):
    st.warning("🔒 Vous devez être connecté pour accéder à cette page.")
    st.info("Veuillez vous connecter via la barre latérale.")
    st.stop()

# Initialiser l'état
if "loan_records" not in st.session_state:
    st.session_state.loan_records = []

st.subheader("➕ Ajouter un prêt")
col1, col2, col3, col4 = st.columns([2, 1.2, 1, 1])

with col1:
    person = st.text_input("Prêteur / Débiteur")
with col2:
    amount = st.number_input("Montant (€)", min_value=0.0, value=0.0, step=10.0)
with col3:
    due = st.date_input("Date d'échéance", value=date.today())
with col4:
    status = st.selectbox("Statut", ["À rembourser", "En retard", "Remboursé"])

notes = st.text_input("Commentaire (optionnel)")

if st.button("Ajouter", use_container_width=True):
    if person and amount > 0:
        st.session_state.loan_records.append({
            "Personne": person,
            "Montant": amount,
            "Échéance": due.strftime("%Y-%m-%d"),
            "Statut": status,
            "Commentaire": notes
        })
        st.success("Prêt ajouté")
        st.rerun()
    else:
        st.error("Nom et montant doivent être renseignés")

st.markdown("---")

st.subheader("📊 Synthèse")
records = st.session_state.loan_records

if records:
    df = pd.DataFrame(records)
    df["Échéance"] = pd.to_datetime(df["Échéance"])
    today = pd.to_datetime(date.today())

    outstanding = df[df["Statut"] != "Remboursé"]["Montant"].sum()
    reimbursed = df[df["Statut"] == "Remboursé"]["Montant"].sum()
    overdue = df[(df["Échéance"] < today) & (df["Statut"] != "Remboursé")]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total prêts", f"{df['Montant'].sum():.2f} €")
    with c2:
        st.metric("À rembourser", f"{outstanding:.2f} €")
    with c3:
        st.metric("Remboursé", f"{reimbursed:.2f} €")

    if not overdue.empty:
        st.warning(f"⚠️ {len(overdue)} prêt(s) en retard")

    st.markdown("---")
    st.subheader("📄 Détail des prêts")
    df_display = df.copy()
    df_display["Échéance"] = df_display["Échéance"].dt.strftime("%Y-%m-%d")
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    if st.button("🗑️ Effacer tous les prêts", type="secondary"):
        st.session_state.loan_records = []
        st.rerun()
else:
    st.info("Aucun prêt enregistré pour le moment.")
