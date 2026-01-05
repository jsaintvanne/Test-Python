import streamlit as st
import pandas as pd
from datetime import datetime
from utils.auth import require_login
from utils.sidebar import render_sidebar
from utils.config import apply_compact_layout
from utils.storage import load_transactions, save_transactions

st.set_page_config(page_title="Compte Lucile", layout="wide")
apply_compact_layout()

# Afficher le menu de navigation
render_sidebar()

st.title("💰 Compte de Lucile")

# Vérifier la connexion
if not st.session_state.get("logged_in", False):
    st.warning("🔒 Vous devez être connecté pour accéder à cette page.")
    st.info("Veuillez vous connecter via la barre latérale.")
    st.stop()

# Initialiser les données dans session_state si nécessaire
if "lucile_transactions" not in st.session_state:
    st.session_state.lucile_transactions = load_transactions("lucile")

# Formulaire d'ajout de transaction
st.subheader("➕ Ajouter une transaction")
col1, col2, col3, col4 = st.columns(4)

with col1:
    date = st.date_input("Date", value=datetime.now())
with col2:
    description = st.text_input("Description")
with col3:
    montant = st.number_input("Montant (€)", min_value=-10000.0, max_value=10000.0, value=0.0, step=0.01)
with col4:
    categorie = st.selectbox("Catégorie", ["Alimentation", "Transport", "Loisirs", "Santé", "Logement", "Autre"])

if st.button("Ajouter", use_container_width=True):
    if description:
        transaction = {
            "Date": date.strftime("%Y-%m-%d"),
            "Description": description,
            "Montant": montant,
            "Catégorie": categorie
        }
        st.session_state.lucile_transactions.append(transaction)
        # Sauvegarder les données
        save_transactions("lucile", st.session_state.lucile_transactions)
        st.success("✅ Transaction ajoutée et sauvegardée")
        st.rerun()
    else:
        st.error("La description est obligatoire")

st.markdown("---")

# Affichage du tableau des transactions
st.subheader("📊 Historique des transactions")

if st.session_state.lucile_transactions:
    df = pd.DataFrame(st.session_state.lucile_transactions)
    
    # Calculer le solde
    total = df["Montant"].sum()
    
    # Afficher les métriques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Solde total", f"{total:.2f} €")
    with col2:
        revenus = df[df["Montant"] > 0]["Montant"].sum()
        st.metric("Revenus", f"{revenus:.2f} €")
    with col3:
        depenses = df[df["Montant"] < 0]["Montant"].sum()
        st.metric("Dépenses", f"{depenses:.2f} €")
    
    st.markdown("---")
    
    # Afficher le tableau
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Bouton pour effacer les données
    if st.button("🗑️ Effacer toutes les transactions", type="secondary"):
        st.session_state.lucile_transactions = []
        save_transactions("lucile", [])
        st.rerun()
else:
    st.info("Aucune transaction enregistrée. Ajoutez-en une ci-dessus.")