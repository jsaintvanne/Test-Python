import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from utils.auth import require_login
from utils.sidebar import render_sidebar
from utils.config import apply_compact_layout
from utils.storage import load_transactions, save_transactions
from utils.pdf_import import parse_pdf_statement

st.set_page_config(page_title="Compte Lucile", layout="wide")
apply_compact_layout()

CATEGORY_OPTIONS = ["Alimentation", "Transport", "Loisirs", "Santé", "Logement", "Autre"]
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

# Afficher le menu de navigation
render_sidebar()

# En-tête et vue d'ensemble
st.title("👤 Compte Lulu")

# Vérifier la connexion
if not st.session_state.get("logged_in", False):
    st.warning("🔒 Vous devez être connecté pour accéder à cette page.")
    st.info("Veuillez vous connecter via la barre latérale.")
    st.stop()

# Initialiser les données dans session_state si nécessaire
if "lucile_transactions" not in st.session_state:
    st.session_state.lucile_transactions = load_transactions("lucile")

# Import de relevé PDF (ajout rapide en haut de page)
st.subheader("📄 Ajouter un relevé PDF")
pdf_file = st.file_uploader("Ajouter un relevé de compte (PDF)", type=["pdf"], key="lucile_pdf_file")
pdf_category = st.selectbox("Catégorie par défaut pour les lignes importées", CATEGORY_OPTIONS, key="lucile_pdf_cat")

if pdf_file is not None:
    parsed_df, info_msg = parse_pdf_statement(pdf_file)
    if parsed_df.empty:
        st.error(info_msg or "Aucune ligne détectée dans le PDF. Assurez-vous que le tableau est bien lisible (PDF texte, pas scanné).")
    else:
        comptes = sorted(parsed_df["Compte"].dropna().unique().tolist()) if "Compte" in parsed_df.columns else []
        selected_comptes = st.multiselect("Comptes détectés à importer", comptes, default=comptes, key="lucile_pdf_comptes") if comptes else []
        df_view = parsed_df if not selected_comptes else parsed_df[parsed_df["Compte"].isin(selected_comptes)]
        st.caption(f"Lignes détectées : {len(df_view)}")
        st.dataframe(df_view.head(150), width="stretch", hide_index=True)
        if st.button("Importer ces lignes", type="primary", width="stretch", key="lucile_pdf_import_btn"):
            for _, row in df_view.iterrows():
                st.session_state.lucile_transactions.append({
                    "Date": row["Date"],
                    "Description": row["Description"],
                    "Montant": float(row["Montant"]),
                    "Catégorie": pdf_category
                })
            save_transactions("lucile", st.session_state.lucile_transactions)
            st.success(f"{len(df_view)} ligne(s) importée(s) et sauvegardée(s).")
            st.rerun()

# Helpers
def format_eur(amount: float) -> str:
    txt = f"{amount:,.0f} €" if abs(amount) >= 1 else f"{amount:,.2f} €"
    return txt.replace(",", " ")

def month_str(dt: datetime) -> str:
    return dt.strftime("%Y-%m")

# Préparer DataFrame et filtres
df_all = pd.DataFrame(st.session_state.lucile_transactions) if st.session_state.lucile_transactions else pd.DataFrame(columns=["Date","Description","Montant","Catégorie"])
if not df_all.empty:
    df_all["Date"] = pd.to_datetime(df_all["Date"]) 
    df_all["Mois"] = df_all["Date"].dt.strftime("%Y-%m")
    months = sorted(df_all["Mois"].unique(), reverse=True)
else:
    months = [month_str(datetime.now())]

current_month = month_str(datetime.now())
selected_month_state = st.session_state.get("lulu_month", current_month if current_month in months else months[0])
month_index = months.index(selected_month_state) if selected_month_state in months else 0

# Solde actuel et delta vs mois dernier (affiché juste sous le titre)
solde_actuel = float(df_all["Montant"].sum()) if not df_all.empty else 0.0
prev_months = sorted([m for m in months if m < selected_month_state], reverse=True)
prev_month = prev_months[0] if prev_months else None
net_current = float(df_all[df_all["Mois"] == selected_month_state]["Montant"].sum()) if not df_all.empty else 0.0
net_prev = float(df_all[df_all["Mois"] == prev_month]["Montant"].sum()) if (not df_all.empty and prev_month) else 0.0
delta_vs_prev = net_current - net_prev
delta_sign = "+" if delta_vs_prev >= 0 else ""

st.caption(f"Solde actuel : {format_eur(solde_actuel)}  ({delta_sign}{format_eur(delta_vs_prev)} vs mois dernier)")

colf1, colf2 = st.columns([2,2])
with colf1:
    selected_month = st.selectbox("Mois", options=months, index=month_index, key="lulu_month")
with colf2:
    cat_filter = st.selectbox("Catégorie", options=["Toutes"] + CATEGORY_OPTIONS, key="lulu_cat")

df_month = df_all[df_all["Mois"] == selected_month].copy() if not df_all.empty else df_all.copy()
if cat_filter != "Toutes" and not df_month.empty:
    df_month = df_month[df_month["Catégorie"] == cat_filter]

# Ligne de métriques
depenses_mois = float(df_month[df_month["Montant"] < 0]["Montant"].sum()) if not df_month.empty else 0.0
revenus_mois = float(df_month[df_month["Montant"] > 0]["Montant"].sum()) if not df_month.empty else 0.0
if not df_month.empty:
    daily_sum = df_month.groupby(df_month["Date"].dt.date)["Montant"].sum().sort_index()
    solde_min_val = float(daily_sum.cumsum().min())
else:
    solde_min_val = 0.0

mc1, mc2, mc3 = st.columns(3)
with mc1:
    st.metric("💸 Dépenses", format_eur(abs(depenses_mois)))
with mc2:
    st.metric("💰 Revenus", format_eur(revenus_mois))
with mc3:
    st.metric("📉 Solde min", format_eur(solde_min_val))

st.markdown("---")

# 📈 Évolution du solde (jour par jour)
st.subheader("📈 Évolution du solde (jour par jour)")
if not df_month.empty:
    daily = df_month.groupby(df_month["Date"].dt.date)["Montant"].sum().sort_index().reset_index()
    daily.columns = ["Jour", "Montant"]
    daily["Solde"] = daily["Montant"].cumsum()
    fig_line = px.line(daily, x="Jour", y="Solde", markers=True, labels={"Solde":"Solde (€)","Jour":"Jour"})
    fig_line.add_hline(y=0, line_dash="dash", line_color="#666")
    fig_line.update_layout(height=300)
    st.plotly_chart(fig_line, width="stretch")
else:
    st.info("Aucune donnée pour le mois sélectionné.")

st.markdown("---")

# Deux colonnes: Dépenses par catégorie | Dépenses par semaine
c1, c2 = st.columns(2)
with c1:
    st.subheader("📊 Dépenses par catégorie")
    exp_cat = (
        df_month[df_month["Montant"] < 0]
        .groupby("Catégorie")["Montant"].sum()
        .abs()
        .sort_values(ascending=False)
    ) if not df_month.empty else pd.Series(dtype=float)
    if not exp_cat.empty:
        fig_pie = go.Figure(data=[go.Pie(labels=[f"{CATEGORY_ICONS.get(cat,'📦')} {cat}" for cat in exp_cat.index], values=exp_cat.values)])
        fig_pie.update_layout(height=300, showlegend=True)
        st.plotly_chart(fig_pie, width="stretch")
    else:
        st.info("Aucune dépense sur ce mois.")

with c2:
    st.subheader("📊 Dépenses par semaine")
    if not df_month.empty:
        df_week = df_month[df_month["Montant"] < 0].copy()
        if not df_week.empty:
            df_week["Semaine"] = df_week["Date"].dt.isocalendar().week
            week_exp = df_week.groupby("Semaine")["Montant"].sum().abs().reset_index()
            fig_week = px.bar(week_exp, x="Semaine", y="Montant", labels={"Montant":"Montant (€)","Semaine":"Semaine"}, title=None)
            fig_week.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_week, width="stretch")
        else:
            st.info("Aucune dépense hebdomadaire.")
    else:
        st.info("Aucune donnée semaine.")

st.markdown("---")

# 🧾 Transactions (aperçu filtré)
st.subheader("🧾 Transactions")
st.caption("Filtres : mois / catégorie")
if not df_month.empty:
    df_disp = df_month.copy().sort_values("Date", ascending=False)
    for _, trans in df_disp.iterrows():
        with st.container():
            d1, d2, d3, d4 = st.columns([2,4,3,2])
            d1.write(pd.to_datetime(trans.get("Date")).strftime("%d/%m"))
            d2.write(trans.get("Description", ""))
            cat = trans.get("Catégorie", "")
            d3.write(f"{CATEGORY_ICONS.get(cat,'📦')} {cat}" if cat else "📦 Autre")
            amount = float(trans.get("Montant", 0))
            color = "#2ecc71" if amount >= 0 else "#e74c3c"
            sign = "+" if amount > 0 else ""
            d4.markdown(f"<span style='color:{color}; font-weight:600;'>{sign}{amount:.2f} €</span>", unsafe_allow_html=True)
            st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

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
    categorie = st.selectbox(
        "Catégorie",
        CATEGORY_OPTIONS,
        format_func=format_category
    )

if st.button("Ajouter", width="stretch"):
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
    
    # Afficher le tableau avec actions
    for idx, trans in enumerate(st.session_state.lucile_transactions):
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])
            c1.write(trans.get("Date", ""))
            c2.write(trans.get("Description", ""))
            amount = float(trans.get("Montant", 0))
            color = "#2ecc71" if amount >= 0 else "#e74c3c"
            c3.markdown(f"<span style='color:{color}; font-weight:600;'>{amount:.2f} €</span>", unsafe_allow_html=True)
            cat = trans.get("Catégorie", "")
            c4.write(format_category(cat))

            edit_state_key = f"edit_state_lucile_{idx}"
            edit_btn_key = f"edit_btn_lucile_{idx}"
            delete_btn_key = f"del_lucile_{idx}"

            with c5:
                b1, b2 = st.columns(2)
                if b1.button("✏️", key=edit_btn_key):
                    st.session_state[edit_state_key] = True
                if b2.button("🗑️", key=delete_btn_key):
                    st.session_state.lucile_transactions.pop(idx)
                    save_transactions("lucile", st.session_state.lucile_transactions)
                    st.success("Ligne supprimée")
                    st.rerun()

            st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

        # Formulaire d'édition inline
        if st.session_state.get(edit_state_key, False):
            with st.form(key=f"form_{edit_state_key}"):
                try:
                    default_date = datetime.strptime(trans.get("Date", ""), "%Y-%m-%d").date()
                except Exception:
                    default_date = datetime.now().date()
                new_date = st.date_input("Date", value=default_date, key=f"date_{edit_state_key}")
                new_desc = st.text_input("Description", value=trans.get("Description", ""), key=f"desc_{edit_state_key}")
                new_amount = st.number_input("Montant (€)", value=float(trans.get("Montant", 0)), step=0.01, format="%0.2f", key=f"amt_{edit_state_key}")
                current_cat = trans.get("Catégorie", "Alimentation")
                cat_idx = CATEGORY_OPTIONS.index(current_cat) if current_cat in CATEGORY_OPTIONS else 0
                new_cat = st.selectbox(
                    "Catégorie",
                    CATEGORY_OPTIONS,
                    index=cat_idx,
                    key=f"cat_{edit_state_key}",
                    format_func=format_category
                )

                submitted = st.form_submit_button("Enregistrer")
                if submitted:
                    st.session_state.lucile_transactions[idx] = {
                        "Date": new_date.strftime("%Y-%m-%d"),
                        "Description": new_desc,
                        "Montant": new_amount,
                        "Catégorie": new_cat
                    }
                    save_transactions("lucile", st.session_state.lucile_transactions)
                    st.session_state[edit_state_key] = False
                    st.success("Ligne mise à jour")
                    st.rerun()
else:
    st.info("Aucune transaction enregistrée. Ajoutez-en une ci-dessus.")