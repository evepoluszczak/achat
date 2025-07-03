# Remplacez le contenu de votre app.py par celui-ci

import streamlit as st
import pandas as pd
import math
import database as db

# --- Configuration de la Page ---
st.set_page_config(layout="wide", page_title="Gestion Fournisseurs GA")

# --- Initialisation de la DB ---
db.init_db()

# --- État de Session ---
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1

RECORDS_PER_PAGE = 10

# --- Fonctions de l'UI ---
@st.dialog("Ajouter / Modifier un Fournisseur")
def supplier_form(supplier_id=None):
    """Affiche un formulaire pour créer ou modifier un fournisseur."""
    if supplier_id:
        supplier_data = db.get_supplier_by_id(supplier_id)
    else:
        supplier_data = {}

    # Pour l'autocomplétion
    suppliers_map = db.get_suppliers_map()
    supplier_names = [""] + list(suppliers_map.keys())

    with st.form("supplier_form"):
        # Section d'autocomplétion
        st.write("Pour pré-remplir, choisissez un fournisseur connu :")
        selected_name = st.selectbox("Choisir un fournisseur", options=supplier_names, index=0, label_visibility="collapsed")
        
        st.markdown("---")

        # Pré-remplissage des champs
        default_name = selected_name if selected_name else supplier_data.get('raison_sociale', '')
        default_id_oracle = suppliers_map.get(selected_name, supplier_data.get('id_oracle', ''))


        tab1, tab2 = st.tabs(["📄 Informations Générales", "📞 Contacts & Suivi"])
        
        with tab1:
            raison_sociale = st.text_input("Raison Sociale", value=default_name)
            id_oracle = st.text_input("ID Oracle", value=default_id_oracle)
            adresse = st.text_area("Adresse", value=supplier_data.get('adresse', ''))
            pays_canton = st.selectbox("Pays/Canton", ["Genève", "Vaud", "France", "Autre"], index=0)
            est_prospect = st.checkbox("Prospect", value=supplier_data.get('est_prospect', False))

        with tab2:
            contacts = st.text_area("Contacts", value=supplier_data.get('contacts', ''))
            tags = st.multiselect("Tags", ["Fournisseur critique", "Conforme", "RSE+"], default=supplier_data.get('tags', '').split(',') if supplier_data.get('tags') else [])
            statut_audit = st.selectbox("Statut Audit", ["Non concerné", "En attente", "Réalisé"], index=0)
            commentaires = st.text_area("Commentaires", value=supplier_data.get('commentaires', ''))

        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            form_data = {
                "raison_sociale": raison_sociale, "id_oracle": id_oracle, "adresse": adresse,
                "pays_canton": pays_canton, "est_prospect": est_prospect, "contacts": contacts,
                "tags": tags, "statut_audit": statut_audit, "commentaires": commentaires
            }
            if supplier_id:
                db.update_supplier(supplier_id, form_data)
                st.toast(f"Fournisseur '{raison_sociale}' mis à jour !", icon="✅")
            else:
                db.add_supplier(form_data)
                st.toast(f"Fournisseur '{raison_sociale}' ajouté !", icon="🎉")
            st.rerun()


# --- BARRE LATERALE (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Actions")
    st.subheader("Importer une liste")
    uploaded_file = st.file_uploader(
        "Importer un fichier (CSV ou Excel)", 
        type=['csv', 'xlsx']
    )
    if uploaded_file:
        if st.button("Lancer l'importation"):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Vérification des colonnes
                if 'Raison Sociale' in df.columns and 'ID Oracle' in df.columns:
                    with st.spinner("Importation en cours..."):
                        inserted, updated = db.upsert_suppliers_from_df(df)
                    st.success(f"Importation terminée ! 🎉\n- {inserted} fournisseurs ajoutés.\n- {updated} fournisseurs mis à jour.")
                else:
                    st.error("Le fichier doit contenir les colonnes 'Raison Sociale' et 'ID Oracle'.")
            except Exception as e:
                st.error(f"Une erreur est survenue lors de l'import : {e}")


# --- AFFICHAGE PRINCIPAL ---
st.title("✈️ Outil de Gestion des Données Fournisseurs")

col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input("Rechercher par raison sociale", placeholder="Rechercher...")
with col2:
    st.write("")
    st.write("")
    if st.button("➕ Ajouter un nouveau fournisseur", use_container_width=True):
        supplier_form()

# Récupération des données
offset = (st.session_state.page_number - 1) * RECORDS_PER_PAGE
suppliers_df, total_records = db.get_suppliers(RECORDS_PER_PAGE, offset, search_term)
total_pages = math.ceil(total_records / RECORDS_PER_PAGE) if total_records > 0 else 1

st.header("Liste des Fournisseurs")
st.write(f"Affichage de {len(suppliers_df)} sur {total_records} fournisseurs.")

if not suppliers_df.empty:
    for index, row in suppliers_df.iterrows():
        expander = st.expander(f"**{row['raison_sociale']}** (ID: {row['id']})")
        with expander:
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Statut Audit:** {row['statut_audit']}")
                st.write(f"**Pays/Canton:** {row['pays_canton']}")
                st.write(f"**Tags:** {row['tags']}")
            with col2:
                st.write(f"**ID Oracle:** {row['id_oracle']}")
                st.write(f"**Adresse:** {row['adresse']}")
                st.write(f"**Prospect:** {'Oui' if row['est_prospect'] else 'Non'}")
            
            with col3:
                if st.button("Modifier", key=f"edit_{row['id']}", use_container_width=True):
                    supplier_form(row['id'])
                if st.button("Supprimer", key=f"del_{row['id']}", type="primary", use_container_width=True):
                    db.delete_supplier(row['id'])
                    st.toast(f"Fournisseur '{row['raison_sociale']}' supprimé.", icon="🗑️")
                    st.rerun()
    
    st.write("")
    col_nav1, col_nav2, col_nav3 = st.columns([2, 1, 2])
    with col_nav1:
        if st.session_state.page_number > 1:
            if st.button("⬅️ Précédent"):
                st.session_state.page_number -= 1
                st.rerun()
    with col_nav2:
        st.write(f"Page **{st.session_state.page_number}** sur **{total_pages}**")
    with col_nav3:
        if st.session_state.page_number < total_pages:
            if st.button("Suivant ➡️", use_container_width=True):
                st.session_state.page_number += 1
                st.rerun()
else:
    st.info("Aucun fournisseur trouvé. Importez une liste ou cliquez sur 'Ajouter un nouveau fournisseur' pour commencer.")
