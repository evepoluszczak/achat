import streamlit as st
import pandas as pd
import plotly.express as px
import database as db

st.set_page_config(layout="wide", page_title="Dashboard Fournisseurs")

# Utilisation de markdown pour le titre avec icône
st.markdown("<h3><i class='bi bi-bar-chart-line-fill'></i> Dashboard et Indicateurs Clés (KPIs)</h3>", unsafe_allow_html=True)

# --- Style CSS pour les cartes et importation des icônes ---
st.markdown("""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
<style>
    .kpi-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease-in-out;
        height: 100%;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    .kpi-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0d6efd;
    }
    .kpi-label {
        font-size: 1.1rem;
        color: #6c757d;
    }
    .kpi-icon {
        font-size: 3rem;
        color: #0d6efd;
        opacity: 0.7;
    }
</style>
""", unsafe_allow_html=True)

# --- Chargement des données ---
def load_full_data():
    conn = db.get_db_connection()
    df = pd.read_sql_query("SELECT * FROM suppliers", conn)
    conn.close()
    # Convertir les dates pour les graphiques temporels
    df['date_creation'] = pd.to_datetime(df['date_creation'])
    return df

df = load_full_data()

if df.empty:
    st.warning("Aucune donnée fournisseur à afficher. Veuillez en ajouter via la page de gestion.")
    st.stop()

# --- NOUVEAU : Filtres rapides (simulent le clic sur les KPIs) ---
st.write("Filtres rapides :")
col_f1, col_f2, col_f3, col_f4 = st.columns(4)
if col_f1.button("Voir Tout", use_container_width=True):
    st.session_state.quick_filter = "all"
if col_f2.button("Fournisseurs Critiques", use_container_width=True):
    st.session_state.quick_filter = "critical"
if col_f3.button("Prospects Uniquement", use_container_width=True):
    st.session_state.quick_filter = "prospects"
if col_f4.button("Audits à planifier", use_container_width=True):
    st.session_state.quick_filter = "audit"

# Pré-filtrage des données basé sur les filtres rapides
if 'quick_filter' in st.session_state:
    if st.session_state.quick_filter == "critical":
        df = df[df['tags'].str.contains('Fournisseur critique', na=False)]
    elif st.session_state.quick_filter == "prospects":
        df = df[df['est_prospect'] == True]
    elif st.session_state.quick_filter == "audit":
        df = df[df['statut_audit'] == "Audit à planifier"]
    # Si 'all', on ne filtre pas et on garde le df complet

# --- Filtres du Dashboard ---
st.sidebar.header("Filtres avancés")
selected_cantons = st.sidebar.multiselect("Filtrer par Pays/Canton", options=df['pays_canton'].unique())
selected_status = st.sidebar.multiselet("Filtrer par Statut d'Audit", options=df['statut_audit'].unique())

if not selected_cantons: selected_cantons = df['pays_canton'].unique().tolist()
if not selected_status: selected_status = df['statut_audit'].unique().tolist()

df_filtered = df[
    df['pays_canton'].isin(selected_cantons) &
    df['statut_audit'].isin(selected_status)
]

# --- Affichage des KPIs ---
st.header("Indicateurs Clés de Performance")
total_fournisseurs = len(df_filtered)
nb_critiques = df_filtered['tags'].str.contains('Fournisseur critique', na=False).sum()
nb_prospects = df_filtered['est_prospect'].sum()

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.markdown(f'<div class="kpi-card"><div style="display: flex; justify-content: space-between; align-items: center;"><div><div class="kpi-label">Fournisseurs (filtrés)</div><div class="kpi-value">{total_fournisseurs}</div></div><i class="bi bi-building kpi-icon"></i></div></div>
