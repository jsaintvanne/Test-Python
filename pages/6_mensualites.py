import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sidebar import render_sidebar
from utils.config import apply_compact_layout
from utils.storage import load_data, save_data

st.set_page_config(page_title="Mensualités récurrentes", layout="wide")
apply_compact_layout()

CATEGORY_OPTIONS = ["Logement", "Alimentation", "Transport", "Loisirs", "Santé", "Autre"]
CATEGORY_ICONS = {
    "Alimentation": "🍽️",
    "Transport": "🚌",
    "Loisirs": "🎯",
    "Santé": "💊",
    "Logement": "🏠",
    "Autre": "📦"
}


def format_category(category: str) -> str:
    if not category:
        return "📦 Autre"
    return f"{CATEGORY_ICONS.get(category, '📦')} {category}"

render_sidebar()

st.title("📅 Mensualités récurrentes")

# Protection du contenu
if not st.session_state.get("logged_in", False):
    st.warning("🔒 Vous devez être connecté pour accéder à cette page.")
    st.info("Veuillez vous connecter via la barre latérale.")
    st.stop()

# Charger/sauvegarder les mensualités
def load_recurring():
    data = load_data()
    return data.get("recurring_payments", {
        "lucile": [],
        "julien": [],
        "commun": []
    })

def save_recurring(recurring):
    data = load_data()
    data["recurring_payments"] = recurring
    save_data(data)

# Initialiser l'état
if "recurring_payments" not in st.session_state:
    st.session_state.recurring_payments = load_recurring()

# Onglets pour chaque compte
tab1, tab2, tab3, tab4 = st.tabs(["💰 Lucile", "💰 Julien", "💑 Commun", "📊 Récapitulatif"])

def manage_recurring_for_account(account_name, account_label):
    """Gère les mensualités pour un compte donné"""
    st.subheader(f"Mensualités de {account_label}")
    
    # Section d'ajout avec pie chart
    col_form, col_chart = st.columns([2, 1])
    
    with col_form:
        st.markdown("#### ➕ Ajouter une mensualité")
        col1, col2 = st.columns(2)
        
        with col1:
            description = st.text_input("Description (ex: Netflix, Loyer)", key=f"{account_name}_desc")
            montant = st.number_input("Montant (€)", min_value=0.0, value=0.0, step=1.0, key=f"{account_name}_montant")
        
        with col2:
            jour = st.number_input("Jour de prélèvement (1-31)", min_value=1, max_value=31, value=1, key=f"{account_name}_jour")
            categorie = st.selectbox(
                "Catégorie",
                CATEGORY_OPTIONS,
                key=f"{account_name}_cat",
                format_func=format_category
            )
        
        if st.button("💾 Ajouter", key=f"{account_name}_add", width="stretch"):
            if description and montant > 0:
                new_recurring = {
                    "id": len(st.session_state.recurring_payments[account_name]) + 1,
                    "description": description,
                    "montant": montant,
                    "jour": jour,
                    "categorie": categorie
                }
                st.session_state.recurring_payments[account_name].append(new_recurring)
                save_recurring(st.session_state.recurring_payments)
                st.success("✅ Mensualité ajoutée")
                st.rerun()
            else:
                st.error("Description et montant obligatoires")
    
    with col_chart:
        # Pie chart des catégories
        st.markdown("#### 📊 Répartition par catégorie")
        recurring = st.session_state.recurring_payments[account_name]
        if recurring:
            import plotly.express as px
            df_rec = pd.DataFrame(recurring)
            
            if not df_rec.empty:
                df_cat = df_rec.groupby("categorie")["montant"].sum().reset_index()
                df_cat["categorie_icon"] = df_cat["categorie"].apply(format_category)
                
                fig = px.pie(
                    df_cat,
                    values="montant",
                    names="categorie_icon",
                    hole=0.3
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=350, showlegend=False, margin=dict(t=10, b=20, l=20, r=20))
                st.plotly_chart(fig, width="stretch")
            else:
                st.info("🔍 Aucune mensualité")
        else:
            st.info("🔍 Aucune mensualité")
    
    st.markdown("---")
    
    # Affichage des mensualités
    recurring = st.session_state.recurring_payments[account_name]
    
    if recurring:
        df = pd.DataFrame(recurring)
        
        # Calculer le total
        total = df["montant"].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("💰 Total mensuel", f"{total:.2f} €")
        with col2:
            st.metric("📊 Nombre", len(recurring))
        
        st.markdown("---")
        st.subheader("Liste des mensualités")
        
        # Afficher chaque mensualité avec possibilité de modification
        for idx, rec in enumerate(recurring):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])
                
                with col1:
                    st.write(f"**{rec.get('description', 'N/A')}**")
                
                with col2:
                    st.write(f"💶 {rec.get('montant', 0):.2f} €")
                
                with col3:
                    st.write(f"📅 Le {rec.get('jour', 1)} du mois")
                
                with col4:
                    st.write(f"🏷️ {format_category(rec.get('categorie', 'Autre'))}")
                
                with col5:
                    if st.button("🗑️", key=f"{account_name}_del_{idx}"):
                        st.session_state.recurring_payments[account_name].pop(idx)
                        save_recurring(st.session_state.recurring_payments)
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("Aucune mensualité enregistrée")

# Gérer chaque compte
with tab1:
    manage_recurring_for_account("lucile", "Lucile")

with tab2:
    manage_recurring_for_account("julien", "Julien")

with tab3:
    manage_recurring_for_account("commun", "Commun")

with tab4:
    st.subheader("📊 Récapitulatif global")
    
    all_recurring = []
    for account in ["lucile", "julien", "commun"]:
        for rec in st.session_state.recurring_payments[account]:
            all_recurring.append({
                **rec,
                "Compte": account.capitalize()
            })
    
    if all_recurring:
        df_all = pd.DataFrame(all_recurring)
        
        # Métriques globales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_lucile = df_all[df_all["Compte"] == "Lucile"]["montant"].sum()
            st.metric("💰 Lucile", f"{total_lucile:.2f} €")
        
        with col2:
            total_julien = df_all[df_all["Compte"] == "Julien"]["montant"].sum()
            st.metric("💰 Julien", f"{total_julien:.2f} €")
        
        with col3:
            total_commun = df_all[df_all["Compte"] == "Commun"]["montant"].sum()
            st.metric("💑 Commun", f"{total_commun:.2f} €")
        
        with col4:
            total_global = df_all["montant"].sum()
            st.metric("🌍 Total global", f"{total_global:.2f} €")
        
        st.markdown("---")
        
        # Graphique par catégorie
        import plotly.express as px
        
        df_cat = df_all.groupby("categorie")["montant"].sum().reset_index()
        df_cat = df_cat.sort_values("montant", ascending=False)
        df_cat["categorie_icon"] = df_cat["categorie"].apply(format_category)
        
        fig = px.bar(
            df_cat,
            x="categorie_icon",
            y="montant",
            title="💸 Mensualités par catégorie",
            labels={"categorie_icon": "Catégorie", "montant": "Montant (€)"},
            color="montant",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig, width="stretch")
        
        st.markdown("---")
        
        # Mensualités du mois en cours
        st.subheader("📅 Mensualités à venir ce mois")
        current_day = datetime.now().day
        
        df_a_venir = df_all[df_all["jour"].fillna(1) >= current_day].copy()
        df_a_venir = df_a_venir.sort_values("jour")
        
        if not df_a_venir.empty:
            df_display = df_a_venir[["Compte", "description", "montant", "jour", "categorie"]].copy()
            df_display.columns = ["Compte", "Description", "Montant (€)", "Jour", "Catégorie"]
            df_display["Catégorie"] = df_display["Catégorie"].apply(format_category)
            st.dataframe(df_display, width="stretch", hide_index=True)
            
            st.metric("💰 Total à venir", f"{df_a_venir['montant'].sum():.2f} €")
        else:
            st.info("Toutes les mensualités du mois ont été débitées")
        
        st.markdown("---")
        
        # Tableau complet
        st.subheader("📋 Toutes les mensualités")
        df_recap = df_all[["Compte", "description", "montant", "jour", "categorie"]].copy()
        df_recap.columns = ["Compte", "Description", "Montant (€)", "Jour", "Catégorie"]
        df_recap["Catégorie"] = df_recap["Catégorie"].apply(format_category)
        df_recap = df_recap.sort_values(["Compte", "Jour"])
        st.dataframe(df_recap, width="stretch", hide_index=True)
    else:
        st.info("Aucune mensualité enregistrée")
