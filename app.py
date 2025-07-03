# Remplacez entièrement le contenu de app.py par ce code.

import streamlit as st
import pandas as pd
import math
import database as db

# --- Configuration de la Page ---
st.set_page_config(layout="wide", page_title="Gestion Fournisseurs GA")

# --- Constantes pour les options ---
TAG_OPTIONS = ["Fournisseur critique", "Fournisseur non critique", "Conforme", "Non conforme", "Audit à planifier", "RSE+", "Innovation"]
AUDIT_STATUS_OPTIONS = ["Non concerné", "En attente", "Planifié", "Réalisé", "Non-conformité majeure"]

# --- État de Session ---
if 'page_number' not in st.session_state:
    st.session_state.page_number = 1
if 'import_analysis' not in st.session_state:
    st.session_state.import_analysis = None

RECORDS_PER_PAGE = 10

# --- Fonctions de l'UI ---
@st.dialog("Ajouter / Modifier un Fournisseur")
def supplier_form(supplier_id=None):
    # (Le code de cette fonction ne change pas, il est identique à la version précédente)
    if supplier_id:
        supplier_data = db.get_supplier_by_id(supplier_id)
    else:
        supplier_data = {}

    prefill_data = db.get_suppliers_prefill_data()
    supplier_names = [""] + list(prefill_data.keys())

    with st.form("supplier_form"):
        st.write("Pour pré-remplir, choisissez un fournisseur connu :")
        selected_name = st.selectbox("Choisir un fournisseur", options=supplier_names, index=0, label_visibility="collapsed")
        st.markdown("---")
        default_name = selected_name if selected_name else supplier_data.get('raison_sociale', '')
        selected_data = prefill_data.get(selected_name, {})
        default_id_oracle = selected_data.get('id_oracle', supplier_data.get('id_oracle', ''))
        default_adresse = selected_data.get('adresse', supplier_data.get('adresse', ''))

        tab1, tab2 = st.tabs(["📄 Informations Générales", "📞 Contacts & Suivi"])
        with tab1:
            raison_sociale = st.text_input("Raison Sociale", value=default_name)
            id_oracle = st.text_input("ID Oracle", value=default_id_oracle)
            adresse = st.text_area("Adresse", value=default_adresse)
            pays_canton = st.selectbox("Pays/Canton", ["Genève", "Vaud", "France", "Autre"], index=0)
            est_prospect = st.checkbox("Prospect", value=supplier_data.get('est_prospect', False))
        with tab2:
            contacts = st.text_area("Contacts", value=supplier_data.get('contacts', ''))
            tags = st.multiselect("Tags", options=TAG_OPTIONS, default=supplier_data.get('tags', '').split(',') if supplier_data.get('tags') else [])
            statut_audit = st.selectbox("Statut Audit", options=AUDIT_STATUS_OPTIONS, index=0)
            commentaires = st.text_area("Commentaires", value=supplier_data.get('commentaires', ''))

        submitted = st.form_submit_button("Enregistrer")
        if submitted:
            form_data = {"raison_sociale": raison_sociale, "id_oracle": id_oracle, "adresse": adresse, "pays_canton": pays_canton, "est_prospect": est_prospect, "contacts": contacts, "tags": tags, "statut_audit": statut_audit, "commentaires": commentaires}
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
    uploaded_file = st.file_uploader("Importer un fichier (CSV ou Excel)", type=['csv', 'xlsx'])
    
    if uploaded_file:
        if st.button("Analyser le fichier d'import"):
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                required_cols = ['Raison Sociale', 'ID Oracle', 'Adresse']
                if all(col in df.columns for col in required_cols):
                    with st.spinner("Analyse en cours..."):
                        new, conflicts = db.analyze_import_data(df)
                        # Stocker les résultats dans l'état de la session
                        st.session_state.import_analysis = {'new': new, 'conflicts': conflicts}
                else:
                    st.error(f"Le fichier doit contenir les colonnes : {', '.join(required_cols)}.")
                    st.session_state.import_analysis = None
            except Exception as e:
                st.error(f"Une erreur est survenue lors de l'analyse : {e}")
                st.session_state.import_analysis = None
    
    # --- Section de Confirmation d'Import ---
    if st.session_state.import_analysis:
        st.markdown("---")
        st.subheader("Résultat de l'analyse")
        
        analysis = st.session_state.import_analysis
        new_suppliers = analysis['new']
        conflicts = analysis['conflicts']

        st.info(f"**{len(new_suppliers)}** nouveaux fournisseurs seront ajoutés.")
        
        if conflicts:
            st.warning(f"**{len(conflicts)}** fournisseurs existants ont des données différentes.")
            approved_conflicts = []
            with st.form("conflict_form"):
                for conflict in conflicts:
                    with st.expander(f"**{conflict['raison_sociale']}** - Données modifiées"):
                        st.write(f"**ID Oracle :** `{conflict['old_id']}` ➡️ `{conflict['new_id']}`")
                        st.write(f"**Adresse :** `{conflict['old_adresse']}` ➡️ `{conflict['new_adresse']}`")
                        
                        approve = st.checkbox("Approuver ce changement", key=conflict['raison_sociale'])
                        if approve:
                            approved_conflicts.append(conflict)
                
                submitted = st.form_submit_button("Confirmer et appliquer les changements")
                if submitted:
                    with st.spinner("Application des changements..."):
                        inserted, updated = db.execute_import(new_suppliers, approved_conflicts)
                    st.success(f"{inserted} fournisseurs ajoutés, {updated} mis à jour.")
                    st.session_state.import_analysis = None # Nettoyer l'état
                    st.rerun()
        else:
            if st.button("Confirmer l'ajout des nouveaux fournisseurs"):
                with st.spinner("Application des changements..."):
                    inserted, _ = db.execute_import(new_suppliers, [])
                st.success(f"{inserted} nouveaux fournisseurs ajoutés.")
                st.session_state.import_analysis = None # Nettoyer l'état
                st.rerun()


# --- AFFICHAGE PRINCIPAL ---
# (Le code de cette section ne change pas, il est identique à la version précédente)
st.title("✈️ Outil de Gestion des Données Fournisseurs")
col1, col2 = st.columns([3, 1])
with col1:
    search_term = st.text_input("Rechercher par raison sociale", placeholder="Rechercher...")
with col2:
    st.write("")
    st.write("")
    if st.button("➕ Ajouter un nouveau fournisseur", use_container_width=True):
        supplier_form()
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
