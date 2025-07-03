import streamlit as st
import pandas as pd
import plotly.express as px
import database as db

st.set_page_config(layout="wide", page_title="Dashboard Fournisseurs")

st.title("📊 Dashboard et Indicateurs Clés (KPIs)")

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
    return df

df = load_full_data()

if df.empty:
    st.warning("Aucune donnée fournisseur à afficher. Veuillez en ajouter via la page de gestion.")
    st.stop()

# --- Filtres du Dashboard ---
st.sidebar.header("Filtres du Dashboard")
selected_cantons = st.sidebar.multiselect(
    "Filtrer par Pays/Canton",
    options=df['pays_canton'].unique()
)
selected_status = st.sidebar.multiselect(
    "Filtrer par Statut d'Audit",
    options=df['statut_audit'].unique()
)

if not selected_cantons:
    selected_cantons = df['pays_canton'].unique().tolist()
if not selected_status:
    selected_status = df['statut_audit'].unique().tolist()

df_filtered = df[
    df['pays_canton'].isin(selected_cantons) &
    df['statut_audit'].isin(selected_status)
]

# --- Affichage des KPIs dans des cartes ---
st.header("Indicateurs Clés de Performance")

total_fournisseurs = len(df_filtered)
nb_critiques = df_filtered['tags'].str.contains('Fournisseur critique', na=False).sum()
nb_prospects = df_filtered['est_prospect'].sum()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="kpi-label">Fournisseurs Actifs</div>
                <div class="kpi-value">{total_fournisseurs}</div>
            </div>
            <i class="bi bi-building kpi-icon"></i>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="kpi-label">Fournisseurs Critiques</div>
                <div class="kpi-value">{nb_critiques}</div>
            </div>
            <i class="bi bi-exclamation-triangle-fill kpi-icon"></i>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div class="kpi-label">Prospects</div>
                <div class="kpi-value">{nb_prospects}</div>
            </div>
            <i class="bi bi-binoculars-fill kpi-icon"></i>
        </div>
    </div>
    """, unsafe_allow_html=True)


st.markdown("---")

# --- Graphiques Dynamiques ---
st.header("Analyses Visuelles")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Répartition par Pays/Canton")
    if not df_filtered.empty:
        fig_canton = px.pie(
            df_filtered['pays_canton'].value_counts().reset_index(),
            values='count',
            names='pays_canton',
            title="Distribution Géographique"
        )
        st.plotly_chart(fig_canton, use_container_width=True)
    else:
        st.info("Aucune donnée pour ce filtre.")

with col2:
    st.subheader("Répartition par Statut d'Audit")
    if not df_filtered.empty:
        fig_audit = px.bar(
            df_filtered['statut_audit'].value_counts().reset_index(),
            x='statut_audit',
            y='count',
            title="Statuts des Audits Fournisseurs",
            labels={'statut_audit': 'Statut', 'count': 'Nombre'}
        )
        st.plotly_chart(fig_audit, use_container_width=True)
    else:
        st.info("Aucune donnée pour ce filtre.")
