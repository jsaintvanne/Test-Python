import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from utils.auth import require_login
from utils.sidebar import render_sidebar
from utils.config import apply_compact_layout
from utils.storage import load_transactions, save_transactions, load_data
from utils.pdf_import import parse_pdf_statement

st.set_page_config(page_title="Compte Commun", layout="wide")
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

st.title("👥 Compte Commun")

# Vérifier la connexion
if not st.session_state.get("logged_in", False):
    st.warning("🔒 Vous devez être connecté pour accéder à cette page.")
    st.info("Veuillez vous connecter via la barre latérale.")
    st.stop()

# Initialiser les données dans session_state si nécessaire
if "commun_transactions" not in st.session_state:
    st.session_state.commun_transactions = load_transactions("commun")

# Import de relevé PDF (ajout rapide en haut de page)
st.subheader("📄 Ajouter un relevé PDF")
pdf_file = st.file_uploader("Ajouter un relevé de compte (PDF)", type=["pdf"], key="commun_pdf_file")
pdf_category = st.selectbox("Catégorie par défaut pour les lignes importées", CATEGORY_OPTIONS, key="commun_pdf_cat")

if pdf_file is not None:
    parsed_df, info_msg = parse_pdf_statement(pdf_file)
    if parsed_df.empty:
        st.error(info_msg or "Aucune ligne détectée dans le PDF. Assurez-vous que le tableau est bien lisible (PDF texte, pas scanné).")
    else:
        comptes = sorted(parsed_df["Compte"].dropna().unique().tolist()) if "Compte" in parsed_df.columns else []
        selected_comptes = st.multiselect("Comptes détectés à importer", comptes, default=comptes, key="commun_pdf_comptes") if comptes else []
        df_view = parsed_df if not selected_comptes else parsed_df[parsed_df["Compte"].isin(selected_comptes)]
        st.caption(f"Lignes détectées : {len(df_view)}")
        st.dataframe(df_view.head(150), width="stretch", hide_index=True)
        if st.button("Importer ces lignes", type="primary", width="stretch", key="commun_pdf_import_btn"):
            for _, row in df_view.iterrows():
                st.session_state.commun_transactions.append({
                    "Date": row["Date"],
                    "Description": row["Description"],
                    "Montant": float(row["Montant"]),
                    "Catégorie": pdf_category
                })
            save_transactions("commun", st.session_state.commun_transactions)
            st.success(f"{len(df_view)} ligne(s) importée(s) et sauvegardée(s).")
            st.rerun()

# ===== Tableau de bord commun (mois courant) =====
def _format_eur(amount: float) -> str:
    txt = f"{amount:,.0f} €" if abs(amount) >= 1 else f"{amount:,.2f} €"
    return txt.replace(",", " ")

df_all = pd.DataFrame(st.session_state.commun_transactions) if st.session_state.commun_transactions else pd.DataFrame(columns=["Date","Description","Montant","Catégorie"])
if not df_all.empty:
    df_all["Date"] = pd.to_datetime(df_all["Date"])
    df_all["Mois"] = df_all["Date"].dt.strftime("%Y-%m")
    months = sorted(df_all["Mois"].unique(), reverse=True)
else:
    months = [datetime.now().strftime("%Y-%m")]

current_month = datetime.now().strftime("%Y-%m")
selected_month_state = st.session_state.get("commun_month", current_month if current_month in months else months[0])
month_index = months.index(selected_month_state) if selected_month_state in months else 0

solde_actuel = float(df_all["Montant"].sum()) if not df_all.empty else 0.0
st.caption(f"Solde actuel : {_format_eur(solde_actuel)}")

col_month, col_loans = st.columns([1, 3])
with col_month:
    selected_month = st.selectbox("Mois", options=months, index=month_index, key="commun_month")

with col_loans:
    st.subheader("🏦 Mensualités du mois")
    data = load_data()
    loans = data.get("loans", [])

    mensualites_mois = []
    if loans:
        for loan in loans:
            remaining = loan.get("montant", 0)
            mensualites_triees = sorted(loan.get("mensualites", []), key=lambda x: x.get("Date", ""))

            for mensualite in mensualites_triees:
                principal = float(mensualite.get("Prêt", 0) or 0)
                interest = float(mensualite.get("Intérêt", 0) or 0)
                insurance = float(mensualite.get("Assurance", 0) or 0)
                total = float(mensualite.get("Total", principal + interest + insurance))

                remaining = max(0, remaining - principal)

                date_mensualite = pd.to_datetime(mensualite.get("Date", None), errors="coerce").strftime("%Y-%m") if mensualite.get("Date") else None
                if date_mensualite and date_mensualite == selected_month:
                    mensualites_mois.append({
                        "Prêt": loan.get("nom", ""),
                        "Date": mensualite.get("Date", ""),
                        "Capital": principal,
                        "Intérêt": interest,
                        "Assurance": insurance,
                        "Total": total,
                        "Capital restant": remaining
                    })

    if mensualites_mois:
        df_mensualites = pd.DataFrame(mensualites_mois)
        df_mensualites["Date"] = pd.to_datetime(df_mensualites["Date"]).dt.strftime("%d/%m")

        total_mois = df_mensualites["Total"].sum()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total mensualités", f"{total_mois:.2f} €", delta=f"{len(mensualites_mois)} prêt(s)")
        with col2:
            st.metric("📊 Capital", f"{df_mensualites['Capital'].sum():.2f} €")
        with col3:
            st.metric("💸 Intérêts + Assurance", f"{(df_mensualites['Intérêt'].sum() + df_mensualites['Assurance'].sum()):.2f} €")
        with col4:
            st.metric("🏦 Capital restant", f"{df_mensualites['Capital restant'].sum():.2f} €")

        df_display = df_mensualites[["Date", "Prêt", "Capital", "Intérêt", "Assurance", "Total", "Capital restant"]]
        st.dataframe(df_display, width="stretch", hide_index=True)
    else:
        st.info(f"Aucune mensualité pour {selected_month}")

df_month = df_all[df_all["Mois"] == selected_month].copy() if not df_all.empty else df_all.copy()

# Métriques : Charges (fixes) vs Variables
fixed_keywords = [
    "loyer", "élec", "electric", "edf", "gaz", "internet", "assurance", "taxe", "impôt", "impots", "wifi", "box", "mutuelle", "abonnement"
]
fixed_categories = {"Logement", "Santé"}

def classify_type(cat: str, desc: str) -> str:
    c = (cat or "").strip()
    d = (desc or "").lower()
    if c in fixed_categories:
        return "Fixe"
    if any(k in d for k in fixed_keywords):
        return "Fixe"
    return "Variable"

def guess_payer(desc: str) -> str:
    s = (desc or "").lower()
    if "julien" in s or s.startswith("ju ") or s.endswith(" ju") or " ju " in s or s == "ju":
        return "Ju"
    if "lucile" in s or "lulu" in s or s.startswith("lu ") or s.endswith(" lu") or " lu " in s:
        return "Lulu"
    return "Commun"

charges = 0.0
variables = 0.0
if not df_month.empty:
    df_m_exp = df_month[df_month["Montant"] < 0].copy()
    if not df_m_exp.empty:
        df_m_exp["Type"] = [classify_type(row.get("Catégorie"), row.get("Description")) for _, row in df_m_exp.iterrows()]
        charges = float(df_m_exp[df_m_exp["Type"] == "Fixe"]["Montant"].sum() * -1)
        variables = float(df_m_exp[df_m_exp["Type"] == "Variable"]["Montant"].sum() * -1)

mc1, mc2 = st.columns(2)
with mc1:
    st.metric("🏠 Charges", _format_eur(charges))
with mc2:
    st.metric("🛒 Variables", _format_eur(variables))

st.markdown("---")

# 📊 Dépenses communes par catégorie (camembert)
st.subheader("📊 Dépenses communes par catégorie")
if not df_month.empty:
    exp_by_cat = (
        df_month[df_month["Montant"] < 0]
        .groupby("Catégorie")["Montant"].sum()
        .abs()
        .sort_values(ascending=False)
    )
    if not exp_by_cat.empty:
        fig_pie = go.Figure(data=[go.Pie(
            labels=[f"{CATEGORY_ICONS.get(cat,'📦')} {cat}" for cat in exp_by_cat.index],
            values=exp_by_cat.values,
            hole=0.0
        )])
        fig_pie.update_layout(height=350, showlegend=True)
        st.plotly_chart(fig_pie, width="stretch")
    else:
        st.info("Aucune dépense ce mois-ci.")
else:
    st.info("Aucune donnée pour le mois sélectionné.")

st.markdown("---")

# 🧾 Dépenses communes (table)
st.subheader("🧾 Dépenses communes")
if not df_month.empty:
    df_tab = df_month[df_month["Montant"] < 0].copy()
    if not df_tab.empty:
        df_tab["Type"] = [classify_type(row.get("Catégorie"), row.get("Description")) for _, row in df_tab.iterrows()]
        df_tab["Payé par"] = [guess_payer(row.get("Description")) for _, row in df_tab.iterrows()]
        df_tab["Date"] = pd.to_datetime(df_tab["Date"]).dt.strftime("%d/%m")
        df_tab["Montant (€)"] = df_tab["Montant"].abs().round(2)
        df_display = df_tab[["Date", "Description", "Type", "Payé par", "Montant (€)"]]
        df_display = df_display.rename(columns={"Description": "Libellé"})
        st.dataframe(df_display, width="stretch", hide_index=True)
    else:
        st.info("Aucune dépense à afficher pour ce mois.")
else:
    st.info("Aucune donnée disponible.")

st.markdown("---")

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
        st.session_state.commun_transactions.append(transaction)
        # Sauvegarder les données
        save_transactions("commun", st.session_state.commun_transactions)
        st.success("✅ Transaction ajoutée et sauvegardée")
        st.rerun()
    else:
        st.error("La description est obligatoire")

st.markdown("---")

# Affichage du tableau des transactions
st.subheader("📊 Historique des transactions")

if st.session_state.commun_transactions:
    df = pd.DataFrame(st.session_state.commun_transactions)
    
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
    for idx, trans in enumerate(st.session_state.commun_transactions):
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([2, 3, 2, 2, 1])
            c1.write(trans.get("Date", ""))
            c2.write(trans.get("Description", ""))
            amount = float(trans.get("Montant", 0))
            color = "#2ecc71" if amount >= 0 else "#e74c3c"
            c3.markdown(f"<span style='color:{color}; font-weight:600;'>{amount:.2f} €</span>", unsafe_allow_html=True)
            cat = trans.get("Catégorie", "")
            c4.write(format_category(cat))

            edit_state_key = f"edit_state_commun_{idx}"
            edit_btn_key = f"edit_btn_commun_{idx}"
            delete_btn_key = f"del_commun_{idx}"

            with c5:
                b1, b2 = st.columns(2)
                if b1.button("✏️", key=edit_btn_key):
                    st.session_state[edit_state_key] = True
                if b2.button("🗑️", key=delete_btn_key):
                    st.session_state.commun_transactions.pop(idx)
                    save_transactions("commun", st.session_state.commun_transactions)
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
                    st.session_state.commun_transactions[idx] = {
                        "Date": new_date.strftime("%Y-%m-%d"),
                        "Description": new_desc,
                        "Montant": new_amount,
                        "Catégorie": new_cat
                    }
                    save_transactions("commun", st.session_state.commun_transactions)
                    st.session_state[edit_state_key] = False
                    st.success("Ligne mise à jour")
                    st.rerun()
else:
    st.info("Aucune transaction enregistrée. Ajoutez-en une ci-dessus.")