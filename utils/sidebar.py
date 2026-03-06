import streamlit as st
from utils.auth import check_login
from utils.storage import load_transactions


def render_sidebar():
    """Affiche le menu de navigation et le formulaire de connexion dans la barre latérale"""
    with st.sidebar:
        st.header("Navigation")
        st.page_link("app.py", label="🏠 Accueil")
        st.page_link("pages/1_lucile.py", label="💰 Compte Lucile")
        st.page_link("pages/2_julien.py", label="💰 Compte Julien")
        st.page_link("pages/3_commun.py", label="💑 Compte Commun")
        st.page_link("pages/5_pret.py", label="🏦 Suivi des prêts")
        st.page_link("pages/6_mensualites.py", label="📅 Mensualités")
        
        # Séparateur entre la navigation et l'aperçu des soldes
        st.markdown("---")

        # Affichage des soldes rapides uniquement après connexion
        logged_in = st.session_state.get("logged_in", False)

        if logged_in:
            # Helper de formatage en euros avec séparateur de milliers
            def format_eur(amount: float) -> str:
                txt = f"{amount:,.2f} €"
                return txt.replace(",", " ")

            # Calcul des soldes par compte
            def account_total(name: str) -> float:
                try:
                    transactions = load_transactions(name)
                    return sum(float(t.get("Montant", 0)) for t in transactions)
                except Exception:
                    return 0.0

            ju_total = account_total("julien")
            lulu_total = account_total("lucile")
            commun_total = account_total("commun")

            st.subheader("💰 Soldes rapides")
            st.write(f"Julien : {format_eur(ju_total)}")
            st.write(f"Lucile : {format_eur(lulu_total)}")
            st.write(f"Commun : {format_eur(commun_total)}")

        # Séparateur avant la section d'authentification
        st.markdown("---")

        # Section authentification
        st.subheader("🔐 Authentification")

        if logged_in:
            username = st.session_state.get("username", "Utilisateur")
            st.success(f"✅ Connecté ({username})")
            if st.button("🚪 Déconnexion", width="stretch"):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()
        else:
            st.info("Non connecté")
            username = st.text_input("Utilisateur", key="sidebar_username")
            password = st.text_input("Mot de passe", type="password", key="sidebar_password")
            
            if st.button("Se connecter", width="stretch"):
                if check_login(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success("Connexion réussie")
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
