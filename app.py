import streamlit as st
import numpy as np
import pandas as pd
from utils.config import __version__, APP_NAME, CONTACT_EMAIL, apply_compact_layout
from utils.sidebar import render_sidebar

st.set_page_config(
    page_title=APP_NAME,
    layout="wide"
)

apply_compact_layout()

st.title(f"🎈 {APP_NAME}")
st.caption("Statistiques • Data science • Visualisation • Authentification simple")

# Afficher le menu de navigation
render_sidebar()

# Bloc d’intro en colonnes
col1, col2 = st.columns([2, 1])
with col1:
    st.subheader("Bienvenue")
    st.write(
        "Explore des statistiques rapides, un modèle Random Forest sur Iris, "
        "et expérimente l’authentification basique."
    )
    st.button("Aller à Data Science", on_click=lambda: st.switch_page("pages/2_data_sciences.py"))
with col2:
    st.metric("Échantillon par défaut", "100 points")
    st.metric("Variables Iris", "4")
    st.metric("Modèle", "Random Forest")

st.markdown("---")

# Aperçu visuel rapide
st.subheader("Aperçu immédiat")
n = st.slider("Taille d'échantillon", 50, 1000, 200, key="home_sample_size")
data = np.random.normal(loc=0, scale=1, size=n)
df = pd.DataFrame(data, columns=["X"])
st.write("Histogramme de l’échantillon simulé")
st.bar_chart(df)

# Pied de page
st.markdown("---")
st.caption(f"Version {__version__} • Demo interne • Contact: {CONTACT_EMAIL}")
