"""
================================================================================
SCANNER LIVRE - APPLICATION PRINCIPALE
================================================================================
Interface graphique complète avec onglets pour scanner, enrichir et vendre
10,000+ livres sur eBay.

Auteur: Scanner Livre Project
Date: 2025-10-28
Version: 2.0 (avec corrections Dashboard + nouvel onglet Base de données)
================================================================================
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from datetime import datetime, date
import sys
import csv

# Import des modules du projet
try:
    import config
    import database
    import utils
    import enrichment_module
    import ebay_export_module
    import manifest_module
    import sales_import_module
    import dashboard_module
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Assurez-vous que tous les modules sont dans le même dossier que main_app.py")
    sys.exit(1)


class ScannerLivreApp(tk.Tk):
    """Application principale Scanner Livre"""
    
    def __init__(self):
        super().__init__()
        
        # Configuration fenêtre
        self.title("📚 Scanner Livre Pro - v2.0")
        self.geometry("1200x800")
        
        # Initialisation base de données
        try:
            database.init_database()
        except Exception as e:
            messagebox.showerror("Erreur DB", f"Impossible d'initialiser la base de données:\n{e}")
            self.destroy()
            return
        
        # Variables
        self.status_text = tk.StringVar(value="Prêt")
        
        # Création de l'interface
        self.create_menu()
        self.create_notebook()
        self.create_status_bar()
        
        # Configuration style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Centrer fenêtre
        self.center_window()
        
    def center_window(self):
        """Centre la fenêtre sur l'écran"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_menu(self):
        """Crée la barre de menu"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="💾 Backup DB", command=self.backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit_app)
        
        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        tools_menu.add_command(label="⚙️ Paramètres", command=self.show_settings)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="📖 Guide d'utilisation", command=self.show_help)
        help_menu.add_command(label="À propos", command=self.show_about)
    
    def create_notebook(self):
        """Crée le notebook avec tous les onglets"""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Onglet 1: Scanner
        self.scanner_tab = ScannerTab(self.notebook, self)
        self.notebook.add(self.scanner_tab, text="📱 Scanner")
        
        # Onglet 2: Enrichissement
        self.enrichment_tab = EnrichmentTab(self.notebook, self)
        self.notebook.add(self.enrichment_tab, text="📚 Enrichissement")
        
        # Onglet 3: Export eBay
        self.export_tab = ExportTab(self.notebook, self)
        self.notebook.add(self.export_tab, text="📤 Export eBay")
        
        # Onglet 4: Ventes
        self.sales_tab = SalesTab(self.notebook, self)
        self.notebook.add(self.sales_tab, text="📥 Ventes")
        
        # Onglet 5: MANIFEST
        self.manifest_tab = ManifestTab(self.notebook, self)
        self.notebook.add(self.manifest_tab, text="📋 MANIFEST")
        
        # Onglet 6: 🆕 BASE DE DONNÉES SCANS
        self.database_tab = DatabaseTab(self.notebook, self)
        self.notebook.add(self.database_tab, text="🗄️ Base de données")
        
        # Onglet 7: Dashboard
        self.dashboard_tab = DashboardTab(self.notebook, self)
        self.notebook.add(self.dashboard_tab, text="📊 Dashboard")
    
    def create_status_bar(self):
        """Crée la barre de statut en bas"""
        status_frame = ttk.Frame(self)
        status_frame.pack(side='bottom', fill='x')
        
        status_label = ttk.Label(status_frame, textvariable=self.status_text, relief='sunken', anchor='w')
        status_label.pack(side='left', fill='x', expand=True, padx=5, pady=2)
        
        # Date/heure
        time_label = ttk.Label(status_frame, text=datetime.now().strftime("%Y-%m-%d %H:%M"), relief='sunken')
        time_label.pack(side='right', padx=5, pady=2)
        
        # Mettre à jour l'heure chaque minute
        def update_time():
            time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M"))
            self.after(60000, update_time)
        update_time()
    
    def update_status(self, message):
        """Met à jour le message de statut"""
        self.status_text.set(message)
        self.update_idletasks()
    
    def backup_database(self):
        """Crée une sauvegarde de la base de données"""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"scans_backup_{timestamp}.db")
            
            import shutil
            shutil.copy2(config.DB_PATH, backup_path)
            
            messagebox.showinfo("Backup", f"Sauvegarde créée:\n{backup_path}")
            self.update_status(f"Backup créé: {backup_path}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du backup:\n{e}")
    
    def show_settings(self):
        """Affiche la fenêtre de paramètres"""
        messagebox.showinfo("Paramètres", "Fonctionnalité à venir...")
    
    def show_help(self):
        """Affiche l'aide"""
        help_window = tk.Toplevel(self)
        help_window.title("Guide d'utilisation")
        help_window.geometry("800x600")
        
        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, font=('Courier', 10))
        text.pack(fill='both', expand=True, padx=10, pady=10)
        
        help_text = """
📚 SCANNER LIVRE PRO - GUIDE D'UTILISATION

═══════════════════════════════════════════════════════════════

🎯 WORKFLOW QUOTIDIEN:

1. SCANNER (Onglet Scanner)
   - Format: BIN UPC CONDITION
   - Exemple: C001 9781234567890 USED
   - Popup quantité (défaut: 1)
   - Popup dimensions si nouveau UPC
   - Raccourcis: F2=focus, F3=undo, F4=clear

2. ENRICHISSEMENT (Onglet Enrichissement)
   - Voir la liste des scans non enrichis
   - Click "Enrichir scans non enrichis"
   - APIs: Google Books + OpenLibrary
   - Calcul prix automatique
   - Génération description HTML

3. EXPORT EBAY (Onglet Export eBay)
   - Sélectionne date
   - Click "Exporter CSV"
   - Upload sur eBay File Exchange

4. VENTES (Onglet Ventes)
   - Download CSV ventes eBay (mensuel)
   - Click "Importer ventes"
   - Tracking automatique

5. BASE DE DONNÉES (Onglet Base de données)
   - Voir TOUS les scans dans un tableau
   - Rafraîchir les données
   - Exporter en CSV

6. DASHBOARD (Onglet Dashboard)
   - Stats temps réel
   - Progression globale
   - Revenue tracking

═══════════════════════════════════════════════════════════════

📝 COMMANDES SPÉCIALES:

Scanner:
- CANCEL: Annule dernier scan
- UNDOLOT: Annule tout le dernier lot

═══════════════════════════════════════════════════════════════

🔧 RACCOURCIS CLAVIER:

- F2: Focus sur champ scan
- F3: Undo dernier scan
- F4: Clear champ
- Ctrl+Q: Quitter

═══════════════════════════════════════════════════════════════

💡 TIPS:

- Scannez en lot (50-100 livres)
- Enrichissez à la maison (Internet stable)
- Exportez quotidiennement
- Backup hebdomadaire (Menu → Backup DB)

═══════════════════════════════════════════════════════════════

🐛 TROUBLESHOOTING:

- "API timeout": Retry automatique (3x)
- "DB locked": Fermez autres instances
- "UPC non trouvé": Vérifiez MANIFEST importé

═══════════════════════════════════════════════════════════════

Bon scanning! 📚
        """
        
        text.insert('1.0', help_text)
        text.config(state='disabled')
    
    def show_about(self):
        """Affiche la fenêtre À propos"""
        messagebox.showinfo("À propos", 
                          "📚 Scanner Livre Pro\n\n"
                          "Version: 2.0\n"
                          "Date: 2025-10-28\n\n"
                          "Application de scan et vente de livres sur eBay\n"
                          "Objectif: 10,000+ livres\n\n"
                          "Stack: Python + SQLite + Tkinter\n"
                          "Localisation: Valcourt, QC, Canada")
    
    def quit_app(self):
        """Quitte l'application"""
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter?"):
            self.destroy()


# ============================================================================
# ONGLET 1: SCANNER
# ============================================================================

class ScannerTab(ttk.Frame):
    """Onglet pour scanner les livres"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Variables
        self.scan_entry_var = tk.StringVar()
        self.current_bin = tk.StringVar(value="")
        self.current_upc = tk.StringVar(value="")
        self.current_condition = tk.StringVar(value="")
        self.last_scan_id = None
        
        self.create_widgets()
        
    def create_widgets(self):
        """Crée les widgets de l'onglet Scanner"""
        # Titre
        title_label = ttk.Label(self, text="📱 SCANNER LIVRES", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Instructions
        instructions = ttk.Label(self, text="Format: BIN UPC CONDITION (ex: C001 9781234567890 USED)", 
                               font=('Arial', 10))
        instructions.pack(pady=5)
        
        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Champ de scan
        scan_frame = ttk.LabelFrame(main_frame, text="Scan", padding=10)
        scan_frame.pack(fill='x', pady=10)
        
        self.scan_entry = ttk.Entry(scan_frame, textvariable=self.scan_entry_var, font=('Arial', 14))
        self.scan_entry.pack(fill='x', pady=5)
        self.scan_entry.bind('<Return>', lambda e: self.process_scan())
        self.scan_entry.focus()
        
        # Boutons
        button_frame = ttk.Frame(scan_frame)
        button_frame.pack(pady=5)
        
        ttk.Button(button_frame, text="Scan", command=self.process_scan).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Annuler dernier", command=self.undo_last_scan).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Clear", command=self.clear_entry).pack(side='left', padx=5)
        
        # Informations scan actuel
        info_frame = ttk.LabelFrame(main_frame, text="Scan actuel", padding=10)
        info_frame.pack(fill='x', pady=10)
        
        ttk.Label(info_frame, text="BIN:").grid(row=0, column=0, sticky='e', padx=5)
        ttk.Label(info_frame, textvariable=self.current_bin, font=('Arial', 12, 'bold')).grid(row=0, column=1, sticky='w', padx=5)
        
        ttk.Label(info_frame, text="UPC:").grid(row=1, column=0, sticky='e', padx=5)
        ttk.Label(info_frame, textvariable=self.current_upc, font=('Arial', 12, 'bold')).grid(row=1, column=1, sticky='w', padx=5)
        
        ttk.Label(info_frame, text="Condition:").grid(row=2, column=0, sticky='e', padx=5)
        ttk.Label(info_frame, textvariable=self.current_condition, font=('Arial', 12, 'bold')).grid(row=2, column=1, sticky='w', padx=5)
        
        # Derniers scans
        scans_frame = ttk.LabelFrame(main_frame, text="Derniers scans", padding=10)
        scans_frame.pack(fill='both', expand=True, pady=10)
        
        # Treeview
        columns = ('timestamp', 'bin', 'upc', 'title', 'condition', 'qty')
        self.scans_tree = ttk.Treeview(scans_frame, columns=columns, show='headings', height=10)
        
        self.scans_tree.heading('timestamp', text='Timestamp')
        self.scans_tree.heading('bin', text='BIN')
        self.scans_tree.heading('upc', text='UPC')
        self.scans_tree.heading('title', text='Titre')
        self.scans_tree.heading('condition', text='Condition')
        self.scans_tree.heading('qty', text='Qty')
        
        self.scans_tree.column('timestamp', width=150)
        self.scans_tree.column('bin', width=80)
        self.scans_tree.column('upc', width=120)
        self.scans_tree.column('title', width=300)
        self.scans_tree.column('condition', width=80)
        self.scans_tree.column('qty', width=50)
        
        self.scans_tree.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(scans_frame, orient='vertical', command=self.scans_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.scans_tree.configure(yscrollcommand=scrollbar.set)
        
        # Charger les derniers scans
        self.refresh_scans()
    
    def process_scan(self):
        """Traite le scan"""
        scan_text = self.scan_entry_var.get().strip().upper()
        
        if not scan_text:
            return
        
        # Parse le scan (accepte virgules ou espaces)
        parts = scan_text.replace(',', ' ').split()
        
        if len(parts) != 3:
            messagebox.showerror("Erreur", "Format invalide! Utilisez: BIN UPC CONDITION")
            return
        
        bin_code, upc, condition = parts
        
        # Valider UPC
        if not utils.validate_upc(upc):
            messagebox.showerror("Erreur", f"UPC invalide: {upc}")
            return
        
        # Valider condition
        if condition not in config.CONDITIONS:
            messagebox.showerror("Erreur", f"Condition invalide: {condition}\nUtilisez: {', '.join(config.CONDITIONS)}")
            return
        
        # Vérifier dans MANIFEST
        manifest_data = database.get_manifest_data(upc)
        if not manifest_data:
            response = messagebox.askyesno("UPC non trouvé", 
                                         f"UPC {upc} non trouvé dans le MANIFEST.\nContinuer quand même?")
            if not response:
                return
        
        # Demander quantité
        qty = self.ask_quantity()
        if qty is None:
            return
        
        # Demander dimensions si nouveau UPC
        dimensions = database.get_dimensions_for_upc(upc)
        if not dimensions:
            dimensions = self.ask_dimensions()
            if dimensions:
                database.save_dimensions_for_upc(upc, dimensions)
        
        # Créer le scan
        scan_data = {
            'bin': bin_code,
            'upc': upc,
            'condition': condition,
            'quantity': qty,
            'weight_major': dimensions.get('weight_major', 0) if dimensions else 0,
            'weight_minor': dimensions.get('weight_minor', 0) if dimensions else 0,
            'pkg_length': dimensions.get('pkg_length', 0) if dimensions else 0,
            'pkg_depth': dimensions.get('pkg_depth', 0) if dimensions else 0,
            'pkg_width': dimensions.get('pkg_width', 0) if dimensions else 0,
        }
        
        # Ajouter infos du manifest si disponibles
        if manifest_data:
            scan_data['pallet'] = manifest_data.get('pallet', '')
            scan_data['sku'] = manifest_data.get('sku', '')
            scan_data['title'] = manifest_data.get('title', '')
            scan_data['msrp'] = manifest_data.get('msrp', 0)
        
        # Insérer dans la DB
        scan_id = database.insert_scan(scan_data)
        self.last_scan_id = scan_id
        
        # Mettre à jour l'affichage
        self.current_bin.set(bin_code)
        self.current_upc.set(upc)
        self.current_condition.set(condition)
        
        # Clear entry
        self.scan_entry_var.set("")
        
        # Refresh liste
        self.refresh_scans()
        
        # Message de succès
        title = scan_data.get('title', 'Livre')
        self.app.update_status(f"✅ Scanné: {title} ({condition}) x{qty}")
        
    def ask_quantity(self):
        """Demande la quantité à l'utilisateur"""
        dialog = tk.Toplevel(self)
        dialog.title("Quantité")
        dialog.geometry("300x150")
        dialog.transient(self)
        dialog.grab_set()
        
        result = {'qty': None}
        
        ttk.Label(dialog, text="Quantité:", font=('Arial', 12)).pack(pady=10)
        
        qty_var = tk.IntVar(value=1)
        qty_spinbox = ttk.Spinbox(dialog, from_=1, to=100, textvariable=qty_var, width=10, font=('Arial', 14))
        qty_spinbox.pack(pady=10)
        qty_spinbox.focus()
        
        def confirm():
            result['qty'] = qty_var.get()
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=confirm).pack(pady=10)
        
        qty_spinbox.bind('<Return>', lambda e: confirm())
        
        dialog.wait_window()
        return result['qty']
    
    def ask_dimensions(self):
        """Demande les dimensions à l'utilisateur"""
        dialog = tk.Toplevel(self)
        dialog.title("Dimensions du livre")
        dialog.geometry("400x300")
        dialog.transient(self)
        dialog.grab_set()
        
        result = {'dims': None}
        
        ttk.Label(dialog, text="Entrez les dimensions:", font=('Arial', 12, 'bold')).pack(pady=10)
        
        frame = ttk.Frame(dialog)
        frame.pack(pady=10, padx=20, fill='both', expand=True)
        
        # Weight (oz)
        ttk.Label(frame, text="Poids (oz):").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        weight_var = tk.DoubleVar(value=16.0)
        ttk.Entry(frame, textvariable=weight_var, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        # Length (inches)
        ttk.Label(frame, text="Longueur (in):").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        length_var = tk.DoubleVar(value=9.0)
        ttk.Entry(frame, textvariable=length_var, width=10).grid(row=1, column=1, padx=5, pady=5)
        
        # Width (inches)
        ttk.Label(frame, text="Largeur (in):").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        width_var = tk.DoubleVar(value=6.0)
        ttk.Entry(frame, textvariable=width_var, width=10).grid(row=2, column=1, padx=5, pady=5)
        
        # Depth (inches)
        ttk.Label(frame, text="Épaisseur (in):").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        depth_var = tk.DoubleVar(value=1.0)
        ttk.Entry(frame, textvariable=depth_var, width=10).grid(row=3, column=1, padx=5, pady=5)
        
        def confirm():
            weight_oz = weight_var.get()
            result['dims'] = {
                'weight_major': int(weight_oz),
                'weight_minor': int((weight_oz % 1) * 16),
                'pkg_length': length_var.get(),
                'pkg_width': width_var.get(),
                'pkg_depth': depth_var.get()
            }
            dialog.destroy()
        
        def skip():
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="OK", command=confirm).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Ignorer", command=skip).pack(side='left', padx=5)
        
        dialog.wait_window()
        return result['dims']
    
    def undo_last_scan(self):
        """Annule le dernier scan"""
        if not self.last_scan_id:
            messagebox.showwarning("Aucun scan", "Aucun scan à annuler")
            return
        
        if messagebox.askyesno("Confirmer", "Annuler le dernier scan?"):
            database.delete_scan(self.last_scan_id)
            self.last_scan_id = None
            self.refresh_scans()
            self.app.update_status("Dernier scan annulé")
    
    def clear_entry(self):
        """Vide le champ de saisie"""
        self.scan_entry_var.set("")
        self.scan_entry.focus()
    
    def refresh_scans(self):
        """Rafraîchit la liste des derniers scans"""
        # Vider le treeview
        for item in self.scans_tree.get_children():
            self.scans_tree.delete(item)
        
        # Charger les derniers scans
        scans = database.get_recent_scans(20)
        
        for scan in scans:
            self.scans_tree.insert('', 'end', values=(
                scan.get('timestamp', '')[:16],  # Timestamp sans les secondes
                scan.get('bin', ''),
                scan.get('upc', ''),
                scan.get('title', 'N/A')[:40],  # Titre tronqué
                scan.get('condition', ''),
                scan.get('quantity', 0)
            ))


# ============================================================================
# ONGLET 2: ENRICHISSEMENT
# ============================================================================

class EnrichmentTab(ttk.Frame):
    """Onglet pour enrichir les scans avec les APIs"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()
        
    def create_widgets(self):
        """Crée les widgets de l'onglet Enrichissement"""
        # Titre
        title_label = ttk.Label(self, text="📚 ENRICHISSEMENT DES SCANS", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Stats
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding=10)
        stats_frame.pack(fill='x', pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="Chargement...", font=('Arial', 11))
        self.stats_label.pack()
        
        # Preview des scans à enrichir (51 COLONNES EBAY)
        preview_frame = ttk.LabelFrame(main_frame, text="📋 Scans à enrichir (format eBay 51 colonnes)", padding=10)
        preview_frame.pack(fill='both', expand=True, pady=10)
        
        # Treeview avec 51 colonnes eBay
        columns = (
            'action', 'custom_label', 'category_id', 'category_name', 'title',
            'relationship', 'relationship_details', 'schedule_time', 'epid',
            'start_price', 'quantity', 'item_photo_url', 'video_id', 'condition_id',
            'description', 'format', 'duration', 'buy_it_now_price',
            'best_offer_enabled', 'best_offer_auto_accept', 'min_best_offer',
            'immediate_pay', 'location', 'shipping_service_1', 'shipping_cost_1',
            'shipping_priority_1', 'shipping_service_2', 'shipping_cost_2',
            'shipping_priority_2', 'max_dispatch_time', 'returns_accepted',
            'returns_within', 'refund_option', 'return_shipping_paid_by',
            'shipping_profile', 'return_profile', 'payment_profile',
            'compliance_policy_id', 'regional_compliance', 'author', 'book_title',
            'language', 'book_format', 'pub_year', 'weight_major', 'weight_minor',
            'weight_unit', 'pkg_length', 'pkg_depth', 'pkg_width', 'postal_code'
        )
        
        self.preview_tree = ttk.Treeview(preview_frame, columns=columns, show='headings', height=15)
        
        # Headers (noms courts pour lisibilité)
        headers_short = [
            'Action', 'SKU', 'Cat ID', 'Cat Name', 'Title',
            'Rel', 'Rel Details', 'Schedule', 'EPID',
            'Price', 'Qty', 'Photo', 'Video', 'Cond ID',
            'Desc', 'Format', 'Duration', 'BuyNow',
            'BestOffer', 'Auto Accept', 'Min Offer',
            'Immed Pay', 'Location', 'Ship1', 'Cost1',
            'Prior1', 'Ship2', 'Cost2', 'Prior2',
            'Dispatch', 'Returns', 'Return Days', 'Refund',
            'Return Ship', 'Ship Profile', 'Return Profile', 'Pay Profile',
            'Compliance', 'Regional', 'Author', 'Book Title',
            'Lang', 'Format', 'Year', 'W.Maj', 'W.Min',
            'W.Unit', 'Length', 'Depth', 'Width', 'Postal'
        ]
        
        for i, col in enumerate(columns):
            self.preview_tree.heading(col, text=headers_short[i])
            self.preview_tree.column(col, width=80)
        
        # Colonnes plus larges pour Title et Description
        self.preview_tree.column('title', width=250)
        self.preview_tree.column('description', width=200)
        self.preview_tree.column('author', width=120)
        self.preview_tree.column('book_title', width=200)
        
        self.preview_tree.pack(fill='both', expand=True, side='left')
        
        # Scrollbars (vertical + horizontal)
        scrollbar_y = ttk.Scrollbar(preview_frame, orient='vertical', command=self.preview_tree.yview)
        scrollbar_y.pack(side='right', fill='y')

        scrollbar_x = ttk.Scrollbar(preview_frame, orient='horizontal', command=self.preview_tree.xview)
        scrollbar_x.pack(side='bottom', fill='x')

        self.preview_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)

        self.refresh_btn = ttk.Button(button_frame, text="🔄 Rafraîchir", command=self.refresh_preview)
        self.refresh_btn.pack(side='left', padx=5)

        self.enrich_btn = ttk.Button(button_frame, text="📚 Enrichir tous", command=self.start_enrichment)
        self.enrich_btn.pack(side='left', padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill='x', pady=10)
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding=10)
        log_frame.pack(fill='both', expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # Charger les données initiales
        self.refresh_preview()
    
    def refresh_preview(self):
        """Rafraîchit la preview des scans à enrichir (format eBay 51 colonnes)"""
        # Vider le treeview
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # Charger les scans non enrichis
        scans = database.get_unenriched_scans()
        
        # Mettre à jour les stats
        total = len(scans)
        enriched = database.get_enriched_count()
        self.stats_label.config(text=f"Scans enrichis: {enriched} | À enrichir: {total}")
        
        # Remplir le treeview avec format eBay
        for scan in scans[:100]:  # Limiter à 100 pour ne pas surcharger
            ebay_row = self.build_ebay_row_preview(scan)
            self.preview_tree.insert('', 'end', values=ebay_row)
        
        if total > 100:
            self.log(f"Affichage des 100 premiers sur {total} scans à enrichir")
    
    def build_ebay_row_preview(self, scan):
        """Construit une ligne au format eBay (51 colonnes) pour preview"""
        # Valeurs par défaut (comme dans Google Sheet)
        return (
            'Add',                                      # Action
            scan.get('upc', ''),                        # Custom label (SKU) = UPC
            '',                                         # Category ID
            '',                                         # Category name
            scan.get('title', 'N/A')[:100],            # Title
            '',                                         # Relationship
            '',                                         # Relationship details
            '',                                         # Schedule Time
            '',                                         # P:EPID
            '',                                         # Start price (sera calculé)
            scan.get('quantity', 0),                    # Quantity
            '',                                         # Item photo URL
            '',                                         # VideoID
            self.get_condition_id(scan.get('condition', 'USED')),  # Condition ID
            '',                                         # Description (sera enrichi)
            'FixedPrice',                              # Format
            'GTC',                                     # Duration
            '',                                         # Buy It Now price
            '',                                         # Best Offer Enabled
            '',                                         # Best Offer Auto Accept Price
            '',                                         # Minimum Best Offer Price
            '',                                         # Immediate pay required
            'VALCOURT,QC',                             # Location (FIXE)
            '',                                         # Shipping service 1 option
            '',                                         # Shipping service 1 cost
            '',                                         # Shipping service 1 priority
            '',                                         # Shipping service 2 option
            '',                                         # Shipping service 2 cost
            '',                                         # Shipping service 2 priority
            '',                                         # Max dispatch time
            '',                                         # Returns accepted option
            '',                                         # Returns within option
            '',                                         # Refund option
            '',                                         # Return shipping cost paid by
            '',                                         # Shipping profile name
            '',                                         # Return profile name
            '',                                         # Payment profile name
            '',                                         # ProductCompliancePolicyID
            '',                                         # Regional ProductCompliancePolicies
            scan.get('author', ''),                     # C:Author (sera enrichi)
            scan.get('title', '')[:100],               # C:Book Title
            scan.get('language', ''),                   # C:Language (sera enrichi)
            '',                                         # C:Format (sera enrichi)
            scan.get('pub_year', ''),                   # C:Publication Year (sera enrichi)
            scan.get('weight_major', 0),               # WeightMajor
            scan.get('weight_minor', 0),               # WeightMinor
            '',                                         # WeightUnit
            scan.get('pkg_length', 0),                 # PackageLength
            scan.get('pkg_depth', 0),                  # PackageDepth
            scan.get('pkg_width', 0),                  # PackageWidth
            'J0E2L0'                                   # PostalCode (FIXE)
        )
    
    def get_condition_id(self, condition):
        """Retourne l'ID de condition eBay"""
        condition_map = {
            'NEW': '1000',
            'GOOD': '2750',
            'USED': '5000'
        }
        return condition_map.get(condition.upper(), '5000')
    
    def start_enrichment(self):
        """Lance l'enrichissement en arrière-plan"""
        if messagebox.askyesno("Confirmer", "Lancer l'enrichissement de tous les scans non enrichis?"):
            self.enrich_btn.config(state='disabled')
            self.refresh_btn.config(state='disabled')
            self.progress.start()
            
            thread = threading.Thread(target=self.run_enrichment)
            thread.start()
    
    def run_enrichment(self):
        """Exécute l'enrichissement avec debug, update DB, et stats"""
        try:
            self.log("🚀 Démarrage de l'enrichissement...")
            result = enrichment_module.enrich_unenriched_scans(progress_callback=self.log_progress)
            success_count = 0
            fail_count = 0
            for idx, res in enumerate(result.get('results', []), 1):
                upc = res.get('upc')
                success = res.get('success', False)
                data = res.get('data', {})
                msg = res.get('message', '')
                self.log(f"[DEBUG] Résultat {idx}: UPC={upc} | Succès={success} | Message={msg}")
                # Chercher le scan_id correspondant à l'UPC
                scan = None
                try:
                    scans = database.get_unenriched_scans()
                    scan = next((s for s in scans if s.get('upc') == upc), None)
                except Exception as e:
                    self.log(f"[DEBUG] Erreur recherche scan pour UPC {upc}: {e}")
                if scan and success:
                    scan_id = scan.get('id')
                    if scan_id is not None:
                        try:
                            ok = database.update_scan_enrichment(scan_id, data)
                            if ok:
                                self.log(f"[DEBUG] update_scan_enrichment OK pour scan_id={scan_id}")
                                success_count += 1
                            else:
                                self.log(f"[DEBUG] update_scan_enrichment ECHEC pour scan_id={scan_id}")
                                fail_count += 1
                        except Exception as e:
                            self.log(f"[DEBUG] Exception update_scan_enrichment: {e}")
                            fail_count += 1
                    else:
                        self.log(f"[DEBUG] scan_id introuvable pour UPC {upc}")
                        fail_count += 1
                else:
                    self.log(f"[DEBUG] Scan non trouvé ou enrichissement échoué pour UPC {upc}")
                    fail_count += 1
            self.log(f"✅ Terminé! Succès: {success_count}, Échecs: {fail_count}")
            messagebox.showinfo("Enrichissement terminé", f"Succès: {success_count}\nÉchecs: {fail_count}")
        except Exception as e:
            self.log(f"❌ Erreur: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'enrichissement:\n{e}")
        finally:
            self.progress.stop()
            self.enrich_btn.config(state='normal')
            self.refresh_btn.config(state='normal')
            self.refresh_preview()
    
    def log_progress(self, current, total, message=""):
        """Log enrichment progress with current/total count."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if message:
            log_msg = f"[{timestamp}] [{current}/{total}] {message}\n"
        else:
            log_msg = f"[{timestamp}] Progression: {current}/{total}\n"
        self.log_text.insert('end', log_msg)
        self.log_text.see('end')
        self.log_text.update_idletasks()

    def log(self, message):
        """Log a simple message without progress counter."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        self.log_text.update_idletasks()


# ============================================================================
# ONGLET 3: EXPORT EBAY
# ============================================================================

class ExportTab(ttk.Frame):
    """Onglet pour exporter vers eBay"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()
        
    def create_widgets(self):
        """Crée les widgets de l'onglet Export"""
        # Titre
        title_label = ttk.Label(self, text="📤 EXPORT EBAY", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                               text="Sélectionnez une date et exportez les scans enrichis vers un CSV eBay",
                               font=('Arial', 10))
        instructions.pack(pady=10)
        
        # Sélection date
        date_frame = ttk.LabelFrame(main_frame, text="Date d'export", padding=10)
        date_frame.pack(fill='x', pady=10)
        
        ttk.Label(date_frame, text="Exporter les scans du:").pack(side='left', padx=5)
        
        self.date_var = tk.StringVar(value=date.today().isoformat())
        date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=12)
        date_entry.pack(side='left', padx=5)
        
        ttk.Button(date_frame, text="Aujourd'hui", 
                  command=lambda: self.date_var.set(date.today().isoformat())).pack(side='left', padx=5)
        
        # Stats
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding=10)
        stats_frame.pack(fill='x', pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="Chargement...", font=('Arial', 11))
        self.stats_label.pack()
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="🔄 Rafraîchir stats", 
                  command=self.refresh_stats).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="📤 Exporter CSV", 
                  command=self.export_csv, style='Accent.TButton').pack(side='left', padx=5)
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding=10)
        log_frame.pack(fill='both', expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # Charger stats
        self.refresh_stats()
    
    def export_csv(self):
        """Exporte les scans vers un CSV eBay"""
        try:
            self.log("🚀 Génération du CSV eBay...")

            # Sélectionner le chemin de sauvegarde
            output_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"ebay-{date.today().isoformat()}.csv"
            )
            if not output_path:
                self.log("❌ Export annulé par l'utilisateur")
                return

            # Récupérer les scans enrichis à exporter
            scans_data = database.get_all_enriched_scans()

            # Appeler le module d'export (ORDRE IMPORTANT: path d'abord, data ensuite)
            result = ebay_export_module.export_to_ebay_csv(output_path, scans_data)

            # Vérifier le résultat
            if result and result.get('success'):
                self.log(f"✅ {result['message']}")
                self.log(f"📁 Fichier: {result['file_path']}")
                messagebox.showinfo("Succès", f"{result['message']}\n\nFichier: {result['file_path']}")
                self.refresh_stats()
            else:
                error_msg = result.get('message', 'Erreur inconnue') if result else 'Erreur inconnue'
                self.log(f"❌ {error_msg}")
                messagebox.showerror("Erreur", error_msg)
        except Exception as e:
            self.log(f"❌ Erreur: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'export:\n{e}")
                messagebox.showinfo("Succès", f"{result['message']}\n\nFichier: {result['file_path']}")
                self.refresh_stats()
            else:
                error_msg = result.get('message', 'Erreur inconnue') if result else 'Erreur inconnue'
                self.log(f"❌ {error_msg}")
                messagebox.showerror("Erreur", error_msg)
        except Exception as e:
            self.log(f"❌ Erreur: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'export:\n{e}")
    
    def log(self, message):
        """Ajoute un message au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')


# ============================================================================
# ONGLET 4: VENTES
# ============================================================================

class SalesTab(ttk.Frame):
    """Onglet pour importer les ventes eBay"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()
        
    def create_widgets(self):
        """Crée les widgets de l'onglet Ventes"""
        # Titre
        title_label = ttk.Label(self, text="📥 IMPORT VENTES EBAY", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                               text="Importez le CSV de ventes eBay (mensuel) pour mettre à jour le tracking",
                               font=('Arial', 10))
        instructions.pack(pady=10)
        
        # Stats
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques ventes", padding=10)
        stats_frame.pack(fill='x', pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="Chargement...", font=('Arial', 11))
        self.stats_label.pack()
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="🔄 Rafraîchir stats", 
                  command=self.refresh_stats).pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="📥 Importer CSV ventes", 
                  command=self.import_sales, style='Accent.TButton').pack(side='left', padx=5)
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Logs", padding=10)
        log_frame.pack(fill='both', expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, font=('Courier', 9))
        self.log_text.pack(fill='both', expand=True)
        
        # Charger stats
        self.refresh_stats()
    
    def refresh_stats(self):
        """Rafraîchit les statistiques"""
        summary = sales_import_module.get_sales_summary()
        
        text = (f"Total ventes: {summary['total_orders']} commandes | "
               f"{summary['total_items_sold']} items | "
               f"${summary['total_revenue']:,.2f} revenue")
        
        self.stats_label.config(text=text)
        self.log(f"Stats mises à jour: {summary['total_items_sold']} items vendus")
    
    def import_sales(self):
        """Importe le CSV de ventes"""
        try:
            csv_path = filedialog.askopenfilename(
                title="Sélectionnez le CSV de ventes eBay",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not csv_path:
                return
            
            self.log(f"📂 Import du fichier: {os.path.basename(csv_path)}")
            
            result = sales_import_module.import_sales_csv(csv_path)
            
            if result['success']:
                self.log(f"✅ {result['message']}")
                messagebox.showinfo("Succès", result['message'])
                self.refresh_stats()
            else:
                self.log(f"❌ Erreur: {result['message']}")
                messagebox.showerror("Erreur", result['message'])
                
        except Exception as e:
            self.log(f"❌ Erreur: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'import:\n{e}")
    
    def log(self, message):
        """Ajoute un message au log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')


# ============================================================================
# ONGLET 5: MANIFEST
# ============================================================================

class ManifestTab(ttk.Frame):
    """Onglet pour gérer le MANIFEST"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()
        
    def create_widgets(self):
        """Crée les widgets de l'onglet MANIFEST"""
        # Titre
        title_label = ttk.Label(self, text="📋 MANIFEST (Inventaire)", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Stats
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding=10)
        stats_frame.pack(fill='x', pady=10)
        
        self.stats_label = ttk.Label(stats_frame, text="Chargement...", font=('Arial', 11))
        self.stats_label.pack()
        
        # Recherche
        search_frame = ttk.LabelFrame(main_frame, text="Recherche", padding=10)
        search_frame.pack(fill='x', pady=10)
        
        ttk.Label(search_frame, text="UPC ou Titre:").pack(side='left', padx=5)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<Return>', lambda e: self.search())
        
        ttk.Button(search_frame, text="🔍 Rechercher", command=self.search).pack(side='left', padx=5)
        ttk.Button(search_frame, text="🔄 Rafraîchir", command=self.refresh_stats).pack(side='left', padx=5)
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="📥 Importer MANIFEST CSV", 
                  command=self.import_manifest, style='Accent.TButton').pack(side='left', padx=5)
        
        # Résultats recherche
        results_frame = ttk.LabelFrame(main_frame, text="Résultats", padding=10)
        results_frame.pack(fill='both', expand=True, pady=10)
        
        # Treeview
        columns = ('pallet', 'upc', 'sku', 'title', 'msrp', 'qty')
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show='headings', height=15)
        
        self.results_tree.heading('pallet', text='Pallet')
        self.results_tree.heading('upc', text='UPC')
        self.results_tree.heading('sku', text='SKU')
        self.results_tree.heading('title', text='Titre')
        self.results_tree.heading('msrp', text='MSRP')
        self.results_tree.heading('qty', text='Qty')
        
        self.results_tree.column('pallet', width=80)
        self.results_tree.column('upc', width=120)
        self.results_tree.column('sku', width=100)
        self.results_tree.column('title', width=400)
        self.results_tree.column('msrp', width=80)
        self.results_tree.column('qty', width=60)
        
        self.results_tree.pack(fill='both', expand=True, side='left')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient='vertical', command=self.results_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Charger stats
        self.refresh_stats()
    
    def refresh_stats(self):
        """Rafraîchit les statistiques"""
        count = database.count_manifest()
        self.stats_label.config(text=f"Total livres dans MANIFEST: {count:,}")
        self.app.update_status(f"MANIFEST: {count:,} livres")
    
    def import_manifest(self):
        """Importe le CSV du MANIFEST"""
        try:
            csv_path = filedialog.askopenfilename(
                title="Sélectionnez le fichier MANIFEST CSV",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not csv_path:
                return
            
            if messagebox.askyesno("Confirmer", 
                                  f"Importer le MANIFEST depuis:\n{os.path.basename(csv_path)}?\n\n"
                                  "Cela peut prendre quelques minutes pour 10,000+ lignes."):
                
                self.app.update_status("Import en cours...")
                result = manifest_module.import_manifest_csv(csv_path)
                
                if result['success']:
                    messagebox.showinfo("Succès", result['message'])
                    self.refresh_stats()
                else:
                    messagebox.showerror("Erreur", result['message'])
                    
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'import:\n{e}")
    
    def search(self):
        """Recherche dans le MANIFEST"""
        # Nettoyer le terme de recherche (enlever virgules, espaces)
        search_term = self.search_var.get().strip().replace(',', '').replace(' ', '')

        if not search_term:
            messagebox.showwarning("Recherche", "Veuillez entrer un UPC ou titre à rechercher")
            return

        # LOG dans la console
        print(f"🔍 Recherche MANIFEST: '{search_term}'")

        # Vider le treeview
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Rechercher
        results = database.search_manifest(search_term)

        for item in results:
            self.results_tree.insert('', 'end', values=(
                item.get('pallet', ''),
                item.get('upc', ''),
                item.get('sku', ''),
                item.get('title', '')[:50],
                f"${item.get('msrp', 0):.2f}",
                item.get('quantity', 0)
            ))

        self.app.update_status(f"Recherche: {len(results)} résultat(s) trouvé(s)")


# ============================================================================
# ONGLET 6: 🆕 BASE DE DONNÉES SCANS
# ============================================================================


class DatabaseTab(ttk.Frame):
    """Onglet pour voir TOUS les scans dans un tableau"""

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()

    def create_widgets(self):
        """Crée les widgets de l'onglet Base de données"""
        # Titre
        title_label = ttk.Label(self, text="🗄️ BASE DE DONNÉES - TOUS LES SCANS", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)

        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Stats
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill='x', pady=5)
        self.stats_label = ttk.Label(stats_frame, text="Chargement...", font=('Arial', 11))
        self.stats_label.pack(side='left', padx=5)

        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=5)
        ttk.Button(button_frame, text="🔄 Rafraîchir", command=self.load_all_scans).pack(side='left', padx=5)
        ttk.Button(button_frame, text="📤 Exporter CSV", command=self.export_csv).pack(side='left', padx=5)

        # Treeview
        columns = (
            'timestamp', 'pallet', 'upc', 'sku', 'title', 'qty', 'qty_total_upc',
            'msrp', 'bin', 'condition', 'qty_condition', 'weight', 'length', 'width',
            'depth', 'qty_vendue', 'restant', 'status'
        )
        self.scans_tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=20)

        # Headers
        self.scans_tree.heading('timestamp', text='Timestamp')
        self.scans_tree.heading('pallet', text='Pallet')
        self.scans_tree.heading('upc', text='UPC')
        self.scans_tree.heading('sku', text='SKU')
        self.scans_tree.heading('title', text='Titre')
        self.scans_tree.heading('qty', text='Qty')
        self.scans_tree.heading('qty_total_upc', text='Qty/Total')
        self.scans_tree.heading('msrp', text='MSRP')
        self.scans_tree.heading('bin', text='Bin')
        self.scans_tree.heading('condition', text='Condition')
        self.scans_tree.heading('qty_condition', text='Qty Condition')
        self.scans_tree.heading('weight', text='Weight (oz)')
        self.scans_tree.heading('length', text='Length (in)')
        self.scans_tree.heading('width', text='Width (in)')
        self.scans_tree.heading('depth', text='Depth (in)')
        self.scans_tree.heading('qty_vendue', text='Qty vendue')
        self.scans_tree.heading('restant', text='Restant')
        self.scans_tree.heading('status', text='Statut')

        # Widths
        self.scans_tree.column('timestamp', width=140)
        self.scans_tree.column('pallet', width=70)
        self.scans_tree.column('upc', width=110)
        self.scans_tree.column('sku', width=90)
        self.scans_tree.column('title', width=280)
        self.scans_tree.column('qty', width=50)
        self.scans_tree.column('qty_total_upc', width=80)
        self.scans_tree.column('msrp', width=70)
        self.scans_tree.column('bin', width=70)
        self.scans_tree.column('condition', width=80)
        self.scans_tree.column('qty_condition', width=100)
        self.scans_tree.column('weight', width=90)
        self.scans_tree.column('length', width=90)
        self.scans_tree.column('width', width=80)
        self.scans_tree.column('depth', width=80)
        self.scans_tree.column('qty_vendue', width=85)
        self.scans_tree.column('restant', width=70)
        self.scans_tree.column('status', width=100)

        self.scans_tree.pack(fill='both', expand=True, side='left')

        # Scrollbar
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.scans_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.scans_tree.configure(yscrollcommand=scrollbar.set)

        # Charger les données initiales
        self.load_all_scans()

    def load_all_scans(self):
        """Charge tous les scans dans le tableau"""
        # Vider le treeview
        for item in self.scans_tree.get_children():
            self.scans_tree.delete(item)

        query = "SELECT * FROM scans ORDER BY timestamp DESC"
        scans = database.fetch_all(query)

        total_qty = 0
        total_vendue = 0

        for scan in scans:
            qty = scan.get('quantity', 0)
            qty_vendue = scan.get('qty_vendue', 0)
            restant = max(0, qty - qty_vendue)
            total_qty += qty
            total_vendue += qty_vendue
            # Calculer qty total pour cet UPC (DEPUIS LE MANIFEST!)
            upc = scan.get('upc', '')

            # Quantité dans le MANIFEST
            manifest_data = database.get_manifest_data(upc)
            if manifest_data and manifest_data.get('quantity'):
                qty_manifest = manifest_data.get('quantity', 0)
            else:
                qty_manifest = database.get_total_scanned_for_upc(upc)

            # Quantité scannée (toutes conditions)
            qty_scanned = database.get_total_scanned_for_upc(upc)

            # Afficher: scannés / manifest
            qty_total_display = f"{qty_scanned}/{qty_manifest}"
            # Calculer qty pour cette condition spécifique
            condition = scan.get('condition', '')
            query_condition = """
                SELECT SUM(quantity) as total 
                FROM scans 
                WHERE upc = ? AND condition = ?
            """
            result_condition = database.fetch_one(query_condition, (upc, condition))
            qty_condition = result_condition['total'] if result_condition and result_condition['total'] else qty
            # Dimensions
            weight = scan.get('weight_minor', 0)
            length = scan.get('pkg_length', 0)
            width = scan.get('pkg_width', 0)
            depth = scan.get('pkg_depth', 0)
            self.scans_tree.insert('', 'end', values=(
                scan.get('timestamp', '')[:19],
                scan.get('pallet', ''),
                scan.get('upc', ''),
                scan.get('sku', ''),
                scan.get('title', 'N/A')[:35],
                qty,
                qty_total_display,
                f"${scan.get('msrp', 0):.2f}" if scan.get('msrp') else '',
                scan.get('bin', ''),
                scan.get('condition', ''),
                qty_condition,
                f"{weight} oz" if weight else '',
                f"{length}\"" if length else '',
                f"{width}\"" if width else '',
                f"{depth}\"" if depth else '',
                qty_vendue,
                restant,
                scan.get('status', 'En attente')
            ))

        # Mettre à jour les stats
        total_scans = len(scans)
        restant_total = total_qty - total_vendue
        self.stats_label.config(
            text=f"Total: {total_scans:,} scans | {total_qty:,} livres | "
                 f"{total_vendue:,} vendus | {restant_total:,} restants"
        )
        self.app.update_status(f"Base de données: {total_scans:,} scans chargés")

    def export_csv(self):
        """Exporte tous les scans vers un CSV"""
        try:
            # Demander où sauvegarder
            save_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile=f"scans_export_{datetime.now().strftime('%Y%m%d')}.csv"
            )

            if not save_path:
                return

            # Charger tous les scans
            query = "SELECT * FROM scans ORDER BY timestamp DESC"
            scans = database.fetch_all(query)

            # Écrire le CSV
            with open(save_path, 'w', newline='', encoding='utf-8') as f:
                if scans:
                    writer = csv.DictWriter(f, fieldnames=scans[0].keys())
                    writer.writeheader()
                    writer.writerows(scans)

            messagebox.showinfo("Succès", f"CSV exporté:\n{save_path}\n\n{len(scans):,} lignes")
            self.app.update_status(f"Export CSV: {len(scans):,} scans exportés")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'export:\n{e}")


# ============================================================================
# ONGLET 7: DASHBOARD
# ============================================================================

class DashboardTab(ttk.Frame):
    """Onglet Dashboard avec statistiques"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()
        
    def create_widgets(self):
        """Crée les widgets de l'onglet Dashboard"""
        # Titre
        title_label = ttk.Label(self, text="📊 DASHBOARD", font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # Frame principale
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Bouton rafraîchir
        ttk.Button(main_frame, text="🔄 Rafraîchir", command=self.refresh_stats).pack(pady=5)
        
        # Cards frame
        cards_frame = ttk.Frame(main_frame)
        cards_frame.pack(fill='x', pady=10)
        
        # 4 cards
        self.card_manifest = self.create_card(cards_frame, "📦 MANIFEST", "0", "livres total")
        self.card_manifest.pack(side='left', padx=5, fill='both', expand=True)
        
        self.card_scanned = self.create_card(cards_frame, "✅ SCANNÉS", "0", "livres scannés")
        self.card_scanned.pack(side='left', padx=5, fill='both', expand=True)
        
        self.card_today = self.create_card(cards_frame, "📅 AUJOURD'HUI", "0", "scans")
        self.card_today.pack(side='left', padx=5, fill='both', expand=True)
        
        self.card_revenue = self.create_card(cards_frame, "💰 REVENUE", "$0", "total")
        self.card_revenue.pack(side='left', padx=5, fill='both', expand=True)
        
        # Progress bar
        progress_frame = ttk.LabelFrame(main_frame, text="Progression globale", padding=10)
        progress_frame.pack(fill='x', pady=10)
        
        self.progress_label = ttk.Label(progress_frame, text="0%", font=('Arial', 14, 'bold'))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(pady=5)
        
        self.progress_text = ttk.Label(progress_frame, text="0 / 0")
        self.progress_text.pack()
        
        # Détails
        details_frame = ttk.LabelFrame(main_frame, text="Détails", padding=10)
        details_frame.pack(fill='both', expand=True, pady=10)
        
        self.details_text = scrolledtext.ScrolledText(details_frame, height=15, font=('Courier', 10))
        self.details_text.pack(fill='both', expand=True)
        
        # Charger les stats
        self.refresh_stats()
    
    def create_card(self, parent, title, value, subtitle):
        """Crée une card de statistique"""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        
        value_label = ttk.Label(frame, text=value, font=('Arial', 20, 'bold'))
        value_label.pack()
        
        subtitle_label = ttk.Label(frame, text=subtitle, font=('Arial', 9))
        subtitle_label.pack()
        
        # Stocker les labels pour update
        frame.value_label = value_label
        frame.subtitle_label = subtitle_label
        
        return frame
    
    def refresh_stats(self):
        """Rafraîchit toutes les statistiques"""
        try:
            metrics = dashboard_module.get_dashboard_metrics()
            
            # Update cards
            self.card_manifest.value_label.config(text=f"{metrics['manifest_total']:,}")
            self.card_scanned.value_label.config(text=f"{metrics['total_scanned']:,}")
            self.card_today.value_label.config(text=f"{metrics['scans_today']}")
            self.card_revenue.value_label.config(text=f"${metrics['total_revenue']:,.2f}")
            
            # Update progress bar
            progress = metrics['progress_percent']
            self.progress_bar['value'] = progress
            self.progress_label.config(text=f"{progress:.1f}%")
            self.progress_text.config(text=f"{metrics['total_scanned']:,} / {metrics['manifest_total']:,}")
            
            # Update details
            self.details_text.delete('1.0', 'end')
            
            details = f"""
═══════════════════════════════════════════════════════════════
📊 DASHBOARD - STATISTIQUES COMPLÈTES
═══════════════════════════════════════════════════════════════

📦 INVENTAIRE:
   Total MANIFEST:    {metrics['manifest_total']:,} livres
   Scannés:           {metrics['total_scanned']:,} livres
   Restants:          {metrics['remaining']:,} livres
   Progression:       {metrics['progress_percent']:.1f}%

📅 AUJOURD'HUI:
   Scans:             {metrics['scans_today']} scans

📚 ENRICHISSEMENT:
   Enrichis:          {metrics['enriched_count']:,}
   Exportés vers eBay: {metrics['exported_count']:,}

💰 VENTES:
   Items vendus:      {metrics['total_sales']:,}
   Revenue total:     ${metrics['total_revenue']:,.2f}

📊 PAR STATUT:
"""
            
            for status in metrics['by_status']:
                details += f"   {status['status']:15s} {status['count']:,}\n"
            
            details += "\n📖 PAR CONDITION:\n"
            for cond in metrics['by_condition']:
                details += f"   {cond['condition']:10s} {cond['count']:,} livres\n"
            
            details += "\n═══════════════════════════════════════════════════════════════\n"
            
            self.details_text.insert('1.0', details)
            
            self.app.update_status("Dashboard mis à jour")
            
        except Exception as e:
            self.details_text.delete('1.0', 'end')
            self.details_text.insert('1.0', f"❌ Erreur lors du chargement:\n{e}")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    app = ScannerLivreApp()
    app.mainloop()