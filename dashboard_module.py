"""
Module Dashboard - Scanner Livre App
Statistiques et visualisations
"""

from datetime import datetime, timedelta
import database
import config

# ========================================================================
# METRICS
# ========================================================================

def get_dashboard_metrics():
    """
    Toutes les métriques pour le dashboard.
    Returns: dict
    """
    # Manifest stats
    manifest_count = database.count_manifest()
    
    # Scans
    total_scanned = database.get_total_scanned()
    scans_today = database.get_scans_today_quantity()
    enriched_count = database.get_enriched_count()
    exported_count = database.get_exported_count()
    
    # Sales
    sales_summary = get_sales_summary_quick()
    
    # Progress
    progress_percent = (total_scanned / manifest_count * 100) if manifest_count > 0 else 0
    
    return {
        # Manifest
        'manifest_total': manifest_count,
        
        # Scans
        'total_scanned': total_scanned,
        'scans_today': scans_today,
        'enriched_count': enriched_count,
        'exported_count': exported_count,
        'remaining': max(0, manifest_count - total_scanned),
        
        # Progress
        'progress_percent': round(progress_percent, 1),
        
        # Sales
        'total_sales': sales_summary['total_items'],
        'total_revenue': sales_summary['revenue'],
        
        # Status breakdown
        'by_status': database.get_scans_by_status(),
        'by_condition': database.get_scans_by_condition()
    }

def get_sales_summary_quick():
    """Quick sales summary."""
    all_sales = database.get_all_sales()
    
    total_items = sum(s['quantity'] for s in all_sales)
    revenue = database.get_total_revenue()
    
    return {
        'total_items': total_items,
        'revenue': revenue
    }

# ========================================================================
# CHARTS DATA
# ========================================================================

def get_daily_scans_chart_data(days=7):
    """
    Données pour graphique scans quotidiens.
    Args: days (int)
    Returns: dict avec labels et values
    """
    data = database.get_daily_scans(days)
    
    labels = []
    values = []
    
    for row in data:
        # Format date: MM-DD
        date_obj = datetime.fromisoformat(row['date'])
        label = date_obj.strftime('%m-%d')
        labels.append(label)
        values.append(row['quantity'])
    
    return {
        'labels': labels,
        'values': values
    }

def get_condition_pie_chart_data():
    """
    Données pour pie chart conditions.
    Returns: dict
    """
    data = database.get_scans_by_condition()
    
    labels = []
    values = []
    
    for row in data:
        labels.append(row['condition'])
        values.append(row['total_qty'])
    
    return {
        'labels': labels,
        'values': values
    }

def get_status_bar_chart_data():
    """
    Données pour bar chart status.
    Returns: dict
    """
    data = database.get_scans_by_status()
    
    labels = []
    values = []
    
    for row in data:
        labels.append(row['status'])
        values.append(row['total_qty'])
    
    return {
        'labels': labels,
        'values': values
    }

# ========================================================================
# LEADERBOARDS
# ========================================================================

def get_top_pallets(limit=5):
    """Top pallets par progression."""
    pallets = database.get_progress_by_pallet()
    
    # Sort by scanned quantity desc
    sorted_pallets = sorted(pallets, key=lambda x: x['scanned_quantity'], reverse=True)
    
    return sorted_pallets[:limit]

def get_recent_activity(limit=10):
    """Activité récente (derniers scans)."""
    return database.get_recent_scans(limit)

# ========================================================================
# SUMMARY STRINGS
# ========================================================================

def get_progress_summary_text():
    """Texte résumé progression."""
    metrics = get_dashboard_metrics()
    
    text = f"""
📊 PROGRESSION GLOBALE
{'='*40}
Total livres: {metrics['manifest_total']:,}
Scannés: {metrics['total_scanned']:,} ({metrics['progress_percent']}%)
Restants: {metrics['remaining']:,}

📅 AUJOURD'HUI
{'='*40}
Scans: {metrics['scans_today']}

💰 VENTES
{'='*40}
Vendus: {metrics['total_sales']:,} livres
Revenue: ${metrics['total_revenue']:,.2f}

✅ STATUT
{'='*40}
Enrichis: {metrics['enriched_count']}
Exportés: {metrics['exported_count']}
"""
    return text.strip()

# ========================================================================
# DEBUG
# ========================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("DASHBOARD MODULE - TEST")
    print("=" * 60)
    
    # Metrics
    metrics = get_dashboard_metrics()
    print(f"\nMétriques:")
    print(f"  Total scanné: {metrics['total_scanned']}")
    print(f"  Aujourd'hui: {metrics['scans_today']}")
    print(f"  Progression: {metrics['progress_percent']}%")
    
    # Summary
    print(f"\n{get_progress_summary_text()}")
    
    print("\n" + "=" * 60)