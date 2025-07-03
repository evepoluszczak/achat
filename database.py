# Remplacez les fonctions get_suppliers_map et upsert_suppliers_from_df
# dans votre fichier database.py par celles-ci.

def get_suppliers_prefill_data():
    """Récupère un dictionnaire de données pour le pré-remplissage du formulaire."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT raison_sociale, id_oracle, adresse FROM suppliers", conn)
    conn.close()
    
    prefill_data = {}
    for _, row in df.iterrows():
        prefill_data[row['raison_sociale']] = {
            'id_oracle': row['id_oracle'],
            'adresse': row['adresse']
        }
    return prefill_data

def upsert_suppliers_from_df(df):
    """
    Met à jour ou insère des fournisseurs depuis un DataFrame.
    Le DataFrame doit contenir 'Raison Sociale', 'ID Oracle', et 'Adresse'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updated_count = 0
    inserted_count = 0

    for _, row in df.iterrows():
        raison_sociale = row['Raison Sociale']
        id_oracle = str(row['ID Oracle']) if pd.notna(row['ID Oracle']) else None
        adresse = str(row['Adresse']) if pd.notna(row['Adresse']) else None

        cursor.execute("SELECT id FROM suppliers WHERE raison_sociale = ?", (raison_sociale,))
        result = cursor.fetchone()

        if result:
            supplier_id = result[0]
            cursor.execute("""
                UPDATE suppliers 
                SET id_oracle = ?, adresse = ?, derniere_modif = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (id_oracle, adresse, supplier_id))
            updated_count += 1
        else:
            cursor.execute("""
                INSERT INTO suppliers (raison_sociale, id_oracle, est_prospect, adresse)
                VALUES (?, ?, ?, ?)
            """, (raison_sociale, id_oracle, False, adresse))
            inserted_count += 1
            
    conn.commit()
    conn.close()
    return inserted_count, updated_count
