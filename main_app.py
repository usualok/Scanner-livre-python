"""
================================================================================
SCANNER LIVRE - APPLICATION PRINCIPALE
================================================================================
Interface graphique complète avec onglets pour scanner, enrichir et vendre
14,000 livres sur eBay.

Auteur: Scanner Livre Project
Date: 2025-10-24
Version: 1.0
================================================================================
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from datetime import datetime, date
import sys

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
        self.title("📚 Scanner Livre Pro - v1.0")
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
        
        # Menu Fichier
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="💾 Backup DB", command=self.backup_database)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Quitter", command=self.quit_app)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        
        # Menu Outils
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="🗄️ Voir base de données", command=self.view_database)
        tools_menu.add_command(label="🧹 Nettoyer cache", command=self.clear_cache)
        menubar.add_cascade(label="Outils", menu=tools_menu)
        
        # Menu Aide
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="📖 Guide utilisateur", command=self.show_help)
        help_menu.add_command(label="ℹ️ À propos", command=self.show_about)
        menubar.add_cascade(label="Aide", menu=help_menu)
        
        self.config(menu=menubar)
    
    def create_notebook(self):
        """Crée le notebook avec les onglets"""
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=(10, 5))
        
        # Création des onglets
        self.scanner_tab = ScannerTab(notebook, self)
        self.enrichment_tab = EnrichmentTab(notebook, self)
        self.export_tab = ExportTab(notebook, self)
        self.sales_tab = SalesTab(notebook, self)
        self.manifest_tab = ManifestTab(notebook, self)
        self.dashboard_tab = DashboardTab(notebook, self)
        
        # Ajout des onglets
        notebook.add(self.scanner_tab, text="📱 Scanner")
        notebook.add(self.enrichment_tab, text="🔍 Enrichissement")
        notebook.add(self.export_tab, text="📤 Export eBay")
        notebook.add(self.sales_tab, text="📥 Ventes")
        notebook.add(self.manifest_tab, text="📋 MANIFEST")
        notebook.add(self.dashboard_tab, text="📊 Dashboard")
        
        self.notebook = notebook
    
    def create_status_bar(self):
        """Crée la barre de statut"""
        status_frame = ttk.Frame(self)
        status_frame.pack(side='bottom', fill='x', padx=10, pady=5)
        
        # Label statut
        status_label = ttk.Label(status_frame, textvariable=self.status_text, relief='sunken')
        status_label.pack(side='left', fill='x', expand=True)
        
        # DB info
        db_size = self.get_db_size()
        db_label = ttk.Label(status_frame, text=f"DB: {db_size}", relief='sunken')
        db_label.pack(side='right', padx=(5, 0))
        
    def get_db_size(self):
        """Retourne la taille de la DB"""
        try:
            size = os.path.getsize(config.DB_PATH)
            if size < 1024:
                return f"{size} B"
            elif size < 1024*1024:
                return f"{size/1024:.1f} KB"
            else:
                return f"{size/(1024*1024):.1f} MB"
        except:
            return "N/A"
    
    def update_status(self, message):
        """Met à jour la barre de statut"""
        self.status_text.set(message)
        self.update_idletasks()
    
    def backup_database(self):
        """Backup de la base de données"""
        try:
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"scans_backup_{timestamp}.db")
            
            import shutil
            shutil.copy2(config.DB_PATH, backup_path)
            
            messagebox.showinfo("Backup réussi", 
                              f"Base de données sauvegardée:\n{backup_path}")
            self.update_status("Backup créé")
        except Exception as e:
            messagebox.showerror("Erreur backup", f"Impossible de créer le backup:\n{e}")
    
    def view_database(self):
        """Ouvre l'explorateur de fichiers sur la DB"""
        try:
            import subprocess
            import platform
            
            db_path = os.path.abspath(config.DB_PATH)
            
            if platform.system() == 'Windows':
                os.startfile(os.path.dirname(db_path))
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', os.path.dirname(db_path)])
            else:  # Linux
                subprocess.Popen(['xdg-open', os.path.dirname(db_path)])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le dossier:\n{e}")
    
    def clear_cache(self):
        """Nettoie le cache de dimensions"""
        response = messagebox.askyesno("Confirmer", 
                                       "Effacer le cache des dimensions?\n"
                                       "Les dimensions devront être re-saisies.")
        if response:
            try:
                database.clear_dimensions_cache()
                messagebox.showinfo("Cache nettoyé", "Cache des dimensions effacé")
                self.update_status("Cache nettoyé")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de nettoyer le cache:\n{e}")
    
    def show_help(self):
        """Affiche le guide utilisateur"""
        help_window = tk.Toplevel(self)
        help_window.title("📖 Guide utilisateur")
        help_window.geometry("800x600")
        
        text = scrolledtext.ScrolledText(help_window, wrap='word', padx=10, pady=10)
        text.pack(fill='both', expand=True)
        
        help_text = """
=== SCANNER LIVRE - GUIDE UTILISATEUR ===

🎯 WORKFLOW QUOTIDIEN:

1. SCANNER (Onglet Scanner)
   - Format: BIN UPC CONDITION
   - Exemple: C001 9781234567890 USED
   - Popup quantité (défaut: 1)
   - Popup dimensions si nouveau UPC
   - Raccourcis: F2=focus, F3=undo, F4=clear

2. ENRICHISSEMENT (Onglet Enrichissement)
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

5. DASHBOARD (Onglet Dashboard)
   - Stats temps réel
   - Progression globale
   - Revenue tracking

📝 COMMANDES SPÉCIALES:

Scanner:
- CANCEL: Annule dernier scan
- UNDOLOT: Annule tout le dernier lot

🔧 RACCOURCIS CLAVIER:

- F2: Focus sur champ scan
- F3: Undo dernier scan
- F4: Clear champ
- Ctrl+Q: Quitter

💡 TIPS:

- Scannez en lot (50-100 livres)
- Enrichissez à la maison (Internet stable)
- Exportez quotidiennement
- Backup hebdomadaire (Menu → Backup DB)

🐛 TROUBLESHOOTING:

- "API timeout": Retry automatique (3x)
- "DB locked": Fermez autres instances
- "UPC non trouvé": Vérifiez MANIFEST importé

📞 SUPPORT:

- Logs: Vérifier console
- Backup: Menu Fichier → Backup DB
- Reset: Supprimer scans.db (recrée vide)

Bon scanning! 📚
        """
        
        text.insert('1.0', help_text)
        text.config(state='disabled')
    
    def show_about(self):
        """Affiche la fenêtre À propos"""
        messagebox.showinfo("À propos", 
                          "📚 Scanner Livre Pro\n\n"
                          "Version: 1.0\n"
                          "Date: 2025-10-24\n\n"
                          "Application de scan et vente de livres sur eBay\n"
                          "Objectif: 14,000 livres\n\n"
                          "Stack: Python + SQLite + Tkinter\n"
                          "Localisation: Valcourt, QC, Canada")
    
    def quit_app(self):
        """Quitte l'application"""
        if messagebox.askyesno("Quitter", "Voulez-vous vraiment quitter?"):
            self.destroy()


class ScannerTab(ttk.Frame):
    """Onglet Scanner"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        # Variables
        self.scan_var = tk.StringVar()
        self.last_scan = None
        
        self.create_widgets()
        
        # Bind shortcuts
        self.scan_entry.bind('<F3>', lambda e: self.undo_scan())
        self.scan_entry.bind('<F4>', lambda e: self.clear_entry())
        
        # Focus auto
        self.after(100, lambda: self.scan_entry.focus_set())
    
    def create_widgets(self):
        """Crée les widgets"""
        # Frame principal
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        title = ttk.Label(main_frame, text="📱 SCANNER", font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Format: BIN UPC CONDITION\n"
                                     "Exemple: C001 9781234567890 USED",
                                justify='center', font=('Arial', 10))
        instructions.pack(pady=(0, 20))
        
        # Frame scan
        scan_frame = ttk.Frame(main_frame)
        scan_frame.pack(fill='x', pady=10)
        
        ttk.Label(scan_frame, text="Scan:", font=('Arial', 12)).pack(side='left', padx=(0, 10))
        
        self.scan_entry = ttk.Entry(scan_frame, textvariable=self.scan_var, 
                                     font=('Arial', 14), width=40)
        self.scan_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.scan_entry.bind('<Return>', lambda e: self.process_scan())
        
        ttk.Button(scan_frame, text="Scanner", 
                  command=self.process_scan).pack(side='left')
        
        # Boutons actions
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="↩️ Undo (F3)", 
                  command=self.undo_scan).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🗑️ Clear (F4)", 
                  command=self.clear_entry).pack(side='left', padx=5)
        
        # Stats
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding=15)
        stats_frame.pack(fill='both', expand=True, pady=20)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=10, 
                                                    wrap='word', font=('Courier', 10))
        self.stats_text.pack(fill='both', expand=True)
        
        # Historique
        history_frame = ttk.LabelFrame(main_frame, text="Derniers scans", padding=15)
        history_frame.pack(fill='both', expand=True)
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=8, 
                                                      wrap='word', font=('Courier', 9))
        self.history_text.pack(fill='both', expand=True)
        
        # Refresh initial
        self.refresh_stats()
        self.refresh_history()
    
    def process_scan(self):
        """Traite un scan"""
        scan_input = self.scan_var.get().strip().upper()
        
        if not scan_input:
            return
        
        try:
            # Parse input
            tokens = utils.parse_scan_input(scan_input)
            
            # Commandes spéciales
            if tokens.get('command') == 'CANCEL':
                self.undo_scan()
                return
            
            if tokens.get('command') == 'UNDOLOT':
                self.undo_lot()
                return
            
            # Validation
            if not tokens.get('bin'):
                raise ValueError("BIN manquant\nFormat: BIN UPC CONDITION")
            
            if not tokens.get('upc'):
                raise ValueError("UPC manquant\nFormat: BIN UPC CONDITION")
            
            if not tokens.get('condition'):
                raise ValueError("Condition manquante\nFormat: BIN UPC CONDITION")
            
            # Valide UPC
            if not utils.validate_upc(tokens['upc']):
                raise ValueError(f"UPC invalide: {tokens['upc']}")
            
            # Recherche dans MANIFEST
            manifest_item = database.get_manifest_by_upc(tokens['upc'])
            if not manifest_item:
                raise ValueError(f"UPC {tokens['upc']} non trouvé dans le MANIFEST")
            
            # Check conflit BIN
            existing_bin = database.get_bin_for_upc(tokens['upc'])
            if existing_bin and existing_bin != tokens['bin']:
                raise ValueError(f"⚠️ CONFLIT BIN!\n\n"
                               f"UPC {tokens['upc']} est déjà dans le BIN {existing_bin}\n"
                               f"Vous essayez de scanner dans le BIN {tokens['bin']}\n\n"
                               f"👉 Utilisez le BIN {existing_bin} pour cet UPC")
            
            # Popup quantité
            quantity = self.prompt_quantity()
            if quantity <= 0:
                return
            
            # Dimensions
            dims = database.get_dimensions_for_upc(tokens['upc'])
            if not dims:
                dims = self.prompt_dimensions(manifest_item['title'])
                if dims:
                    database.save_dimensions(tokens['upc'], dims)
            
            # Insert scan
            scan_data = {
                'bin': tokens['bin'],
                'upc': tokens['upc'],
                'condition': tokens['condition'],
                'quantity': quantity,
                'weight_major': dims.get('weight_major', 0) if dims else 0,
                'weight_minor': dims.get('weight_minor', 0) if dims else 0,
                'pkg_length': dims.get('pkg_length', 0) if dims else 0,
                'pkg_depth': dims.get('pkg_depth', 0) if dims else 0,
                'pkg_width': dims.get('pkg_width', 0) if dims else 0
            }
            
            scan_id = database.insert_scan(scan_data)
            
            # Sauvegarde pour undo
            self.last_scan = {'id': scan_id, 'data': scan_data}
            
            # Clear et focus
            self.scan_var.set("")
            self.scan_entry.focus_set()
            
            # Refresh
            self.refresh_stats()
            self.refresh_history()
            
            # Message succès
            total = database.get_total_scanned_for_upc(tokens['upc'])
            manifest_qty = manifest_item['quantity']
            self.app.update_status(f"✅ {quantity} livre(s) scanné(s) - Total: {total}/{manifest_qty}")
            
            messagebox.showinfo("Scan réussi", 
                              f"✅ {quantity} livre(s) ajouté(s)\n"
                              f"Total: {total}/{manifest_qty}")
            
        except ValueError as e:
            messagebox.showerror("Erreur validation", str(e))
            self.scan_entry.focus_set()
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du scan:\n{e}")
            self.scan_entry.focus_set()
    
    def prompt_quantity(self):
        """Demande la quantité"""
        dialog = QuantityDialog(self)
        self.wait_window(dialog)
        return dialog.quantity if hasattr(dialog, 'quantity') else 0
    
    def prompt_dimensions(self, title):
        """Demande les dimensions"""
        dialog = DimensionsDialog(self, title)
        self.wait_window(dialog)
        return dialog.dimensions if hasattr(dialog, 'dimensions') else None
    
    def undo_scan(self):
        """Annule le dernier scan"""
        if not self.last_scan:
            messagebox.showinfo("Info", "Aucun scan à annuler")
            return
        
        try:
            database.delete_scan(self.last_scan['id'])
            self.last_scan = None
            self.refresh_stats()
            self.refresh_history()
            self.app.update_status("Scan annulé")
            messagebox.showinfo("Annulé", "Dernier scan annulé")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'annuler:\n{e}")
    
    def undo_lot(self):
        """Annule le dernier lot"""
        # TODO: Implémenter si besoin
        messagebox.showinfo("Info", "Fonction UNDO LOT à implémenter")
    
    def clear_entry(self):
        """Efface le champ"""
        self.scan_var.set("")
        self.scan_entry.focus_set()
    
    def refresh_stats(self):
        """Rafraîchit les statistiques"""
        try:
            stats = database.get_scan_stats()
            
            text = f"""
📊 STATISTIQUES GLOBALES
{'='*50}

Total scanné:       {stats['total_scanned']} / 14,000 ({stats['progress']:.1f}%)
Scans aujourd'hui:  {stats['today_scans']}
Scans cette semaine: {stats['week_scans']}

Non enrichis:       {stats['unenriched']}
Non exportés:       {stats['unexported']}

📦 PAR CONDITION:
NEW:     {stats['by_condition'].get('NEW', 0)}
GOOD:    {stats['by_condition'].get('GOOD', 0)}
USED:    {stats['by_condition'].get('USED', 0)}
DONATION: {stats['by_condition'].get('DONATION', 0)}
            """
            
            self.stats_text.config(state='normal')
            self.stats_text.delete('1.0', 'end')
            self.stats_text.insert('1.0', text.strip())
            self.stats_text.config(state='disabled')
        except Exception as e:
            pass
    
    def refresh_history(self):
        """Rafraîchit l'historique"""
        try:
            history = database.get_recent_scans(limit=10)
            
            text = "📜 DERNIERS SCANS\n" + "="*50 + "\n\n"
            
            for scan in history:
                timestamp = scan['timestamp'][:16]  # YYYY-MM-DD HH:MM
                text += f"{timestamp} | {scan['bin']} | {scan['upc']} | {scan['condition']} | Qty:{scan['quantity']}\n"
            
            if not history:
                text += "Aucun scan\n"
            
            self.history_text.config(state='normal')
            self.history_text.delete('1.0', 'end')
            self.history_text.insert('1.0', text)
            self.history_text.config(state='disabled')
        except Exception as e:
            pass


class EnrichmentTab(ttk.Frame):
    """Onglet Enrichissement"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.is_enriching = False
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crée les widgets"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        title = ttk.Label(main_frame, text="🔍 ENRICHISSEMENT", font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        # Info
        info = ttk.Label(main_frame, 
                        text="Enrichit les scans avec Google Books et OpenLibrary\n"
                             "Ajoute: Auteur, Description, Prix, Image, etc.",
                        justify='center')
        info.pack(pady=(0, 20))
        
        # Bouton enrichir
        self.enrich_btn = ttk.Button(main_frame, text="🔍 Enrichir scans non enrichis",
                                     command=self.start_enrichment)
        self.enrich_btn.pack(pady=10)
        
        # Progress
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill='x', pady=20)
        
        self.progress_label = ttk.Label(progress_frame, text="Prêt")
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=400)
        self.progress_bar.pack(pady=10)
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=10)
        log_frame.pack(fill='both', expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, wrap='word')
        self.log_text.pack(fill='both', expand=True)
    
    def start_enrichment(self):
        """Démarre l'enrichissement"""
        if self.is_enriching:
            messagebox.showwarning("En cours", "Enrichissement déjà en cours")
            return
        
        try:
            # Compte scans à enrichir
            count = database.count_unenriched_scans()
            
            if count == 0:
                messagebox.showinfo("Info", "Aucun scan à enrichir!")
                return
            
            response = messagebox.askyesno("Confirmer", 
                                          f"Enrichir {count} scan(s)?\n\n"
                                          "Cela peut prendre quelques minutes.")
            if not response:
                return
            
            # Désactive bouton
            self.enrich_btn.config(state='disabled')
            self.is_enriching = True
            
            # Lance dans thread
            thread = threading.Thread(target=self.enrich_thread)
            thread.start()
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de démarrer:\n{e}")
    
    def enrich_thread(self):
        """Thread d'enrichissement"""
        try:
            def progress_callback(current, total, message):
                self.after(0, lambda: self.update_progress(current, total, message))
            
            result = enrichment_module.enrich_unenriched_scans(progress_callback)
            
            self.after(0, lambda: self.enrichment_complete(result))
            
        except Exception as e:
            self.after(0, lambda: self.enrichment_error(str(e)))
    
    def update_progress(self, current, total, message):
        """Met à jour la progression"""
        percent = (current / total * 100) if total > 0 else 0
        self.progress_bar['value'] = percent
        self.progress_label.config(text=f"{current}/{total} - {message}")
        self.log_text.insert('end', f"{message}\n")
        self.log_text.see('end')
        self.app.update_status(f"Enrichissement: {current}/{total}")
    
    def enrichment_complete(self, result):
        """Enrichissement terminé"""
        self.is_enriching = False
        self.enrich_btn.config(state='normal')
        
        message = (f"✅ Enrichissement terminé!\n\n"
                  f"Succès: {result['success']}\n"
                  f"Échecs: {result['failed']}")
        
        messagebox.showinfo("Terminé", message)
        self.app.update_status("Enrichissement terminé")
    
    def enrichment_error(self, error):
        """Erreur enrichissement"""
        self.is_enriching = False
        self.enrich_btn.config(state='normal')
        messagebox.showerror("Erreur", f"Erreur lors de l'enrichissement:\n{error}")
        self.app.update_status("Erreur enrichissement")


class ExportTab(ttk.Frame):
    """Onglet Export eBay"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crée les widgets"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        title = ttk.Label(main_frame, text="📤 EXPORT EBAY", font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        # Info
        info = ttk.Label(main_frame, 
                        text="Exporte les scans enrichis vers CSV eBay (51 colonnes)\n"
                             "Format: eBay File Exchange",
                        justify='center')
        info.pack(pady=(0, 20))
        
        # Sélection date
        date_frame = ttk.Frame(main_frame)
        date_frame.pack(pady=20)
        
        ttk.Label(date_frame, text="Date:").pack(side='left', padx=(0, 10))
        
        self.date_var = tk.StringVar(value=date.today().isoformat())
        date_entry = ttk.Entry(date_frame, textvariable=self.date_var, width=15)
        date_entry.pack(side='left', padx=(0, 10))
        
        ttk.Button(date_frame, text="📅 Aujourd'hui", 
                  command=lambda: self.date_var.set(date.today().isoformat())).pack(side='left')
        
        # Boutons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="📤 Exporter CSV", 
                  command=self.export_csv, 
                  style='Accent.TButton').pack(side='left', padx=5)
        
        ttk.Button(btn_frame, text="🔄 Rafraîchir stats", 
                  command=self.refresh_stats).pack(side='left', padx=5)
        
        # Stats
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques", padding=15)
        stats_frame.pack(fill='both', expand=True)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=15, wrap='word')
        self.stats_text.pack(fill='both', expand=True)
        
        # Refresh initial
        self.refresh_stats()
    
    def export_csv(self):
        """Exporte le CSV eBay"""
        try:
            export_date = self.date_var.get()
            
            # Compte scans exportables
            count = database.count_exportable_scans(export_date)
            
            if count == 0:
                messagebox.showwarning("Aucune donnée", 
                                      "Aucun scan enrichi à exporter pour cette date")
                return
            
            # Demande où sauvegarder
            default_filename = f"ebay-{export_date}.csv"
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                initialfile=default_filename,
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not filepath:
                return
            
            # Génère CSV
            self.app.update_status("Génération CSV...")
            result = ebay_export_module.generate_ebay_csv(export_date, filepath)
            
            messagebox.showinfo("Export réussi", 
                              f"✅ CSV exporté avec succès!\n\n"
                              f"Fichier: {filepath}\n"
                              f"Lignes: {result['count']}\n\n"
                              "Prêt pour eBay File Exchange!")
            
            self.app.update_status("Export terminé")
            self.refresh_stats()
            
        except Exception as e:
            messagebox.showerror("Erreur export", f"Impossible d'exporter:\n{e}")
            self.app.update_status("Erreur export")
    
    def refresh_stats(self):
        """Rafraîchit les stats"""
        try:
            stats = database.get_export_stats()
            
            text = f"""
📊 STATISTIQUES EXPORT
{'='*50}

Scans enrichis:     {stats['enriched']}
Scans exportés:     {stats['exported']}
Prêts à exporter:   {stats['ready_to_export']}

Revenue estimé:     ${stats['estimated_revenue']:,.2f}
Prix moyen:         ${stats['avg_price']:.2f}

📅 PAR DATE:
"""
            
            for date_info in stats.get('by_date', [])[:5]:
                text += f"{date_info['date']}: {date_info['count']} scans\n"
            
            self.stats_text.config(state='normal')
            self.stats_text.delete('1.0', 'end')
            self.stats_text.insert('1.0', text.strip())
            self.stats_text.config(state='disabled')
        except Exception as e:
            pass


class SalesTab(ttk.Frame):
    """Onglet Ventes"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crée les widgets"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        title = ttk.Label(main_frame, text="📥 VENTES EBAY", font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        # Info
        info = ttk.Label(main_frame, 
                        text="Importe le CSV des ventes eBay pour tracker les revenus",
                        justify='center')
        info.pack(pady=(0, 20))
        
        # Bouton import
        ttk.Button(main_frame, text="📥 Importer CSV ventes", 
                  command=self.import_sales,
                  style='Accent.TButton').pack(pady=10)
        
        # Stats
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiques ventes", padding=15)
        stats_frame.pack(fill='both', expand=True, pady=20)
        
        self.stats_text = scrolledtext.ScrolledText(stats_frame, height=20, wrap='word')
        self.stats_text.pack(fill='both', expand=True)
        
        # Refresh initial
        self.refresh_stats()
    
    def import_sales(self):
        """Importe les ventes"""
        try:
            filepath = filedialog.askopenfilename(
                title="Sélectionner CSV ventes eBay",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if not filepath:
                return
            
            self.app.update_status("Import des ventes...")
            result = sales_import_module.import_sales_csv(filepath)
            
            messagebox.showinfo("Import réussi", 
                              f"✅ Ventes importées!\n\n"
                              f"Ventes: {result['count']}\n"
                              f"Revenue: ${result['revenue']:,.2f}")
            
            self.app.update_status("Ventes importées")
            self.refresh_stats()
            
        except Exception as e:
            messagebox.showerror("Erreur import", f"Impossible d'importer:\n{e}")
            self.app.update_status("Erreur import")
    
    def refresh_stats(self):
        """Rafraîchit les stats"""
        try:
            stats = database.get_sales_stats()
            
            text = f"""
💰 STATISTIQUES VENTES
{'='*50}

Total ventes:       {stats['total_sales']}
Revenue total:      ${stats['total_revenue']:,.2f}

Ce mois:           {stats['month_sales']} ventes
Revenue ce mois:   ${stats['month_revenue']:,.2f}

Prix moyen vente:  ${stats['avg_sale_price']:.2f}

📊 TOP 5 UPCs:
"""
            
            for item in stats.get('top_upcs', [])[:5]:
                text += f"{item['upc']}: {item['sales']} ventes - ${item['revenue']:,.2f}\n"
            
            self.stats_text.config(state='normal')
            self.stats_text.delete('1.0', 'end')
            self.stats_text.insert('1.0', text.strip())
            self.stats_text.config(state='disabled')
        except Exception as e:
            pass


class ManifestTab(ttk.Frame):
    """Onglet MANIFEST"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crée les widgets"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        title = ttk.Label(main_frame, text="📋 MANIFEST", font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        # Bouton import
        ttk.Button(main_frame, text="📥 Importer MANIFEST CSV", 
                  command=self.import_manifest,
                  style='Accent.TButton').pack(pady=10)
        
        # Recherche
        search_frame = ttk.LabelFrame(main_frame, text="Recherche UPC", padding=15)
        search_frame.pack(fill='x', pady=20)
        
        search_entry_frame = ttk.Frame(search_frame)
        search_entry_frame.pack(fill='x')
        
        ttk.Label(search_entry_frame, text="UPC:").pack(side='left', padx=(0, 10))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_entry_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side='left', fill='x', expand=True, padx=(0, 10))
        search_entry.bind('<Return>', lambda e: self.search_upc())
        
        ttk.Button(search_entry_frame, text="🔍 Chercher", 
                  command=self.search_upc).pack(side='left')
        
        # Résultat recherche
        self.search_result = scrolledtext.ScrolledText(search_frame, height=6, wrap='word')
        self.search_result.pack(fill='both', expand=True, pady=(10, 0))
        
        # Progression pallets
        progress_frame = ttk.LabelFrame(main_frame, text="Progression par Pallet", padding=15)
        progress_frame.pack(fill='both', expand=True)
        
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=15, wrap='word')
        self.progress_text.pack(fill='both', expand=True)
        
        # Refresh initial
        self.refresh_progress()
    
    def import_manifest(self):
        """Importe le MANIFEST"""
        try:
            filepath = filedialog.askopenfilename(
                title="Sélectionner MANIFEST CSV",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if not filepath:
                return
            
            response = messagebox.askyesno("Confirmer", 
                                          "Importer le MANIFEST?\n\n"
                                          "Cela peut prendre quelques minutes pour 14,000 livres.")
            if not response:
                return
            
            self.app.update_status("Import MANIFEST...")
            result = manifest_module.import_manifest_csv(filepath)
            
            messagebox.showinfo("Import réussi", 
                              f"✅ MANIFEST importé!\n\n"
                              f"Livres: {result['count']}")
            
            self.app.update_status("MANIFEST importé")
            self.refresh_progress()
            
        except Exception as e:
            messagebox.showerror("Erreur import", f"Impossible d'importer:\n{e}")
            self.app.update_status("Erreur import")
    
    def search_upc(self):
        """Recherche un UPC"""
        upc = self.search_var.get().strip()
        
        if not upc:
            return
        
        try:
            item = database.get_manifest_by_upc(upc)
            
            if not item:
                result = f"❌ UPC {upc} non trouvé dans le MANIFEST"
            else:
                scanned = database.get_total_scanned_for_upc(upc)
                result = f"""
✅ UPC TROUVÉ

UPC:      {item['upc']}
SKU:      {item['sku']}
Title:    {item['title']}
MSRP:     ${item['msrp']:.2f}
Quantity: {item['quantity']}
Pallet:   {item['pallet']}

Scannés:  {scanned} / {item['quantity']} ({scanned/item['quantity']*100:.1f}%)
                """
            
            self.search_result.config(state='normal')
            self.search_result.delete('1.0', 'end')
            self.search_result.insert('1.0', result.strip())
            self.search_result.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la recherche:\n{e}")
    
    def refresh_progress(self):
        """Rafraîchit la progression"""
        try:
            progress = database.get_progress_by_pallet()
            
            text = "📊 PROGRESSION PAR PALLET\n" + "="*60 + "\n\n"
            
            for p in progress:
                pallet = p['pallet'] or 'N/A'
                total = p['total']
                scanned = p['scanned']
                percent = p['percent']
                
                # Barre de progression ASCII
                bar_length = 30
                filled = int(bar_length * percent / 100)
                bar = '█' * filled + '░' * (bar_length - filled)
                
                text += f"{pallet:10} [{bar}] {percent:5.1f}% ({scanned}/{total})\n"
            
            if not progress:
                text += "Aucune donnée. Importez d'abord le MANIFEST.\n"
            
            self.progress_text.config(state='normal')
            self.progress_text.delete('1.0', 'end')
            self.progress_text.insert('1.0', text)
            self.progress_text.config(state='disabled')
        except Exception as e:
            pass


class DashboardTab(ttk.Frame):
    """Onglet Dashboard"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.create_widgets()
    
    def create_widgets(self):
        """Crée les widgets"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Titre
        title = ttk.Label(main_frame, text="📊 DASHBOARD", font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 20))
        
        # Bouton refresh
        ttk.Button(main_frame, text="🔄 Rafraîchir", 
                  command=self.refresh_dashboard).pack(pady=10)
        
        # Metrics cards
        cards_frame = ttk.Frame(main_frame)
        cards_frame.pack(fill='both', expand=True)
        
        # Grid 2x3
        for i in range(2):
            cards_frame.rowconfigure(i, weight=1)
        for i in range(3):
            cards_frame.columnconfigure(i, weight=1)
        
        # Cards
        self.card_total = self.create_card(cards_frame, "📦 Total scanné", "0 / 14,000")
        self.card_total.grid(row=0, column=0, padx=5, pady=5, sticky='nsew')
        
        self.card_today = self.create_card(cards_frame, "📅 Aujourd'hui", "0 scans")
        self.card_today.grid(row=0, column=1, padx=5, pady=5, sticky='nsew')
        
        self.card_week = self.create_card(cards_frame, "📆 Cette semaine", "0 scans")
        self.card_week.grid(row=0, column=2, padx=5, pady=5, sticky='nsew')
        
        self.card_revenue = self.create_card(cards_frame, "💰 Revenue total", "$0.00")
        self.card_revenue.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        
        self.card_avg = self.create_card(cards_frame, "📊 Prix moyen", "$0.00")
        self.card_avg.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')
        
        self.card_remaining = self.create_card(cards_frame, "📚 Restant", "14,000 livres")
        self.card_remaining.grid(row=1, column=2, padx=5, pady=5, sticky='nsew')
        
        # Refresh initial
        self.refresh_dashboard()
    
    def create_card(self, parent, title, value):
        """Crée une carte métrique"""
        frame = ttk.LabelFrame(parent, text=title, padding=15)
        
        value_label = ttk.Label(frame, text=value, font=('Arial', 16, 'bold'))
        value_label.pack(expand=True)
        
        frame.value_label = value_label
        return frame
    
    def refresh_dashboard(self):
        """Rafraîchit le dashboard"""
        try:
            metrics = dashboard_module.get_dashboard_metrics()
            
            # Update cards
            self.card_total.value_label.config(
                text=f"{metrics['total_scanned']} / 14,000\n({metrics['progress']:.1f}%)")
            
            self.card_today.value_label.config(
                text=f"{metrics['today_scans']} scans")
            
            self.card_week.value_label.config(
                text=f"{metrics['week_scans']} scans")
            
            self.card_revenue.value_label.config(
                text=f"${metrics['total_revenue']:,.2f}")
            
            self.card_avg.value_label.config(
                text=f"${metrics['avg_price']:.2f}")
            
            remaining = 14000 - metrics['total_scanned']
            self.card_remaining.value_label.config(
                text=f"{remaining} livres")
            
            self.app.update_status("Dashboard rafraîchi")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de rafraîchir:\n{e}")


class QuantityDialog(tk.Toplevel):
    """Dialog pour saisir la quantité"""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.title("Quantité")
        self.geometry("300x150")
        self.transient(parent)
        self.grab_set()
        
        self.quantity = 0
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Widgets
        ttk.Label(self, text="Combien d'exemplaires?", font=('Arial', 12)).pack(pady=20)
        
        self.qty_var = tk.IntVar(value=1)
        spinbox = ttk.Spinbox(self, from_=1, to=999, textvariable=self.qty_var, 
                              width=10, font=('Arial', 14))
        spinbox.pack(pady=10)
        spinbox.focus_set()
        spinbox.selection_range(0, 'end')
        
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="OK", command=self.ok).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.cancel).pack(side='left', padx=5)
        
        self.bind('<Return>', lambda e: self.ok())
        self.bind('<Escape>', lambda e: self.cancel())
    
    def ok(self):
        self.quantity = self.qty_var.get()
        self.destroy()
    
    def cancel(self):
        self.quantity = 0
        self.destroy()


class DimensionsDialog(tk.Toplevel):
    """Dialog pour saisir les dimensions"""
    
    def __init__(self, parent, title):
        super().__init__(parent)
        
        self.title("Dimensions requises")
        self.geometry("400x300")
        self.transient(parent)
        self.grab_set()
        
        self.dimensions = None
        
        # Center
        self.update_idletasks()
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Widgets
        ttk.Label(self, text=f"Dimensions pour:", font=('Arial', 10, 'bold')).pack(pady=(20, 5))
        ttk.Label(self, text=title[:50], wraplength=350).pack(pady=(0, 20))
        
        # Fields
        fields_frame = ttk.Frame(self)
        fields_frame.pack(padx=20, fill='x')
        
        self.weight_major_var = tk.DoubleVar(value=0)
        self.weight_minor_var = tk.DoubleVar(value=0)
        self.length_var = tk.DoubleVar(value=0)
        self.depth_var = tk.DoubleVar(value=0)
        self.width_var = tk.DoubleVar(value=0)
        
        ttk.Label(fields_frame, text="Poids (kg):").grid(row=0, column=0, sticky='w', pady=5)
        ttk.Entry(fields_frame, textvariable=self.weight_major_var, width=10).grid(row=0, column=1, pady=5)
        
        ttk.Label(fields_frame, text="Poids (g):").grid(row=1, column=0, sticky='w', pady=5)
        ttk.Entry(fields_frame, textvariable=self.weight_minor_var, width=10).grid(row=1, column=1, pady=5)
        
        ttk.Label(fields_frame, text="Longueur (cm):").grid(row=2, column=0, sticky='w', pady=5)
        ttk.Entry(fields_frame, textvariable=self.length_var, width=10).grid(row=2, column=1, pady=5)
        
        ttk.Label(fields_frame, text="Profondeur (cm):").grid(row=3, column=0, sticky='w', pady=5)
        ttk.Entry(fields_frame, textvariable=self.depth_var, width=10).grid(row=3, column=1, pady=5)
        
        ttk.Label(fields_frame, text="Largeur (cm):").grid(row=4, column=0, sticky='w', pady=5)
        ttk.Entry(fields_frame, textvariable=self.width_var, width=10).grid(row=4, column=1, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="OK", command=self.ok).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.cancel).pack(side='left', padx=5)
        
        self.bind('<Return>', lambda e: self.ok())
        self.bind('<Escape>', lambda e: self.cancel())
    
    def ok(self):
        self.dimensions = {
            'weight_major': self.weight_major_var.get(),
            'weight_minor': self.weight_minor_var.get(),
            'pkg_length': self.length_var.get(),
            'pkg_depth': self.depth_var.get(),
            'pkg_width': self.width_var.get()
        }
        self.destroy()
    
    def cancel(self):
        self.dimensions = None
        self.destroy()


def main():
    """Point d'entrée principal"""
    app = ScannerLivreApp()
    app.mainloop()


if __name__ == "__main__":
    main()