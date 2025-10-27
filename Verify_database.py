"""
Script de vérification de la base de données scans.db
Ce script permet de voir si les scans sont bien enregistrés
"""

import sqlite3
import os

# Chemin de la base (même dossier que ce script)
DB_PATH = "scans.db"

def verify_database():
    """Vérifie le contenu de la base de données"""
    
    if not os.path.exists(DB_PATH):
        print("❌ Base de données scans.db introuvable!")
        print(f"   Cherchée dans: {os.path.abspath(DB_PATH)}")
        return
    
    print("✅ Base de données trouvée!")
    print(f"   Emplacement: {os.path.abspath(DB_PATH)}")
    print()
    
    # Connexion
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Vérifie les tables
    print("=" * 50)
    print("📋 TABLES DANS LA BASE")
    print("=" * 50)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    print()
    
    # 2. Compte les scans
    print("=" * 50)
    print("📊 STATISTIQUES SCANS")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM scans")
    total_rows = cursor.fetchone()[0]
    print(f"  Nombre de lignes dans 'scans': {total_rows}")
    
    cursor.execute("SELECT SUM(quantity) FROM scans")
    total_qty = cursor.fetchone()[0] or 0
    print(f"  Total de livres scannés: {total_qty}")
    
    cursor.execute("SELECT COUNT(DISTINCT upc) FROM scans")
    unique_upcs = cursor.fetchone()[0]
    print(f"  UPCs uniques: {unique_upcs}")
    print()
    
    # 3. Affiche les 10 derniers scans
    print("=" * 50)
    print("📚 DERNIERS SCANS (10 max)")
    print("=" * 50)
    
    cursor.execute("""
        SELECT timestamp, bin, upc, condition, quantity, title
        FROM scans
        ORDER BY timestamp DESC
        LIMIT 10
    """)
    
    scans = cursor.fetchall()
    
    if not scans:
        print("  ⚠️ Aucun scan trouvé dans la base!")
    else:
        for scan in scans:
            timestamp, bin_code, upc, condition, qty, title = scan
            title_short = title[:40] + "..." if title and len(title) > 40 else (title or "Sans titre")
            print(f"  [{timestamp[:19]}] {bin_code} | {upc} | {condition} | Qty: {qty}")
            print(f"    → {title_short}")
            print()
    
    # 4. Vérifie MANIFEST
    print("=" * 50)
    print("📦 STATISTIQUES MANIFEST")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM manifest")
    manifest_count = cursor.fetchone()[0]
    print(f"  Livres dans MANIFEST: {manifest_count}")
    
    if manifest_count > 0:
        cursor.execute("SELECT SUM(quantity) FROM manifest")
        manifest_qty = cursor.fetchone()[0] or 0
        print(f"  Quantité totale MANIFEST: {manifest_qty}")
    print()
    
    # 5. Vérifie dimensions cache
    print("=" * 50)
    print("📏 CACHE DIMENSIONS")
    print("=" * 50)
    
    cursor.execute("SELECT COUNT(*) FROM dimensions")
    dims_count = cursor.fetchone()[0]
    print(f"  UPCs avec dimensions en cache: {dims_count}")
    print()
    
    conn.close()
    
    print("=" * 50)
    print("✅ VÉRIFICATION TERMINÉE")
    print("=" * 50)

if __name__ == "__main__":
    verify_database()