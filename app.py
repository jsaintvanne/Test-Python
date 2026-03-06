import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from utils.config import __version__, APP_NAME, CONTACT_EMAIL, apply_compact_layout
from utils.sidebar import render_sidebar
from utils.storage import load_data

st.set_page_config(
    page_title=APP_NAME,
    layout="wide"
)

apply_compact_layout()

# Icones par catégorie pour les affichages
CATEGORY_ICONS = {
    "Alimentation": "🍽️",
    "Transport": "🚌",
    "Loisirs": "🎯",
    "Santé": "💊",
    "Logement": "🏠",
    "Autre": "📦"
}


def add_category_icon(category: str) -> str:
    """Retourne la catégorie préfixée de son icône."""
    if not category:
        return "📦 Autre"
    return f"{CATEGORY_ICONS.get(category, '📦')} {category}"

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

# En-tête du tableau de bord d'accueil
st.title("📊 Tableau de bord financier")
st.caption("Vue globale – Mois en cours")

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

# Helpers
def format_eur(amount: float) -> str:
    txt = f"{amount:,.0f} €" if abs(amount) >= 1 else f"{amount:,.2f} €"
    return txt.replace(",", " ")

def calculer_stats(transactions):
    if not transactions:
        return {"total": 0.0, "revenus": 0.0, "depenses": 0.0}
    df = pd.DataFrame(transactions)
    return {
        "total": float(df["Montant"].sum()),
        "revenus": float(df[df["Montant"] > 0]["Montant"].sum()),
        "depenses": float(df[df["Montant"] < 0]["Montant"].sum())
    }

stats_lucile = calculer_stats(lucile_trans)
stats_julien = calculer_stats(julien_trans)
stats_commun = calculer_stats(commun_trans)

# Ligne de métriques: Total, Ju, Lulu, Commun
total_global = stats_lucile['total'] + stats_julien['total'] + stats_commun['total']
col_total, col_ju, col_lulu, col_comm = st.columns(4)
with col_total:
    st.metric("💰 Total", format_eur(total_global))
with col_ju:
    st.metric("👤 Ju", format_eur(stats_julien['total']))
with col_lulu:
    st.metric("👤 Lulu", format_eur(stats_lucile['total']))
with col_comm:
    st.metric("👥 Commun", format_eur(stats_commun['total']))

st.markdown("---")

# Combiner toutes les transactions
all_transactions = []
for trans in lucile_trans:
    all_transactions.append({**trans, "Compte": "Lulu"})
for trans in julien_trans:
    all_transactions.append({**trans, "Compte": "Ju"})
for trans in commun_trans:
    all_transactions.append({**trans, "Compte": "Commun"})

if all_transactions:
    df = pd.DataFrame(all_transactions)
    df["Date"] = pd.to_datetime(df["Date"]) 
    df["Mois"] = df["Date"].dt.strftime("%Y-%m")

    # 📈 Évolution des soldes (courbe) par compte (cumul)
    st.subheader("📈 Évolution des soldes (courbe)")
    df_sorted = df.sort_values(["Compte", "Date"]) 
    df_sorted["Solde"] = df_sorted.groupby("Compte")["Montant"].cumsum()
    fig_lines = px.line(
        df_sorted,
        x="Date",
        y="Solde",
        color="Compte",
        markers=True,
        labels={"Solde": "Solde (€)", "Date": "Date"},
        title=None
    )
    fig_lines.add_hline(y=0, line_dash="dash", line_color="#666")
    fig_lines.update_layout(height=350, legend_title_text="Comptes")
    st.plotly_chart(fig_lines, width="stretch")

    st.markdown("---")

    # Deux colonnes: Dépenses par catégorie (camembert) | Résumé du mois
    left, right = st.columns(2)

    # Filtre mois en cours
    current_month = datetime.now().strftime("%Y-%m")
    df_month = df[df["Mois"] == current_month].copy()

    with left:
        st.subheader("📊 Dépenses par catégorie")
        expenses_by_category = (
            df_month[df_month["Montant"] < 0]
            .groupby("Catégorie")["Montant"].sum()
            .abs()
            .sort_values(ascending=False)
        )
        if not expenses_by_category.empty:
            fig_pie = go.Figure(data=[go.Pie(
                labels=[add_category_icon(cat) for cat in expenses_by_category.index],
                values=expenses_by_category.values,
                hole=0.0
            )])
            fig_pie.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig_pie, width="stretch")
        else:
            st.info("Aucune dépense ce mois-ci")

    with right:
        st.subheader("📌 Résumé du mois")
        depenses_mois = float(df_month[df_month["Montant"] < 0]["Montant"].sum())
        revenus_mois = float(df_month[df_month["Montant"] > 0]["Montant"].sum())
        difference = revenus_mois + depenses_mois  # dépenses négatives

        st.write(f"- Dépenses : {format_eur(abs(depenses_mois))}")
        st.write(f"- Revenus : {format_eur(revenus_mois)}")
        sign = "+" if difference >= 0 else ""
        st.write(f"- Différence : {sign}{format_eur(difference)}")

        # Plus grosse dépense
        biggest = None
        if not df_month.empty:
            df_exp = df_month[df_month["Montant"] < 0]
            if not df_exp.empty:
                biggest = df_exp.loc[df_exp["Montant"].idxmin()]
        if biggest is not None:
            label = biggest.get("Catégorie") or biggest.get("Description") or "Dépense"
            st.write(f"- Plus grosse dépense : {label} ({format_eur(abs(biggest['Montant']))})")
        else:
            st.write("- Plus grosse dépense : N/A")
else:
    st.info("Aucune transaction enregistrée. Commencez par ajouter des transactions dans les pages de comptes.")

# Pied de page
st.markdown("---")
st.caption(f"Version {__version__} • Gestion de comptes • Contact: {CONTACT_EMAIL}")
