import streamlit as st
import pandas as pd
from datetime import datetime
from utils.config import __version__, APP_NAME, CONTACT_EMAIL, apply_compact_layout
from utils.sidebar import render_sidebar
from utils.storage import load_data

st.set_page_config(
    page_title=APP_NAME,
    layout="wide"
)

apply_compact_layout()

# Charger les données au démarrage
@st.cache_resource
def initialize_session_data():
    """Charge les données persistantes au démarrage de l'application."""
    data = load_data()
    if "lucile_transactions" not in st.session_state:
        st.session_state.lucile_transactions = data.get("lucile_transactions", [])
    if "julien_transactions" not in st.session_state:
        st.session_state.julien_transactions = data.get("julien_transactions", [])
    if "commun_transactions" not in st.session_state:
        st.session_state.commun_transactions = data.get("commun_transactions", [])

initialize_session_data()

# Afficher le menu de navigation
render_sidebar()

st.title(f"🏠 {APP_NAME}")
st.caption("Tableau de bord des dépenses mensuelles")

# Vérifier si l'utilisateur est connecté
logged_in = st.session_state.get("logged_in", False)

if not logged_in:
    st.warning("🔒 Connectez-vous pour voir vos comptes et transactions")
    st.info("Utilisez la barre latérale ou la page de connexion pour vous authentifier.")
    
    # Afficher un message d'accueil
    st.markdown("---")
    st.subheader("Bienvenue sur l'application de gestion de comptes")
    st.write("Cette application vous permet de gérer vos comptes personnels et communs.")
    st.write("**Fonctionnalités :**")
    st.write("- 💰 Gestion des comptes personnels (Lucile et Julien)")
    st.write("- 💑 Gestion du compte commun")
    st.write("- 📊 Tableau de bord avec récapitulatif des dépenses")
    st.write("- 📅 Vue mensuelle des transactions")
    st.stop()

st.markdown("---")

# Récupérer toutes les transactions des trois comptes
lucile_trans = st.session_state.get("lucile_transactions", [])
julien_trans = st.session_state.get("julien_transactions", [])
commun_trans = st.session_state.get("commun_transactions", [])

# Calculer les totaux par compte
def calculer_stats(transactions):
    if not transactions:
        return {"total": 0, "revenus": 0, "depenses": 0}
    df = pd.DataFrame(transactions)
    return {
        "total": df["Montant"].sum(),
        "revenus": df[df["Montant"] > 0]["Montant"].sum(),
        "depenses": df[df["Montant"] < 0]["Montant"].sum()
    }

stats_lucile = calculer_stats(lucile_trans)
stats_julien = calculer_stats(julien_trans)
stats_commun = calculer_stats(commun_trans)

# Afficher les métriques par compte
st.subheader("📊 Vue d'ensemble par compte")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("💰 Compte Lucile", f"{stats_lucile['total']:.2f} €")
    st.caption(f"↗️ Revenus: {stats_lucile['revenus']:.2f} €")
    st.caption(f"↘️ Dépenses: {stats_lucile['depenses']:.2f} €")

with col2:
    st.metric("💰 Compte Julien", f"{stats_julien['total']:.2f} €")
    st.caption(f"↗️ Revenus: {stats_julien['revenus']:.2f} €")
    st.caption(f"↘️ Dépenses: {stats_julien['depenses']:.2f} €")

with col3:
    st.metric("💑 Compte Commun", f"{stats_commun['total']:.2f} €")
    st.caption(f"↗️ Revenus: {stats_commun['revenus']:.2f} €")
    st.caption(f"↘️ Dépenses: {stats_commun['depenses']:.2f} €")

st.markdown("---")

# Calculer le total global
total_global = stats_lucile['total'] + stats_julien['total'] + stats_commun['total']
revenus_global = stats_lucile['revenus'] + stats_julien['revenus'] + stats_commun['revenus']
depenses_global = stats_lucile['depenses'] + stats_julien['depenses'] + stats_commun['depenses']

st.subheader("💎 Total global")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Solde total", f"{total_global:.2f} €")
with col2:
    st.metric("Total revenus", f"{revenus_global:.2f} €")
with col3:
    st.metric("Total dépenses", f"{depenses_global:.2f} €")

st.markdown("---")

# Tableau récapitulatif des dépenses mensuelles
st.subheader("📅 Récapitulatif mensuel")

# Combiner toutes les transactions
all_transactions = []
for trans in lucile_trans:
    all_transactions.append({**trans, "Compte": "Lucile"})
for trans in julien_trans:
    all_transactions.append({**trans, "Compte": "Julien"})
for trans in commun_trans:
    all_transactions.append({**trans, "Compte": "Commun"})

if all_transactions:
    df = pd.DataFrame(all_transactions)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Mois"] = df["Date"].dt.strftime("%Y-%m")
    
    # Grouper par mois
    monthly = df.groupby("Mois").agg({
        "Montant": ["sum", "count"]
    }).reset_index()
    monthly.columns = ["Mois", "Total (€)", "Nb transactions"]
    monthly["Total (€)"] = monthly["Total (€)"].round(2)
    
    st.dataframe(monthly, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Dernières transactions
    st.subheader("🕐 Dernières transactions")
    df_sorted = df.sort_values("Date", ascending=False).head(10)
    df_display = df_sorted[["Date", "Description", "Montant", "Catégorie", "Compte"]].copy()
    df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d")
    st.dataframe(df_display, use_container_width=True, hide_index=True)
else:
    st.info("Aucune transaction enregistrée. Commencez par ajouter des transactions dans les pages de comptes.")

# Pied de page
st.markdown("---")
st.caption(f"Version {__version__} • Gestion de comptes • Contact: {CONTACT_EMAIL}")
