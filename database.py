# Ajoutez ces deux fonctions à votre fichier database.py

def get_suppliers_map():
    """Récupère un dictionnaire {raison_sociale: id_oracle}."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT raison_sociale, id_oracle FROM suppliers", conn)
    conn.close()
    # Filtre les fournisseurs qui ont un ID Oracle
    df = df.dropna(subset=['id_oracle'])
    return pd.Series(df.id_oracle.values, index=df.raison_sociale).to_dict()

def upsert_suppliers_from_df(df):
    """
    Met à jour ou insère des fournisseurs depuis un DataFrame.
    Le DataFrame doit contenir les colonnes 'Raison Sociale' et 'ID Oracle'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    updated_count = 0
    inserted_count = 0

    for _, row in df.iterrows():
        raison_sociale = row['Raison Sociale']
        id_oracle = row['ID Oracle']

        # Vérifie si le fournisseur existe déjà
        cursor.execute("SELECT id FROM suppliers WHERE raison_sociale = ?", (raison_sociale,))
        result = cursor.fetchone()

        if result:
            # Met à jour l'ID Oracle s'il existe déjà
            supplier_id = result[0]
            cursor.execute("UPDATE suppliers SET id_oracle = ?, derniere_modif = CURRENT_TIMESTAMP WHERE id = ?", (id_oracle, supplier_id))
            updated_count += 1
        else:
            # Insère le nouveau fournisseur s'il n'existe pas
            cursor.execute("""
                INSERT INTO suppliers (raison_sociale, id_oracle, est_prospect)
                VALUES (?, ?, ?)
            """, (raison_sociale, id_oracle, False))
            inserted_count += 1
            
    conn.commit()
    conn.close()
    return inserted_count, updated_count
