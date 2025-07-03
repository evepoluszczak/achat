import streamlit as st
import pandas as pd
import os
import plotly.express as px

# --- Configuration ---
st.set_page_config(page_title="Visualisation des données", layout="wide")

# --- File Paths ---
DATA_FILE = 'data/suppliers.csv'

# --- Utility Functions ---
def load_data():
    """Loads data from the CSV file."""
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # Ensure columns that can be lists are treated as strings
        for col in ['tags', 'documents_lies']:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna('')
        return df
    return pd.DataFrame()

# --- Initialization ---
df = load_data()

# --- Streamlit Interface ---
st.title("📊 Visualisation et Recherche")

if df.empty:
    st.warning("Aucune donnée fournisseur n'a été trouvée. Veuillez en ajouter via la page 'Entrée des données'.")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("Filtres")

    # Text search filter
    search_term = st.sidebar.text_input("Rechercher par nom, contact, commentaire...")

    # Tag filter
    all_tags = sorted(list(set(tag for sublist in df['tags'].str.split(', ') for tag in sublist if tag)))
    selected_tags = st.sidebar.multiselect("Filtrer par Tags", options=all_tags)

    # Audit status filter
    all_status = df['statut_audit'].unique().tolist()
    selected_status = st.sidebar.multiselect("Filtrer par Statut d'audit", options=all_status)

    # Location filter
    all_locations = df['pays_canton'].unique().tolist()
    selected_locations = st.sidebar.multiselect("Filtrer par Pays/Canton", options=all_locations)

    # Applying filters
    filtered_df = df.copy()

    if search_term:
        # Case-insensitive search across multiple columns
        filtered_df = filtered_df[filtered_df.apply(
            lambda row: any(search_term.lower() in str(cell).lower() for cell in row),
            axis=1
        )]

    if selected_tags:
        # Supplier must have AT LEAST ONE of the selected tags
        filtered_df = filtered_df[filtered_df['tags'].apply(lambda x: any(tag in x for tag in selected_tags))]

    if selected_status:
        filtered_df = filtered_df[filtered_df['statut_audit'].isin(selected_status)]

    if selected_locations:
        filtered_df = filtered_df[filtered_df['pays_canton'].isin(selected_locations)]

    st.header("Base de données Fournisseurs")
    st.markdown(f"**{len(filtered_df)}** fournisseur(s) trouvé(s) sur **{len(df)}** au total.")
    
    # Display the filtered DataFrame
    st.dataframe(filtered_df, use_container_width=True)

    st.download_button(
        label="📥 Télécharger les données filtrées (CSV)",
        data=filtered_df.to_csv(index=False).encode('utf-8'),
        file_name='donnees_fournisseurs_filtrees.csv',
        mime='text/csv',
    )

    # --- Visualization Section (similar to Power BI) ---
    st.header("📈 Statistiques")
    
    if not filtered_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Fournisseurs par Pays/Canton")
            location_counts = filtered_df['pays_canton'].value_counts()
            fig_loc = px.pie(values=location_counts.values, names=location_counts.index, title="Répartition géographique")
            st.plotly_chart(fig_loc, use_container_width=True)

        with col2:
            st.subheader("Fournisseurs par Statut d'audit")
            status_counts = filtered_df['statut_audit'].value_counts()
            fig_status = px.bar(status_counts, x=status_counts.index, y=status_counts.values, 
                                title="Répartition par statut d'audit", labels={'x': 'Statut', 'y': 'Nombre'})
            st.plotly_chart(fig_status, use_container_width=True)
    else:
        st.info("Aucune donnée à afficher pour les filtres sélectionnés.")
