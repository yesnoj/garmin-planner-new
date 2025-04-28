#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog per la configurazione dei parametri degli allenamenti
"""

import tkinter as tk
from tkinter import ttk, messagebox
import copy
import re
from .styles import COLORS

class WorkoutConfigDialog(tk.Toplevel):
    """Dialog per la configurazione dei parametri degli allenamenti"""
    
    def __init__(self, parent, config=None):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        
        # Copia di sicurezza della configurazione originale
        self.orig_config = config if config else {}
        self.config = copy.deepcopy(self.orig_config)
        
        # Configurazione del dialog
        self.title("Configurazione allenamenti")
        self.geometry("800x600")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi il dialog modale
        self.transient(parent)
        self.grab_set()
        
        # Inizializza l'interfaccia
        self.init_ui()
        
        # Centra il dialog
        self.center_window()
        
        # Attendi la chiusura
        self.wait_window()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook per le varie schede
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Scheda generale
        general_frame = ttk.Frame(notebook)
        notebook.add(general_frame, text="Generale")
        self.create_general_tab(general_frame)
        
        # Scheda ritmi (per la corsa)
        paces_frame = ttk.Frame(notebook)
        notebook.add(paces_frame, text="Ritmi (Corsa)")
        self.create_paces_tab(paces_frame)
        
        # Scheda velocità (per il ciclismo)
        speeds_frame = ttk.Frame(notebook)
        notebook.add(speeds_frame, text="Velocità (Ciclismo)")
        self.create_speeds_tab(speeds_frame)
        
        # Scheda passi vasca (per il nuoto)
        swim_frame = ttk.Frame(notebook)
        notebook.add(swim_frame, text="Passi vasca (Nuoto)")
        self.create_swim_tab(swim_frame)
        
        # Scheda frequenze cardiache
        hr_frame = ttk.Frame(notebook)
        notebook.add(hr_frame, text="Frequenze cardiache")
        self.create_hr_tab(hr_frame)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Annulla", command=self.on_cancel).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Ripristina predefiniti", 
                  command=self.reset_to_defaults).pack(side=tk.RIGHT)
    
    def center_window(self):
        """Centra il dialog sullo schermo"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_general_tab(self, parent):
        """Crea la scheda delle impostazioni generali"""
        # Frame per la griglia
        grid_frame = ttk.Frame(parent, padding=10)
        grid_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tipo di sport predefinito
        ttk.Label(grid_frame, text="Sport predefinito:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.sport_var = tk.StringVar(value=self.config.get('sport_type', 'running'))
        sport_combo = ttk.Combobox(grid_frame, textvariable=self.sport_var, 
                                  values=["running", "cycling", "swimming"], 
                                  state="readonly", width=15)
        sport_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Prefisso nome
        ttk.Label(grid_frame, text="Prefisso nome:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.prefix_var = tk.StringVar(value=self.config.get('name_prefix', ''))
        ttk.Entry(grid_frame, textvariable=self.prefix_var, width=30).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Margini
        margins_frame = ttk.LabelFrame(grid_frame, text="Margini di tolleranza")
        margins_frame.grid(row=2, column=0, columnspan=2, padx=5, pady=10, sticky=tk.W+tk.E+tk.N+tk.S)
        
        # Margini per ritmo
        ttk.Label(margins_frame, text="Margine più veloce (ritmo):").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        margins = self.config.get('margins', {})
        self.faster_var = tk.StringVar(value=margins.get('faster', '0:03'))
        ttk.Entry(margins_frame, textvariable=self.faster_var, width=10).grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(margins_frame, text="(mm:ss)").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(margins_frame, text="Margine più lento (ritmo):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.slower_var = tk.StringVar(value=margins.get('slower', '0:03'))
        ttk.Entry(margins_frame, textvariable=self.slower_var, width=10).grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(margins_frame, text="(mm:ss)").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        
        # Margini per velocità
        ttk.Label(margins_frame, text="Margine più veloce (velocità):").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        self.faster_spd_var = tk.StringVar(value=margins.get('faster_spd', '2.0'))
        ttk.Entry(margins_frame, textvariable=self.faster_spd_var, width=10).grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        ttk.Label(margins_frame, text="(km/h)").grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(margins_frame, text="Margine più lento (velocità):").grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        self.slower_spd_var = tk.StringVar(value=margins.get('slower_spd', '2.0'))
        ttk.Entry(margins_frame, textvariable=self.slower_spd_var, width=10).grid(row=1, column=4, padx=5, pady=5, sticky=tk.W)
        ttk.Label(margins_frame, text="(km/h)").grid(row=1, column=5, padx=5, pady=5, sticky=tk.W)
        
        # Margini per frequenza cardiaca
        ttk.Label(margins_frame, text="Tolleranza superiore (FC):").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.hr_up_var = tk.StringVar(value=str(margins.get('hr_up', 5)))
        ttk.Entry(margins_frame, textvariable=self.hr_up_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(margins_frame, text="(bpm)").grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(margins_frame, text="Tolleranza inferiore (FC):").grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)
        
        self.hr_down_var = tk.StringVar(value=str(margins.get('hr_down', 5)))
        ttk.Entry(margins_frame, textvariable=self.hr_down_var, width=10).grid(row=2, column=4, padx=5, pady=5, sticky=tk.W)
        ttk.Label(margins_frame, text="(bpm)").grid(row=2, column=5, padx=5, pady=5, sticky=tk.W)
        
        # Testo informativo
        info_text = (
            "Le impostazioni generali controllano il comportamento predefinito dell'applicazione. "
            "Il prefisso nome viene aggiunto automaticamente a tutti gli allenamenti creati. "
            "I margini di tolleranza definiscono quanto può variare un ritmo/velocità/FC "
            "rispetto al valore target nelle fasi di allenamento."
        )
        
        info_label = ttk.Label(grid_frame, text=info_text, wraplength=600, 
                             style="Instructions.TLabel")
        info_label.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky=tk.W)
    
    def create_paces_tab(self, parent):
        """Crea la scheda per i ritmi di corsa"""
        # Frame superiore per la spiegazione
        info_frame = ttk.Frame(parent, padding=10)
        info_frame.pack(fill=tk.X)
        
        info_text = (
            "Definisci i ritmi di corsa utilizzando il formato mm:ss (minuti:secondi) per km. "
            "Puoi utilizzare sia valori singoli (es. '5:00') che intervalli (es. '4:50-5:10')."
        )
        
        info_label = ttk.Label(info_frame, text=info_text, wraplength=600)
        info_label.pack(fill=tk.X)
        
        # Frame per la lista con i ritmi
        list_frame = ttk.Frame(parent, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea la treeview
        columns = ("name", "value", "description")
        self.paces_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Intestazioni
        self.paces_tree.heading("name", text="Nome")
        self.paces_tree.heading("value", text="Valore")
        self.paces_tree.heading("description", text="Descrizione")
        
        # Larghezze colonne
        self.paces_tree.column("name", width=150)
        self.paces_tree.column("value", width=150)
        self.paces_tree.column("description", width=300)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.paces_tree.yview)
        self.paces_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.paces_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click per modificare
        self.paces_tree.bind("<Double-1>", lambda e: self.edit_pace())
        
        # Pulsanti
        button_frame = ttk.Frame(parent, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Aggiungi", command=self.add_pace).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Modifica", command=self.edit_pace).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Elimina", command=self.delete_pace).pack(side=tk.LEFT, padx=5)
        
        # Popola la lista
        self.update_paces_tree()
    
    def create_speeds_tab(self, parent):
        """Crea la scheda per le velocità di ciclismo"""
        # Frame superiore per la spiegazione
        info_frame = ttk.Frame(parent, padding=10)
        info_frame.pack(fill=tk.X)
        
        info_text = (
            "Definisci le velocità di ciclismo utilizzando il formato km/h. "
            "Puoi utilizzare sia valori singoli (es. '25.0') che intervalli (es. '23.0-27.0')."
        )
        
        info_label = ttk.Label(info_frame, text=info_text, wraplength=600)
        info_label.pack(fill=tk.X)
        
        # Frame per la lista con le velocità
        list_frame = ttk.Frame(parent, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea la treeview
        columns = ("name", "value", "description")
        self.speeds_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Intestazioni
        self.speeds_tree.heading("name", text="Nome")
        self.speeds_tree.heading("value", text="Valore")
        self.speeds_tree.heading("description", text="Descrizione")
        
        # Larghezze colonne
        self.speeds_tree.column("name", width=150)
        self.speeds_tree.column("value", width=150)
        self.speeds_tree.column("description", width=300)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.speeds_tree.yview)
        self.speeds_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.speeds_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click per modificare
        self.speeds_tree.bind("<Double-1>", lambda e: self.edit_speed())
        
        # Pulsanti
        button_frame = ttk.Frame(parent, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Aggiungi", command=self.add_speed).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Modifica", command=self.edit_speed).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Elimina", command=self.delete_speed).pack(side=tk.LEFT, padx=5)
        
        # Popola la lista
        self.update_speeds_tree()
    
    def create_swim_tab(self, parent):
        """Crea la scheda per i passi vasca di nuoto"""
        # Frame superiore per la spiegazione
        info_frame = ttk.Frame(parent, padding=10)
        info_frame.pack(fill=tk.X)
        
        info_text = (
            "Definisci i passi vasca di nuoto utilizzando il formato mm:ss (minuti:secondi) per 100m. "
            "Puoi utilizzare sia valori singoli (es. '1:45') che intervalli (es. '1:40-1:50')."
        )
        
        info_label = ttk.Label(info_frame, text=info_text, wraplength=600)
        info_label.pack(fill=tk.X)
        
        # Frame per la lista con i passi vasca
        list_frame = ttk.Frame(parent, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea la treeview
        columns = ("name", "value", "description")
        self.swim_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Intestazioni
        self.swim_tree.heading("name", text="Nome")
        self.swim_tree.heading("value", text="Valore")
        self.swim_tree.heading("description", text="Descrizione")
        
        # Larghezze colonne
        self.swim_tree.column("name", width=150)
        self.swim_tree.column("value", width=150)
        self.swim_tree.column("description", width=300)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.swim_tree.yview)
        self.swim_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.swim_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click per modificare
        self.swim_tree.bind("<Double-1>", lambda e: self.edit_swim())
        
        # Pulsanti
        button_frame = ttk.Frame(parent, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Aggiungi", command=self.add_swim).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Modifica", command=self.edit_swim).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Elimina", command=self.delete_swim).pack(side=tk.LEFT, padx=5)
        
        # Popola la lista
        self.update_swim_tree()
    
    def create_hr_tab(self, parent):
        """Crea la scheda per le frequenze cardiache"""
        # Frame superiore per la spiegazione
        info_frame = ttk.Frame(parent, padding=10)
        info_frame.pack(fill=tk.X)
        
        info_text = (
            "Definisci le zone di frequenza cardiaca utilizzando battiti al minuto (bpm). "
            "Puoi utilizzare sia valori singoli (es. '150') che intervalli (es. '140-160'). "
            "È anche possibile definire zone come percentuale di un altro valore (es. '70-80% max_hr')."
        )
        
        info_label = ttk.Label(info_frame, text=info_text, wraplength=600)
        info_label.pack(fill=tk.X)
        
        # Frame per la lista con le frequenze cardiache
        list_frame = ttk.Frame(parent, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea la treeview
        columns = ("name", "value", "description")
        self.hr_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # Intestazioni
        self.hr_tree.heading("name", text="Nome")
        self.hr_tree.heading("value", text="Valore")
        self.hr_tree.heading("description", text="Descrizione")
        
        # Larghezze colonne
        self.hr_tree.column("name", width=150)
        self.hr_tree.column("value", width=150)
        self.hr_tree.column("description", width=300)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.hr_tree.yview)
        self.hr_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.hr_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click per modificare
        self.hr_tree.bind("<Double-1>", lambda e: self.edit_hr())
        
        # Pulsanti
        button_frame = ttk.Frame(parent, padding=10)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Aggiungi", command=self.add_hr).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Modifica", command=self.edit_hr).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Elimina", command=self.delete_hr).pack(side=tk.LEFT, padx=5)
        
        # Popola la lista
        self.update_hr_tree()
    
    def update_paces_tree(self):
        """Aggiorna la lista dei ritmi"""
        # Pulisci la lista
        for item in self.paces_tree.get_children():
            self.paces_tree.delete(item)
        
        # Descrizioni predefinite per le zone
        descriptions = {
            "Z1": "Ritmo molto facile (zona 1)",
            "Z2": "Ritmo facile (zona 2)",
            "Z3": "Ritmo moderato (zona 3)",
            "Z4": "Ritmo duro (zona 4)",
            "Z5": "Ritmo molto duro (zona 5)",
            "recovery": "Ritmo di recupero",
            "threshold": "Ritmo soglia anaerobica",
            "marathon": "Ritmo maratona",
            "race_pace": "Ritmo gara",
        }
        
        # Aggiungi i ritmi
        paces = self.config.get('paces', {})
        for name, value in paces.items():
            description = descriptions.get(name, "")
            self.paces_tree.insert("", "end", values=(name, value, description))
    
    def update_speeds_tree(self):
        """Aggiorna la lista delle velocità"""
        # Pulisci la lista
        for item in self.speeds_tree.get_children():
            self.speeds_tree.delete(item)
        
        # Descrizioni predefinite per le zone
        descriptions = {
            "Z1": "Velocità molto facile (zona 1)",
            "Z2": "Velocità facile (zona 2)",
            "Z3": "Velocità moderata (zona 3)",
            "Z4": "Velocità dura (zona 4)",
            "Z5": "Velocità molto dura (zona 5)",
            "recovery": "Velocità di recupero",
            "threshold": "Velocità soglia anaerobica",
            "ftp": "Velocità FTP (Functional Threshold Power)",
        }
        
        # Aggiungi le velocità
        speeds = self.config.get('speeds', {})
        for name, value in speeds.items():
            description = descriptions.get(name, "")
            self.speeds_tree.insert("", "end", values=(name, value, description))
    
    def update_swim_tree(self):
        """Aggiorna la lista dei passi vasca"""
        # Pulisci la lista
        for item in self.swim_tree.get_children():
            self.swim_tree.delete(item)
        
        # Descrizioni predefinite per le zone
        descriptions = {
            "Z1": "Passo molto facile (zona 1)",
            "Z2": "Passo facile (zona 2)",
            "Z3": "Passo moderato (zona 3)",
            "Z4": "Passo duro (zona 4)",
            "Z5": "Passo molto duro (zona 5)",
            "recovery": "Passo di recupero",
            "threshold": "Passo soglia anaerobica",
            "sprint": "Passo sprint",
        }
        
        # Aggiungi i passi vasca
        swim_paces = self.config.get('swim_paces', {})
        for name, value in swim_paces.items():
            description = descriptions.get(name, "")
            self.swim_tree.insert("", "end", values=(name, value, description))
    
    def update_hr_tree(self):
        """Aggiorna la lista delle frequenze cardiache"""
        # Pulisci la lista
        for item in self.hr_tree.get_children():
            self.hr_tree.delete(item)
        
        # Descrizioni predefinite per le zone
        descriptions = {
            "max_hr": "Frequenza cardiaca massima",
            "Z1_HR": "FC molto facile (zona 1)",
            "Z2_HR": "FC facile (zona 2)",
            "Z3_HR": "FC moderata (zona 3)",
            "Z4_HR": "FC dura (zona 4)",
            "Z5_HR": "FC molto dura (zona 5)",
        }
        
        # Aggiungi le frequenze cardiache
        heart_rates = self.config.get('heart_rates', {})
        for name, value in heart_rates.items():
            description = descriptions.get(name, "")
            self.hr_tree.insert("", "end", values=(name, value, description))
    
    def add_pace(self):
        """Aggiunge un nuovo ritmo"""
        dialog = ConfigItemDialog(self, "Aggiungi ritmo", "pace")
        
        if dialog.result:
            name, value, description = dialog.result
            
            # Aggiungi alla configurazione
            if not 'paces' in self.config:
                self.config['paces'] = {}
            
            self.config['paces'][name] = value
            
            # Aggiorna la lista
            self.update_paces_tree()
    
    def edit_pace(self):
        """Modifica un ritmo esistente"""
        selection = self.paces_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona un ritmo da modificare", parent=self)
            return
        
        # Ottieni i valori attuali
        name, value, description = self.paces_tree.item(selection[0], "values")
        
        # Apri il dialog per la modifica
        dialog = ConfigItemDialog(self, "Modifica ritmo", "pace", name, value, description)
        
        if dialog.result:
            new_name, new_value, new_description = dialog.result
            
            # Se è cambiato il nome, rimuovi il vecchio
            if new_name != name:
                del self.config['paces'][name]
            
            # Aggiorna la configurazione
            self.config['paces'][new_name] = new_value
            
            # Aggiorna la lista
            self.update_paces_tree()
    
    def delete_pace(self):
        """Elimina un ritmo"""
        selection = self.paces_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona un ritmo da eliminare", parent=self)
            return
        
        # Ottieni il nome
        name = self.paces_tree.item(selection[0], "values")[0]
        
        # Chiedi conferma
        if messagebox.askyesno("Conferma eliminazione", 
                             f"Sei sicuro di voler eliminare il ritmo '{name}'?", 
                             parent=self):
            # Elimina dalla configurazione
            if name in self.config.get('paces', {}):
                del self.config['paces'][name]
            
            # Aggiorna la lista
            self.update_paces_tree()
    
    def add_speed(self):
        """Aggiunge una nuova velocità"""
        dialog = ConfigItemDialog(self, "Aggiungi velocità", "speed")
        
        if dialog.result:
            name, value, description = dialog.result
            
            # Aggiungi alla configurazione
            if not 'speeds' in self.config:
                self.config['speeds'] = {}
            
            self.config['speeds'][name] = value
            
            # Aggiorna la lista
            self.update_speeds_tree()
    
    def edit_speed(self):
        """Modifica una velocità esistente"""
        selection = self.speeds_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona una velocità da modificare", parent=self)
            return
        
        # Ottieni i valori attuali
        name, value, description = self.speeds_tree.item(selection[0], "values")
        
        # Apri il dialog per la modifica
        dialog = ConfigItemDialog(self, "Modifica velocità", "speed", name, value, description)
        
        if dialog.result:
            new_name, new_value, new_description = dialog.result
            
            # Se è cambiato il nome, rimuovi il vecchio
            if new_name != name:
                del self.config['speeds'][name]
            
            # Aggiorna la configurazione
            self.config['speeds'][new_name] = new_value
            
            # Aggiorna la lista
            self.update_speeds_tree()
    
    def delete_speed(self):
        """Elimina una velocità"""
        selection = self.speeds_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona una velocità da eliminare", parent=self)
            return
        
        # Ottieni il nome
        name = self.speeds_tree.item(selection[0], "values")[0]
        
        # Chiedi conferma
        if messagebox.askyesno("Conferma eliminazione", 
                             f"Sei sicuro di voler eliminare la velocità '{name}'?", 
                             parent=self):
            # Elimina dalla configurazione
            if name in self.config.get('speeds', {}):
                del self.config['speeds'][name]
            
            # Aggiorna la lista
            self.update_speeds_tree()
    
    def add_swim(self):
        """Aggiunge un nuovo passo vasca"""
        dialog = ConfigItemDialog(self, "Aggiungi passo vasca", "swim")
        
        if dialog.result:
            name, value, description = dialog.result
            
            # Aggiungi alla configurazione
            if not 'swim_paces' in self.config:
                self.config['swim_paces'] = {}
            
            self.config['swim_paces'][name] = value
            
            # Aggiorna la lista
            self.update_swim_tree()
    
    def edit_swim(self):
        """Modifica un passo vasca esistente"""
        selection = self.swim_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona un passo vasca da modificare", parent=self)
            return
        
        # Ottieni i valori attuali
        name, value, description = self.swim_tree.item(selection[0], "values")
        
        # Apri il dialog per la modifica
        dialog = ConfigItemDialog(self, "Modifica passo vasca", "swim", name, value, description)
        
        if dialog.result:
            new_name, new_value, new_description = dialog.result
            
            # Se è cambiato il nome, rimuovi il vecchio
            if new_name != name:
                del self.config['swim_paces'][name]
            
            # Aggiorna la configurazione
            self.config['swim_paces'][new_name] = new_value
            
            # Aggiorna la lista
            self.update_swim_tree()
    
    def delete_swim(self):
        """Elimina un passo vasca"""
        selection = self.swim_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona un passo vasca da eliminare", parent=self)
            return
        
        # Ottieni il nome
        name = self.swim_tree.item(selection[0], "values")[0]
        
        # Chiedi conferma
        if messagebox.askyesno("Conferma eliminazione", 
                             f"Sei sicuro di voler eliminare il passo vasca '{name}'?", 
                             parent=self):
            # Elimina dalla configurazione
            if name in self.config.get('swim_paces', {}):
                del self.config['swim_paces'][name]
            
            # Aggiorna la lista
            self.update_swim_tree()
    
    def add_hr(self):
        """Aggiunge una nuova frequenza cardiaca"""
        dialog = ConfigItemDialog(self, "Aggiungi frequenza cardiaca", "hr")
        
        if dialog.result:
            name, value, description = dialog.result
            
            # Aggiungi alla configurazione
            if not 'heart_rates' in self.config:
                self.config['heart_rates'] = {}
            
            # Converti in intero se è un numero
            try:
                value = int(value)
            except ValueError:
                # Lascia come stringa
                pass
            
            self.config['heart_rates'][name] = value
            
            # Aggiorna la lista
            self.update_hr_tree()
    
    def edit_hr(self):
        """Modifica una frequenza cardiaca esistente"""
        selection = self.hr_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona una frequenza cardiaca da modificare", parent=self)
            return
        
        # Ottieni i valori attuali
        name, value, description = self.hr_tree.item(selection[0], "values")
        
        # Apri il dialog per la modifica
        dialog = ConfigItemDialog(self, "Modifica frequenza cardiaca", "hr", name, value, description)
        
        if dialog.result:
            new_name, new_value, new_description = dialog.result
            
            # Se è cambiato il nome, rimuovi il vecchio
            if new_name != name:
                del self.config['heart_rates'][name]
            
            # Converti in intero se è un numero
            try:
                new_value = int(new_value)
            except ValueError:
                # Lascia come stringa
                pass
            
            # Aggiorna la configurazione
            self.config['heart_rates'][new_name] = new_value
            
            # Aggiorna la lista
            self.update_hr_tree()
    
    def delete_hr(self):
        """Elimina una frequenza cardiaca"""
        selection = self.hr_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona una frequenza cardiaca da eliminare", parent=self)
            return
        
        # Ottieni il nome
        name = self.hr_tree.item(selection[0], "values")[0]
        
        # Chiedi conferma
        if messagebox.askyesno("Conferma eliminazione", 
                             f"Sei sicuro di voler eliminare la frequenza cardiaca '{name}'?", 
                             parent=self):
            # Elimina dalla configurazione
            if name in self.config.get('heart_rates', {}):
                del self.config['heart_rates'][name]
            
            # Aggiorna la lista
            self.update_hr_tree()
    
    def validate_all(self):
        """Valida tutti i dati inseriti"""
        # Margini
        try:
            # Ritmo
            faster = self.faster_var.get().strip()
            slower = self.slower_var.get().strip()
            
            # Verifica che siano in formato mm:ss
            if not re.match(r'^\d+:\d{2}$', faster):
                messagebox.showerror("Errore", "Il margine più veloce deve essere in formato mm:ss", parent=self)
                return False
            
            if not re.match(r'^\d+:\d{2}$', slower):
                messagebox.showerror("Errore", "Il margine più lento deve essere in formato mm:ss", parent=self)
                return False
            
            # Velocità
            faster_spd = self.faster_spd_var.get().strip()
            slower_spd = self.slower_spd_var.get().strip()
            
            # Verifica che siano numeri
            try:
                float(faster_spd)
                float(slower_spd)
            except ValueError:
                messagebox.showerror("Errore", "I margini di velocità devono essere numeri", parent=self)
                return False
            
            # FC
            hr_up = self.hr_up_var.get().strip()
            hr_down = self.hr_down_var.get().strip()
            
            # Verifica che siano numeri interi
            try:
                int(hr_up)
                int(hr_down)
            except ValueError:
                messagebox.showerror("Errore", "I margini di frequenza cardiaca devono essere numeri interi", parent=self)
                return False
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore di validazione: {str(e)}", parent=self)
            return False
        
        return True
    
    def on_ok(self):
        """Gestisce il pulsante OK"""
        # Valida i dati
        if not self.validate_all():
            return
        
        # Aggiorna la configurazione dalle variabili
        
        # Tipo di sport
        self.config['sport_type'] = self.sport_var.get()
        
        # Prefisso nome
        self.config['name_prefix'] = self.prefix_var.get()
        
        # Margini
        if not 'margins' in self.config:
            self.config['margins'] = {}
        
        self.config['margins']['faster'] = self.faster_var.get()
        self.config['margins']['slower'] = self.slower_var.get()
        self.config['margins']['faster_spd'] = self.faster_spd_var.get()
        self.config['margins']['slower_spd'] = self.slower_spd_var.get()
        self.config['margins']['hr_up'] = int(self.hr_up_var.get())
        self.config['margins']['hr_down'] = int(self.hr_down_var.get())
        
        # Imposta il risultato
        self.result = self.config
        
        # Chiudi il dialog
        self.destroy()
    
    def on_cancel(self):
        """Gestisce il pulsante Annulla"""
        self.destroy()
    
    def reset_to_defaults(self):
        """Ripristina i valori predefiniti"""
        # Chiedi conferma
        if not messagebox.askyesno("Conferma ripristino", 
                                 "Sei sicuro di voler ripristinare tutti i valori predefiniti? "
                                 "Tutte le modifiche andranno perse.", 
                                 parent=self):
            return
        
        # Ripristina le configurazioni di default
        default_config = {
            'paces': {
                "Z1": "6:30",
                "Z2": "6:00",
                "Z3": "5:30",
                "Z4": "5:00",
                "Z5": "4:30",
                "recovery": "7:00",
                "threshold": "5:10",
                "marathon": "5:20",
                "race_pace": "5:10",
            },
            'speeds': {
                "Z1": "15.0",
                "Z2": "20.0",
                "Z3": "25.0",
                "Z4": "30.0",
                "Z5": "35.0",
                "recovery": "12.0",
                "threshold": "28.0",
                "ftp": "32.0",
            },
            'swim_paces': {
                "Z1": "2:30",
                "Z2": "2:15",
                "Z3": "2:00",
                "Z4": "1:45",
                "Z5": "1:30",
                "recovery": "2:45",
                "threshold": "1:55",
                "sprint": "1:25",
            },
            'heart_rates': {
                "max_hr": 180,
                "Z1_HR": "110-125",
                "Z2_HR": "125-140",
                "Z3_HR": "140-155",
                "Z4_HR": "155-165",
                "Z5_HR": "165-180",
            },
            'margins': {
                "faster": "0:03",
                "slower": "0:03",
                "faster_spd": "2.0",
                "slower_spd": "2.0",
                "hr_up": 5,
                "hr_down": 5
            },
            'name_prefix': "",
            'sport_type': "running"
        }
        
        # Aggiorna la configurazione
        self.config = default_config
        
        # Aggiorna le variabili
        self.sport_var.set(self.config['sport_type'])
        self.prefix_var.set(self.config['name_prefix'])
        
        # Margini
        margins = self.config['margins']
        self.faster_var.set(margins['faster'])
        self.slower_var.set(margins['slower'])
        self.faster_spd_var.set(margins['faster_spd'])
        self.slower_spd_var.set(margins['slower_spd'])
        self.hr_up_var.set(margins['hr_up'])
        self.hr_down_var.set(margins['hr_down'])
        
        # Aggiorna le liste
        self.update_paces_tree()
        self.update_speeds_tree()
        self.update_swim_tree()
        self.update_hr_tree()


class ConfigItemDialog(tk.Toplevel):
    """Dialog per l'aggiunta o modifica di un elemento di configurazione"""
    
    def __init__(self, parent, title, item_type, name="", value="", description=""):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.item_type = item_type
        
        # Configurazione del dialog
        self.title(title)
        self.geometry("500x250")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi il dialog modale
        self.transient(parent)
        self.grab_set()
        
        # Inizializza l'interfaccia
        self.init_ui(name, value, description)
        
        # Centra il dialog
        self.center_window()
        
        # Attendi la chiusura
        self.wait_window()
    
    def center_window(self):
        """Centra il dialog sullo schermo"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def init_ui(self, name, value, description):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame per i campi
        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Nome
        ttk.Label(fields_frame, text="Nome:").grid(row=0, column=0, padx=(0, 10), pady=5, sticky=tk.W)
        
        self.name_var = tk.StringVar(value=name)
        ttk.Entry(fields_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, padx=0, pady=5, sticky=tk.W+tk.E)
        
        # Etichetta del valore in base al tipo
        value_label = "Valore:"
        value_placeholder = ""
        
        if self.item_type == "pace":
            value_label = "Ritmo (mm:ss):"
            value_placeholder = "Es. 5:00 o 4:50-5:10"
        elif self.item_type == "speed":
            value_label = "Velocità (km/h):"
            value_placeholder = "Es. 25.0 o 23.0-27.0"
        elif self.item_type == "swim":
            value_label = "Passo (mm:ss):"
            value_placeholder = "Es. 1:45 o 1:40-1:50"
        elif self.item_type == "hr":
            value_label = "FC (bpm):"
            value_placeholder = "Es. 150 o 140-160 o 70-80% max_hr"
        
        # Valore
        ttk.Label(fields_frame, text=value_label).grid(row=1, column=0, padx=(0, 10), pady=5, sticky=tk.W)
        
        self.value_var = tk.StringVar(value=value)
        value_entry = ttk.Entry(fields_frame, textvariable=self.value_var, width=30)
        value_entry.grid(row=1, column=1, padx=0, pady=5, sticky=tk.W+tk.E)
        
        # Placeholder per il valore
        if not value and value_placeholder:
            value_entry.insert(0, value_placeholder)
            value_entry.config(foreground="gray")
            
            def on_entry_focus_in(event):
                if value_entry.get() == value_placeholder:
                    value_entry.delete(0, tk.END)
                    value_entry.config(foreground="black")
            
            def on_entry_focus_out(event):
                if not value_entry.get():
                    value_entry.insert(0, value_placeholder)
                    value_entry.config(foreground="gray")
            
            value_entry.bind("<FocusIn>", on_entry_focus_in)
            value_entry.bind("<FocusOut>", on_entry_focus_out)
        
        # Descrizione
        ttk.Label(fields_frame, text="Descrizione:").grid(row=2, column=0, padx=(0, 10), pady=5, sticky=tk.W)
        
        self.description_var = tk.StringVar(value=description)
        ttk.Entry(fields_frame, textvariable=self.description_var, width=30).grid(row=2, column=1, padx=0, pady=5, sticky=tk.W+tk.E)
        
        # Configura il peso delle colonne
        fields_frame.columnconfigure(1, weight=1)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Annulla", command=self.on_cancel).pack(side=tk.LEFT)
    
    def validate(self):
        """Valida i campi inseriti"""
        name = self.name_var.get().strip()
        value = self.value_var.get().strip()
        
        # Verifica che i campi obbligatori siano compilati
        if not name:
            messagebox.showerror("Errore", "Il nome è obbligatorio", parent=self)
            return False
        
        if not value:
            messagebox.showerror("Errore", "Il valore è obbligatorio", parent=self)
            return False
        
        # Validazione specifica per ogni tipo
        if self.item_type == "pace":
            # Formati validi: "5:00" o "4:50-5:10"
            if not (re.match(r'^\d+:\d{2}$', value) or 
                   re.match(r'^\d+:\d{2}-\d+:\d{2}$', value)):
                messagebox.showerror("Errore", 
                                   "Il ritmo deve essere in formato mm:ss o mm:ss-mm:ss", 
                                   parent=self)
                return False
        
        elif self.item_type == "speed":
            # Formati validi: "25.0" o "23.0-27.0"
            if not (re.match(r'^\d+(\.\d+)?$', value) or 
                   re.match(r'^\d+(\.\d+)?-\d+(\.\d+)?$', value)):
                messagebox.showerror("Errore", 
                                   "La velocità deve essere un numero o un intervallo di numeri", 
                                   parent=self)
                return False
        
        elif self.item_type == "swim":
            # Formati validi: "1:45" o "1:40-1:50"
            if not (re.match(r'^\d+:\d{2}$', value) or 
                   re.match(r'^\d+:\d{2}-\d+:\d{2}$', value)):
                messagebox.showerror("Errore", 
                                   "Il passo vasca deve essere in formato mm:ss o mm:ss-mm:ss", 
                                   parent=self)
                return False
        
        elif self.item_type == "hr":
            # Formati validi: "150" o "140-160" o "70-80% max_hr"
            if not (re.match(r'^\d+$', value) or 
                   re.match(r'^\d+-\d+$', value) or 
                   re.match(r'^\d+-\d+%\s+\w+$', value)):
                messagebox.showerror("Errore", 
                                   "La FC deve essere un numero, un intervallo o una percentuale", 
                                   parent=self)
                return False
        
        return True
    
    def on_ok(self):
        """Gestisce il pulsante OK"""
        # Valida i campi
        if not self.validate():
            return
        
        # Ottieni i valori
        name = self.name_var.get().strip()
        value = self.value_var.get().strip()
        description = self.description_var.get().strip()
        
        # Rimuovi eventuali testi di placeholder
        if self.item_type == "pace" and value == "Es. 5:00 o 4:50-5:10":
            value = ""
        elif self.item_type == "speed" and value == "Es. 25.0 o 23.0-27.0":
            value = ""
        elif self.item_type == "swim" and value == "Es. 1:45 o 1:40-1:50":
            value = ""
        elif self.item_type == "hr" and value == "Es. 150 o 140-160 o 70-80% max_hr":
            value = ""
        
        # Se il valore è ancora vuoto, segnala errore
        if not value:
            messagebox.showerror("Errore", "Il valore è obbligatorio", parent=self)
            return
        
        # Imposta il risultato
        self.result = (name, value, description)
        
        # Chiudi il dialog
        self.destroy()
    
    def on_cancel(self):
        """Gestisce il pulsante Annulla"""
        self.destroy()