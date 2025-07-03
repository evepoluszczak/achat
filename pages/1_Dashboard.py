import streamlit as st
import pandas as pd
import plotly.express as px
import database as db

st.set_page_config(layout="wide", page_title="Dashboard Fournisseurs")

st.title("📊 Dashboard et Indicateurs Clés (KPIs)")

# --- Chargement des données ---
def load_full_data():
    # Pour le dashboard, nous avons besoin de toutes les données
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
    options=df['pays_canton'].unique(),
    default=df['pays_canton'].unique()
)

selected_status = st.sidebar.multiselect(
    "Filtrer par Statut d'Audit",
    options=df['statut_audit'].unique(),
    default=df['statut_audit'].unique()
)

# Application des filtres
df_filtered = df[
    df['pays_canton'].isin(selected_cantons) &
    df['statut_audit'].isin(selected_status)
]


# --- Affichage des KPIs ---
st.header("Indicateurs Clés de Performance")
col1, col2, col3 = st.columns(3)

with col1:
    total_fournisseurs = len(df_filtered)
    st.metric(label="Nombre Total de Fournisseurs", value=total_fournisseurs)

with col2:
    # Compter les fournisseurs avec le tag "critique"
    nb_critiques = df_filtered['tags'].str.contains('Fournisseur critique', na=False).sum()
    st.metric(label="Fournisseurs Critiques", value=f"{nb_critiques}")

with col3:
    nb_prospects = df_filtered['est_prospect'].sum()
    st.metric(label="Nombre de Prospects", value=nb_prospects)


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
