import streamlit as st
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
from utils.sidebar import render_sidebar
from utils.config import apply_compact_layout
from utils.storage import load_data, save_data

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

# Charger les prêts depuis le stockage
def load_loans():
    data = load_data()
    return data.get("loans", [])

def save_loans(loans):
    data = load_data()
    data["loans"] = loans
    save_data(data)

# Initialiser l'état
if "loans" not in st.session_state:
    st.session_state.loans = load_loans()

# Fonction pour calculer les mensualités
def calculate_mensualites(montant, taux_annuel, duree_mois, assurance_mensuelle, date_debut):
    """Calcule les mensualités avec prêt, intérêt et assurance"""
    mensualites = []
    taux_mensuel = taux_annuel / 100 / 12
    capital_restant = montant
    
    for i in range(duree_mois):
        date_mensualite = date_debut + relativedelta(months=i)
        
        # Intérêt sur le capital restant
        interet = capital_restant * taux_mensuel
        
        # Calcul de la part de capital
        if taux_mensuel > 0:
            if i < duree_mois - 1:
                mensualite_capital = (montant * taux_mensuel) / (1 - (1 + taux_mensuel) ** -(duree_mois - i))
            else:
                mensualite_capital = capital_restant
        else:
            mensualite_capital = montant / duree_mois
        
        capital_rembourse = min(mensualite_capital - interet, capital_restant)
        capital_restant -= capital_rembourse
        
        total = capital_rembourse + interet + assurance_mensuelle
        
        mensualites.append({
            "Date": date_mensualite.strftime("%Y-%m-%d"),
            "Prêt": round(capital_rembourse, 2),
            "Intérêt": round(interet, 2),
            "Assurance": round(assurance_mensuelle, 2),
            "Total": round(total, 2),
            "Capital restant": round(max(0, capital_restant), 2)
        })
    
    return mensualites

# Onglets pour la navigation
tab1, tab2 = st.tabs(["📊 Suivi des prêts", "➕ Ajouter un prêt"])

with tab2:
    st.subheader("Créer un nouveau prêt")
    
    sub_tab1, sub_tab2 = st.tabs(["Importer un tableau", "Créer manuellement"])
    
    with sub_tab1:
        st.markdown("**Importer votre tableau d'amortissement (Excel ou CSV)**")
        st.info("Le fichier doit contenir les colonnes: Date, Prêt, Intérêt, Assurance, Total")
        
        uploaded_file = st.file_uploader("Choisir un fichier", type=["xlsx", "csv"], key="loan_file")
        
        if uploaded_file is not None:
            try:
                # Charger le fichier
                if uploaded_file.name.endswith('.csv'):
                    df_import = pd.read_csv(uploaded_file)
                else:
                    df_import = pd.read_excel(uploaded_file)
                
                # Vérifier les colonnes requises
                required_cols = ["Date", "Prêt", "Intérêt", "Assurance", "Total"]
                missing_cols = [col for col in required_cols if col not in df_import.columns]
                
                if missing_cols:
                    st.error(f"Colonnes manquantes: {', '.join(missing_cols)}")
                else:
                    # Afficher un aperçu
                    st.success("✅ Fichier valide !")
                    st.dataframe(df_import.head(10), width="stretch")
                    
                    # Formulaire pour les infos du prêt
                    col1, col2 = st.columns(2)
                    with col1:
                        nom_pret_import = st.text_input("Nom du prêt", key="nom_import")
                        montant_total = st.number_input("Montant total du prêt (€)", min_value=0.0, value=float(df_import["Prêt"].sum()), step=1000.0)
                    with col2:
                        taux_moyen = st.number_input("Taux moyen (%)", min_value=0.0, value=0.0, step=0.1)
                        duree_total = st.number_input("Durée totale (mois)", min_value=1, value=len(df_import), step=1)
                    
                    if st.button("💾 Importer ce prêt", width="stretch", type="primary"):
                        if nom_pret_import:
                            # Convertir les dates
                            df_import["Date"] = pd.to_datetime(df_import["Date"]).dt.strftime("%Y-%m-%d")
                            
                            # Calculer le capital restant s'il n'existe pas
                            if "Capital restant" not in df_import.columns:
                                capital_initial = montant_total
                                capitals_restants = []
                                for idx, row in df_import.iterrows():
                                    capital_initial -= row["Prêt"]
                                    capitals_restants.append(round(max(0, capital_initial), 2))
                                df_import["Capital restant"] = capitals_restants
                            
                            new_loan = {
                                "id": len(st.session_state.loans) + 1,
                                "nom": nom_pret_import,
                                "montant": montant_total,
                                "taux": taux_moyen,
                                "duree": duree_total,
                                "assurance": float(df_import["Assurance"].iloc[0]) if "Assurance" in df_import.columns else 0,
                                "date_debut": str(df_import["Date"].iloc[0]),
                                "mensualites": df_import.to_dict('records')
                            }
                            
                            st.session_state.loans.append(new_loan)
                            save_loans(st.session_state.loans)
                            st.success(f"✅ Prêt '{nom_pret_import}' importé avec {len(df_import)} mensualités !")
                            st.rerun()
                        else:
                            st.error("Veuillez donner un nom au prêt")
            except Exception as e:
                st.error(f"Erreur lors de la lecture du fichier: {e}")
    
    with sub_tab2:
        st.markdown("**Créer un prêt avec calcul automatique**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            nom_pret = st.text_input("Nom du prêt (ex: Maison, Voiture)", key="nom_pret")
            montant = st.number_input("Montant (€)", min_value=0.0, value=0.0, step=1000.0)
            taux = st.number_input("Taux annuel (%)", min_value=0.0, value=3.5, step=0.1)
            
        with col2:
            duree = st.number_input("Durée (mois)", min_value=1, value=60, step=1)
            assurance = st.number_input("Assurance mensuelle (€)", min_value=0.0, value=0.0, step=1.0)
            date_debut = st.date_input("Date de début", value=date.today())
        
        if st.button("💾 Créer le prêt", width="stretch", type="primary"):
            if nom_pret and montant > 0:
                mensualites = calculate_mensualites(montant, taux, duree, assurance, date_debut)
                
                new_loan = {
                    "id": len(st.session_state.loans) + 1,
                    "nom": nom_pret,
                    "montant": montant,
                    "taux": taux,
                    "duree": duree,
                    "assurance": assurance,
                    "date_debut": date_debut.strftime("%Y-%m-%d"),
                    "mensualites": mensualites
                }
                
                st.session_state.loans.append(new_loan)
                save_loans(st.session_state.loans)
                st.success(f"✅ Prêt '{nom_pret}' créé avec {duree} mensualités !")
                st.rerun()
            else:
                st.error("Veuillez remplir tous les champs obligatoires")

with tab1:
    if st.session_state.loans:
        # Sélectionner un prêt
        loan_names = [f"{loan['nom']} - {loan['montant']:.0f}€" for loan in st.session_state.loans]
        selected_idx = st.selectbox("Sélectionner un prêt", range(len(st.session_state.loans)), 
                                     format_func=lambda x: loan_names[x])
        
        loan = st.session_state.loans[selected_idx]
        
        st.markdown("---")
        
        # Résumé du prêt
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Montant total", f"{loan['montant']:.2f}€")
        with col2:
            st.metric("📅 Durée", f"{loan['duree']} mois")
        with col3:
            st.metric("📊 Taux", f"{loan['taux']}%")
        with col4:
            st.metric("🛡️ Assurance/mois", f"{loan['assurance']:.2f}€")
        
        st.markdown("---")
        
        # Tableau des mensualités
        st.subheader("📋 Tableau d'amortissement")
        
        df_mensualites = pd.DataFrame(loan["mensualites"])
        df_mensualites["Date"] = pd.to_datetime(df_mensualites["Date"])
        
        # Calculer le capital restant s'il n'existe pas
        if "Capital restant" not in df_mensualites.columns:
            capital_initial = loan['montant']
            capitals_restants = []
            for idx, row in df_mensualites.iterrows():
                capital_initial -= row["Prêt"]
                capitals_restants.append(round(max(0, capital_initial), 2))
            df_mensualites["Capital restant"] = capitals_restants
        
        # Filtre par mois
        col1, col2 = st.columns([3, 1])
        with col1:
            date_filter = st.date_input("Afficher à partir de", value=date.today())
        with col2:
            st.write("")  # Espacement
            show_all = st.checkbox("Afficher tout")
        
        if not show_all:
            df_filtered = df_mensualites[df_mensualites["Date"] >= pd.Timestamp(date_filter)].copy()
        else:
            df_filtered = df_mensualites.copy()
        
        # Formatage pour l'affichage
        df_display = df_filtered.copy()
        df_display["Date"] = df_display["Date"].dt.strftime("%Y-%m-%d")
        
        # Ajouter une ligne de total
        if not df_display.empty:
            totals = {
                "Date": "TOTAL",
                "Prêt": df_display["Prêt"].sum(),
                "Intérêt": df_display["Intérêt"].sum(),
                "Assurance": df_display["Assurance"].sum(),
                "Total": df_display["Total"].sum(),
                "Capital restant": "-"
            }
            df_display = pd.concat([df_display, pd.DataFrame([totals])], ignore_index=True)
        
        st.dataframe(df_display, width="stretch", hide_index=True)
        
        st.markdown("---")
        
        # Graphique de l'évolution du capital
        import plotly.express as px
        
        df_plot = df_mensualites.copy()
        df_plot["Date"] = df_plot["Date"].dt.strftime("%Y-%m")
        
        fig = px.line(df_plot, x="Date", y="Capital restant", 
                     title="📉 Évolution du capital restant",
                     markers=True)
        fig.update_yaxes(title_text="Capital (€)")
        st.plotly_chart(fig, width="stretch")
        
        # Bouton pour supprimer
        st.markdown("---")
        if st.button(f"🗑️ Supprimer ce prêt", type="secondary"):
            st.session_state.loans.pop(selected_idx)
            save_loans(st.session_state.loans)
            st.success("Prêt supprimé")
            st.rerun()
    else:
        st.info("Aucun prêt enregistré. Créez-en un dans l'onglet 'Ajouter un prêt'.")

