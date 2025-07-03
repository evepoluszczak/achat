import streamlit as st
import pandas as pd
import plotly.express as px
import database as db
import re

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
    df['date_creation'] = pd.to_datetime(df['date_creation'])
    df['tags'] = df['tags'].astype(str)
    return df

df = load_full_data()

if df.empty:
    st.warning("Aucune donnée fournisseur à afficher. Veuillez en ajouter via la page de gestion.")
    st.stop()

# --- Génération des listes complètes d'options AVANT tout filtrage ---
# CORRECTION : Ajout de .dropna() pour supprimer les valeurs vides avant de trier
all_possible_cantons = sorted(df['pays_canton'].dropna().unique())
all_possible_status = sorted(df['statut_audit'].dropna().unique())
all_possible_tags = sorted(df['tags'].str.split(',').explode().str.strip().dropna().unique())


# --- Filtres rapides ---
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

df_to_filter = df.copy()
if 'quick_filter' in st.session_state:
    if st.session_state.quick_filter == "critical":
        df_to_filter = df[df['tags'].str.contains('Fournisseur critique', na=False)]
    elif st.session_state.quick_filter == "prospects":
        df_to_filter = df[df['est_prospect'] == True]
    elif st.session_state.quick_filter == "audit":
        df_to_filter = df[df['statut_audit'] == "Audit à planifier"]

# --- Filtres avancés du Dashboard ---
st.sidebar.header("Filtres avancés")
selected_cantons = st.sidebar.multiselect(
    "Filtrer par Pays/Canton",
    options=all_possible_cantons 
)
selected_status = st.sidebar.multiselect(
    "Filtrer par Statut d'Audit",
    options=all_possible_status
)
selected_tags = st.sidebar.multiselect(
    "Filtrer par Tags",
    options=all_possible_tags
)

# --- LOGIQUE DE FILTRAGE ---
df_filtered = df_to_filter

if selected_cantons:
    df_filtered = df_filtered[df_filtered['pays_canton'].isin(selected_cantons)]
if selected_status:
    df_filtered = df_filtered[df_filtered['statut_audit'].isin(selected_status)]
if selected_tags:
    tag_regex = '|'.join([re.escape(tag) for tag in selected_tags])
    df_filtered = df_filtered[df_filtered['tags'].str.contains(tag_regex, na=False, regex=True)]


# --- Affichage des KPIs ---
st.header("Indicateurs Clés de Performance")
total_fournisseurs = len(df_filtered)
nb_critiques = df_filtered['tags'].str.contains('Fournisseur critique', na=False).sum()
nb_prospects = df_filtered['est_prospect'].sum()

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.markdown(f'<div class="kpi-card"><div style="display: flex; justify-content: space-between; align-items: center;"><div><div class="kpi-label">Fournisseurs (filtrés)</div><div class="kpi-value">{total_fournisseurs}</div></div><i class="bi bi-building kpi-icon"></i></div></div>', unsafe_allow_html=True)
with kpi2:
    st.markdown(f'<div class="kpi-card"><div style="display: flex; justify-content: space-between; align-items: center;"><div><div class="kpi-label">Fournisseurs Critiques</div><div class="kpi-value">{nb_critiques}</div></div><i class="bi bi-exclamation-triangle-fill kpi-icon"></i></div></div>', unsafe_allow_html=True)
with kpi3:
    st.markdown(f'<div class="kpi-card"><div style="display: flex; justify-content: space-between; align-items: center;"><div><div class="kpi-label">Prospects</div><div class="kpi-value">{nb_prospects}</div></div><i class="bi bi-binoculars-fill kpi-icon"></i></div></div>', unsafe_allow_html=True)

st.markdown("---")

# --- Graphiques Dynamiques ---
st.header("Analyses Visuelles")
g1_col1, g1_col2 = st.columns(2)
with g1_col1:
    st.subheader("Répartition par Pays/Canton")
    if not df_filtered.empty:
        fig_canton = px.pie(df_filtered['pays_canton'].value_counts().reset_index(), values='count', names='pays_canton', title="Distribution Géographique")
        st.plotly_chart(fig_canton, use_container_width=True)
    else:
        st.info("Aucune donnée pour ce filtre.")
with g1_col2:
    st.subheader("Répartition par Statut d'Audit")
    if not df_filtered.empty:
        fig_audit = px.bar(df_filtered['statut_audit'].value_counts().reset_index(), x='statut_audit', y='count', title="Statuts des Audits Fournisseurs", labels={'statut_audit': 'Statut', 'count': 'Nombre'})
        st.plotly_chart(fig_audit, use_container_width=True)
    else:
        st.info("Aucune donnée pour ce filtre.")

st.markdown("---")
g2_col1, g2_col2 = st.columns(2)
with g2_col1:
    st.subheader("Analyse des Tags")
    if not df_filtered.empty and not df_filtered['tags'].str.strip().eq('').all():
        tags_df = df_filtered['tags'].str.split(',').explode().str.strip().value_counts().reset_index()
        tags_df.columns = ['tag', 'count']
        fig_tags = px.bar(tags_df, x='count', y='tag', orientation='h', title="Fréquence des Tags")
        st.plotly_chart(fig_tags, use_container_width=True)
    else:
        st.info("Aucun tag à analyser pour la sélection actuelle.")
with g2_col2:
    st.subheader("Évolution des ajouts de fournisseurs")
    if not df_filtered.empty:
        monthly_adds = df_filtered.set_index('date_creation').resample('M').size().reset_index(name='count')
        monthly_adds['date_creation'] = monthly_adds['date_creation'].dt.strftime('%Y-%m')
        fig_time = px.line(monthly_adds, x='date_creation', y='count', title="Nouveaux fournisseurs par mois", markers=True)
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("Aucune donnée pour ce filtre.")

with st.expander("Voir les données détaillées de la sélection"):
    st.dataframe(df_filtered)
