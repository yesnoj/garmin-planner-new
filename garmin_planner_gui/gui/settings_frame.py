#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per la gestione delle impostazioni dell'applicazione
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import re  # Aggiungi questa riga per importare il modulo re
from .styles import COLORS

class SettingsFrame(ttk.Frame):
    """Frame per la gestione delle impostazioni"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Inizializza l'interfaccia
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame per le impostazioni generali
        general_frame = ttk.LabelFrame(main_frame, text="Impostazioni generali")
        general_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Griglia per le impostazioni
        grid_frame = ttk.Frame(general_frame, padding=10)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Cartella OAuth
        ttk.Label(grid_frame, text="Cartella OAuth:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        
        self.oauth_var = tk.StringVar(value=self.controller.config.get('oauth_folder', '~/.garth'))
        oauth_entry = ttk.Entry(grid_frame, textvariable=self.oauth_var, width=40)
        oauth_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, 5), pady=5)
        
        browse_button = ttk.Button(grid_frame, text="Sfoglia...", 
                                  command=self.browse_oauth_folder)
        browse_button.grid(row=0, column=2, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Interfaccia utente
        ui_frame = ttk.LabelFrame(main_frame, text="Interfaccia utente")
        ui_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Griglia per l'interfaccia
        ui_grid = ttk.Frame(ui_frame, padding=10)
        ui_grid.pack(fill=tk.BOTH, expand=True)
        
        # Tema
        ttk.Label(ui_grid, text="Tema:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        
        self.theme_var = tk.StringVar(value=self.controller.config.get('ui_preferences', {}).get('theme', 'default'))
        theme_combo = ttk.Combobox(ui_grid, textvariable=self.theme_var, 
                                  values=["default", "light", "dark"], 
                                  state="readonly", width=15)
        theme_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Dimensione font
        ttk.Label(ui_grid, text="Dimensione font:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        
        self.font_size_var = tk.StringVar(value=self.controller.config.get('ui_preferences', {}).get('font_size', 'medium'))
        font_size_combo = ttk.Combobox(ui_grid, textvariable=self.font_size_var, 
                                      values=["small", "medium", "large"], 
                                      state="readonly", width=15)
        font_size_combo.grid(row=1, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Dimensione finestra
        ttk.Label(ui_grid, text="Dimensione finestra:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        
        self.window_size_var = tk.StringVar(value=self.controller.config.get('ui_preferences', {}).get('window_size', '1024x768'))
        window_size_combo = ttk.Combobox(ui_grid, textvariable=self.window_size_var, 
                                        values=["800x600", "1024x768", "1280x720", "1366x768", "1920x1080"], 
                                        width=15)
        window_size_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Gestione file recenti
        recents_frame = ttk.LabelFrame(main_frame, text="File recenti")
        recents_frame.pack(fill=tk.X, pady=(0, 10))
        
        recents_grid = ttk.Frame(recents_frame, padding=10)
        recents_grid.pack(fill=tk.BOTH, expand=True)
        
        # Numero massimo di file recenti
        ttk.Label(recents_grid, text="Numero massimo:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        
        max_recents = self.controller.config.get('max_recent_files', 10)
        self.max_recents_var = tk.StringVar(value=str(max_recents))
        max_recents_spinbox = ttk.Spinbox(recents_grid, from_=1, to=20, 
                                         textvariable=self.max_recents_var, width=5)
        max_recents_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Pulsante per pulire la lista
        clear_button = ttk.Button(recents_grid, text="Pulisci lista", 
                                 command=self.clear_recent_files)
        clear_button.grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Informazioni sull'applicazione
        info_frame = ttk.LabelFrame(main_frame, text="Informazioni")
        info_frame.pack(fill=tk.BOTH, expand=True)
        
        info_text = (
            "Garmin Planner GUI\n\n"
            "Applicazione per la gestione degli allenamenti di corsa, ciclismo e nuoto.\n"
            "Permette di creare, modificare e pianificare allenamenti, sincronizzandoli con Garmin Connect.\n\n"
            "Basato su garmin-planner: https://github.com/mrippey/garmin-planner\n"
        )
        
        info_label = ttk.Label(info_frame, text=info_text, wraplength=600, 
                             padding=10, justify=tk.LEFT)
        info_label.pack(fill=tk.BOTH, expand=True)
        
        # Pulsanti per salvare/annullare
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        save_button = ttk.Button(button_frame, text="Salva impostazioni", 
                               command=self.save_settings)
        save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        reset_button = ttk.Button(button_frame, text="Ripristina predefiniti", 
                                 command=self.reset_to_defaults)
        reset_button.pack(side=tk.LEFT)
    
    def browse_oauth_folder(self):
        """Apre un selettore di cartelle per la cartella OAuth"""
        folder = filedialog.askdirectory(
            title="Seleziona cartella OAuth",
            initialdir=os.path.expanduser(self.oauth_var.get())
        )
        
        if folder:
            self.oauth_var.set(folder)
    
    def clear_recent_files(self):
        """Pulisce la lista dei file recenti"""
        if messagebox.askyesno("Conferma", 
                             "Sei sicuro di voler pulire la lista dei file recenti?", 
                             parent=self):
            self.controller.config['recent_files'] = []
            messagebox.showinfo("Operazione completata", 
                              "Lista dei file recenti svuotata", 
                              parent=self)
    
    def save_settings(self):
        """Salva le impostazioni"""
        # Ottieni i valori
        oauth_folder = self.oauth_var.get().strip()
        theme = self.theme_var.get()
        font_size = self.font_size_var.get()
        window_size = self.window_size_var.get().strip()
        
        # Ricorda i valori originali per controllare cosa è cambiato
        original_theme = self.controller.config.get('ui_preferences', {}).get('theme', 'default')
        original_font_size = self.controller.config.get('ui_preferences', {}).get('font_size', 'medium')
        original_window_size = self.controller.config.get('ui_preferences', {}).get('window_size', '1024x768')
        
        try:
            max_recents = int(self.max_recents_var.get().strip())
            if max_recents < 1:
                raise ValueError("Il numero massimo di file recenti deve essere almeno 1")
        except ValueError:
            messagebox.showerror("Errore", 
                               "Il numero massimo di file recenti deve essere un numero intero positivo", 
                               parent=self)
            return
        
        # Validazione della dimensione finestra
        if not re.match(r'^\d+x\d+$', window_size):
            messagebox.showerror("Errore", 
                               "La dimensione finestra deve essere nel formato WIDTHxHEIGHT (es. 1024x768)", 
                               parent=self)
            return
        
        # Verifica che la cartella OAuth esista o chiedi di crearla
        if not os.path.exists(os.path.expanduser(oauth_folder)):
            if messagebox.askyesno("Cartella non trovata", 
                                 f"La cartella OAuth '{oauth_folder}' non esiste. Vuoi crearla?", 
                                 parent=self):
                try:
                    os.makedirs(os.path.expanduser(oauth_folder))
                except Exception as e:
                    messagebox.showerror("Errore", 
                                       f"Impossibile creare la cartella: {str(e)}", 
                                       parent=self)
                    return
            else:
                return
        
        # Aggiorna la configurazione
        self.controller.config['oauth_folder'] = oauth_folder
        
        if not 'ui_preferences' in self.controller.config:
            self.controller.config['ui_preferences'] = {}
        
        self.controller.config['ui_preferences']['theme'] = theme
        self.controller.config['ui_preferences']['font_size'] = font_size
        self.controller.config['ui_preferences']['window_size'] = window_size
        
        self.controller.config['max_recent_files'] = max_recents
        
        # Limita i file recenti al nuovo massimo
        if 'recent_files' in self.controller.config:
            self.controller.config['recent_files'] = self.controller.config['recent_files'][:max_recents]
        
        # Applica le modifiche (alcune potrebbero richiedere un riavvio)
        message = "Le impostazioni sono state salvate."
        
        # Verifica se sono state modificate impostazioni che richiedono un riavvio
        if original_theme != theme or original_font_size != font_size or original_window_size != window_size:
            message += "\nAlcune modifiche (tema, dimensione font, dimensione finestra) richiedono il riavvio dell'applicazione per essere applicate completamente."
        
        messagebox.showinfo("Impostazioni salvate", message, parent=self)
    
    def reset_to_defaults(self):
        """Ripristina le impostazioni predefinite"""
        if messagebox.askyesno("Conferma", 
                             "Sei sicuro di voler ripristinare le impostazioni predefinite?", 
                             parent=self):
            # Ripristina le impostazioni
            self.oauth_var.set('~/.garth')
            self.theme_var.set('default')
            self.font_size_var.set('medium')
            self.window_size_var.set('1024x768')
            self.max_recents_var.set('10')
            
            messagebox.showinfo("Operazione completata", 
                              "Impostazioni predefinite ripristinate.\n"
                              "Clicca su 'Salva impostazioni' per applicare le modifiche.", 
                              parent=self)