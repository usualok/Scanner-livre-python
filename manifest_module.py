"""
================================================================================
MANIFEST MODULE - Import et gestion du MANIFEST
================================================================================
Supporte: CSV et XLSX (Excel/Google Sheets)
Gère: Prix européens (virgule décimale), caractères spéciaux, guillemets
================================================================================
"""

import csv
import os
import re
import database


def clean_price(price_str):
    """
    Nettoie un prix au format: " $ 203,90 " ou "203.90" ou "$203.90"
    Retourne un float
    """
    if not price_str:
        return 0.0
    
    try:
        # Convertit en string au cas où
        price_str = str(price_str)
        
        # Enlève tous les caractères bizarres et guillemets
        price_str = price_str.strip().strip('"').strip("'")
        
        # Enlève le symbole $
        price_str = price_str.replace('$', '')
        
        # Enlève les espaces (normaux et Unicode)
        price_str = price_str.replace(' ', '').replace('\xa0', '').replace('\u202f', '')
        
        # Enlève les caractères Unicode bizarres
        price_str = re.sub(r'[^\d,.]', '', price_str)
        
        # Si virgule européenne (ex: 1.234,56 ou 203,90)
        if ',' in price_str:
            # Si point ET virgule: format 1.234,56 (européen)
            if '.' in price_str:
                # Enlève les points (séparateurs de milliers)
                price_str = price_str.replace('.', '')
            # Remplace virgule par point
            price_str = price_str.replace(',', '.')
        
        return float(price_str) if price_str else 0.0
        
    except Exception as e:
        print(f"   ⚠️ Erreur parsing prix '{price_str}': {e}")
        return 0.0


def clean_upc(upc_str):
    """
    Nettoie un UPC en gardant seulement les chiffres
    """
    if not upc_str:
        return ''
    
    upc_str = str(upc_str).strip()
    # Garde seulement les chiffres
    upc_str = re.sub(r'[^\d]', '', upc_str)
    return upc_str


def import_manifest_csv(filepath):
    """
    Importe le MANIFEST depuis un fichier CSV ou XLSX
    
    Args:
        filepath: Chemin vers le fichier CSV ou XLSX
        
    Returns:
        dict: {'success': bool, 'count': int, 'message': str}
    """
    
    if not os.path.exists(filepath):
        return {
            'success': False,
            'count': 0,
            'message': f"Fichier introuvable: {filepath}"
        }
    
    # Log pour debug
    print(f"📥 Import MANIFEST...")
    print(f"   Fichier: {filepath}")
    
    # Détermine le type de fichier
    file_extension = os.path.splitext(filepath)[1].lower()
    
    try:
        if file_extension == '.csv':
            return import_from_csv(filepath)
        elif file_extension in ['.xlsx', '.xls']:
            return import_from_excel(filepath)
        else:
            return {
                'success': False,
                'count': 0,
                'message': f"Format non supporté: {file_extension}\nUtilisez .csv ou .xlsx"
            }
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return {
            'success': False,
            'count': 0,
            'message': f"Erreur lors de l'import:\n{str(e)}"
        }


def import_from_csv(filepath):
    """
    Importe depuis un fichier CSV
    """
    count = 0
    errors = 0
    skipped = 0
    total_lines = 0
    
    try:
        with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                total_lines += 1
                
                if not row:
                    skipped += 1
                    continue
                
                try:
                    # Extraction et nettoyage des données
                    pallet = str(row.get('Pallet', '')).strip()
                    upc = clean_upc(row.get('UPC', ''))
                    sku = str(row.get('Merchant SKU', '')).strip()
                    
                    # Quantity
                    try:
                        quantity = int(float(row.get('Quantity', 0)))
                    except:
                        quantity = 0
                    
                    category = str(row.get('Category', 'Books')).strip()
                    title = str(row.get('Title', 'Sans titre')).strip()
                    
                    # MSRP avec nettoyage spécial
                    msrp = clean_price(row.get('MSRP', '0'))
                    
                    # Validation UPC (10-14 chiffres)
                    if not upc or len(upc) < 10 or len(upc) > 14:
                        skipped += 1
                        if total_lines <= 5:  # Log seulement les 5 premiers
                            print(f"   ⚠️ Ligne {total_lines}: UPC invalide '{upc}' (longueur: {len(upc)})")
                        continue
                    
                    # Validation titre
                    if not title or title == 'Sans titre':
                        skipped += 1
                        if total_lines <= 5:
                            print(f"   ⚠️ Ligne {total_lines}: Titre manquant")
                        continue
                    
                    # Création de l'item
                    item = {
                        'pallet': pallet,
                        'upc': upc,
                        'sku': sku,
                        'quantity': quantity,
                        'category': category,
                        'title': title,
                        'msrp': msrp
                    }
                    
                    # Insert dans DB
                    database.insert_manifest_item(item)
                    count += 1
                    
                    # Log progression tous les 1000
                    if count % 1000 == 0:
                        print(f"   📊 Importé: {count} livres...")
                    
                except Exception as e:
                    errors += 1
                    if errors <= 5:  # Log seulement les 5 premières erreurs
                        print(f"   ❌ Ligne {total_lines}: {e}")
        
        # Résumé final
        print("=" * 60)
        print(f"   Total lignes: {total_lines}")
        print(f"   ✅ Importé: {count}")
        print(f"   ⚠️ Ignoré: {skipped}")
        print(f"   ❌ Erreurs: {errors}")
        print("=" * 60)
        
        if count > 0:
            return {
                'success': True,
                'count': count,
                'message': f'{count} livres importés avec succès!\n'
                          f'Ignorés: {skipped}\nErreurs: {errors}'
            }
        else:
            return {
                'success': False,
                'count': 0,
                'message': f'Aucun livre importé!\n\n'
                          f'Total lignes: {total_lines}\n'
                          f'Ignorés: {skipped}\n'
                          f'Erreurs: {errors}\n\n'
                          'Vérifiez le format du fichier CSV.'
            }
        
    except Exception as e:
        print(f"   ❌ Erreur fatale: {e}")
        return {
            'success': False,
            'count': count,
            'message': f"Erreur CSV:\n{str(e)}"
        }


def import_from_excel(filepath):
    """
    Importe depuis un fichier Excel (.xlsx ou .xls)
    """
    try:
        # Essaie d'importer openpyxl
        try:
            import openpyxl
        except ImportError:
            return {
                'success': False,
                'count': 0,
                'message': "Module 'openpyxl' manquant.\n\n"
                          "Pour lire les fichiers Excel, installez-le:\n"
                          "pip install openpyxl\n\n"
                          "OU utilisez un fichier CSV à la place."
            }
        
        count = 0
        errors = 0
        skipped = 0
        
        print(f"📥 Import EXCEL...")
        
        # Ouvre le fichier Excel
        workbook = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
        sheet = workbook.active
        
        # Lit la première ligne (headers)
        headers = [cell.value for cell in sheet[1]]
        
        # Trouve les index des colonnes
        col_map = {}
        for i, h in enumerate(headers):
            if h == 'Pallet':
                col_map['pallet'] = i
            elif h == 'UPC':
                col_map['upc'] = i
            elif h == 'Merchant SKU':
                col_map['sku'] = i
            elif h == 'Quantity':
                col_map['quantity'] = i
            elif h == 'Category':
                col_map['category'] = i
            elif h == 'Title':
                col_map['title'] = i
            elif h == 'MSRP':
                col_map['msrp'] = i
        
        # Lit les données (skip header)
        row_num = 0
        for row in sheet.iter_rows(min_row=2, values_only=True):
            row_num += 1
            
            if not any(row):
                skipped += 1
                continue
            
            try:
                pallet = str(row[col_map.get('pallet', 0)] or '').strip()
                upc = clean_upc(row[col_map.get('upc', 1)] or '')
                sku = str(row[col_map.get('sku', 2)] or '').strip()
                
                try:
                    quantity = int(float(row[col_map.get('quantity', 3)] or 0))
                except:
                    quantity = 0
                
                category = str(row[col_map.get('category', 4)] or 'Books').strip()
                title = str(row[col_map.get('title', 5)] or 'Sans titre').strip()
                msrp = clean_price(row[col_map.get('msrp', 6)] or '0')
                
                # Validation
                if not upc or len(upc) < 10 or len(upc) > 14:
                    skipped += 1
                    continue
                
                if not title or title == 'Sans titre':
                    skipped += 1
                    continue
                
                item = {
                    'pallet': pallet,
                    'upc': upc,
                    'sku': sku,
                    'quantity': quantity,
                    'category': category,
                    'title': title,
                    'msrp': msrp
                }
                
                database.insert_manifest_item(item)
                count += 1
                
                if count % 1000 == 0:
                    print(f"   📊 Importé: {count} livres...")
                
            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"   ❌ Ligne {row_num}: {e}")
        
        workbook.close()
        
        print("=" * 60)
        print(f"   ✅ Importé: {count}")
        print(f"   ⚠️ Ignoré: {skipped}")
        print(f"   ❌ Erreurs: {errors}")
        print("=" * 60)
        
        if count > 0:
            return {
                'success': True,
                'count': count,
                'message': f'{count} livres importés avec succès!'
            }
        else:
            return {
                'success': False,
                'count': 0,
                'message': f'Aucun livre importé!\nVérifiez le format du fichier.'
            }
        
    except Exception as e:
        return {
            'success': False,
            'count': 0,
            'message': f"Erreur Excel:\n{str(e)}"
        }


def search_manifest_by_upc(upc):
    """
    Recherche un item dans le MANIFEST par UPC
    """
    return database.get_manifest_by_upc(upc)


def get_progress_summary():
    """
    Retourne un résumé de la progression globale
    """
    try:
        total_items = database.get_total_manifest_items()
        total_scanned = database.get_total_scanned()
        
        if total_items > 0:
            progress_percent = (total_scanned / total_items) * 100
        else:
            progress_percent = 0
        
        return {
            'total_items': total_items,
            'total_scanned': total_scanned,
            'remaining': total_items - total_scanned,
            'progress_percent': round(progress_percent, 1)
        }
    except Exception as e:
        return {
            'total_items': 0,
            'total_scanned': 0,
            'remaining': 0,
            'progress_percent': 0
        }


# Test unitaire
if __name__ == "__main__":
    # Test de la fonction clean_price
    test_prices = [
        '" $ 203,90 "',
        '" $ 2\u202f650,70 "',
        '$960.50',
        '203,90',
        '1.234,56'
    ]
    
    print("Test clean_price:")
    for p in test_prices:
        print(f"  {p} -> {clean_price(p)}")