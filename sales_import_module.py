"""
Module Import Ventes - Scanner Livre App
Importe les ventes eBay et met à jour les stocks
"""

import csv
from pathlib import Path
from datetime import datetime
import database
import config

# ========================================================================
# IMPORT VENTES
# ========================================================================

def import_sales_csv(csv_path, progress_callback=None):
    """
    Importe CSV ventes eBay.
    Args:
        csv_path (str): Chemin fichier CSV eBay
        progress_callback (callable): fonction(current, total, message)
    Returns:
        dict: {
            'success': bool,
            'imported': int,
            'total_revenue': float,
            'errors': list,
            'message': str
        }
    """
    print(f"\n📥 Import ventes eBay...")
    print(f"   Fichier: {csv_path}")
    print("=" * 60)
    
    if not Path(csv_path).exists():
        return {
            'success': False,
            'imported': 0,
            'total_revenue': 0,
            'errors': [f'Fichier introuvable: {csv_path}'],
            'message': 'Fichier introuvable'
        }
    
    imported = 0
    total_revenue = 0.0
    errors = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            rows = list(reader)
            total = len(rows)
            
            print(f"   Total lignes: {total}")
            
            for i, row in enumerate(rows):
                if progress_callback:
                    progress_callback(i + 1, total, f"Import vente {i + 1}/{total}")
                
                try:
                    # Extract fields (noms de colonnes eBay)
                    order_number = row.get('Order Number') or row.get('Order number') or ''
                    
                    # UPC est dans Custom label (SKU)
                    upc = row.get('Custom label (SKU)') or row.get('Custom Label') or ''
                    
                    quantity = row.get('Quantity') or row.get('Quantity sold') or 1
                    sale_price = row.get('Sale Price') or row.get('Price') or 0
                    sale_date = row.get('Sale Date') or row.get('Date') or datetime.now().isoformat()
                    buyer = row.get('Buyer Username') or row.get('Buyer') or ''
                    
                    # Validate UPC
                    if not upc:
                        errors.append(f"Ligne {i+2}: UPC manquant")
                        continue
                    
                    # Convert types
                    try:
                        quantity = int(quantity)
                        sale_price = float(str(sale_price).replace('$', '').replace(',', ''))
                    except ValueError:
                        errors.append(f"Ligne {i+2}: Erreur conversion quantity/price")
                        continue
                    
                    # Insert sale
                    sale_data = {
                        'order_number': order_number,
                        'upc': upc,
                        'quantity': quantity,
                        'sale_price': sale_price,
                        'sale_date': sale_date,
                        'buyer_username': buyer
                    }
                    
                    database.insert_sale(sale_data)
                    
                    # Update scan qty vendue
                    database.update_scan_qty_vendue(upc, quantity)
                    
                    # Check if sold out
                    check_and_update_sold_out(upc)
                    
                    # Revenue
                    revenue = quantity * sale_price
                    total_revenue += revenue
                    
                    imported += 1
                
                except Exception as e:
                    errors.append(f"Ligne {i+2}: {str(e)}")
            
            print(f"   ✅ Importé: {imported} ventes")
            print(f"   💰 Revenue: ${total_revenue:,.2f}")
            if errors:
                print(f"   ❌ Erreurs: {len(errors)}")
            print("=" * 60)
            
            return {
                'success': True,
                'imported': imported,
                'total_revenue': total_revenue,
                'errors': errors,
                'message': f"{imported} vente(s) importée(s), ${total_revenue:,.2f} revenue"
            }
    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        print("=" * 60)
        
        return {
            'success': False,
            'imported': 0,
            'total_revenue': 0,
            'errors': [str(e)],
            'message': f'Erreur: {str(e)}'
        }

# ========================================================================
# STATUS UPDATES
# ========================================================================

def check_and_update_sold_out(upc):
    """
    Vérifie si un UPC est sold out et met à jour status.
    Args: upc (str)
    """
    # Get total scanned
    scans = database.get_scans_by_upc(upc)
    total_scanned = sum(scan['quantity'] for scan in scans)
    total_vendue = sum(scan['qty_vendue'] for scan in scans)
    
    # If sold out
    if total_vendue >= total_scanned:
        database.update_scan_status(upc, config.STATUS_SOLD)

def update_all_status():
    """
    Met à jour tous les status basé sur qty vendue.
    """
    query = "SELECT DISTINCT upc FROM scans"
    upcs = database.fetch_all(query)
    
    for item in upcs:
        check_and_update_sold_out(item['upc'])

# ========================================================================
# ANALYTICS
# ========================================================================

def get_sales_summary():
    """
    Résumé des ventes.
    Returns: dict
    """
    # Total sales
    all_sales = database.get_all_sales()
    
    total_orders = len(all_sales)
    total_items = sum(sale['quantity'] for sale in all_sales)
    total_revenue = database.get_total_revenue()
    
    # Average
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    avg_item_price = total_revenue / total_items if total_items > 0 else 0
    
    return {
        'total_orders': total_orders,
        'total_items_sold': total_items,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'avg_item_price': avg_item_price
    }

def get_top_sellers(limit=10):
    """
    Top livres vendus.
    Args: limit (int)
    Returns: list of dict
    """
    query = f"""
        SELECT 
            s.upc,
            s.title,
            SUM(sa.quantity) as total_sold,
            SUM(sa.quantity * sa.sale_price) as revenue
        FROM sales sa
        JOIN scans s ON sa.upc = s.upc
        GROUP BY s.upc, s.title
        ORDER BY total_sold DESC
        LIMIT ?
    """
    return database.fetch_all(query, (limit,))

def get_sales_by_condition():
    """
    Ventes par condition.
    Returns: list of dict
    """
    query = """
        SELECT 
            s.condition,
            COUNT(sa.id) as order_count,
            SUM(sa.quantity) as items_sold,
            SUM(sa.quantity * sa.sale_price) as revenue
        FROM sales sa
        JOIN scans s ON sa.upc = s.upc
        GROUP BY s.condition
        ORDER BY revenue DESC
    """
    return database.fetch_all(query)

# ========================================================================
# DEBUG
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SALES IMPORT MODULE - TEST")
    print("=" * 60)
    
    # Summary
    summary = get_sales_summary()
    print(f"\nRésumé ventes:")
    print(f"  Total commandes: {summary['total_orders']}")
    print(f"  Total items vendus: {summary['total_items_sold']}")
    print(f"  Revenue total: ${summary['total_revenue']:,.2f}")
    print(f"  Prix moyen/item: ${summary['avg_item_price']:.2f}")
    
    print("\n" + "=" * 60)