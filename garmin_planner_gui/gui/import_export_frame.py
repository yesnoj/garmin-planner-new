#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per l'importazione e l'esportazione degli allenamenti
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import threading
import json
import yaml
import re
import datetime
from .styles import COLORS

class ImportExportFrame(ttk.Frame):
    """Frame per l'importazione e l'esportazione degli allenamenti"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.garmin_client = None
        
        # Inizializza l'interfaccia
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Utilizziamo un approccio con pesi uguali per le colonne
        main_frame.columnconfigure(0, weight=1, uniform="col")  # uniform fa sì che le colonne con lo stesso valore abbiano uguale larghezza
        main_frame.columnconfigure(1, weight=1, uniform="col")
        main_frame.rowconfigure(0, weight=3)  # La parte superiore occupa 3/4 dello spazio
        main_frame.rowconfigure(1, weight=1)  # La parte inferiore occupa 1/4 dello spazio
        
        # Sezione importazione (sinistra in alto)
        import_frame = ttk.LabelFrame(main_frame, text="Importazione")
        import_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        
        # Configurazione del frame di importazione
        import_frame.columnconfigure(0, weight=1)
        import_frame.rowconfigure(0, weight=1)
        
        # Schede per diversi tipi di importazione
        import_notebook = ttk.Notebook(import_frame)
        import_notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Scheda unificata per importazione da file
        file_import_frame = ttk.Frame(import_notebook)
        import_notebook.add(file_import_frame, text="File Import")
        self.create_file_import_tab(file_import_frame)
        
        # Scheda per importazione da Garmin Connect
        garmin_frame = ttk.Frame(import_notebook)
        import_notebook.add(garmin_frame, text="Garmin Connect")
        self.create_garmin_import_tab(garmin_frame)
        
        # Sezione esportazione (destra in alto)
        export_frame = ttk.LabelFrame(main_frame, text="Esportazione")
        export_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))
        
        # Configurazione del frame di esportazione
        export_frame.columnconfigure(0, weight=1)
        export_frame.rowconfigure(0, weight=1)
        
        # Schede per diversi tipi di esportazione
        export_notebook = ttk.Notebook(export_frame)
        export_notebook.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Scheda unificata per esportazione in file
        file_export_frame = ttk.Frame(export_notebook)
        export_notebook.add(file_export_frame, text="File Export")
        self.create_file_export_tab(file_export_frame)
        
        # Scheda per esportazione in Garmin Connect
        garmin_export_frame = ttk.Frame(export_notebook)
        export_notebook.add(garmin_export_frame, text="Garmin Connect")
        self.create_garmin_export_tab(garmin_export_frame)
        
        # Sezione recenti (sinistra in basso)
        recents_frame = ttk.LabelFrame(main_frame, text="File recenti")
        recents_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        # Configurazione del frame recenti
        recents_frame.columnconfigure(0, weight=1)
        recents_frame.rowconfigure(0, weight=1)
        
        # Lista dei file recenti con container
        recents_container = ttk.Frame(recents_frame)
        recents_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        recents_container.columnconfigure(0, weight=1)
        recents_container.rowconfigure(0, weight=1)
        
        self.recents_listbox = tk.Listbox(recents_container)
        self.recents_listbox.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar per la lista dei file recenti
        recents_scrollbar = ttk.Scrollbar(recents_container, orient=tk.VERTICAL, command=self.recents_listbox.yview)
        self.recents_listbox.configure(yscrollcommand=recents_scrollbar.set)
        recents_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Carica i file recenti
        self.update_recent_files()
        
        # Evento di doppio click
        self.recents_listbox.bind("<Double-1>", self.on_recent_file_select)
        
        # Sezione log (destra in basso)
        log_frame = ttk.LabelFrame(main_frame, text="Log operazioni")
        log_frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))
        
        # Configurazione del frame log
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=0)  # Pulsanti non espandibili
        
        # Creiamo un frame contenitore per il log e la scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        log_container.columnconfigure(0, weight=1)
        log_container.rowconfigure(0, weight=1)
        
        # Area di testo per il log con altezza fissa per garantire altezza uguale
        # L'altezza è fissata a 7 righe di testo per corrispondere meglio alla listbox dei file recenti
        self.log_text = tk.Text(log_container, wrap=tk.WORD, height=7)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(log_container, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Configura il log
        self.log_text.configure(state=tk.DISABLED)  # Solo lettura
        
        # Bottoni per il log
        log_buttons = ttk.Frame(log_frame)
        log_buttons.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        # Pulsante per pulire il log
        ttk.Button(log_buttons, text="Pulisci log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=(0, 5))
        
        # Pulsante per copiare il log negli appunti
        ttk.Button(log_buttons, text="Copia negli appunti", 
                  command=self.copy_log_to_clipboard).pack(side=tk.LEFT, padx=5)

    def create_yaml_import_tab(self, parent):
        """Crea la scheda per l'importazione da file YAML/JSON"""
        # Configurazione del parent per espandersi correttamente
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Per le istruzioni
        parent.rowconfigure(1, weight=0)  # Per il file frame
        parent.rowconfigure(2, weight=0)  # Per le opzioni
        parent.rowconfigure(3, weight=0)  # Per i pulsanti
        parent.rowconfigure(4, weight=1)  # Spazio espandibile
        
        # Frame principale
        # Etichetta per le istruzioni
        instructions = (
            "Importa allenamenti da un file YAML o JSON.\n"
            "Puoi selezionare un file esistente o trascinarlo qui."
        )
        ttk.Label(parent, text=instructions, wraplength=300, 
                style="Instructions.TLabel").grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Frame per il file
        file_frame = ttk.Frame(parent)
        file_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        file_frame.columnconfigure(1, weight=1)  # L'entry deve espandersi
        
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.yaml_file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.yaml_file_var)
        file_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        browse_button = ttk.Button(file_frame, text="Sfoglia...", 
                                  command=self.browse_yaml_file)
        browse_button.grid(row=0, column=2, sticky="e")
        
        # Opzioni di importazione
        options_frame = ttk.LabelFrame(parent, text="Opzioni")
        options_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        options_frame.columnconfigure(0, weight=1)
        
        # Sovrascrittura
        self.yaml_overwrite_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Sovrascrivi allenamenti esistenti con lo stesso nome", 
                       variable=self.yaml_overwrite_var).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Pulsante per l'importazione in un frame dedicato per centrarlo
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, sticky="ew", pady=10)
        button_frame.columnconfigure(0, weight=1)
        
        import_button = ttk.Button(button_frame, text="Importa", 
                                  command=self.import_from_yaml)
        import_button.grid(row=0, column=0)
        
        # Frame vuoto espandibile per riempire lo spazio rimanente
        spacer_frame = ttk.Frame(parent)
        spacer_frame.grid(row=4, column=0, sticky="nsew")    

    
    def create_excel_import_tab(self, parent):
        """Crea la scheda per l'importazione da file Excel"""
        # Frame principale
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Etichetta per le istruzioni
        instructions = (
            "Importa allenamenti da un file Excel.\n"
            "Il file deve essere nel formato corretto, con colonne per settimana, sessione, descrizione e passi."
        )
        ttk.Label(frame, text=instructions, wraplength=300, 
                style="Instructions.TLabel").pack(pady=(0, 10))
        
        # Frame per il file
        file_frame = ttk.Frame(frame)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(file_frame, text="File:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.excel_file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.excel_file_var, width=30)
        file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_button = ttk.Button(file_frame, text="Sfoglia...", 
                                  command=self.browse_excel_file)
        browse_button.pack(side=tk.LEFT)
        
        # Opzioni di importazione
        options_frame = ttk.LabelFrame(frame, text="Opzioni")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Sovrascrittura
        overwrite_frame = ttk.Frame(options_frame)
        overwrite_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        self.excel_overwrite_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(overwrite_frame, text="Sovrascrivi allenamenti esistenti con lo stesso nome", 
                       variable=self.excel_overwrite_var).pack(side=tk.LEFT)
        
        # Pulsante per l'importazione
        import_button = ttk.Button(frame, text="Importa", 
                                 command=self.import_from_excel)
        import_button.pack(pady=(0, 10))
        
        # Pulsante per creare un file di esempio
        sample_button = ttk.Button(frame, text="Crea file di esempio", 
                                  command=self.create_sample_excel)
        sample_button.pack()
    

    def create_garmin_import_tab(self, parent):
        """Crea la scheda per l'importazione da Garmin Connect"""
        # Frame principale
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Etichetta per le istruzioni
        instructions = (
            "Importa allenamenti direttamente da Garmin Connect.\n"
            "Devi essere connesso al tuo account Garmin Connect per utilizzare questa funzione."
        )
        ttk.Label(frame, text=instructions, wraplength=300, 
                 style="Instructions.TLabel").pack(pady=(0, 10))
        
        # Stato del login
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Stato:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.garmin_status_var = tk.StringVar(value="Non connesso")
        status_label = ttk.Label(status_frame, textvariable=self.garmin_status_var)
        status_label.pack(side=tk.LEFT)
        
        # Pulsante per aggiornare la lista
        self.garmin_refresh_button = ttk.Button(status_frame, text="Aggiorna", 
                                              command=self.refresh_garmin_workouts)
        self.garmin_refresh_button.pack(side=tk.RIGHT)
        
        # Disabilitato finché non si effettua il login
        self.garmin_refresh_button['state'] = 'disabled'
        
        # Lista degli allenamenti
        list_frame = ttk.LabelFrame(frame, text="Allenamenti disponibili")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Filtro
        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        ttk.Label(filter_frame, text="Filtro:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.garmin_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.garmin_filter_var, width=20)
        filter_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Associa evento di modifica del filtro
        self.garmin_filter_var.trace_add("write", lambda *args: self.update_garmin_workout_list())
        
        # Lista con checkbox
        self.garmin_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=10)
        self.garmin_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.garmin_listbox, orient=tk.VERTICAL, command=self.garmin_listbox.yview)
        self.garmin_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pulsanti per selezionare/deselezionare tutti
        select_frame = ttk.Frame(list_frame)
        select_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(select_frame, text="Seleziona tutti", 
                  command=self.select_all_garmin).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(select_frame, text="Deseleziona tutti", 
                  command=self.deselect_all_garmin).pack(side=tk.LEFT)
        
        # Opzioni di importazione
        options_frame = ttk.LabelFrame(frame, text="Opzioni")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        overwrite_frame = ttk.Frame(options_frame)
        overwrite_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        self.garmin_overwrite_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(overwrite_frame, text="Sovrascrivi allenamenti esistenti con lo stesso nome", 
                       variable=self.garmin_overwrite_var).pack(side=tk.LEFT)
        
        # Pulsante per l'importazione
        self.garmin_import_button = ttk.Button(frame, text="Importa selezionati", 
                                             command=self.import_from_garmin)
        self.garmin_import_button.pack()
        
        # Disabilitato finché non si effettua il login
        self.garmin_import_button['state'] = 'disabled'

    
    
    def create_garmin_export_tab(self, parent):
        """Crea la scheda per l'esportazione in Garmin Connect"""
        # Frame principale
        frame = ttk.Frame(parent, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Etichetta per le istruzioni
        instructions = (
            "Scarica allenamenti direttamente da Garmin Connect.\n"
            "Devi essere connesso al tuo account Garmin Connect per utilizzare questa funzione."
        )
        ttk.Label(frame, text=instructions, wraplength=300, 
                style="Instructions.TLabel").pack(pady=(0, 10))
        
        # Stato del login
        status_frame = ttk.Frame(frame)
        status_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(status_frame, text="Stato:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.garmin_export_status_var = tk.StringVar(value="Non connesso")
        status_label = ttk.Label(status_frame, textvariable=self.garmin_export_status_var)
        status_label.pack(side=tk.LEFT)
        
        # Pulsante per aggiornare la lista
        self.export_refresh_button = ttk.Button(status_frame, text="Aggiorna", 
                                              command=self.refresh_remote_workouts)
        self.export_refresh_button.pack(side=tk.RIGHT)
        
        # Disabilitato finché non si effettua il login
        self.export_refresh_button['state'] = 'disabled'
        
        # Lista degli allenamenti remoti
        list_frame = ttk.LabelFrame(frame, text="Allenamenti su Garmin Connect")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Filtro
        filter_frame = ttk.Frame(list_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        ttk.Label(filter_frame, text="Filtro:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.remote_filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.remote_filter_var, width=20)
        filter_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Associa evento di modifica del filtro
        self.remote_filter_var.trace_add("write", lambda *args: self.update_remote_workout_list())
        
        # Lista con checkbox
        self.remote_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=10)
        self.remote_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.remote_listbox, orient=tk.VERTICAL, command=self.remote_listbox.yview)
        self.remote_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pulsanti per selezionare/deselezionare tutti
        select_frame = ttk.Frame(list_frame)
        select_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(select_frame, text="Seleziona tutti", 
                  command=self.select_all_remote).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(select_frame, text="Deseleziona tutti", 
                  command=self.deselect_all_remote).pack(side=tk.LEFT)
        
        # Pulsante per l'esportazione
        self.download_button = ttk.Button(frame, text="Scarica selezionati", 
                                         command=self.download_selected_workouts)
        self.download_button.pack()
        
        # Disabilitato finché non si effettua il login
        self.download_button['state'] = 'disabled'
    
    def export_to_file(self):
        """Esporta allenamenti in un file YAML (o Excel in base all'estensione)"""
        import os  # Reimportiamo os per sicurezza
        
        # Ottieni il nome del file destinazione
        filename = self.export_dest_file_var.get().strip()
        if not filename:
            messagebox.showerror("Errore", 
                               "Specifica un file di destinazione", 
                               parent=self)
            return
        
        # Determina il formato di esportazione dall'estensione
        ext = os.path.splitext(filename.lower())[1]
        
        # Log
        self.write_log(f"Esportazione in {filename}")
        
        # Verifica che l'estensione sia supportata
        if ext not in ['.yaml', '.yml', '.xlsx']:
            # Se non è un formato supportato, imposta .yaml come default
            filename = os.path.splitext(filename)[0] + '.yaml'
            ext = '.yaml'
            self.write_log(f"Formato non supportato, utilizzo YAML: nuovo file {filename}")
        
        # Ottieni le opzioni comuni
        use_source = self.use_source_file_var.get()
        clean = self.clean_var.get()
        
        try:
            # Se usando file sorgente
            if use_source:
                source_file = self.export_source_file_var.get().strip()
                if not source_file:
                    messagebox.showerror("Errore", 
                                       "Specifica un file sorgente o disattiva l'opzione 'Usa file sorgente'", 
                                       parent=self)
                    return
                    
                self.write_log(f"Usando file sorgente: {source_file}")
                
                # Determina il tipo di file sorgente
                source_ext = os.path.splitext(source_file.lower())[1]
                
                # Carica il file sorgente
                if source_ext in ['.yaml', '.yml']:
                    with open(source_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    self.write_log("File YAML caricato")
                elif source_ext == '.json':
                    with open(source_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.write_log("File JSON caricato e convertito in YAML")
                elif source_ext == '.xlsx':
                    # Importa da Excel
                    from planner.excel_to_yaml_converter import excel_to_yaml
                    
                    # Usa un file temporaneo per la conversione
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
                        tmp_filename = tmp.name
                        
                    # Converti il file Excel in YAML
                    data = excel_to_yaml(source_file, tmp_filename)
                    
                    # Elimina il file temporaneo
                    try:
                        os.unlink(tmp_filename)
                    except:
                        pass
                        
                    self.write_log("File Excel caricato e convertito")
                else:
                    # Prova prima come YAML per altri formati
                    try:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        self.write_log("File caricato come YAML")
                    except Exception as e:
                        messagebox.showerror("Errore", 
                                          f"Formato file non supportato", 
                                          parent=self)
                        return
                
                # Se clean è attivo, pulisci i dati
                if clean:
                    self.write_log("Pulizia dei dati in corso...")
                    # Rimuovi eventuali passi vuoti o nulli
                    for name, steps in list(data.items()):
                        if not isinstance(steps, list) and not name.startswith('config') and name not in ['athlete_name', 'paces', 'power_values', 'swim_paces']:
                            continue  # Salta le chiavi che non sono allenamenti
                        
                        if isinstance(steps, list):
                            cleaned_steps = []
                            for step in steps:
                                if step:  # Se non è None
                                    cleaned_steps.append(step)
                            data[name] = cleaned_steps
            else:
                # Usa gli allenamenti in memoria
                workouts = self.controller.workout_editor_frame.workouts
                
                # Se non ci sono allenamenti, mostra un errore
                if not workouts:
                    messagebox.showwarning("Nessun allenamento", 
                                         "Non ci sono allenamenti da esportare", 
                                         parent=self)
                    return
                
                # Crea il dizionario per l'esportazione
                data = {}
                
                # Aggiungi la configurazione
                if self.include_config_var.get() and 'workout_config' in self.controller.config:
                    # Copia la configurazione per non modificare l'originale
                    config = dict(self.controller.config['workout_config'])
                    
                    # Escludi i valori paces, power_values e swim_paces dalla config
                    # e mettili come chiavi principali
                    for section in ['paces', 'power_values', 'swim_paces']:
                        if section in config:
                            data[section] = config.pop(section)
                    
                    # Il resto della configurazione va in config
                    data['config'] = config
                    
                    # Aggiungi il nome dell'atleta
                    if 'athlete_name' in self.controller.config and self.controller.config['athlete_name']:
                        data['config']['athlete_name'] = self.controller.config['athlete_name']
                        data['athlete_name'] = self.controller.config['athlete_name']
                
                # Aggiungi gli allenamenti
                for name, steps in workouts:
                    if clean:
                        # Rimuovi passi vuoti o nulli
                        cleaned_steps = []
                        for step in steps:
                            if step:
                                cleaned_steps.append(step)
                        data[name] = cleaned_steps
                    else:
                        data[name] = steps
            
            # Esporta in base al formato
            if ext in ['.yaml', '.yml']:
                # Esporta in YAML
                with open(filename, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, default_flow_style=False)
                self.write_log("Esportato in formato YAML")
            elif ext == '.xlsx':
                # Esporta in Excel
                from planner.excel_to_yaml_converter import yaml_to_excel
                result = yaml_to_excel(data, filename)
                
                if not result:
                    messagebox.showerror("Errore", 
                                       "Errore nella creazione del file Excel", 
                                       parent=self)
                    self.write_log("Errore nella creazione del file Excel")
                    return
                    
                self.write_log("Esportato in formato Excel")
            
            # Aggiungi ai file recenti
            self.add_to_recent_files(filename)
            
            # Mostra un messaggio di conferma
            messagebox.showinfo("Esportazione completata", 
                              f"Esportazione in {filename} completata con successo", 
                              parent=self)
            
            # Log
            self.write_log(f"Esportazione completata: file {filename} creato")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.write_log(f"Errore dettagliato: {error_details}")
            messagebox.showerror("Errore", 
                               f"Errore durante l'esportazione: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")



    def create_file_import_tab(self, parent):
        """Crea la scheda unificata per l'importazione da file (YAML, JSON o Excel)"""
        # Configurazione del parent per espandersi correttamente
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Per le istruzioni
        parent.rowconfigure(1, weight=0)  # Per il file
        parent.rowconfigure(2, weight=0)  # Per le opzioni
        parent.rowconfigure(3, weight=0)  # Per i pulsanti
        parent.rowconfigure(4, weight=0)  # Per il pulsante crea file di esempio
        parent.rowconfigure(5, weight=1)  # Spazio espandibile
        
        # Etichetta per le istruzioni
        instructions = (
            "Importa allenamenti da un file YAML, JSON o Excel.\n"
            "Puoi selezionare un file esistente o trascinarlo qui."
        )
        ttk.Label(parent, text=instructions, wraplength=300, 
                style="Instructions.TLabel").grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Frame per il file
        file_frame = ttk.Frame(parent)
        file_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        file_frame.columnconfigure(1, weight=1)  # L'entry deve espandersi
        
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.import_file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.import_file_var)
        file_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        browse_button = ttk.Button(file_frame, text="Sfoglia...", 
                                  command=self.browse_import_file)
        browse_button.grid(row=0, column=2, sticky="e")
        
        # Opzioni di importazione
        options_frame = ttk.LabelFrame(parent, text="Opzioni")
        options_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        options_frame.columnconfigure(0, weight=1)
        
        # Sovrascrittura
        self.import_overwrite_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Sovrascrivi allenamenti esistenti con lo stesso nome", 
                       variable=self.import_overwrite_var).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Pulsante per l'importazione
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=3, column=0, sticky="ew", pady=10)
        button_frame.columnconfigure(0, weight=1)
        
        import_button = ttk.Button(button_frame, text="Importa", 
                                 command=self.import_from_file)
        import_button.grid(row=0, column=0)
        
        # Pulsante per creare un file di esempio
        example_frame = ttk.Frame(parent)
        example_frame.grid(row=4, column=0, sticky="ew", pady=5)
        example_frame.columnconfigure(0, weight=1)
        
        sample_button = ttk.Button(example_frame, text="Crea file di esempio", 
                                 command=self.create_sample_excel)
        sample_button.grid(row=0, column=0)
        
        # Frame vuoto espandibile per riempire lo spazio rimanente
        spacer_frame = ttk.Frame(parent)
        spacer_frame.grid(row=5, column=0, sticky="nsew")


    def create_file_export_tab(self, parent):
        """Crea la scheda unificata per l'esportazione in file (YAML, JSON o Excel)"""
        # Configurazione del parent per espandersi correttamente
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # Per le istruzioni
        parent.rowconfigure(1, weight=0)  # Per il file sorgente
        parent.rowconfigure(2, weight=0)  # Per il file destinazione
        parent.rowconfigure(3, weight=0)  # Per le opzioni
        parent.rowconfigure(4, weight=0)  # Per i pulsanti
        parent.rowconfigure(5, weight=1)  # Spazio espandibile
        
        # Etichetta per le istruzioni
        instructions = (
            "Esporta allenamenti in un file YAML, JSON o Excel.\n"
            "Puoi selezionare un file sorgente o esportare gli allenamenti caricati.\n"
            "Il formato di esportazione verrà determinato in base all'estensione del file destinazione."
        )
        ttk.Label(parent, text=instructions, wraplength=300, 
                style="Instructions.TLabel").grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Frame per il file sorgente
        source_frame = ttk.Frame(parent)
        source_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        source_frame.columnconfigure(1, weight=1)  # L'entry deve espandersi
        
        ttk.Label(source_frame, text="File sorgente:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Variabile per il file sorgente - definita come attributo dell'istanza
        self.export_source_file_var = tk.StringVar()
        
        # Widget Entry per visualizzare il percorso del file
        source_entry = ttk.Entry(source_frame, textvariable=self.export_source_file_var)
        source_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        # Pulsante per sfogliare
        browse_source_button = ttk.Button(source_frame, text="Sfoglia...", 
                                  command=lambda: self.browse_source_file(self.export_source_file_var))
        browse_source_button.grid(row=0, column=2, sticky="e")
        
        # Frame per il file di destinazione
        dest_frame = ttk.Frame(parent)
        dest_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        dest_frame.columnconfigure(1, weight=1)  # L'entry deve espandersi
        
        ttk.Label(dest_frame, text="File destinazione:").grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Variabile per il file destinazione - definita come attributo dell'istanza
        self.export_dest_file_var = tk.StringVar()
        
        # Widget Entry per visualizzare il percorso del file destinazione
        dest_entry = ttk.Entry(dest_frame, textvariable=self.export_dest_file_var)
        dest_entry.grid(row=0, column=1, sticky="ew", padx=(0, 5))
        
        # Pulsante per sfogliare
        browse_dest_button = ttk.Button(dest_frame, text="Sfoglia...", 
                                  command=self.browse_export_dest_file)
        browse_dest_button.grid(row=0, column=2, sticky="e")
        
        # Opzioni di esportazione
        options_frame = ttk.LabelFrame(parent, text="Opzioni")
        options_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        options_frame.columnconfigure(0, weight=1)
        
        # Opzione per indicare se usare il file sorgente o gli allenamenti caricati
        self.use_source_file_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Usa file sorgente (altrimenti usa allenamenti caricati)", 
                       variable=self.use_source_file_var).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        # Pulizia (per JSON/YAML)
        self.clean_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Pulisci il file rimuovendo dati non necessari (per YAML/JSON)", 
                       variable=self.clean_var).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        # Includi configurazione (per Excel)
        self.include_config_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Includi configurazione (ritmi, velocità, FC, ecc.) (per Excel)", 
                       variable=self.include_config_var).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        
        # Pulsante per l'esportazione in un frame dedicato per centrarlo
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, sticky="ew", pady=10)
        button_frame.columnconfigure(0, weight=1)
        
        # Qui è l'errore: stai chiamando "export_to_file" ma il metodo è definito più avanti nel codice
        # Usa il metodo corretto
        export_button = ttk.Button(button_frame, text="Esporta", 
                                  command=self.export_to_file)
        export_button.grid(row=0, column=0)
        
        # Frame vuoto espandibile per riempire lo spazio rimanente
        spacer_frame = ttk.Frame(parent)
        spacer_frame.grid(row=5, column=0, sticky="nsew")


    def import_from_file(self):
        """Importa allenamenti da un file (YAML o Excel)"""
        import os  # Reimportiamo os all'interno della funzione per assicurarci che sia disponibile
        
        # Ottieni il nome del file
        filename = self.import_file_var.get().strip()
        if not filename:
            messagebox.showerror("Errore", 
                               "Seleziona un file da importare", 
                               parent=self)
            return
        
        # Verifica che il file esista
        if not os.path.exists(filename):
            messagebox.showerror("Errore", 
                               f"Il file {filename} non esiste", 
                               parent=self)
            return
        
        # Ottieni le opzioni
        overwrite = self.import_overwrite_var.get()
        
        # Log
        self.write_log(f"Importazione da {filename}")
        
        try:
            # Determina il tipo di file
            ext = os.path.splitext(filename.lower())[1]
            
            if ext in ['.yaml', '.yml']:
                # Importa da YAML
                with open(filename, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                self.write_log("File YAML caricato")
            elif ext == '.json':
                # Importa da JSON e converti in YAML
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.write_log("File JSON caricato e convertito in YAML")
            elif ext == '.xlsx':
                # Importa da Excel
                from planner.excel_to_yaml_converter import excel_to_yaml
                
                # Usa un file temporaneo per la conversione
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
                    tmp_filename = tmp.name
                    
                # Converti il file Excel in YAML
                data = excel_to_yaml(filename, tmp_filename)
                
                # Elimina il file temporaneo
                try:
                    os.unlink(tmp_filename)
                except:
                    pass
                    
                self.write_log("File Excel caricato e convertito")
            else:
                # Prova come YAML per altri formati
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    self.write_log("File caricato come YAML")
                except Exception as e:
                    messagebox.showerror("Errore", 
                                      f"Formato file non supportato: {ext}. Usa .yaml, .yml o .xlsx", 
                                      parent=self)
                    self.write_log(f"Errore: formato file non supportato: {ext}")
                    return
            
            # Lista delle chiavi speciali che non sono allenamenti
            config_keys = ['config', 'athlete_name', 'paces', 'power_values', 'swim_paces', 'heart_rates']
            
            # Estrai la configurazione se presente
            if 'config' in data:
                # Aggiorna la configurazione
                new_config = data.pop('config')
                
                # Aggiorna in modo sicuro (senza sovrascrivere tutto)
                if not 'workout_config' in self.controller.config:
                    self.controller.config['workout_config'] = {}
                
                # Aggiorna le varie sezioni
                for section in ['paces', 'speeds', 'swim_paces', 'heart_rates', 'power_values', 'margins']:
                    if section in new_config:
                        if section not in self.controller.config['workout_config']:
                            self.controller.config['workout_config'][section] = {}
                        
                        # Per ogni chiave nella sezione
                        for key, value in new_config[section].items():
                            self.controller.config['workout_config'][section][key] = value
                
                # Altri parametri
                for param in ['name_prefix', 'sport_type', 'athlete_name']:
                    if param in new_config:
                        self.controller.config['workout_config'][param] = new_config[param]
                
                self.write_log("Configurazione aggiornata")
            
            # Estrai athlete_name se presente nella radice
            if 'athlete_name' in data:
                athlete_name = data.pop('athlete_name')
                # Aggiorna il nome dell'atleta nella configurazione principale
                self.controller.config['athlete_name'] = athlete_name
                # E anche in workout_config per mantenere la coerenza
                if 'workout_config' not in self.controller.config:
                    self.controller.config['workout_config'] = {}
                self.controller.config['workout_config']['athlete_name'] = athlete_name
                self.write_log(f"Nome atleta aggiornato: {athlete_name}")
            
            # Estrai direttamente le sezioni di configurazione dalla radice e aggiornale
            for config_section in ['paces', 'power_values', 'swim_paces', 'speeds', 'heart_rates']:
                if config_section in data:
                    section_data = data.pop(config_section)
                    # Assicurati che workout_config esista
                    if 'workout_config' not in self.controller.config:
                        self.controller.config['workout_config'] = {}
                    # Aggiorna la sezione
                    self.controller.config['workout_config'][config_section] = section_data
                    self.write_log(f"Sezione {config_section} aggiornata")
            
            # Conta gli allenamenti
            total_workouts = sum(1 for name in data.keys() if name not in config_keys)
            imported_workouts = 0
            skipped_workouts = 0
            
            # Ottieni gli allenamenti correnti dall'editor
            current_workouts = self.controller.workout_editor_frame.workouts
            current_names = [name for name, _ in current_workouts]
            
            # Importa gli allenamenti
            for name, steps in data.items():
                # Salta le chiavi di configurazione
                if name in config_keys:
                    continue
                
                # Verifica se esiste già
                if name in current_names:
                    if overwrite:
                        # Rimuovi l'allenamento esistente
                        idx = current_names.index(name)
                        current_workouts[idx] = (name, steps)
                        self.write_log(f"Allenamento aggiornato: {name}")
                    else:
                        skipped_workouts += 1
                        self.write_log(f"Allenamento saltato (già esistente): {name}")
                        continue
                else:
                    # Aggiungi il nuovo allenamento
                    current_workouts.append((name, steps))
                    self.write_log(f"Allenamento importato: {name}")
                
                imported_workouts += 1
            
            # Aggiorna la lista degli allenamenti
            self.controller.workout_editor_frame.refresh_workout_list()
            
            # Mostra un messaggio di conferma
            messagebox.showinfo("Importazione completata", 
                              f"Importati {imported_workouts} allenamenti.\n"
                              f"Saltati {skipped_workouts} allenamenti.", 
                              parent=self)
            
            # Log
            self.write_log(f"Importazione completata: {imported_workouts} importati, {skipped_workouts} saltati")
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.write_log(f"Errore dettagliato: {error_details}")
            messagebox.showerror("Errore", 
                               f"Errore durante l'importazione: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")


    def browse_yaml_export_file(self):
        """Apre un selettore di file per scegliere dove salvare il file YAML"""
        filename = filedialog.asksaveasfilename(
            title="Salva file", 
            defaultextension=".yaml",
            filetypes=[("File YAML", "*.yaml *.yml"), ("Tutti i file", "*.*")]
        )
        
        if filename:
            self.yaml_export_file_var.set(filename)

    def browse_import_file(self):
        """Apre un selettore di file per scegliere un file da importare"""
        filetypes = [
            ("Tutti i file supportati", "*.yaml *.yml *.xlsx"),
            ("File YAML", "*.yaml *.yml"),
            ("File Excel", "*.xlsx"),
            ("Tutti i file", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Seleziona file da importare", 
            filetypes=filetypes
        )
        
        if filename:
            self.import_file_var.set(filename)
            self.add_to_recent_files(filename)

    def browse_source_file(self, var_to_update):
        """Apre un selettore di file per scegliere un file sorgente di qualsiasi formato supportato
        
        Args:
            var_to_update: La variabile StringVar da aggiornare con il percorso del file
        """
        filetypes = [
            ("Tutti i file supportati", "*.yaml *.yml *.xlsx"),
            ("File YAML", "*.yaml *.yml"),
            ("File Excel", "*.xlsx"),
            ("Tutti i file", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Seleziona file sorgente", 
            filetypes=filetypes
        )
        
        if filename:
            # Imposta la variabile StringVar con il percorso del file
            var_to_update.set(filename)
            # Aggiunge il file alla lista dei recenti
            self.add_to_recent_files(filename)
            # Attiva automaticamente l'opzione per utilizzare il file sorgente
            self.use_source_file_var.set(True)
            
            # Debug: verifica che la variabile sia stata effettivamente aggiornata
            self.write_log(f"File sorgente selezionato: {filename}")
            self.write_log(f"Valore della variabile: {var_to_update.get()}")

    def browse_export_dest_file(self):
        """Apre un selettore di file per scegliere dove salvare il file esportato"""
        filetypes = [
            ("File YAML", "*.yaml *.yml"),
            ("File Excel", "*.xlsx"),
            ("Tutti i file", "*.*")
        ]
        filename = filedialog.asksaveasfilename(
            title="Salva file", 
            defaultextension=".yaml",
            filetypes=filetypes
        )
        
        if filename:
            # Assicurati che abbia un'estensione
            if not any(filename.lower().endswith(ext) for ext in ['.yaml', '.yml', '.xlsx']):
                # Aggiungi estensione predefinita .yaml
                filename += '.yaml'
                    
            self.export_dest_file_var.set(filename)



    def write_log(self, message):
        """Scrive un messaggio nel log"""
        # Ottieni la data e l'ora correnti
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Formatta il messaggio
        log_message = f"[{now}] {message}\n"
        
        # Abilita la modifica
        self.log_text.configure(state=tk.NORMAL)
        
        # Inserisci il messaggio alla fine
        self.log_text.insert(tk.END, log_message)
        
        # Scorri alla fine
        self.log_text.see(tk.END)
        
        # Disabilita la modifica
        self.log_text.configure(state=tk.DISABLED)
        
        # Invece di aggiornare l'intera interfaccia, aggiorniamo solo il widget specifico
        # per evitare di causare ridimensionamenti a cascata
        self.log_text.update_idletasks()
    

    def clear_log(self):
        """Pulisce il log"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def copy_log_to_clipboard(self):
        """Copia il contenuto del log negli appunti"""
        log_content = self.log_text.get(1.0, tk.END)
        self.clipboard_clear()
        self.clipboard_append(log_content)
        messagebox.showinfo("Copia negli appunti", 
                           "Il contenuto del log è stato copiato negli appunti", 
                           parent=self)


    def browse_yaml_file(self):
        """Apre un selettore di file per scegliere un file YAML"""
        filetypes = [
            ("File YAML", "*.yaml *.yml"),
            ("Tutti i file", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Seleziona file", 
            filetypes=filetypes
        )
        
        if filename:
            self.yaml_file_var.set(filename)
            self.add_to_recent_files(filename)
    
    def browse_excel_file(self):
        """Apre un selettore di file per scegliere un file Excel"""
        filetypes = [
            ("File Excel", "*.xlsx"),
            ("Tutti i file", "*.*")
        ]
        filename = filedialog.askopenfilename(
            title="Seleziona file", 
            filetypes=filetypes
        )
        
        if filename:
            self.excel_file_var.set(filename)
            self.add_to_recent_files(filename)
    
    def browse_json_export_file(self):
        """Apre un selettore di file per scegliere dove salvare il file JSON"""
        filename = filedialog.asksaveasfilename(
            title="Salva file", 
            defaultextension=".json",
            filetypes=[("File JSON", "*.json"), ("Tutti i file", "*.*")]
        )
        
        if filename:
            self.yaml_export_file_var.set(filename)
    
    def browse_excel_export_file(self):
        """Apre un selettore di file per scegliere dove salvare il file Excel"""
        filename = filedialog.asksaveasfilename(
            title="Salva file", 
            defaultextension=".xlsx",
            filetypes=[("File Excel", "*.xlsx"), ("Tutti i file", "*.*")]
        )
        
        if filename:
            self.excel_export_file_var.set(filename)
    
    def add_to_recent_files(self, filename):
        """Aggiunge un file alla lista dei file recenti"""
        # Ottieni la lista dei file recenti
        recent_files = self.controller.config.get('recent_files', [])
        
        # Aggiungi il nuovo file all'inizio (se non c'è già)
        if filename in recent_files:
            recent_files.remove(filename)
        
        recent_files.insert(0, filename)
        
        # Mantieni al massimo 10 file
        recent_files = recent_files[:10]
        
        # Aggiorna la configurazione
        self.controller.config['recent_files'] = recent_files
        
        # Aggiorna la lista
        self.update_recent_files()
    
    def update_recent_files(self):
        """Aggiorna la lista dei file recenti"""
        # Pulisci la lista
        self.recents_listbox.delete(0, tk.END)
        
        # Aggiungi i file recenti
        recent_files = self.controller.config.get('recent_files', [])
        for filename in recent_files:
            self.recents_listbox.insert(tk.END, filename)
    
    def on_recent_file_select(self, event):
        """Gestisce la selezione di un file recente"""
        # Ottieni l'indice del file selezionato
        selection = self.recents_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        filename = self.recents_listbox.get(index)
        
        # Verifica il tipo di file
        if filename.lower().endswith(('.yaml', '.yml')):
            self.yaml_file_var.set(filename)
        elif filename.lower().endswith('.xlsx'):
            self.excel_file_var.set(filename)
        else:
            # Per altri tipi di file, chiedi all'utente
            if messagebox.askyesno("Formato sconosciuto", 
                                 f"Il file {filename} ha un formato sconosciuto.\n"
                                 f"Vuoi provare a importarlo come YAML?", 
                                 parent=self):
                self.yaml_file_var.set(filename)
            else:
                self.excel_file_var.set(filename)
    
    def import_from_yaml(self):
        """Importa allenamenti da un file YAML/JSON"""
        # Ottieni il nome del file
        filename = self.yaml_file_var.get().strip()
        if not filename:
            messagebox.showerror("Errore", 
                               "Seleziona un file da importare", 
                               parent=self)
            return
        
        # Verifica che il file esista
        if not os.path.exists(filename):
            messagebox.showerror("Errore", 
                               f"Il file {filename} non esiste", 
                               parent=self)
            return
        
        # Ottieni le opzioni
        overwrite = self.yaml_overwrite_var.get()
        
        # Log
        self.write_log(f"Importazione da {filename}")
        
        try:
            # Determina il tipo di file
            if filename.lower().endswith(('.yaml', '.yml')):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            elif filename.lower().endswith('.json'):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # Prova prima come YAML, poi come JSON
                try:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                except:
                    with open(filename, 'r', encoding='utf-8') as f:
                        data = json.load(f)
            
            # Lista delle chiavi speciali che non sono allenamenti
            config_keys = ['config', 'athlete_name', 'paces', 'power_values', 'swim_paces', 'speeds', 'heart_rates']
            
            # Estrai la configurazione se presente
            if 'config' in data:
                # Aggiorna la configurazione
                new_config = data.pop('config')
                
                # Aggiorna in modo sicuro (senza sovrascrivere tutto)
                if not 'workout_config' in self.controller.config:
                    self.controller.config['workout_config'] = {}
                
                # Aggiorna le varie sezioni
                for section in ['paces', 'speeds', 'swim_paces', 'heart_rates', 'power_values', 'margins']:
                    if section in new_config:
                        if section not in self.controller.config['workout_config']:
                            self.controller.config['workout_config'][section] = {}
                        
                        # Per ogni chiave nella sezione
                        for key, value in new_config[section].items():
                            self.controller.config['workout_config'][section][key] = value
                
                # Altri parametri
                for param in ['name_prefix', 'sport_type', 'athlete_name']:
                    if param in new_config:
                        self.controller.config['workout_config'][param] = new_config[param]
                
                self.write_log("Configurazione aggiornata")
            
            # Estrai athlete_name se presente nella radice
            if 'athlete_name' in data:
                athlete_name = data.pop('athlete_name')
                # Aggiorna il nome dell'atleta nella configurazione principale
                self.controller.config['athlete_name'] = athlete_name
                # E anche in workout_config per mantenere la coerenza
                if 'workout_config' not in self.controller.config:
                    self.controller.config['workout_config'] = {}
                self.controller.config['workout_config']['athlete_name'] = athlete_name
                self.write_log(f"Nome atleta aggiornato: {athlete_name}")
            
            # Estrai direttamente le sezioni di configurazione dalla radice e aggiornale
            for config_section in ['paces', 'power_values', 'swim_paces', 'speeds', 'heart_rates']:
                if config_section in data:
                    section_data = data.pop(config_section)
                    # Assicurati che workout_config esista
                    if 'workout_config' not in self.controller.config:
                        self.controller.config['workout_config'] = {}
                    # Aggiorna la sezione
                    self.controller.config['workout_config'][config_section] = section_data
                    self.write_log(f"Sezione {config_section} aggiornata")
            
            # Conta gli allenamenti
            total_workouts = sum(1 for name in data.keys() if name not in config_keys)
            imported_workouts = 0
            skipped_workouts = 0
            
            # Ottieni gli allenamenti correnti dall'editor
            current_workouts = self.controller.workout_editor_frame.workouts
            current_names = [name for name, _ in current_workouts]
            
            # Importa gli allenamenti
            for name, steps in data.items():
                # Salta le chiavi di configurazione
                if name in config_keys:
                    continue
                
                # Verifica se esiste già
                if name in current_names:
                    if overwrite:
                        # Rimuovi l'allenamento esistente
                        idx = current_names.index(name)
                        current_workouts[idx] = (name, steps)
                        self.write_log(f"Allenamento aggiornato: {name}")
                    else:
                        skipped_workouts += 1
                        self.write_log(f"Allenamento saltato (già esistente): {name}")
                        continue
                else:
                    # Aggiungi il nuovo allenamento
                    current_workouts.append((name, steps))
                    self.write_log(f"Allenamento importato: {name}")
                
                imported_workouts += 1
            
            # Aggiorna la lista degli allenamenti
            self.controller.workout_editor_frame.refresh_workout_list()
            
            # Mostra un messaggio di conferma
            messagebox.showinfo("Importazione completata", 
                              f"Importati {imported_workouts} allenamenti.\n"
                              f"Saltati {skipped_workouts} allenamenti.", 
                              parent=self)
            
            # Log
            self.write_log(f"Importazione completata: {imported_workouts} importati, {skipped_workouts} saltati")
            
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Errore durante l'importazione: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")
    
    def import_from_excel(self):
        """Importa allenamenti da un file Excel"""
        # Ottieni il nome del file
        filename = self.excel_file_var.get().strip()
        if not filename:
            messagebox.showerror("Errore", 
                               "Seleziona un file da importare", 
                               parent=self)
            return
        
        # Verifica che il file esista
        if not os.path.exists(filename):
            messagebox.showerror("Errore", 
                               f"Il file {filename} non esiste", 
                               parent=self)
            return
        
        # Ottieni le opzioni
        overwrite = self.excel_overwrite_var.get()
        
        # Log
        self.write_log(f"Importazione da {filename}")
        
        try:
            # Importa il file Excel
            from planner.excel_to_yaml_converter import excel_to_yaml
            
            # Crea un file temporaneo per il YAML
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
                tmp_filename = tmp.name
            
            # Converti da Excel a YAML - usiamo il tipo di sport predefinito dalla configurazione
            sport_type = self.controller.config.get('workout_config', {}).get('sport_type', 'running')
            yaml_data = excel_to_yaml(filename, tmp_filename, sport_type)
            
            # Ora importa dal file YAML
            if yaml_data:
                # Estrai il nome dell'atleta se presente
                if 'athlete_name' in yaml_data:
                    athlete_name = yaml_data.pop('athlete_name')
                    # Aggiorna il nome dell'atleta nella configurazione principale
                    self.controller.config['athlete_name'] = athlete_name
                    # E anche in workout_config per mantenere la coerenza
                    if 'workout_config' not in self.controller.config:
                        self.controller.config['workout_config'] = {}
                    self.controller.config['workout_config']['athlete_name'] = athlete_name
                    self.write_log(f"Nome atleta aggiornato: {athlete_name}")
                
                # Estrai la configurazione se presente
                if 'config' in yaml_data:
                    # Controlla anche se il nome atleta è nella configurazione
                    if 'athlete_name' in yaml_data['config']:
                        athlete_name = yaml_data['config']['athlete_name']
                        # Aggiorna il nome dell'atleta nella configurazione principale
                        self.controller.config['athlete_name'] = athlete_name
                        # E anche in workout_config per mantenere la coerenza
                        if 'workout_config' not in self.controller.config:
                            self.controller.config['workout_config'] = {}
                        self.controller.config['workout_config']['athlete_name'] = athlete_name
                        self.write_log(f"Nome atleta aggiornato: {athlete_name}")
                    
                    # Aggiorna la configurazione
                    new_config = yaml_data.pop('config')
                    
                    # Aggiorna in modo sicuro (senza sovrascrivere tutto)
                    if not 'workout_config' in self.controller.config:
                        self.controller.config['workout_config'] = {}
                    
                    # Aggiorna le varie sezioni
                    for section in ['margins', 'name_prefix', 'sport_type', 'heart_rates', 'preferred_days']:
                        if section in new_config:
                            self.controller.config['workout_config'][section] = new_config[section]
                    
                    self.write_log("Configurazione aggiornata")
                
                # Estrai paces, power_values e swim_paces dalle chiavi principali
                # Questi sono ora fuori dalla sezione config (per evitare duplicazione)
                if 'paces' in yaml_data:
                    paces_data = yaml_data.pop('paces')
                    if 'workout_config' not in self.controller.config:
                        self.controller.config['workout_config'] = {}
                    self.controller.config['workout_config']['paces'] = paces_data
                    self.write_log("Ritmi per la corsa aggiornati")
                    
                if 'power_values' in yaml_data:
                    power_data = yaml_data.pop('power_values')
                    if 'workout_config' not in self.controller.config:
                        self.controller.config['workout_config'] = {}
                    self.controller.config['workout_config']['power_values'] = power_data
                    self.write_log("Valori potenza per il ciclismo aggiornati")
                    
                if 'swim_paces' in yaml_data:
                    swim_data = yaml_data.pop('swim_paces')
                    if 'workout_config' not in self.controller.config:
                        self.controller.config['workout_config'] = {}
                    self.controller.config['workout_config']['swim_paces'] = swim_data
                    self.write_log("Passi vasca per il nuoto aggiornati")
                
                # Conta gli allenamenti
                total_workouts = len(yaml_data)
                imported_workouts = 0
                skipped_workouts = 0
                
                # Ottieni gli allenamenti correnti dall'editor
                current_workouts = self.controller.workout_editor_frame.workouts
                current_names = [name for name, _ in current_workouts]
                
                # Importa gli allenamenti
                for name, steps in yaml_data.items():
                    # Salta athlete_name e config che non sono allenamenti
                    if name in ['athlete_name', 'config', 'paces', 'power_values', 'swim_paces']:
                        continue
                        
                    # Salta se name è 'athlete_name' (nel caso fosse stato erroneamente importato come allenamento)
                    if 'athlete_name' in name.lower():
                        self.write_log(f"Ignorato allenamento con nome '{name}' (sembra essere un nome atleta, non un allenamento)")
                        skipped_workouts += 1
                        continue
                    
                    # Verifica se esiste già
                    if name in current_names:
                        if overwrite:
                            # Rimuovi l'allenamento esistente
                            idx = current_names.index(name)
                            current_workouts[idx] = (name, steps)
                            self.write_log(f"Allenamento aggiornato: {name}")
                        else:
                            skipped_workouts += 1
                            self.write_log(f"Allenamento saltato (già esistente): {name}")
                            continue
                    else:
                        # Aggiungi il nuovo allenamento
                        current_workouts.append((name, steps))
                        self.write_log(f"Allenamento importato: {name}")
                    
                    imported_workouts += 1
                
                # Aggiorna la lista degli allenamenti
                self.controller.workout_editor_frame.refresh_workout_list()
                
                # Aggiorna il nome dell'atleta nell'interfaccia, se esiste il campo
                if hasattr(self.controller.workout_editor_frame, 'athlete_name_var'):
                    self.controller.workout_editor_frame.athlete_name_var.set(
                        self.controller.config.get('athlete_name', '')
                    )
                
                # Mostra un messaggio di conferma
                messagebox.showinfo("Importazione completata", 
                                  f"Importati {imported_workouts} allenamenti.\n"
                                  f"Saltati {skipped_workouts} allenamenti.", 
                                  parent=self)
                
                # Log
                self.write_log(f"Importazione completata: {imported_workouts} importati, {skipped_workouts} saltati")
                
            # Elimina il file temporaneo
            try:
                os.unlink(tmp_filename)
            except:
                pass
            
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Errore durante l'importazione: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")
    
    def create_sample_excel(self):
        """Crea un file Excel di esempio"""
        # Apri un selettore di file per scegliere dove salvare il file
        filename = filedialog.asksaveasfilename(
            title="Salva file di esempio", 
            defaultextension=".xlsx",
            filetypes=[("File Excel", "*.xlsx"), ("Tutti i file", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            # Usa il tipo di sport di default dalla configurazione
            sport_type = self.controller.config.get('workout_config', {}).get('sport_type', 'running')

            # Log
            self.write_log(f"Creazione file di esempio {filename}")
            self.write_log(f"Tipo di sport: {sport_type}")
            
            # Crea il file di esempio
            from planner.excel_to_yaml_converter import create_sample_excel
            
            # Passa correttamente il filename come primo parametro e il tipo di sport come secondo
            sample_file = create_sample_excel(filename, sport_type)
            
            if sample_file:
                messagebox.showinfo("File creato", 
                                  f"File di esempio creato con successo:\n{filename}", 
                                  parent=self)
                
                # Aggiungi ai file recenti
                self.add_to_recent_files(filename)
                
                # Imposta nel campo di importazione (usa import_file_var invece di excel_file_var)
                self.import_file_var.set(filename)
                
                # Log
                self.write_log("File di esempio creato con successo")
            else:
                messagebox.showerror("Errore", 
                                  "Impossibile creare il file di esempio", 
                                  parent=self)
                self.write_log("Errore nella creazione del file di esempio")
        
        except Exception as e:
            messagebox.showerror("Errore", 
                              f"Errore durante la creazione del file di esempio: {str(e)}", 
                              parent=self)
            self.write_log(f"Errore: {str(e)}")
    
    def refresh_garmin_workouts(self):
        """Aggiorna la lista degli allenamenti disponibili su Garmin Connect"""
        if not self.garmin_client:
            messagebox.showerror("Errore", 
                               "Devi essere connesso a Garmin Connect", 
                               parent=self)
            return
        
        # Log
        self.write_log("Aggiornamento lista allenamenti da Garmin Connect")
        
        # Crea una finestra di progresso
        progress = tk.Toplevel(self)
        progress.title("Caricamento in corso")
        progress.geometry("300x100")
        progress.transient(self)
        progress.grab_set()
        
        # Etichetta
        ttk.Label(progress, text="Recupero allenamenti...").pack(pady=(20, 10))
        
        # Barra di progresso
        progressbar = ttk.Progressbar(progress, mode='indeterminate')
        progressbar.pack(fill=tk.X, padx=20)
        progressbar.start()
        
        # Aggiorna la finestra
        progress.update()
        
        try:
            # Ottieni la lista degli allenamenti
            self.garmin_workouts = self.garmin_client.list_workouts()
            
            # Aggiorna la lista
            self.update_garmin_workout_list()
            
            # Log
            self.write_log(f"{len(self.garmin_workouts)} allenamenti trovati")
            
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Impossibile ottenere gli allenamenti: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")
        
        finally:
            # Chiudi la finestra di progresso
            progress.destroy()

    def refresh_remote_workouts(self):
        """Aggiorna la lista degli allenamenti remoti per la scheda di esportazione"""
        if not self.garmin_client:
            messagebox.showerror("Errore", 
                              "Devi essere connesso a Garmin Connect", 
                              parent=self)
            return
        
        # Log
        self.write_log("Aggiornamento lista allenamenti remoti da Garmin Connect")
        
        # Crea una finestra di progresso
        progress = tk.Toplevel(self)
        progress.title("Caricamento in corso")
        progress.geometry("300x100")
        progress.transient(self)
        progress.grab_set()
        
        # Etichetta
        ttk.Label(progress, text="Recupero allenamenti remoti...").pack(pady=(20, 10))
        
        # Barra di progresso
        progressbar = ttk.Progressbar(progress, mode='indeterminate')
        progressbar.pack(fill=tk.X, padx=20)
        progressbar.start()
        
        # Aggiorna la finestra
        progress.update()
        
        try:
            # Ottieni la lista degli allenamenti remoti
            self.remote_workouts = self.garmin_client.list_workouts()
            
            # Aggiorna la lista
            self.update_remote_workout_list()
            
            # Log
            self.write_log(f"{len(self.remote_workouts)} allenamenti remoti trovati")
            
        except Exception as e:
            messagebox.showerror("Errore", 
                              f"Impossibile ottenere gli allenamenti remoti: {str(e)}", 
                              parent=self)
            self.write_log(f"Errore: {str(e)}")
        
        finally:
            # Chiudi la finestra di progresso
            progress.destroy()
    
    def update_garmin_workout_list(self):
        """Aggiorna la lista degli allenamenti disponibili su Garmin Connect"""
        # Pulisci la lista
        self.garmin_listbox.delete(0, tk.END)
        
        # Se non ci sono allenamenti, esci
        if not hasattr(self, 'garmin_workouts') or not self.garmin_workouts:
            return
        
        # Filtra gli allenamenti
        filter_text = self.garmin_filter_var.get().lower()
        
        # Aggiungi gli allenamenti filtrati
        for workout in self.garmin_workouts:
            # Ottieni il nome
            name = workout.get('workoutName', '')
            
            # Filtra per testo
            if filter_text and filter_text not in name.lower():
                continue
            
            # Formatta il tipo di sport
            sport_type = workout.get('sportType', {}).get('sportTypeKey', 'running')
            
            # Aggiungi alla lista
            self.garmin_listbox.insert(tk.END, f"{name} ({sport_type})")

    def update_remote_workout_list(self):
        """Aggiorna la lista degli allenamenti remoti"""
        # Pulisci la lista
        self.remote_listbox.delete(0, tk.END)
        
        # Se non ci sono allenamenti remoti, esci
        if not hasattr(self, 'remote_workouts') or not self.remote_workouts:
            return
        
        # Filtra gli allenamenti
        filter_text = self.remote_filter_var.get().lower()
        
        # Aggiungi gli allenamenti filtrati
        for workout in self.remote_workouts:
            # Ottieni il nome
            name = workout.get('workoutName', '')
            
            # Filtra per testo
            if filter_text and filter_text not in name.lower():
                continue
            
            # Formatta il tipo di sport
            sport_type = workout.get('sportType', {}).get('sportTypeKey', 'running')
            
            # Aggiungi alla lista
            self.remote_listbox.insert(tk.END, f"{name} ({sport_type})")
    
    def select_all_garmin(self):
        """Seleziona tutti gli allenamenti nella lista Garmin"""
        self.garmin_listbox.selection_set(0, tk.END)
    
    def deselect_all_garmin(self):
        """Deseleziona tutti gli allenamenti nella lista Garmin"""
        self.garmin_listbox.selection_clear(0, tk.END)

    def select_all_remote(self):
        """Seleziona tutti gli allenamenti nella lista remota"""
        self.remote_listbox.selection_set(0, tk.END)
    
    def deselect_all_remote(self):
        """Deseleziona tutti gli allenamenti nella lista remota"""
        self.remote_listbox.selection_clear(0, tk.END)
    
    def import_from_garmin(self):
        """Importa allenamenti selezionati da Garmin Connect"""
        if not self.garmin_client:
            messagebox.showerror("Errore", 
                               "Devi essere connesso a Garmin Connect", 
                               parent=self)
            return
        
        # Ottieni gli allenamenti selezionati
        selection = self.garmin_listbox.curselection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", 
                                 "Seleziona almeno un allenamento da importare", 
                                 parent=self)
            return
        
        # Ottieni le opzioni
        overwrite = self.garmin_overwrite_var.get()
        
        # Log
        self.write_log(f"Importazione di {len(selection)} allenamenti da Garmin Connect")
        
        # Crea una finestra di progresso
        progress = tk.Toplevel(self)
        progress.title("Importazione in corso")
        progress.geometry("400x150")
        progress.transient(self)
        progress.grab_set()
        
        # Etichetta
        status_var = tk.StringVar(value="Importazione in corso...")
        status_label = ttk.Label(progress, textvariable=status_var)
        status_label.pack(pady=(20, 10))
        
        # Barra di progresso
        progressbar = ttk.Progressbar(progress, mode='determinate', length=300, maximum=len(selection))
        progressbar.pack(pady=10)
        
        # Aggiorna la finestra
        progress.update()
        
        try:
            # Ottieni gli allenamenti correnti dall'editor
            current_workouts = self.controller.workout_editor_frame.workouts
            current_names = [name for name, _ in current_workouts]
            
            # Contatori
            imported = 0
            updated = 0
            skipped = 0
            errors = 0
            
            # Importa gli allenamenti selezionati
            for i, index in enumerate(selection):
                try:
                    # Aggiorna lo stato
                    workout = self.garmin_workouts[index]
                    name = workout.get('workoutName', '')
                    status_var.set(f"Importazione {i+1}/{len(selection)}: {name}")
                    progressbar['value'] = i
                    progress.update()
                    
                    # Ottieni i dettagli dell'allenamento
                    workout_id = workout.get('workoutId')
                    workout_detail = self.garmin_client.get_workout(workout_id)
                    
                    # Converti in formato interno
                    steps = self.convert_garmin_to_internal(workout_detail)
                    
                    # Verifica se esiste già
                    if name in current_names:
                        if overwrite:
                            # Aggiorna l'allenamento esistente
                            idx = current_names.index(name)
                            current_workouts[idx] = (name, steps)
                            updated += 1
                            self.write_log(f"Allenamento aggiornato: {name}")
                        else:
                            # Salta l'allenamento
                            skipped += 1
                            self.write_log(f"Allenamento saltato (già esistente): {name}")
                            continue
                    else:
                        # Aggiungi il nuovo allenamento
                        current_workouts.append((name, steps))
                        imported += 1
                        self.write_log(f"Allenamento importato: {name}")
                
                except Exception as e:
                    # Log dell'errore
                    errors += 1
                    self.write_log(f"Errore nell'importazione di '{name}': {str(e)}")
            
            # Aggiorna la lista degli allenamenti
            self.controller.workout_editor_frame.refresh_workout_list()
            
            # Mostra un messaggio di conferma
            messagebox.showinfo("Importazione completata", 
                              f"Importati {imported} allenamenti.\n"
                              f"Aggiornati {updated} allenamenti.\n"
                              f"Saltati {skipped} allenamenti.\n"
                              f"Errori: {errors}", 
                              parent=self)
            
            # Log
            self.write_log(f"Importazione completata: {imported} importati, {updated} aggiornati, {skipped} saltati, {errors} errori")
            
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Errore durante l'importazione: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")
        
        finally:
            # Chiudi la finestra di progresso
            progress.destroy()
    
    def convert_garmin_to_internal(self, workout_detail):
        """Converte un allenamento dal formato Garmin al formato interno"""
        # Utilizza la funzione già definita nell'editor di allenamenti
        return self.controller.workout_editor_frame.convert_garmin_to_internal(workout_detail)
    
    def export_to_json(self):
        """Esporta allenamenti in un file JSON"""
        # Ottieni il nome del file destinazione
        filename = self.yaml_export_file_var.get().strip()
        if not filename:
            messagebox.showerror("Errore", 
                               "Specifica un file di destinazione", 
                               parent=self)
            return
        
        # Ottieni le opzioni
        clean = self.yaml_clean_var.get()
        use_source = self.use_source_file_var.get()
        
        # Log
        self.write_log(f"Esportazione in {filename}")
        self.write_log(f"Formato: JSON")
        
        try:
            # Se usando file sorgente
            if use_source:
                source_file = self.yaml_source_file_var.get().strip()
                if not source_file:
                    messagebox.showerror("Errore", 
                                       "Specifica un file sorgente o disattiva l'opzione 'Usa file sorgente'", 
                                       parent=self)
                    return
                    
                self.write_log(f"Usando file sorgente: {source_file}")
                
                # Determina il tipo di file sorgente
                import os
                ext = os.path.splitext(source_file.lower())[1]
                
                # Carica il file in base all'estensione
                if ext in ['.yaml', '.yml']:
                    with open(source_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    self.write_log("File YAML caricato")
                elif ext == '.json':
                    with open(source_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.write_log("File JSON caricato")
                elif ext == '.xlsx':
                    # Usa il convertitore Excel-YAML
                    from planner.excel_to_yaml_converter import excel_to_yaml
                    # Usa un file temporaneo per la conversione se necessario
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
                        tmp_filename = tmp.name
                        
                    # Converti il file Excel in YAML
                    data = excel_to_yaml(source_file, tmp_filename)
                    os.unlink(tmp_filename)  # Elimina il file temporaneo
                    self.write_log("File Excel convertito e caricato")
                else:
                    # Estensione non riconosciuta, prova come YAML, poi come JSON
                    try:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        self.write_log("File caricato come YAML")
                    except:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        self.write_log("File caricato come JSON")
                
                # Se clean è attivo, pulisci i dati
                if clean:
                    self.write_log("Pulizia dei dati in corso...")
                    # Rimuovi eventuali passi vuoti o nulli
                    for name, steps in list(data.items()):
                        if not isinstance(steps, list) and not name.startswith('config') and name not in ['athlete_name', 'paces', 'power_values', 'swim_paces']:
                            continue  # Salta le chiavi che non sono allenamenti
                        
                        if isinstance(steps, list):
                            cleaned_steps = []
                            for step in steps:
                                if step:  # Se non è None
                                    cleaned_steps.append(step)
                            data[name] = cleaned_steps
                
                # Esporta nel file JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
            
            # Se usando allenamenti in memoria
            else:
                # Ottieni gli allenamenti
                workouts = self.controller.workout_editor_frame.workouts
                
                # Se non ci sono allenamenti, mostra un errore
                if not workouts:
                    messagebox.showwarning("Nessun allenamento", 
                                         "Non ci sono allenamenti da esportare", 
                                         parent=self)
                    return
                
                # Crea il dizionario per l'esportazione
                export_data = {}
                
                # Aggiungi la configurazione base (esclusi i valori di paces, power_values e swim_paces)
                if 'workout_config' in self.controller.config:
                    # Copia la configurazione per non modificare l'originale
                    config = dict(self.controller.config['workout_config'])
                    
                    # Escludi i valori paces, power_values e swim_paces dalla config
                    # e mettili come chiavi principali del JSON
                    if 'paces' in config:
                        export_data['paces'] = config.pop('paces')
                    
                    if 'power_values' in config:
                        export_data['power_values'] = config.pop('power_values')
                        
                    if 'swim_paces' in config:
                        export_data['swim_paces'] = config.pop('swim_paces')
                    
                    # Il resto della configurazione va in config
                    export_data['config'] = config
                    
                    # Aggiungi il nome dell'atleta alla configurazione esportata
                    if 'athlete_name' in self.controller.config and self.controller.config['athlete_name']:
                        export_data['config']['athlete_name'] = self.controller.config['athlete_name']
                        # Aggiungi anche come chiave principale per compatibilità
                        export_data['athlete_name'] = self.controller.config['athlete_name']
                
                # Aggiungi gli allenamenti
                for name, steps in workouts:
                    # Se clean è attivo, pulisci i passi
                    if clean:
                        # Rimuovi eventuali passi vuoti o nulli
                        cleaned_steps = []
                        for step in steps:
                            if step:  # Se non è None
                                cleaned_steps.append(step)
                        export_data[name] = cleaned_steps
                    else:
                        export_data[name] = steps
                
                # Esporta nel file JSON
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2)
            
            # Aggiungi ai file recenti
            self.add_to_recent_files(filename)
            
            # Mostra un messaggio di conferma
            messagebox.showinfo("Esportazione completata", 
                              f"Esportazione in {filename} completata con successo", 
                              parent=self)
            
            # Log
            self.write_log(f"Esportazione completata: file {filename} creato")
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.write_log(f"Errore dettagliato: {error_details}")
            messagebox.showerror("Errore", 
                               f"Errore durante l'esportazione: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")
    
    def export_to_excel(self):
        """Esporta allenamenti in un file Excel"""
        # Ottieni il nome del file
        filename = self.excel_export_file_var.get().strip()
        if not filename:
            messagebox.showerror("Errore", 
                               "Specifica un file di destinazione", 
                               parent=self)
            return
        
        # Ottieni le opzioni
        include_config = self.excel_include_config_var.get()
        use_source = self.use_excel_source_file_var.get()
        
        # Log
        self.write_log(f"Esportazione in {filename}")
        
        try:
            # Creiamo una funzione per convertire allenamenti + config in formato adatto per Excel
            def prepare_export_data(data_dict):
                export_data = {}
                
                # Aggiungi la configurazione
                if include_config:
                    if 'config' in data_dict:
                        export_data['config'] = data_dict['config']
                    elif 'workout_config' in self.controller.config:
                        export_data['config'] = self.controller.config['workout_config']
                    
                    # Assicurati che la sezione power_values esista se non c'è
                    if 'power_values' not in export_data.get('config', {}):
                        if 'power_values' in data_dict:
                            if 'config' not in export_data:
                                export_data['config'] = {}
                            export_data['config']['power_values'] = data_dict['power_values']
                        else:
                            if 'config' in export_data and 'power_values' not in export_data['config']:
                                export_data['config']['power_values'] = {'ftp': 250}
                    
                    # Assicurati che ci siano i margini di potenza
                    if 'config' in export_data and 'margins' in export_data['config']:
                        if 'power_up' not in export_data['config']['margins']:
                            export_data['config']['margins']['power_up'] = 10
                        if 'power_down' not in export_data['config']['margins']:
                            export_data['config']['margins']['power_down'] = 10
                    
                    # Includi le sezioni paces, power_values, swim_paces se presenti
                    for section in ['paces', 'power_values', 'swim_paces']:
                        if section in data_dict:
                            export_data[section] = data_dict[section]
                    
                    # Aggiungi anche il nome dell'atleta se presente
                    if 'athlete_name' in data_dict:
                        export_data['athlete_name'] = data_dict['athlete_name']
                    elif 'athlete_name' in self.controller.config:
                        export_data['athlete_name'] = self.controller.config['athlete_name']
                
                # Aggiungi gli allenamenti
                for name, steps in data_dict.items():
                    if name not in ['config', 'paces', 'power_values', 'swim_paces', 'athlete_name'] and isinstance(steps, list):
                        export_data[name] = steps
                
                return export_data

            # Se usando file sorgente
            if use_source:
                source_file = self.excel_source_file_var.get().strip()
                if not source_file:
                    messagebox.showerror("Errore", 
                                       "Specifica un file sorgente o disattiva l'opzione 'Usa file sorgente'", 
                                       parent=self)
                    return
                    
                self.write_log(f"Usando file sorgente: {source_file}")
                
                # Determina il tipo di file sorgente
                import os
                ext = os.path.splitext(source_file.lower())[1]
                
                # Carica il file in base all'estensione
                if ext in ['.yaml', '.yml']:
                    with open(source_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    self.write_log("File YAML caricato")
                elif ext == '.json':
                    with open(source_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.write_log("File JSON caricato")
                elif ext == '.xlsx':
                    # Se è già un Excel, cerchiamo di importarlo prima
                    # Usa il convertitore Excel-YAML
                    from planner.excel_to_yaml_converter import excel_to_yaml
                    # Usa un file temporaneo per la conversione se necessario
                    import tempfile
                    with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp:
                        tmp_filename = tmp.name
                        
                    # Converti il file Excel in YAML
                    data = excel_to_yaml(source_file, tmp_filename)
                    try:
                        os.unlink(tmp_filename)  # Elimina il file temporaneo
                    except:
                        pass
                    self.write_log("File Excel caricato")
                else:
                    # Estensione non riconosciuta, prova come YAML, poi come JSON
                    try:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            data = yaml.safe_load(f)
                        self.write_log("File caricato come YAML")
                    except:
                        with open(source_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        self.write_log("File caricato come JSON")
                
                # Prepara i dati per l'esportazione
                export_data = prepare_export_data(data)
                
                # Converti in Excel
                from planner.excel_to_yaml_converter import yaml_to_excel
                result = yaml_to_excel(export_data, filename)
                
            # Se usando allenamenti in memoria
            else:
                # Ottieni gli allenamenti
                workouts = self.controller.workout_editor_frame.workouts
                
                # Se non ci sono allenamenti, mostra un errore
                if not workouts:
                    messagebox.showwarning("Nessun allenamento", 
                                         "Non ci sono allenamenti da esportare", 
                                         parent=self)
                    return
                
                # Crea il dizionario per l'esportazione
                raw_data = {}
                
                # Aggiungi le sezioni di configurazione se richiesto
                if include_config and 'workout_config' in self.controller.config:
                    raw_data['config'] = self.controller.config['workout_config']
                    
                    # Aggiungi anche il nome dell'atleta se presente
                    if 'athlete_name' in self.controller.config:
                        raw_data['athlete_name'] = self.controller.config['athlete_name']
                
                # Aggiungi gli allenamenti
                for name, steps in workouts:
                    raw_data[name] = steps
                
                # Prepara i dati per l'esportazione
                export_data = prepare_export_data(raw_data)
                
                # Converti in Excel
                from planner.excel_to_yaml_converter import yaml_to_excel
                result = yaml_to_excel(export_data, filename)
            
            if result:
                # Aggiungi ai file recenti
                self.add_to_recent_files(filename)
                
                # Mostra un messaggio di conferma
                messagebox.showinfo("Esportazione completata", 
                                  f"Esportati gli allenamenti in {filename}", 
                                  parent=self)
                
                # Log
                self.write_log(f"Esportazione completata: file {filename} creato")
            else:
                messagebox.showerror("Errore", 
                                   "Errore nella creazione del file Excel", 
                                   parent=self)
                self.write_log("Errore nella creazione del file Excel")
                    
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.write_log(f"Errore dettagliato: {error_details}")
            messagebox.showerror("Errore", 
                               f"Errore durante l'esportazione: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")
    
    def download_selected_workouts(self):
        """Scarica gli allenamenti selezionati da Garmin Connect"""
        if not self.garmin_client:
            messagebox.showerror("Errore", 
                               "Devi essere connesso a Garmin Connect", 
                               parent=self)
            return
        
        # Ottieni gli allenamenti selezionati
        selection = self.remote_listbox.curselection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", 
                                 "Seleziona almeno un allenamento da scaricare", 
                                 parent=self)
            return
        
        # Log
        self.write_log(f"Scaricamento di {len(selection)} allenamenti da Garmin Connect")
        
        # Crea una finestra di progresso
        progress = tk.Toplevel(self)
        progress.title("Scaricamento in corso")
        progress.geometry("400x150")
        progress.transient(self)
        progress.grab_set()
        
        # Etichetta
        status_var = tk.StringVar(value="Scaricamento in corso...")
        status_label = ttk.Label(progress, textvariable=status_var)
        status_label.pack(pady=(20, 10))
        
        # Barra di progresso
        progressbar = ttk.Progressbar(progress, mode='determinate', length=300, maximum=len(selection))
        progressbar.pack(pady=10)
        
        # Aggiorna la finestra
        progress.update()
        
        try:
            # Ottieni gli allenamenti correnti dall'editor
            current_workouts = self.controller.workout_editor_frame.workouts
            current_names = [name for name, _ in current_workouts]
            
            # Contatori
            downloaded = 0
            updated = 0
            skipped = 0
            errors = 0
            
            # Scarica gli allenamenti selezionati
            for i, index in enumerate(selection):
                try:
                    # Aggiorna lo stato
                    workout = self.remote_workouts[index]
                    name = workout.get('workoutName', '')
                    status_var.set(f"Scaricamento {i+1}/{len(selection)}: {name}")
                    progressbar['value'] = i
                    progress.update()
                    
                    # Ottieni i dettagli dell'allenamento
                    workout_id = workout.get('workoutId')
                    workout_detail = self.garmin_client.get_workout(workout_id)
                    
                    # Converti in formato interno
                    steps = self.convert_garmin_to_internal(workout_detail)
                    
                    # Verifica se esiste già
                    if name in current_names:
                        # Aggiorna l'allenamento esistente
                        idx = current_names.index(name)
                        current_workouts[idx] = (name, steps)
                        updated += 1
                        self.write_log(f"Allenamento aggiornato: {name}")
                    else:
                        # Aggiungi il nuovo allenamento
                        current_workouts.append((name, steps))
                        downloaded += 1
                        self.write_log(f"Allenamento scaricato: {name}")
                
                except Exception as e:
                    # Log dell'errore
                    errors += 1
                    self.write_log(f"Errore nel download di '{name}': {str(e)}")
            
            # Aggiorna la lista degli allenamenti
            self.controller.workout_editor_frame.refresh_workout_list()
            
            # Mostra un messaggio di conferma
            messagebox.showinfo("Download completato", 
                              f"Scaricati {downloaded} allenamenti.\n"
                              f"Aggiornati {updated} allenamenti.\n"
                              f"Errori: {errors}", 
                              parent=self)
            
            # Log
            self.write_log(f"Download completato: {downloaded} scaricati, {updated} aggiornati, {errors} errori")
            
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Errore durante il download: {str(e)}", 
                               parent=self)
            self.write_log(f"Errore: {str(e)}")
        
        finally:
            # Chiudi la finestra di progresso
            progress.destroy()
    
    def on_login(self, client):
        """Gestisce l'evento di login completato"""
        self.garmin_client = client
        
        # Aggiorna lo stato
        self.garmin_status_var.set("Connesso a Garmin Connect")
        self.garmin_export_status_var.set("Connesso a Garmin Connect")
        
        # Abilita i pulsanti
        self.garmin_refresh_button['state'] = 'normal'
        self.garmin_import_button['state'] = 'normal'
        self.export_refresh_button['state'] = 'normal'
        self.download_button['state'] = 'normal'
        
        # Aggiorna le liste degli allenamenti
        self.refresh_garmin_workouts()
        self.refresh_remote_workouts()
        
        # Log
        self.write_log("Connesso a Garmin Connect")
    
    def on_logout(self):
        """Gestisce l'evento di logout"""
        self.garmin_client = None
        
        # Aggiorna lo stato
        self.garmin_status_var.set("Non connesso")
        self.garmin_export_status_var.set("Non connesso")
        
        # Disabilita i pulsanti
        self.garmin_refresh_button['state'] = 'disabled'
        self.garmin_import_button['state'] = 'disabled'
        self.export_refresh_button['state'] = 'disabled'
        self.download_button['state'] = 'disabled'
        
        # Pulisci le liste
        self.garmin_listbox.delete(0, tk.END)
        if hasattr(self, 'garmin_workouts'):
            del self.garmin_workouts
        
        self.remote_listbox.delete(0, tk.END)
        if hasattr(self, 'remote_workouts'):
            del self.remote_workouts
        
        # Log
        self.write_log("Disconnesso da Garmin Connect")