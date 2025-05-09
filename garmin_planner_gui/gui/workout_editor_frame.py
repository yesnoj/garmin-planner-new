#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per la creazione e modifica degli allenamenti
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import logging
import json
import copy
import datetime
import re

from .styles import COLORS, STEP_ICONS, SPORT_ICONS
from .workout_step_dialog import StepDialog
from .repeat_dialog import RepeatDialog
from .workout_config_dialog import WorkoutConfigDialog
from garmin_planner_gui.gui.utils import (
    show_error, show_warning, show_info, ask_yes_no,
    format_workout_name, parse_workout_name
)

from garmin_planner_gui.gui.scheduling import schedule_workouts_by_week, apply_scheduled_dates, clear_workout_dates

class WorkoutEditorFrame(ttk.Frame):
    """Frame per la creazione e modifica degli allenamenti"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.garmin_client = None
        self.workouts = []  # Lista degli allenamenti in memoria
        
        # Carica la configurazione degli allenamenti
        self.workout_config = self.controller.config.get('workout_config', {})
        
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Dividi in sezione superiore e inferiore
        upper_frame = ttk.Frame(main_frame)
        upper_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Dividi la sezione superiore in due parti (lista e editor)
        list_frame = ttk.LabelFrame(upper_frame, text="Allenamenti disponibili")
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        editor_frame = ttk.LabelFrame(upper_frame, text="Editor allenamento")
        editor_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # Sezione lista allenamenti
        self.create_workout_list(list_frame)
        
        # Sezione editor
        self.create_workout_editor(editor_frame)
        
        # Sezione inferiore per i pulsanti e lo stato
        lower_frame = ttk.Frame(main_frame)
        lower_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Frame per il nome dell'atleta
        athlete_frame = ttk.Frame(lower_frame)
        athlete_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Campo per il nome dell'atleta
        ttk.Label(athlete_frame, text="Nome Atleta:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Ottieni il nome atleta dalla configurazione
        athlete_name = self.controller.config.get('athlete_name', '')
        
        # Variabile per tenere traccia del nome atleta
        self.athlete_name_var = tk.StringVar(value=athlete_name)
        ttk.Entry(athlete_frame, textvariable=self.athlete_name_var, width=30).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Pulsante per salvare il nome atleta
        ttk.Button(athlete_frame, text="Salva Nome Atleta", 
                  command=self.save_athlete_name).pack(side=tk.LEFT)
        
        # Pulsanti principali
        button_frame = ttk.Frame(lower_frame)
        button_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Pulsante per sincronizzare con Garmin Connect
        self.sync_button = ttk.Button(button_frame, text="Sincronizza con Garmin Connect", 
                                     command=self.sync_with_garmin)
        self.sync_button.pack(side=tk.RIGHT, padx=5)
        
        # Inizialmente disabilitato fino al login
        self.sync_button['state'] = 'disabled'
        
        # Pulsante per gestire le configurazioni
        config_button = ttk.Button(button_frame, text="Gestisci configurazioni", 
                                 command=self.open_config_dialog)
        config_button.pack(side=tk.LEFT, padx=5)
        
        # Etichetta per lo stato
        self.status_var = tk.StringVar(value="Pronto")
        status_label = ttk.Label(lower_frame, textvariable=self.status_var, 
                               style="Status.TLabel")
        status_label.pack(anchor=tk.W, pady=5)
        self.load_planning_config()


    def schedule_workouts_dialog(self):
        """Reindirizza al metodo di pianificazione diretta"""
        self.schedule_workouts_direct()


    def clear_workout_dates(self):
        """Rimuove le date dagli allenamenti selezionati"""
        # Verifica che ci siano allenamenti selezionati
        selection = self.workout_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", 
                                "Seleziona gli allenamenti da cui rimuovere le date.", 
                                parent=self)
            return
        
        # Ottieni gli indici degli allenamenti selezionati
        indices = [self.workout_tree.index(item) for item in selection]
        
        # Chiedi conferma
        if not messagebox.askyesno("Conferma rimozione", 
                                f"Sei sicuro di voler rimuovere le date da {len(indices)} allenamenti selezionati?", 
                                parent=self):
            return
        
        try:
            # Importa la funzione per rimuovere le date
            from garmin_planner_gui.gui.scheduling import clear_workout_dates
            
            # Rimuovi le date
            self.workouts = clear_workout_dates(self.workouts, indices)
            
            # Aggiorna la lista
            self.refresh_workout_list()
            
            # Mostra messaggio di conferma
            messagebox.showinfo("Operazione completata", 
                              f"Date rimosse da {len(indices)} allenamenti.", 
                              parent=self)
            
        except Exception as e:
            logging.error(f"Errore nella rimozione delle date: {str(e)}")
            messagebox.showerror("Errore", 
                              f"Si è verificato un errore durante la rimozione delle date:\n{str(e)}", 
                              parent=self)




    def save_athlete_name(self):
        """Salva il nome dell'atleta nella configurazione"""
        # Ottieni il nome dell'atleta
        athlete_name = self.athlete_name_var.get().strip()
        
        # Salva il nome dell'atleta sia nella radice che in workout_config
        self.controller.config['athlete_name'] = athlete_name
        
        # Assicurati che workout_config esista
        if 'workout_config' not in self.controller.config:
            self.controller.config['workout_config'] = {}
        
        # Salva anche in workout_config per la compatibilità con l'export
        self.controller.config['workout_config']['athlete_name'] = athlete_name
        
        # Salva la configurazione
        from garmin_planner_gui.gui.utils import save_config
        save_config(self.controller.config)
        
        # Aggiorna l'interfaccia
        self.status_var.set(f"Nome atleta impostato: {athlete_name}")
        self.controller.set_status(f"Nome atleta impostato: {athlete_name}")
        
        # Mostra conferma
        messagebox.showinfo("Nome atleta salvato", 
                          f"Il nome atleta '{athlete_name}' è stato salvato.", 
                          parent=self)


    def create_workout_list(self, parent):
        """Crea la lista degli allenamenti"""
        # Barra degli strumenti sopra la lista
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Filtro per tipo di sport
        ttk.Label(toolbar, text="Sport:").pack(side=tk.LEFT, padx=(0, 5))
        self.sport_filter_var = tk.StringVar(value="Tutti")
        sport_combo = ttk.Combobox(toolbar, textvariable=self.sport_filter_var, 
                                  values=["Tutti", "Corsa", "Ciclismo", "Nuoto"],
                                  width=10, state="readonly")
        sport_combo.pack(side=tk.LEFT, padx=(0, 10))
        sport_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Filtro per settimana
        ttk.Label(toolbar, text="Settimana:").pack(side=tk.LEFT, padx=(0, 5))
        self.week_filter_var = tk.StringVar(value="Tutte")
        self.week_combo = ttk.Combobox(toolbar, textvariable=self.week_filter_var, 
                                     values=["Tutte"],
                                     width=10, state="readonly")
        self.week_combo.pack(side=tk.LEFT)
        self.week_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # Filtro per ricerca
        ttk.Label(toolbar, text="Cerca:").pack(side=tk.LEFT, padx=(10, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=15)
        search_entry.pack(side=tk.LEFT)
        self.search_var.trace_add("write", lambda *args: self.apply_filters())
        
        # Frame per la lista con scrollbar
        list_container = ttk.Frame(parent)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        # Crea la treeview per la lista
        columns = ("name", "sport", "date", "steps")
        self.workout_tree = ttk.Treeview(list_container, columns=columns, show="headings", 
                                       selectmode="extended")  # Modificato da "browse" a "extended" per consentire selezioni multiple
        
        # Definisci le intestazioni
        self.workout_tree.heading("name", text="Nome")
        self.workout_tree.heading("sport", text="Sport")
        self.workout_tree.heading("date", text="Data")
        self.workout_tree.heading("steps", text="Passi")
        
        # Definisci le larghezze delle colonne
        self.workout_tree.column("name", width=250)
        self.workout_tree.column("sport", width=80)
        self.workout_tree.column("date", width=100)
        self.workout_tree.column("steps", width=60)
        
        # Aggiungi scrollbar
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, 
                                command=self.workout_tree.yview)
        self.workout_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.workout_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Associa eventi
        self.workout_tree.bind("<<TreeviewSelect>>", self.on_workout_select)
        self.workout_tree.bind("<Double-1>", self.on_workout_double_click)
        
        # Pulsanti sotto la lista - MODIFICATO: rimosso pulsante "Pianifica..." e mantenuto "Rimuovi date"
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Pulsante per nuovo allenamento
        new_button = ttk.Button(button_frame, text="Nuovo", command=self.new_workout)
        new_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Pulsante per copiare un allenamento
        copy_button = ttk.Button(button_frame, text="Copia", command=self.copy_workout)
        copy_button.pack(side=tk.LEFT, padx=5)
        
        # Pulsante per eliminare un allenamento
        delete_button = ttk.Button(button_frame, text="Elimina", command=self.delete_workout)
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # Pulsante per rimuovere le date pianificate
        self.clear_dates_button = ttk.Button(button_frame, text="Rimuovi date", command=self.clear_workout_dates)
        self.clear_dates_button.pack(side=tk.LEFT, padx=5)
        
        # Pulsante per aggiornare la lista
        refresh_button = ttk.Button(button_frame, text="Aggiorna", command=self.refresh_workout_list)
        refresh_button.pack(side=tk.RIGHT)


    
    def create_workout_editor(self, parent):
        """Crea l'editor per l'allenamento selezionato"""
        # Frame per le proprietà dell'allenamento
        properties_frame = ttk.Frame(parent)
        properties_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Griglia per le proprietà
        ttk.Label(properties_frame, text="Nome:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(properties_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, 5), pady=5)
        
        # Settimana e sessione
        ttk.Label(properties_frame, text="Settimana:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.week_var = tk.StringVar(value="01")
        week_entry = ttk.Entry(properties_frame, textvariable=self.week_var, width=5)
        week_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        
        ttk.Label(properties_frame, text="Sessione:").grid(row=1, column=2, sticky=tk.W, padx=(10, 5), pady=5)
        self.session_var = tk.StringVar(value="01")
        session_entry = ttk.Entry(properties_frame, textvariable=self.session_var, width=5)
        session_entry.grid(row=1, column=3, sticky=tk.W, padx=(0, 5), pady=5)
        
        ttk.Label(properties_frame, text="Descrizione:").grid(row=1, column=4, sticky=tk.W, padx=(10, 5), pady=5)
        self.description_var = tk.StringVar()
        description_entry = ttk.Entry(properties_frame, textvariable=self.description_var, width=20)
        description_entry.grid(row=1, column=5, sticky=tk.W+tk.E, padx=(0, 5), pady=5)
        
        # Tipo di sport
        ttk.Label(properties_frame, text="Sport:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.sport_var = tk.StringVar(value="running")
        sport_combo = ttk.Combobox(properties_frame, textvariable=self.sport_var, 
                                  values=["running", "cycling", "swimming"],
                                  width=15, state="readonly")
        sport_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        sport_combo.bind("<<ComboboxSelected>>", self.on_sport_change)
        
        # Data pianificata
        ttk.Label(properties_frame, text="Data:").grid(row=2, column=2, sticky=tk.W, padx=(10, 5), pady=5)
        self.date_var = tk.StringVar()
        date_entry = ttk.Entry(properties_frame, textvariable=self.date_var, width=12)
        date_entry.grid(row=2, column=3, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Pulsante calendario
        calendar_button = ttk.Button(properties_frame, text="📅", width=3, 
                                    command=self.show_calendar)
        calendar_button.grid(row=2, column=4, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Configurazione colonne
        properties_frame.columnconfigure(1, weight=1)
        properties_frame.columnconfigure(5, weight=2)
        
        # Frame per gli step dell'allenamento
        steps_frame = ttk.LabelFrame(parent, text="Passi dell'allenamento")
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Toolbar per gli step
        steps_toolbar = ttk.Frame(steps_frame)
        steps_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Pulsanti per gestire gli step
        self.add_step_button = ttk.Button(steps_toolbar, text="Aggiungi passo", 
                                        command=self.add_step)
        self.add_step_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.add_repeat_button = ttk.Button(steps_toolbar, text="Aggiungi ripetizione", 
                                          command=self.add_repeat)
        self.add_repeat_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_step_button = ttk.Button(steps_toolbar, text="Modifica", 
                                         command=self.edit_step)
        self.edit_step_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_step_button = ttk.Button(steps_toolbar, text="Elimina", 
                                           command=self.delete_step)
        self.delete_step_button.pack(side=tk.LEFT, padx=5)
        
        self.move_up_button = ttk.Button(steps_toolbar, text="↑", width=3, 
                                       command=self.move_step_up)
        self.move_up_button.pack(side=tk.LEFT, padx=5)
        
        self.move_down_button = ttk.Button(steps_toolbar, text="↓", width=3, 
                                         command=self.move_step_down)
        self.move_down_button.pack(side=tk.LEFT, padx=5)
        
        # Lista degli step
        steps_list_frame = ttk.Frame(steps_frame)
        steps_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea la treeview per gli step
        columns = ("index", "type", "details")
        self.steps_tree = ttk.Treeview(steps_list_frame, columns=columns, show="headings", 
                                     selectmode="browse")
        
        # Definisci le intestazioni
        self.steps_tree.heading("index", text="#")
        self.steps_tree.heading("type", text="Tipo")
        self.steps_tree.heading("details", text="Dettagli")
        
        # Definisci le larghezze delle colonne
        self.steps_tree.column("index", width=30)
        self.steps_tree.column("type", width=100)
        self.steps_tree.column("details", width=400)
        
        # Aggiungi scrollbar
        scrollbar = ttk.Scrollbar(steps_list_frame, orient=tk.VERTICAL, 
                                command=self.steps_tree.yview)
        self.steps_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.steps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Associa eventi
        self.steps_tree.bind("<Double-1>", self.on_step_double_click)
        
        # Frame per le azioni
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Pulsanti per salvare/annullare
        self.save_button = ttk.Button(action_frame, text="Salva allenamento", 
                                    style="Success.TButton", 
                                    command=self.save_workout)
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_button = ttk.Button(action_frame, text="Annulla modifiche", 
                                      command=self.cancel_edit)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Stato iniziale: disabilitato
        self.disable_editor()
    
    def disable_editor(self):
        """Disabilita l'editor"""
        for widget in [
            self.add_step_button, self.add_repeat_button, 
            self.edit_step_button, self.delete_step_button,
            self.move_up_button, self.move_down_button,
            self.save_button, self.cancel_button
        ]:
            widget['state'] = 'disabled'
    
    def enable_editor(self):
        """Abilita l'editor"""
        for widget in [
            self.add_step_button, self.add_repeat_button, 
            self.save_button, self.cancel_button
        ]:
            widget['state'] = 'normal'
    
    def new_workout(self):
        """Crea un nuovo allenamento"""
        # Pulisci l'editor
        self.clear_editor()
        
        # Imposta valori di default
        self.name_var.set("Nuovo allenamento")
        self.week_var.set("01")
        self.session_var.set("01")
        self.description_var.set("")
        
        # Imposta il tipo di sport di default dalla configurazione
        default_sport = self.workout_config.get('sport_type', 'running')
        self.sport_var.set(default_sport)
        
        # Nessuna data predefinita
        self.date_var.set("")
        
        # Nuova lista di step vuota
        self.current_steps = []
        self.update_steps_tree()
        
        # Abilita l'editor
        self.enable_editor()
    
    def copy_workout(self):
        """Copia l'allenamento selezionato"""
        selection = self.workout_tree.selection()
        if not selection:
            show_warning("Nessuna selezione", "Seleziona un allenamento da copiare", parent=self)
            return
        
        # Ottieni l'indice
        index = self.workout_tree.index(selection[0])
        
        # Verifica che ci siano ancora allenamenti
        if not self.workouts or index >= len(self.workouts):
            show_warning("Errore", "Nessun allenamento disponibile da copiare", parent=self)
            return
        
        # Ottieni l'allenamento originale
        orig_name, orig_steps = self.workouts[index]
        
        # Estrai settimana, sessione e descrizione
        week, session, description = parse_workout_name(orig_name)
        
        if week is not None:
            # Incrementa la sessione per il nuovo allenamento
            session += 1
            new_description = f"Copia di {description}"
            new_name = format_workout_name(week, session, new_description)
        else:
            # Se il nome non è in formato standard
            new_name = f"Copia di {orig_name}"
        
        # Crea una copia profonda degli step
        new_steps = copy.deepcopy(orig_steps)
        
        # Aggiungi il nuovo allenamento alla lista
        self.workouts.append((new_name, new_steps))
        
        # Aggiorna la lista
        self.refresh_workout_list()
        
        # Seleziona il nuovo allenamento
        for i, (name, _) in enumerate(self.workouts):
            if name == new_name:
                item = self.workout_tree.get_children()[i]
                self.workout_tree.selection_set(item)
                self.workout_tree.see(item)
                self.on_workout_select()
                break
    
    def delete_workout(self):
        """Elimina l'allenamento selezionato"""
        selection = self.workout_tree.selection()
        if not selection:
            show_warning("Nessuna selezione", "Seleziona un allenamento da eliminare", parent=self)
            return
        
        # Ottieni l'indice
        index = self.workout_tree.index(selection[0])
        
        # Verifica che ci siano ancora allenamenti
        if not self.workouts or index >= len(self.workouts):
            show_warning("Errore", "Nessun allenamento disponibile da eliminare", parent=self)
            return
        
        # Ottieni il nome dell'allenamento da eliminare
        workout_name = self.workouts[index][0]
        
        # Chiedi conferma
        if not ask_yes_no("Conferma eliminazione", 
                        f"Sei sicuro di voler eliminare l'allenamento '{workout_name}'?", 
                        parent=self):
            return
        
        # Elimina l'allenamento
        self.workouts.pop(index)
        
        # Aggiorna la lista
        self.refresh_workout_list()
        
        # Pulisci l'editor
        self.clear_editor()
        self.disable_editor()
    
    def on_workout_select(self, event=None):
        """Gestisce la selezione di un allenamento dalla lista"""
        selection = self.workout_tree.selection()
        if not selection:
            return
        
        # Se è selezionato solo un elemento, caricalo nell'editor
        if len(selection) == 1:
            # Ottieni l'indice
            index = self.workout_tree.index(selection[0])
            
            # Ottieni l'allenamento
            name, steps = self.workouts[index]
            
            # Aggiorna l'editor
            self.load_workout(name, steps)
        else:
            # Se sono selezionati più elementi, disabilita l'editor
            self.clear_editor()
            self.disable_editor()
            
            # Aggiorna lo stato per indicare quanti allenamenti sono selezionati
            self.status_var.set(f"{len(selection)} allenamenti selezionati")
    
    def on_workout_double_click(self, event):
        """Gestisce il doppio click su un allenamento"""
        self.on_workout_select(event)
    
    def load_workout(self, name, steps):
        """Carica un allenamento nell'editor"""
        # Pulisci eventuali dati precedenti
        self.clear_editor()
        
        # Imposta il nome
        self.name_var.set(name)
        
        # Estrai settimana, sessione e descrizione
        week, session, description = parse_workout_name(name)
        
        if week is not None:
            self.week_var.set(str(week).zfill(2))
            self.session_var.set(str(session).zfill(2))
            self.description_var.set(description)
        else:
            # Se il nome non è in formato standard
            self.week_var.set("01")
            self.session_var.set("01")
            self.description_var.set(name)
        
        # Estrai eventuali metadati
        sport_type = "running"  # Default
        date = ""
        
        # Crea una copia profonda degli step
        self.current_steps = copy.deepcopy(steps)
        
        # Cerca i metadati negli step
        filtered_steps = []
        for step in self.current_steps:
            if isinstance(step, dict):
                if 'sport_type' in step:
                    sport_type = step['sport_type']
                elif 'date' in step:
                    date = step['date']
                else:
                    filtered_steps.append(step)
        
        # Aggiorna il tipo di sport e la data
        self.sport_var.set(sport_type)
        self.date_var.set(date)
        
        # Aggiorna la lista degli step
        self.current_steps = filtered_steps
        self.update_steps_tree()
        
        # Abilita l'editor
        self.enable_editor()
    
    def clear_editor(self):
        """Pulisce l'editor"""
        self.name_var.set("")
        self.week_var.set("")
        self.session_var.set("")
        self.description_var.set("")
        self.sport_var.set("running")
        self.date_var.set("")
        self.current_steps = []
        self.update_steps_tree()
    
    def update_steps_tree(self):
        """Aggiorna la lista degli step nell'editor"""
        # Pulisci la lista attuale
        for item in self.steps_tree.get_children():
            self.steps_tree.delete(item)
        
        # Aggiungi i nuovi step
        for i, step in enumerate(self.current_steps):
            # Gestisci diversi formati di step
            if isinstance(step, dict):
                if 'repeat' in step and 'steps' in step:
                    # Step di tipo "repeat"
                    iterations = step['repeat']
                    substeps = step['steps']
                    step_type = "repeat"
                    details = f"{iterations} ripetizioni ({len(substeps)} passi)"
                    
                    # Aggiungi alla treeview
                    item = self.steps_tree.insert("", "end", values=(i+1, step_type, details))
                
                elif len(step) == 1:
                    # Step normale
                    step_type = list(step.keys())[0]
                    details = step[step_type]
                    
                    # Aggiungi alla treeview
                    self.steps_tree.insert("", "end", values=(i+1, step_type, details))
        
        # Abilita/disabilita i pulsanti di modifica
        if self.current_steps:
            self.edit_step_button['state'] = 'normal'
            self.delete_step_button['state'] = 'normal'
            self.move_up_button['state'] = 'normal'
            self.move_down_button['state'] = 'normal'
        else:
            self.edit_step_button['state'] = 'disabled'
            self.delete_step_button['state'] = 'disabled'
            self.move_up_button['state'] = 'disabled'
            self.move_down_button['state'] = 'disabled'
        
        # Aggiorna anche la rappresentazione grafica
        self.draw_workout()
    
    def add_step(self):
        """Aggiunge un nuovo step all'allenamento"""
        # Ottieni il tipo di sport corrente
        sport_type = self.sport_var.get()
        
        # Apri il dialog per la definizione dello step
        dialog = StepDialog(self, sport_type=sport_type)
        
        # Se l'utente ha confermato
        if dialog.result:
            step_type, step_detail = dialog.result
            
            # Aggiungi lo step alla lista
            self.current_steps.append({step_type: step_detail})
            
            # Aggiorna la lista
            self.update_steps_tree()
    
    def add_repeat(self):
        """Aggiunge una sezione di ripetizioni all'allenamento"""
        # Ottieni il tipo di sport corrente
        sport_type = self.sport_var.get()
        
        # Apri il dialog per definire le ripetizioni
        dialog = RepeatDialog(self, sport_type=sport_type)
        
        # Se l'utente ha confermato
        if dialog.result:
            iterations, steps = dialog.result
            
            # Crea lo step di ripetizione
            repeat_step = {'repeat': iterations, 'steps': steps}
            
            # Aggiungi lo step alla lista
            self.current_steps.append(repeat_step)
            
            # Aggiorna la lista
            self.update_steps_tree()
    
    def edit_step(self):
        """Modifica lo step selezionato"""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona un passo da modificare", parent=self)
            return
        
        # Ottieni l'indice
        index = int(self.steps_tree.item(selection[0], "values")[0]) - 1
        
        # Ottieni lo step
        step = self.current_steps[index]
        
        # Controlla il formato
        if isinstance(step, dict):
            if 'repeat' in step and 'steps' in step:
                # È un passo di tipo "repeat", aprire il dialog delle ripetizioni
                iterations = step['repeat']
                substeps = step['steps']
                
                # Usa la classe RepeatDialog per modificare la ripetizione
                dialog = RepeatDialog(self, iterations=iterations, steps=substeps, sport_type=self.sport_var.get())
                
                if dialog.result:
                    new_iterations, new_steps = dialog.result
                    
                    # Aggiorna lo step di ripetizione con i nuovi valori
                    self.current_steps[index] = {'repeat': new_iterations, 'steps': new_steps}
                    
                    # Aggiorna la lista
                    self.update_steps_tree()
            else:
                # Passo normale
                step_type = list(step.keys())[0]
                step_detail = step[step_type]
                
                # Usa la classe StepDialog per modificare il passo
                dialog = StepDialog(self, step_type=step_type, step_detail=step_detail, sport_type=self.sport_var.get())
                
                if dialog.result:
                    new_type, new_detail = dialog.result
                    
                    # Aggiorna lo step
                    self.current_steps[index] = {new_type: new_detail}
                    
                    # Aggiorna la lista
                    self.update_steps_tree()
    
    def delete_step(self):
        """Elimina lo step selezionato"""
        selection = self.steps_tree.selection()
        if not selection:
            show_warning("Nessuna selezione", "Seleziona un passo da eliminare", parent=self)
            return
        
        # Ottieni l'indice
        index = int(self.steps_tree.item(selection[0], "values")[0]) - 1
        
        # Chiedi conferma
        if not ask_yes_no("Conferma eliminazione", 
                        "Sei sicuro di voler eliminare questo passo?", 
                        parent=self):
            return
        
        # Elimina lo step
        self.current_steps.pop(index)
        
        # Aggiorna la lista
        self.update_steps_tree()
    
    def on_step_double_click(self, event):
        """Gestisce il doppio click su uno step"""
        self.edit_step()
    
    def move_step_up(self):
        """Sposta lo step selezionato verso l'alto"""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice
        index = int(self.steps_tree.item(selection[0], "values")[0]) - 1
        
        # Non si può spostare il primo elemento in alto
        if index == 0:
            return
        
        # Scambia gli step
        self.current_steps[index], self.current_steps[index-1] = self.current_steps[index-1], self.current_steps[index]
        
        # Aggiorna la lista
        self.update_steps_tree()
        
        # Seleziona lo step spostato
        new_selection = self.steps_tree.get_children()[index-1]
        self.steps_tree.selection_set(new_selection)
        self.steps_tree.see(new_selection)
    
    def move_step_down(self):
        """Sposta lo step selezionato verso il basso"""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice
        index = int(self.steps_tree.item(selection[0], "values")[0]) - 1
        
        # Non si può spostare l'ultimo elemento in basso
        if index >= len(self.current_steps) - 1:
            return
        
        # Scambia gli step
        self.current_steps[index], self.current_steps[index+1] = self.current_steps[index+1], self.current_steps[index]
        
        # Aggiorna la lista
        self.update_steps_tree()
        
        # Seleziona lo step spostato
        new_selection = self.steps_tree.get_children()[index+1]
        self.steps_tree.selection_set(new_selection)
        self.steps_tree.see(new_selection)
    
    def on_sport_change(self, event=None):
        """Gestisce il cambio di tipo di sport"""
        sport_type = self.sport_var.get()
        
        # Se non è un evento reale o non ci sono step, non fare nulla
        if event is None or not hasattr(self, 'current_steps') or not self.current_steps:
            return
        
        # Trova il tipo di sport attuale dai metadati
        current_sport_type = "running"  # Default
        for step in self.current_steps:
            if isinstance(step, dict) and 'sport_type' in step:
                current_sport_type = step['sport_type']
                break
        
        # Se il tipo di sport è cambiato, chiedi conferma
        if current_sport_type != sport_type:
            if ask_yes_no("Cambio tipo di sport", 
                        f"Hai cambiato il tipo di sport da {current_sport_type} a {sport_type}.\n"
                        f"Questo potrebbe richiedere l'adattamento dei passi esistenti.\n"
                        f"Continuare?", 
                        parent=self):
                # Aggiorna il tipo di sport nei metadati
                for i, step in enumerate(self.current_steps):
                    if isinstance(step, dict) and 'sport_type' in step:
                        self.current_steps[i] = {'sport_type': sport_type}
                        break
                else:
                    # Se non è stato trovato un passo con sport_type, aggiungi un nuovo passo
                    self.current_steps.insert(0, {'sport_type': sport_type})
                
                # Informa l'utente che alcuni passi potrebbero richiedere modifiche manuali
                show_info("Tipo di sport aggiornato", 
                        "Il tipo di sport è stato aggiornato. Potresti dover rivedere i passi esistenti "
                        "per assicurarti che siano compatibili con il nuovo tipo di sport.", 
                        parent=self)
                
            else:
                # Ripristina il tipo di sport precedente senza triggerare nuovi eventi
                self.sport_var.set(current_sport_type)
    
    def show_calendar(self):
        """Mostra un selettore di data"""
        try:
            from tkcalendar import Calendar
            
            # Crea una finestra top-level
            top = tk.Toplevel(self)
            top.title("Seleziona data")
            top.geometry("450x300")
            top.transient(self)
            top.grab_set()
            
            # Data iniziale
            if self.date_var.get():
                try:
                    initial_date = datetime.datetime.strptime(self.date_var.get(), "%Y-%m-%d").date()
                except ValueError:
                    initial_date = datetime.date.today()
            else:
                initial_date = datetime.date.today()
            
            # Crea il calendario
            cal = Calendar(top, selectmode='day', year=initial_date.year, 
                          month=initial_date.month, day=initial_date.day,
                          date_pattern="yyyy-mm-dd")
            cal.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Funzione per selezionare la data
            def select_date():
                self.date_var.set(cal.get_date())
                top.destroy()
            
            # Pulsante per confermare
            ttk.Button(top, text="Seleziona", command=select_date).pack(pady=10)
            
        except ImportError:
            # Se tkcalendar non è disponibile, usa un semplice dialogo
            date_str = simpledialog.askstring("Data", "Inserisci la data (YYYY-MM-DD):", 
                                            parent=self, initialvalue=self.date_var.get())
            if date_str:
                try:
                    # Verifica che sia una data valida
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    self.date_var.set(date_str)
                except ValueError:
                    show_error("Errore", "Formato data non valido. Usa YYYY-MM-DD.", parent=self)
    
    def save_workout(self):
        """Salva l'allenamento corrente"""
        # Ottieni i valori
        week = self.week_var.get().strip()
        session = self.session_var.get().strip()
        description = self.description_var.get().strip()
        sport_type = self.sport_var.get()
        date = self.date_var.get().strip()
        
        # Validazione
        if not week.isdigit() or not session.isdigit():
            show_error("Errore", "Settimana e sessione devono essere numeri", parent=self)
            return
        
        if not description:
            show_error("Errore", "Inserisci una descrizione", parent=self)
            return
        
        # Formatta il nome dell'allenamento
        name = format_workout_name(int(week), int(session), description)
        
        # Crea una lista di passi completa con i metadati
        steps = []
        
        # Aggiungi il tipo di sport come primo elemento
        steps.append({"sport_type": sport_type})
        
        # Aggiungi la data se presente
        if date:
            try:
                # Verifica che sia una data valida
                datetime.datetime.strptime(date, "%Y-%m-%d")
                steps.append({"date": date})
            except ValueError:
                show_error("Errore", "Formato data non valido. Usa YYYY-MM-DD.", parent=self)
                return
        
        # Aggiungi gli step dell'allenamento
        steps.extend(self.current_steps)
        
        # Cerca se esiste già un allenamento con lo stesso nome
        existing_index = None
        for i, (workout_name, _) in enumerate(self.workouts):
            if workout_name == name:
                existing_index = i
                break
        
        if existing_index is not None:
            # Chiedi conferma per la sovrascrittura
            if not ask_yes_no("Allenamento esistente", 
                            f"L'allenamento '{name}' esiste già. Sovrascrivere?", 
                            parent=self):
                return
            
            # Aggiorna l'allenamento esistente
            self.workouts[existing_index] = (name, steps)
        else:
            # Aggiungi il nuovo allenamento
            self.workouts.append((name, steps))
        
        # Aggiorna la lista
        self.refresh_workout_list()
        
        # Seleziona l'allenamento salvato
        for i, (workout_name, _) in enumerate(self.workouts):
            if workout_name == name:
                item = self.workout_tree.get_children()[i]
                self.workout_tree.selection_set(item)
                self.workout_tree.see(item)
                break
        
        # Aggiorna lo stato
        self.status_var.set(f"Allenamento '{name}' salvato")
        self.controller.set_status(f"Allenamento '{name}' salvato")
    
    def cancel_edit(self):
        """Annulla le modifiche correnti"""
        # Chiedi conferma solo se ci sono modifiche
        if self.name_var.get() or self.current_steps:
            if ask_yes_no("Annulla modifiche", 
                        "Sei sicuro di voler annullare le modifiche correnti?", 
                        parent=self):
                self.clear_editor()
                self.disable_editor()
        else:
            self.clear_editor()
            self.disable_editor()
    
    def refresh_workout_list(self):
        """Aggiorna la lista degli allenamenti"""
        # Salva la selezione corrente
        selection = self.workout_tree.selection()
        selected_name = ""
        if selection:
            index = self.workout_tree.index(selection[0])
            # Verifica che l'indice sia valido
            if self.workouts and index < len(self.workouts):
                selected_name = self.workouts[index][0]
        
        # Pulisci la lista attuale
        for item in self.workout_tree.get_children():
            self.workout_tree.delete(item)
        
        # Estrai le settimane disponibili per il filtro
        weeks = set()
        
        # Aggiungi gli allenamenti filtrati
        filtered_workouts = self.get_filtered_workouts()
        for name, steps in filtered_workouts:
            # Estrai il tipo di sport e la data dagli step
            sport_type = "running"  # Default
            workout_date = ""
            
            # Conta i passi effettivi
            actual_steps = 0
            
            for step in steps:
                if isinstance(step, dict):
                    if 'sport_type' in step:
                        sport_type = step['sport_type']
                    elif 'date' in step:
                        workout_date = step['date']
                    else:
                        actual_steps += 1
            
            # Estrai la settimana dal nome per il filtro
            week, _, _ = parse_workout_name(name)
            if week is not None:
                weeks.add(str(week).zfill(2))
            
            # Formatta il tipo di sport per la visualizzazione
            sport_display = sport_type.capitalize()
            
            # Formatta il testo per il numero di passi
            steps_text = f"{actual_steps} passo" if actual_steps == 1 else f"{actual_steps} passi"
            
            # Aggiungi alla lista
            self.workout_tree.insert("", "end", values=(name, sport_display, workout_date, steps_text))
        
        # Aggiorna il filtro per settimana
        weeks = sorted(list(weeks))
        self.week_combo['values'] = ["Tutte"] + weeks
        
        # Ripristina la selezione
        if selected_name and filtered_workouts:
            for i, (name, _) in enumerate(filtered_workouts):
                if name == selected_name:
                    try:
                        item = self.workout_tree.get_children()[i]
                        self.workout_tree.selection_set(item)
                        self.workout_tree.see(item)
                    except IndexError:
                        pass
                    break
    
    def get_filtered_workouts(self):
        """Restituisce gli allenamenti filtrati"""
        # Ottieni i filtri
        sport_filter = self.sport_filter_var.get()
        week_filter = self.week_filter_var.get()
        search_text = self.search_var.get().lower()
        
        # Converti il filtro sport
        if sport_filter == "Tutti":
            sport_filter = None
        elif sport_filter == "Corsa":
            sport_filter = "running"
        elif sport_filter == "Ciclismo":
            sport_filter = "cycling"
        elif sport_filter == "Nuoto":
            sport_filter = "swimming"
        
        # Converti il filtro settimana
        if week_filter == "Tutte":
            week_filter = None
        
        # Filtra gli allenamenti
        filtered = []
        for name, steps in self.workouts:
            # Filtra per sport
            if sport_filter:
                sport_match = False
                for step in steps:
                    if isinstance(step, dict) and 'sport_type' in step and step['sport_type'] == sport_filter:
                        sport_match = True
                        break
                if not sport_match:
                    continue
            
            # Filtra per settimana
            if week_filter:
                week, _, _ = parse_workout_name(name)
                if week is None or str(week).zfill(2) != week_filter:
                    continue
            
            # Filtra per testo di ricerca
            if search_text and search_text not in name.lower():
                continue
            
            # Aggiungi all'elenco filtrato
            filtered.append((name, steps))
        
        return filtered
    
    def apply_filters(self, event=None):
        """Applica i filtri alla lista degli allenamenti"""
        self.refresh_workout_list()
    
    def open_config_dialog(self):
        """Apre il dialog per la gestione delle configurazioni"""
        dialog = WorkoutConfigDialog(self, self.workout_config)
        
        # Se l'utente ha confermato
        if dialog.result:
            # Aggiorna la configurazione
            self.workout_config = dialog.result
            
            # Aggiorna la configurazione nel controller
            self.controller.config['workout_config'] = self.workout_config
            
            # Aggiorna l'interfaccia se necessario
            self.refresh_workout_list()
    

    def sync_with_garmin(self):
        """Sincronizza gli allenamenti con Garmin Connect"""
        if not self.garmin_client:
            show_error("Errore", "Devi essere connesso a Garmin Connect", parent=self)
            return
        
        # Crea un dialog personalizzato
        sync_dialog = tk.Toplevel(self)
        sync_dialog.title("Sincronizza con Garmin Connect")
        sync_dialog.geometry("400x350")  # Aumentato l'altezza per la nuova opzione
        sync_dialog.transient(self)
        sync_dialog.grab_set()
        
        # Configurazione del dialog
        ttk.Label(sync_dialog, text="Scegli cosa sincronizzare:", 
                 style="Heading.TLabel").pack(pady=(10, 20))
        
        # Opzioni
        sync_var = tk.IntVar(value=1)
        ttk.Radiobutton(sync_dialog, text="Carica tutti gli allenamenti su Garmin Connect", 
                       variable=sync_var, value=1).pack(anchor=tk.W, padx=20, pady=5)
        
        ttk.Radiobutton(sync_dialog, text="Carica solo gli allenamenti selezionati", 
                       variable=sync_var, value=2).pack(anchor=tk.W, padx=20, pady=5)
        
        ttk.Radiobutton(sync_dialog, text="Scarica allenamenti da Garmin Connect", 
                       variable=sync_var, value=3).pack(anchor=tk.W, padx=20, pady=5)
        
        # NUOVO: Opzione per rimuovere date pianificate
        ttk.Radiobutton(sync_dialog, text="Rimuovi date dagli allenamenti selezionati", 
                       variable=sync_var, value=4).pack(anchor=tk.W, padx=20, pady=5)
        
        # Separatore per chiarezza visiva
        ttk.Separator(sync_dialog, orient='horizontal').pack(fill='x', padx=20, pady=10)
        
        # Flag per sovrascrittura
        replace_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sync_dialog, text="Sovrascrivi allenamenti esistenti con lo stesso nome", 
                       variable=replace_var).pack(anchor=tk.W, padx=20, pady=5)
        
        # Flag per pianificazione
        schedule_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sync_dialog, text="Pianifica gli allenamenti nelle date specificate", 
                       variable=schedule_var).pack(anchor=tk.W, padx=20, pady=5)
        
        # Pulsanti
        button_frame = ttk.Frame(sync_dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Variabile per il risultato
        result = {"action": None, "replace": False, "schedule": False}
        
        def on_ok():
            result["action"] = sync_var.get()
            result["replace"] = replace_var.get()
            result["schedule"] = schedule_var.get()
            sync_dialog.destroy()
        
        def on_cancel():
            result["action"] = None
            sync_dialog.destroy()
        
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annulla", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Attendi la chiusura del dialog
        self.wait_window(sync_dialog)
        
        # Se l'utente ha annullato
        if result["action"] is None:
            return
        
        # Esegui l'azione richiesta
        if result["action"] == 1:
            # Carica tutti gli allenamenti
            self.upload_all_workouts(result["replace"])
        elif result["action"] == 2:
            # Carica solo gli allenamenti selezionati
            self.upload_selected_workout(result["replace"])
        elif result["action"] == 3:
            # Scarica allenamenti
            self.download_workouts()
        elif result["action"] == 4:
            # NUOVO: Rimuovi date dagli allenamenti selezionati
            self.clear_workout_dates()

        
    def upload_all_workouts(self, replace=False):
        """Carica tutti gli allenamenti su Garmin Connect"""
        if not self.workouts:
            show_info("Informazione", "Nessun allenamento da caricare", parent=self)
            return
        
        # Conferma
        if not ask_yes_no("Conferma", 
                        f"Stai per caricare {len(self.workouts)} allenamenti su Garmin Connect. Continuare?", 
                        parent=self):
            return
        
        # Ottieni la lista degli allenamenti esistenti su Garmin Connect
        try:
            existing_workouts = self.garmin_client.list_workouts()
        except Exception as e:
            show_error("Errore", f"Impossibile ottenere la lista degli allenamenti: {str(e)}", parent=self)
            return
        
        # Crea un dizionario nome -> id per gli allenamenti esistenti
        existing_map = {}
        for workout in existing_workouts:
            existing_map[workout["workoutName"]] = workout["workoutId"]
        
        # Converti e carica gli allenamenti
        from planner.workout import Workout
        
        # Conta i successi/errori
        success_count = 0
        error_count = 0
        scheduled_count = 0
        
        # Crea una finestra di progresso
        progress_window = tk.Toplevel(self)
        progress_window.title("Caricamento in corso")
        progress_window.geometry("400x170")
        progress_window.transient(self)
        progress_window.grab_set()
        
        # Label per lo stato
        status_var = tk.StringVar(value="Caricamento in corso...")
        status_label = ttk.Label(progress_window, textvariable=status_var)
        status_label.pack(pady=(20, 10))
        
        # Barra di progresso
        progress = ttk.Progressbar(progress_window, mode='determinate', length=350, maximum=len(self.workouts))
        progress.pack(pady=10)
        
        # Label per il messaggio di pianificazione
        schedule_status_var = tk.StringVar(value="")
        schedule_label = ttk.Label(progress_window, textvariable=schedule_status_var)
        schedule_label.pack(pady=5)
        
        # Aggiorna la finestra
        progress_window.update()
        
        for i, (name, steps) in enumerate(self.workouts):
            try:
                # Aggiorna lo stato
                status_var.set(f"Caricamento {i+1}/{len(self.workouts)}: {name}")
                progress['value'] = i
                progress_window.update()
                
                # Estrai il tipo di sport dagli step
                sport_type = "running"  # Default
                workout_date = None
                
                # Estrai metadati e passi effettivi
                actual_steps = []
                
                for step in steps:
                    if isinstance(step, dict):
                        if 'sport_type' in step:
                            sport_type = step['sport_type']
                        elif 'date' in step:
                            workout_date = step['date']
                        else:
                            actual_steps.append(step)
                
                # Verifica se il tipo di sport è supportato
                from planner.workout import SPORT_TYPES
                if sport_type not in SPORT_TYPES:
                    logging.error(f"Tipo di sport '{sport_type}' non supportato")
                    error_count += 1
                    continue
                
                # Crea il workout
                workout = Workout(sport_type, name)
                
                # Converti i passi
                self.convert_steps_to_workout(workout, actual_steps)
                
                # ID dell'allenamento su Garmin (sarà impostato dopo il caricamento)
                workout_id = None
                
                # Carica o aggiorna l'allenamento
                if name in existing_map and replace:
                    # Aggiorna l'allenamento esistente
                    workout_id = existing_map[name]
                    self.garmin_client.update_workout(workout_id, workout)
                else:
                    # Crea un nuovo allenamento
                    response = self.garmin_client.add_workout(workout)
                    # Estrai l'ID dal nuovo allenamento creato
                    if response and "workoutId" in response:
                        workout_id = response["workoutId"]
                
                # Pianifica l'allenamento se è stata specificata una data
                if workout_date and workout_id:
                    try:
                        schedule_status_var.set(f"Pianificazione di '{name}' per il {workout_date}...")
                        progress_window.update()
                        
                        # Pianifica l'allenamento
                        self.garmin_client.schedule_workout(workout_id, workout_date)
                        scheduled_count += 1
                        
                        schedule_status_var.set(f"Pianificato '{name}' per il {workout_date}")
                        progress_window.update()
                    except Exception as sch_err:
                        logging.error(f"Errore nella pianificazione dell'allenamento '{name}': {str(sch_err)}")
                        schedule_status_var.set(f"Errore nella pianificazione di '{name}'")
                        progress_window.update()
                
                success_count += 1
                
            except Exception as e:
                logging.error(f"Errore nel caricamento dell'allenamento '{name}': {str(e)}")
                error_count += 1
        
        # Chiudi la finestra di progresso
        progress_window.destroy()
        
        # Mostra il risultato
        result_msg = f"Caricati {success_count} allenamenti su Garmin Connect."
        if scheduled_count > 0:
            result_msg += f"\nPianificati {scheduled_count} allenamenti nelle date specificate."
        
        if error_count == 0:
            show_info("Completato", result_msg, parent=self)
        else:
            show_warning("Completato con errori", 
                       f"{result_msg}\nSi sono verificati {error_count} errori. Controlla il log per i dettagli.", 
                       parent=self)
    
    def upload_selected_workout(self, replace=False):
        """Carica l'allenamento selezionato su Garmin Connect"""
        selection = self.workout_tree.selection()
        if not selection:
            show_warning("Nessuna selezione", "Seleziona uno o più allenamenti da caricare", parent=self)
            return
        
        # Creare una lista di indici
        indices = [self.workout_tree.index(item) for item in selection]
        
        # Conferma di caricamento
        msg = f"Stai per caricare {len(indices)} allenamento/i su Garmin Connect."
        if len(indices) > 3:
            # Mostra solo i primi 3 nomi, poi "e altri..."
            names = [self.workouts[idx][0] for idx in indices[:3]]
            msg += f"\n- {names[0]}"
            for name in names[1:]:
                msg += f"\n- {name}"
            msg += f"\n- e altri {len(indices) - 3} allenamenti..."
        else:
            # Mostra tutti i nomi
            names = [self.workouts[idx][0] for idx in indices]
            for name in names:
                msg += f"\n- {name}"
        
        msg += "\n\nContinuare?"
        
        if not ask_yes_no("Conferma", msg, parent=self):
            return
        
        # Ottieni la lista degli allenamenti esistenti su Garmin Connect
        try:
            existing_workouts = self.garmin_client.list_workouts()
        except Exception as e:
            show_error("Errore", f"Impossibile ottenere la lista degli allenamenti: {str(e)}", parent=self)
            return
        
        # Crea un dizionario nome -> id per gli allenamenti esistenti
        existing_map = {}
        for workout in existing_workouts:
            existing_map[workout["workoutName"]] = workout["workoutId"]
        
        # Crea una finestra di progresso
        progress_window = tk.Toplevel(self)
        progress_window.title("Caricamento in corso")
        progress_window.geometry("400x170")
        progress_window.transient(self)
        progress_window.grab_set()
        
        # Label per lo stato
        status_var = tk.StringVar(value="Caricamento in corso...")
        status_label = ttk.Label(progress_window, textvariable=status_var)
        status_label.pack(pady=(20, 10))
        
        # Barra di progresso
        progress = ttk.Progressbar(progress_window, mode='determinate', length=350, maximum=len(indices))
        progress.pack(pady=10)
        
        # Label per il messaggio di pianificazione
        schedule_status_var = tk.StringVar(value="")
        schedule_label = ttk.Label(progress_window, textvariable=schedule_status_var)
        schedule_label.pack(pady=5)
        
        # Aggiorna la finestra
        progress_window.update()
        
        # Conta successi/errori
        success_count = 0
        error_count = 0
        scheduled_count = 0
        
        # Per ogni allenamento selezionato
        for idx, index in enumerate(indices):
            name, steps = self.workouts[index]
            
            # Aggiorna lo stato
            status_var.set(f"Caricamento {idx+1}/{len(indices)}: {name}")
            progress['value'] = idx
            progress_window.update()
            
            try:
                # Estrai il tipo di sport dagli step
                sport_type = "running"  # Default
                workout_date = None
                
                # Estrai metadati e passi effettivi
                actual_steps = []
                
                for step in steps:
                    if isinstance(step, dict):
                        if 'sport_type' in step:
                            sport_type = step['sport_type']
                        elif 'date' in step:
                            workout_date = step['date']
                        else:
                            actual_steps.append(step)
                
                # Verifica se il tipo di sport è supportato
                from planner.workout import SPORT_TYPES
                if sport_type not in SPORT_TYPES:
                    logging.error(f"Tipo di sport '{sport_type}' non supportato")
                    error_count += 1
                    continue
                
                # Crea il workout
                from planner.workout import Workout
                workout = Workout(sport_type, name)
                
                # Converti i passi
                self.convert_steps_to_workout(workout, actual_steps)
                
                # ID dell'allenamento su Garmin (sarà impostato dopo il caricamento)
                workout_id = None
                
                # Carica o aggiorna l'allenamento
                if name in existing_map and replace:
                    # Aggiorna l'allenamento esistente
                    workout_id = existing_map[name]
                    self.garmin_client.update_workout(workout_id, workout)
                else:
                    # Crea un nuovo allenamento
                    response = self.garmin_client.add_workout(workout)
                    # Estrai l'ID dal nuovo allenamento creato
                    if response and "workoutId" in response:
                        workout_id = response["workoutId"]
                
                # Pianifica l'allenamento se è stata specificata una data
                if workout_date and workout_id:
                    try:
                        schedule_status_var.set(f"Pianificazione di '{name}' per il {workout_date}...")
                        progress_window.update()
                        
                        # Pianifica l'allenamento
                        self.garmin_client.schedule_workout(workout_id, workout_date)
                        scheduled_count += 1
                        
                        schedule_status_var.set(f"Pianificato '{name}' per il {workout_date}")
                        progress_window.update()
                    except Exception as sch_err:
                        logging.error(f"Errore nella pianificazione dell'allenamento '{name}': {str(sch_err)}")
                        schedule_status_var.set(f"Errore nella pianificazione di '{name}'")
                        progress_window.update()
                
                success_count += 1
                
            except Exception as e:
                logging.error(f"Errore nel caricamento dell'allenamento '{name}': {str(e)}")
                error_count += 1
        
        # Chiudi la finestra di progresso
        progress_window.destroy()
        
        # Mostra il risultato
        result_msg = f"Caricati {success_count} allenamenti su Garmin Connect."
        if scheduled_count > 0:
            result_msg += f"\nPianificati {scheduled_count} allenamenti nelle date specificate."
        
        if error_count == 0:
            show_info("Completato", result_msg, parent=self)
        else:
            show_warning("Completato con errori", 
                       f"{result_msg}\nSi sono verificati {error_count} errori. Controlla il log per i dettagli.", 
                       parent=self)

    
    def convert_steps_to_workout(self, workout, steps):
        """Converte la lista di passi in un oggetto Workout"""
        # Implementazione corretta e completa
        from planner.workout import WorkoutStep, Target
        
        for step in steps:
            if isinstance(step, dict):
                if 'repeat' in step and 'steps' in step:
                    # Passo di tipo repeat
                    iterations = step['repeat']
                    substeps = step['steps']
                    
                    # Crea lo step di repeat
                    repeat_step = WorkoutStep(
                        0,  # order (sarà assegnato automaticamente)
                        'repeat',
                        end_condition='iterations',
                        end_condition_value=iterations
                    )
                    
                    # Aggiungi i substep
                    for substep in substeps:
                        if isinstance(substep, dict) and len(substep) == 1:
                            substep_type = list(substep.keys())[0]
                            substep_detail = substep[substep_type]
                            
                            # Estrai il target se presente
                            target = self.extract_target(substep_detail)
                            
                            # Estrai la condizione di fine
                            end_condition, end_value = self.extract_end_condition(substep_detail)
                            
                            # Estrai la descrizione
                            description = self.extract_description(substep_detail)
                            
                            # Crea il substep
                            sub_step = WorkoutStep(
                                0,  # order (sarà assegnato automaticamente)
                                substep_type,
                                description,
                                end_condition=end_condition,
                                end_condition_value=end_value,
                                target=target
                            )
                            
                            # Aggiungi al passo di repeat
                            repeat_step.add_step(sub_step)
                    
                    # Aggiungi al workout
                    workout.add_step(repeat_step)
                
                elif len(step) == 1:
                    # Passo normale
                    step_type = list(step.keys())[0]
                    step_detail = step[step_type]
                    
                    # Estrai il target se presente
                    target = self.extract_target(step_detail)
                    
                    # Estrai la condizione di fine
                    end_condition, end_value = self.extract_end_condition(step_detail)
                    
                    # Estrai la descrizione
                    description = self.extract_description(step_detail)
                    
                    # Crea lo step
                    workout_step = WorkoutStep(
                        0,  # order (sarà assegnato automaticamente)
                        step_type,
                        description,
                        end_condition=end_condition,
                        end_condition_value=end_value,
                        target=target
                    )
                    
                    # Aggiungi al workout
                    workout.add_step(workout_step)
        
        return workout
    
    def extract_target(self, step_detail):
        """Estrae il target dal dettaglio di uno step"""
        from planner.workout import Target
        
        # Se non c'è un dettaglio o è vuoto, nessun target
        if not step_detail:
            return None
        
        try:
            # Pattern per '@' o '@spd' o '@hr' o '@pwr'
            if ' @ ' in step_detail:
                # Estrai la zona dopo '@'
                parts = step_detail.split(' @ ', 1)
                if len(parts) < 2:
                    return None
                    
                zone_part = parts[1]
                zone = zone_part.split(' -- ')[0].strip() if ' -- ' in zone_part else zone_part.strip()
                
                # Importa pace_to_ms in modo sicuro
                try:
                    from planner.utils import pace_to_ms
                except ImportError:
                    logging.error("Impossibile importare pace_to_ms da planner.utils")
                    return Target('pace.zone', 2.5, 3.0)  # Valori di default
                
                # Verifica se è una zona definita o un valore diretto
                paces_dict = self.workout_config.get('paces', {})
                if zone in paces_dict:
                    pace_value = paces_dict[zone]
                    
                    # Gestisci diversi formati di ritmo
                    if '-' in pace_value:
                        # Formato intervallo (es. "4:30-5:00")
                        pace_parts = pace_value.split('-')
                        if len(pace_parts) == 2:
                            try:
                                slow_pace = pace_to_ms(pace_parts[0])
                                fast_pace = pace_to_ms(pace_parts[1])
                                return Target('pace.zone', fast_pace, slow_pace)
                            except Exception as e:
                                logging.warning(f"Errore nella conversione del ritmo '{pace_value}': {str(e)}")
                        
                    # Formato singolo valore
                    try:
                        pace_ms = pace_to_ms(pace_value)
                        # Aggiungi margini del 10%
                        return Target('pace.zone', pace_ms * 0.9, pace_ms * 1.1)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione del ritmo '{pace_value}': {str(e)}")
                        
                # Prova come valore diretto
                elif re.match(r'^\d{1,2}:\d{2}$', zone):
                    try:
                        pace_ms = pace_to_ms(zone)
                        return Target('pace.zone', pace_ms * 0.9, pace_ms * 1.1)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione del ritmo diretto '{zone}': {str(e)}")
                
                # Zona numerica (es. Z1, Z2, etc)
                elif re.match(r'^Z\d+$', zone):
                    try:
                        zone_num = int(zone[1:])
                        # Valori tipici per le zone
                        pace_ranges = {
                            1: (3.0, 3.5),  # Zona 1: ritmo lento
                            2: (3.2, 3.7),  # Zona 2: ritmo medio
                            3: (3.5, 4.0),  # Zona 3: ritmo moderato
                            4: (3.8, 4.3),  # Zona 4: ritmo veloce
                            5: (4.2, 4.7)   # Zona 5: ritmo molto veloce
                        }
                        
                        zone_range = pace_ranges.get(zone_num, (2.5, 3.0))
                        return Target('pace.zone', zone_range[0], zone_range[1])
                    except Exception as e:
                        logging.warning(f"Errore nella conversione della zona '{zone}': {str(e)}")
                
                # Valore di default se nessuna conversione è riuscita
                return Target('pace.zone', 2.5, 3.0)
            
            # Velocità (ciclismo vecchio stile)
            elif ' @spd ' in step_detail:
                # Estrai la zona dopo '@spd'
                parts = step_detail.split(' @spd ', 1)
                if len(parts) < 2:
                    return None
                    
                zone_part = parts[1]
                zone = zone_part.split(' -- ')[0].strip() if ' -- ' in zone_part else zone_part.strip()
                
                # Verifica se è una zona definita
                speeds_dict = self.workout_config.get('speeds', {})
                if zone in speeds_dict:
                    speed_value = speeds_dict[zone]
                    
                    # Gestisci diversi formati di velocità
                    if '-' in str(speed_value):
                        # Formato intervallo (es. "23.0-27.0")
                        speed_parts = str(speed_value).split('-')
                        if len(speed_parts) == 2:
                            try:
                                low_speed = float(speed_parts[0]) / 3.6  # km/h to m/s
                                high_speed = float(speed_parts[1]) / 3.6  # km/h to m/s
                                return Target('speed.zone', low_speed, high_speed)
                            except Exception as e:
                                logging.warning(f"Errore nella conversione della velocità '{speed_value}': {str(e)}")
                    
                    # Formato singolo valore
                    try:
                        speed_ms = float(speed_value) / 3.6  # km/h to m/s
                        # Aggiungi margini del 10%
                        return Target('speed.zone', speed_ms * 0.9, speed_ms * 1.1)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione della velocità '{speed_value}': {str(e)}")
                
                # Prova come valore diretto
                elif re.match(r'^\d+(\.\d+)?$', zone):
                    try:
                        speed_ms = float(zone) / 3.6  # km/h to m/s
                        return Target('speed.zone', speed_ms * 0.9, speed_ms * 1.1)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione della velocità diretta '{zone}': {str(e)}")
                
                # Zona numerica (es. Z1, Z2, etc)
                elif re.match(r'^Z\d+$', zone):
                    try:
                        zone_num = int(zone[1:])
                        # Valori tipici per le zone
                        speed_ranges = {
                            1: (3.0, 4.0),  # Zona 1: velocità bassa
                            2: (4.0, 5.0),  # Zona 2: velocità media-bassa
                            3: (5.0, 6.0),  # Zona 3: velocità media
                            4: (6.0, 7.0),  # Zona 4: velocità alta
                            5: (7.0, 8.0)   # Zona 5: velocità molto alta
                        }
                        
                        zone_range = speed_ranges.get(zone_num, (5.0, 6.0))
                        return Target('speed.zone', zone_range[0], zone_range[1])
                    except Exception as e:
                        logging.warning(f"Errore nella conversione della zona '{zone}': {str(e)}")
                
                # Valore di default per velocità
                return Target('speed.zone', 5.0, 6.0)
            
            # Potenza (ciclismo nuovo stile)
            elif ' @pwr ' in step_detail:
                # Estrai la zona dopo '@pwr'
                parts = step_detail.split(' @pwr ', 1)
                if len(parts) < 2:
                    return None
                    
                zone_part = parts[1]
                zone = zone_part.split(' -- ')[0].strip() if ' -- ' in zone_part else zone_part.strip()
                
                # Verifica se è una zona definita
                power_values = self.workout_config.get('power_values', {})
                if zone in power_values and zone != 'ftp':
                    power_value = power_values[zone]
                    
                    # Gestisci diversi formati di potenza
                    if '-' in str(power_value):
                        # Formato intervallo (es. "230-270")
                        power_parts = str(power_value).split('-')
                        if len(power_parts) == 2:
                            try:
                                low_power = float(power_parts[0])
                                high_power = float(power_parts[1])
                                return Target('power.zone', low_power, high_power)
                            except Exception as e:
                                logging.warning(f"Errore nella conversione della potenza '{power_value}': {str(e)}")
                    
                    # Formato singolo valore
                    try:
                        power = float(power_value)
                        # Aggiungi margini del 5%
                        return Target('power.zone', power * 0.95, power * 1.05)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione della potenza '{power_value}': {str(e)}")
                
                # Controlla se è una percentuale dell'FTP
                if '%' in zone:
                    # Formato percentuale singola (es. "75%")
                    match = re.match(r'^(\d+)%$', zone)
                    if match:
                        try:
                            percent = int(match.group(1))
                            
                            # Ottieni l'FTP dalla configurazione
                            ftp = self.workout_config.get('power_values', {}).get('ftp', 250)
                            
                            # Calcola il valore di potenza
                            power = int((percent / 100) * ftp)
                            
                            # Aggiungi margini del 5%
                            low_power = int(power * 0.95)
                            high_power = int(power * 1.05)
                            
                            logging.info(f"Convertito {zone} in {low_power}-{high_power} W (FTP: {ftp})")
                            return Target('power.zone', low_power, high_power)
                        except Exception as e:
                            logging.warning(f"Errore nella conversione della percentuale FTP '{zone}': {str(e)}")
                    
                    # Formato intervallo percentuale (es. "75-85%")
                    match = re.match(r'^(\d+)-(\d+)%$', zone)
                    if match:
                        try:
                            low_percent = int(match.group(1))
                            high_percent = int(match.group(2))
                            
                            # Ottieni l'FTP dalla configurazione
                            ftp = self.workout_config.get('power_values', {}).get('ftp', 250)
                            
                            # Calcola i valori di potenza
                            low_power = int((low_percent / 100) * ftp)
                            high_power = int((high_percent / 100) * ftp)
                            
                            logging.info(f"Convertito {zone} in {low_power}-{high_power} W (FTP: {ftp})")
                            return Target('power.zone', low_power, high_power)
                        except Exception as e:
                            logging.warning(f"Errore nella conversione dell'intervallo percentuale FTP '{zone}': {str(e)}")
                
                # Prova come valore diretto
                if re.match(r'^\d+$', zone):
                    try:
                        power = float(zone)
                        return Target('power.zone', power * 0.95, power * 1.05)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione della potenza diretta '{zone}': {str(e)}")
                
                # Prova come intervallo diretto
                if re.match(r'^\d+-\d+$', zone):
                    try:
                        power_parts = zone.split('-')
                        low_power = float(power_parts[0])
                        high_power = float(power_parts[1])
                        return Target('power.zone', low_power, high_power)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione dell'intervallo di potenza '{zone}': {str(e)}")
                
                # Valore di default per potenza
                return Target('power.zone', 200, 250)
            
            # Frequenza cardiaca
            elif ' @hr ' in step_detail:
                # Estrai la zona dopo '@hr'
                parts = step_detail.split(' @hr ', 1)
                if len(parts) < 2:
                    return None
                    
                zone_part = parts[1]
                zone = zone_part.split(' -- ')[0].strip() if ' -- ' in zone_part else zone_part.strip()
                
                # Verifica se è una zona definita
                heart_rates = self.workout_config.get('heart_rates', {})
                if zone in heart_rates:
                    hr_value = heart_rates[zone]
                    
                    # Gestisci diversi formati di FC
                    if isinstance(hr_value, str) and '-' in hr_value:
                        # Formato intervallo (es. "140-160")
                        hr_parts = hr_value.split('-')
                        if len(hr_parts) == 2:
                            try:
                                # Verifica se contiene percentuali o max_hr
                                if "%" in hr_parts[1]:
                                    # Esempio: 62-76% max_hr
                                    max_hr = heart_rates.get('max_hr', 180)
                                    
                                    # Estrai i valori percentuali
                                    match1 = re.search(r'(\d+)', hr_parts[0])
                                    match2 = re.search(r'(\d+)', hr_parts[1])
                                    
                                    if match1 and match2:
                                        low_percent = int(match1.group(1))
                                        high_percent = int(match2.group(1))
                                        
                                        # Calcola i valori BPM
                                        low_hr = int((low_percent / 100) * max_hr)
                                        high_hr = int((high_percent / 100) * max_hr)
                                        
                                        return Target('heart.rate.zone', low_hr, high_hr)
                                else:
                                    # Intervallo semplice (es. "140-160")
                                    low_hr = int(hr_parts[0])
                                    high_hr = int(hr_parts[1])
                                    return Target('heart.rate.zone', low_hr, high_hr)
                            except Exception as e:
                                logging.warning(f"Errore nella conversione della FC '{hr_value}': {str(e)}")
                        
                    # Formato singolo valore
                    try:
                        hr = int(hr_value)
                        # Aggiungi margini di ±5 bpm
                        return Target('heart.rate.zone', hr - 5, hr + 5)
                    except Exception as e:
                        # Verifica se è un valore percentuale
                        if isinstance(hr_value, str) and "%" in hr_value:
                            try:
                                max_hr = heart_rates.get('max_hr', 180)
                                match = re.search(r'(\d+)', hr_value)
                                if match:
                                    percent = int(match.group(1))
                                    hr = int((percent / 100) * max_hr)
                                    return Target('heart.rate.zone', hr - 5, hr + 5)
                            except Exception as e2:
                                logging.warning(f"Errore nella conversione della FC percentuale '{hr_value}': {str(e2)}")
                        else:
                            logging.warning(f"Errore nella conversione della FC '{hr_value}': {str(e)}")
                
                # Prova come zona numerica
                elif re.match(r'^Z\d+_HR$', zone):
                    try:
                        zone_num = int(zone[1:-3])
                        return Target('heart.rate.zone', zone=zone_num)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione della zona HR '{zone}': {str(e)}")
                
                # Verifica se è un intervallo di percentuali (es. "70-80%")
                if '%' in zone:
                    match = re.match(r'^(\d+)-(\d+)%$', zone)
                    if match:
                        try:
                            low_percent = int(match.group(1))
                            high_percent = int(match.group(2))
                            
                            # Ottieni il valore max_hr dalla configurazione
                            max_hr = self.workout_config.get('heart_rates', {}).get('max_hr', 180)
                            
                            # Calcola i valori di BPM
                            low_hr = int((low_percent / 100) * max_hr)
                            high_hr = int((high_percent / 100) * max_hr)
                            
                            logging.info(f"Convertito {zone} in {low_hr}-{high_hr} BPM (max_hr: {max_hr})")
                            return Target('heart.rate.zone', low_hr, high_hr)
                        except Exception as e:
                            logging.warning(f"Errore nella conversione dell'intervallo percentuale '{zone}': {str(e)}")
                    
                    # Singola percentuale (es. "70%")
                    match = re.match(r'^(\d+)%$', zone)
                    if match:
                        try:
                            percent = int(match.group(1))
                            
                            # Ottieni il valore max_hr dalla configurazione
                            max_hr = self.workout_config.get('heart_rates', {}).get('max_hr', 180)
                            
                            # Calcola il valore di BPM con margine di ±3%
                            hr = int((percent / 100) * max_hr)
                            low_hr = int(((percent - 3) / 100) * max_hr)
                            high_hr = int(((percent + 3) / 100) * max_hr)
                            
                            logging.info(f"Convertito {zone} in {low_hr}-{high_hr} BPM (max_hr: {max_hr})")
                            return Target('heart.rate.zone', low_hr, high_hr)
                        except Exception as e:
                            logging.warning(f"Errore nella conversione della percentuale singola '{zone}': {str(e)}")
                
                # Prova come valore diretto o intervallo
                if '-' in zone:
                    try:
                        hr_parts = zone.split('-')
                        low_hr = int(hr_parts[0])
                        high_hr = int(hr_parts[1])
                        return Target('heart.rate.zone', low_hr, high_hr)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione dell'intervallo HR '{zone}': {str(e)}")
                elif zone.isdigit():
                    try:
                        hr = int(zone)
                        return Target('heart.rate.zone', hr - 5, hr + 5)
                    except Exception as e:
                        logging.warning(f"Errore nella conversione della FC diretta '{zone}': {str(e)}")
                
                # Valore di default per FC
                return Target('heart.rate.zone', 130, 150)
            
            # Nessun target riconosciuto
            return None
        
        except Exception as e:
            logging.error(f"Errore imprevisto nell'estrazione del target: {str(e)}")
            return None
    
    def extract_end_condition(self, step_detail):
        """Estrae la condizione di fine dal dettaglio di uno step"""
        if not step_detail:
            return "lap.button", None
            
        try:
            # Rimuovi eventuali parti dopo " -- " (descrizione)
            if ' -- ' in step_detail:
                step_detail = step_detail.split(' -- ')[0]
            
            # Rimuovi le parti di target
            if ' @ ' in step_detail:
                step_detail = step_detail.split(' @ ')[0]
            elif ' @spd ' in step_detail:
                step_detail = step_detail.split(' @spd ')[0]
            elif ' @hr ' in step_detail:
                step_detail = step_detail.split(' @hr ')[0]
            
            # Ora abbiamo solo la parte di durata/distanza
            step_detail = step_detail.strip()
            
            # Gestisci il caso speciale "lap-button"
            if step_detail == "lap-button":
                return "lap.button", None
            
            # Estrai la condizione di fine
            if 'min' in step_detail:
                # Durata in minuti
                try:
                    # Usa una regex per estrarre il numero (supporta anche decimali)
                    match = re.search(r'(\d+(?:\.\d+)?)\s*min', step_detail)
                    if match:
                        minutes = float(match.group(1))
                        return "time", str(int(minutes * 60))  # Converti in secondi
                except Exception as e:
                    logging.warning(f"Errore nell'estrazione della durata in minuti: {str(e)}")
                    return "lap.button", None
            elif 'km' in step_detail:
                # Distanza in km
                try:
                    # Usa una regex per estrarre il numero (supporta anche decimali)
                    match = re.search(r'(\d+(?:\.\d+)?)\s*km', step_detail)
                    if match:
                        km = float(match.group(1))
                        return "distance", str(int(km * 1000))  # Converti in metri
                except Exception as e:
                    logging.warning(f"Errore nell'estrazione della distanza in km: {str(e)}")
                    return "lap.button", None
            elif 'm' in step_detail and 'min' not in step_detail:
                # Distanza in metri
                try:
                    # Usa una regex per estrarre il numero (supporta anche decimali)
                    match = re.search(r'(\d+(?:\.\d+)?)\s*m', step_detail)
                    if match:
                        meters = float(match.group(1))
                        return "distance", str(int(meters))
                except Exception as e:
                    logging.warning(f"Errore nell'estrazione della distanza in metri: {str(e)}")
                    return "lap.button", None
            elif re.match(r'^\d+:\d{2}$', step_detail):
                # Formato mm:ss
                try:
                    from planner.utils import hhmmss_to_seconds
                    seconds = hhmmss_to_seconds(step_detail)
                    return "time", str(seconds)
                except Exception as e:
                    logging.warning(f"Errore nella conversione del tempo '{step_detail}': {str(e)}")
                    return "lap.button", None
            elif step_detail.isdigit():
                # Numero di ripetizioni per gli step di tipo "repeat"
                return "iterations", int(step_detail)
                
            # Default
            return "lap.button", None
            
        except Exception as e:
            logging.error(f"Errore imprevisto nell'estrazione della condizione di fine: {str(e)}")
            return "lap.button", None
    
    def extract_description(self, step_detail):
        """Estrae la descrizione dal dettaglio di uno step"""
        if ' -- ' in step_detail:
            return step_detail.split(' -- ')[1].strip()
        return ""
    
    def download_workouts(self):
        """Scarica gli allenamenti da Garmin Connect"""
        try:
            # Ottieni la lista degli allenamenti
            remote_workouts = self.garmin_client.list_workouts()
            
            # Verifica se ci sono allenamenti
            if not remote_workouts:
                show_info("Informazione", "Nessun allenamento trovato su Garmin Connect", parent=self)
                return
            
            # Dialog per selezionare gli allenamenti da scaricare
            select_dialog = tk.Toplevel(self)
            select_dialog.title("Seleziona allenamenti da scaricare")
            select_dialog.geometry("600x400")
            select_dialog.transient(self)
            select_dialog.grab_set()
            
            # Label informativa
            ttk.Label(select_dialog, text=f"Trovati {len(remote_workouts)} allenamenti su Garmin Connect", 
                     style="Heading.TLabel").pack(pady=(10, 0))
            
            ttk.Label(select_dialog, text="Seleziona gli allenamenti da scaricare:", 
                     style="Instructions.TLabel").pack(pady=(0, 10))
            
            # Frame per la lista
            list_frame = ttk.Frame(select_dialog)
            list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            
            # Crea la lista con checkbox
            columns = ("select", "name", "sport", "created")
            tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="none")
            
            # Definisci le intestazioni
            tree.heading("select", text="")
            tree.heading("name", text="Nome")
            tree.heading("sport", text="Sport")
            tree.heading("created", text="Data creazione")
            
            # Larghezze colonne
            tree.column("select", width=30, stretch=False)
            tree.column("name", width=300)
            tree.column("sport", width=100)
            tree.column("created", width=150)
            
            # Scrollbar
            scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            
            # Pack
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Dizionario per tenere traccia delle selezioni
            selected = {}
            
            # Funzione per invertire la selezione
            def toggle_selection(event):
                item = tree.identify_row(event.y)
                if item:
                    workout_id = tree.item(item, "values")[3]  # Usa la data come ID univoco
                    selected[workout_id] = not selected.get(workout_id, False)
                    
                    # Aggiorna il segno di spunta
                    current_values = list(tree.item(item, "values"))
                    current_values[0] = "✓" if selected[workout_id] else ""
                    tree.item(item, values=current_values)
            
            # Associa l'evento di click
            tree.bind("<ButtonRelease-1>", toggle_selection)
            
            # Aggiungi gli allenamenti
            for wo in remote_workouts:
                name = wo["workoutName"]
                sport = wo.get("sportType", {}).get("sportTypeKey", "unknown")
                
                # Formatta il tipo di sport
                sport_display = sport.capitalize()
                
                # Data di creazione
                created_date = wo.get("createdDate", "")
                if created_date:
                    try:
                        # Convert timestamp to date
                        created_date = datetime.datetime.fromtimestamp(created_date / 1000.0).strftime('%Y-%m-%d')
                    except:
                        pass
                
                # ID univoco (usando la data come chiave)
                workout_id = created_date
                
                # Inizialmente non selezionato
                selected[workout_id] = False
                
                # Aggiungi alla lista
                tree.insert("", "end", values=("", name, sport_display, created_date))
            
            # Pulsanti per selezionare/deselezionare tutti
            select_buttons = ttk.Frame(select_dialog)
            select_buttons.pack(fill=tk.X, padx=10, pady=5)
            
            def select_all():
                for item in tree.get_children():
                    workout_id = tree.item(item, "values")[3]  # Usa la data come ID univoco
                    selected[workout_id] = True
                    
                    # Aggiorna il segno di spunta
                    current_values = list(tree.item(item, "values"))
                    current_values[0] = "✓"
                    tree.item(item, values=current_values)
            
            def select_none():
                for item in tree.get_children():
                    workout_id = tree.item(item, "values")[3]  # Usa la data come ID univoco
                    selected[workout_id] = False
                    
                    # Aggiorna il segno di spunta
                    current_values = list(tree.item(item, "values"))
                    current_values[0] = ""
                    tree.item(item, values=current_values)
            
            ttk.Button(select_buttons, text="Seleziona tutti", command=select_all).pack(side=tk.LEFT, padx=5)
            ttk.Button(select_buttons, text="Deseleziona tutti", command=select_none).pack(side=tk.LEFT, padx=5)
            
            # Pulsanti OK/Cancel
            button_frame = ttk.Frame(select_dialog)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # Variabile per memorizzare il risultato
            result = {"confirmed": False, "selected": {}}
            
            def on_ok():
                result["confirmed"] = True
                result["selected"] = selected.copy()
                select_dialog.destroy()
            
            def on_cancel():
                select_dialog.destroy()
            
            ttk.Button(button_frame, text="Scarica selezionati", command=on_ok).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Annulla", command=on_cancel).pack(side=tk.LEFT, padx=5)
            
            # Attendi la chiusura del dialog
            self.wait_window(select_dialog)
            
            # Se l'utente ha annullato o non ha selezionato nulla
            if not result["confirmed"]:
                return
            
            # Conta quanti allenamenti sono stati selezionati
            count_selected = sum(1 for v in result["selected"].values() if v)
            
            if count_selected == 0:
                show_info("Informazione", "Nessun allenamento selezionato", parent=self)
                return
            
            # Conferma
            if not ask_yes_no("Conferma", 
                            f"Stai per scaricare {count_selected} allenamenti da Garmin Connect. Continuare?", 
                            parent=self):
                return
            
            # Crea una finestra di progresso
            progress_window = tk.Toplevel(self)
            progress_window.title("Download in corso")
            progress_window.geometry("400x150")
            progress_window.transient(self)
            progress_window.grab_set()
            
            # Label per lo stato
            status_var = tk.StringVar(value="Download in corso...")
            status_label = ttk.Label(progress_window, textvariable=status_var)
            status_label.pack(pady=(20, 10))
            
            # Barra di progresso
            progress = ttk.Progressbar(progress_window, mode='determinate', length=300, maximum=count_selected)
            progress.pack(pady=10)
            
            # Aggiorna la finestra
            progress_window.update()
            
            # Scarica e converti gli allenamenti selezionati
            downloaded = 0
            success_count = 0
            error_count = 0
            
            for i, wo in enumerate(remote_workouts):
                workout_id = wo.get("createdDate", "")
                if isinstance(workout_id, int):
                    workout_id = str(datetime.datetime.fromtimestamp(workout_id / 1000.0).strftime('%Y-%m-%d'))
                
                # Verifica se è stato selezionato
                if not result["selected"].get(workout_id, False):
                    continue
                
                # Aggiorna lo stato
                downloaded += 1
                name = wo["workoutName"]
                status_var.set(f"Download {downloaded}/{count_selected}: {name}")
                progress['value'] = downloaded
                progress_window.update()
                
                try:
                    # Ottieni i dettagli dell'allenamento
                    workout_detail = self.garmin_client.get_workout(wo["workoutId"])
                    
                    # Converti in formato interno
                    converted_steps = self.convert_garmin_to_internal(workout_detail)
                    
                    # Aggiungi alla lista degli allenamenti
                    self.workouts.append((name, converted_steps))
                    
                    success_count += 1
                
                except Exception as e:
                    logging.error(f"Errore nel download dell'allenamento '{name}': {str(e)}")
                    error_count += 1
            
            # Chiudi la finestra di progresso
            progress_window.destroy()
            
            # Aggiorna la lista
            self.refresh_workout_list()
            
            # Mostra il risultato
            if error_count == 0:
                show_info("Completato", f"Scaricati {success_count} allenamenti da Garmin Connect.", parent=self)
            else:
                show_warning("Completato con errori", 
                           f"Scaricati {success_count} allenamenti da Garmin Connect.\n"
                           f"Si sono verificati {error_count} errori. Controlla il log per i dettagli.", 
                           parent=self)
        
        except Exception as e:
            show_error("Errore", f"Impossibile scaricare gli allenamenti: {str(e)}", parent=self)
    
    def convert_garmin_to_internal(self, workout_detail):
        """Converte un allenamento dal formato Garmin al formato interno"""
        steps = []
        
        # Aggiungi il tipo di sport
        sport_type = workout_detail.get("sportType", {}).get("sportTypeKey", "running")
        steps.append({"sport_type": sport_type})
        
        # Estrai gli step
        for segment in workout_detail.get("workoutSegments", []):
            for step in segment.get("workoutSteps", []):
                converted = self.convert_garmin_step(step)
                if converted:
                    steps.append(converted)
        
        return steps
    
    def convert_garmin_step(self, garmin_step):
        """Converte un singolo step dal formato Garmin al formato interno"""
        # Tipo di step
        step_type_key = garmin_step.get("stepType", {}).get("stepTypeKey", "other")
        
        # Se è un gruppo di ripetizioni
        if garmin_step.get("type") == "RepeatGroupDTO":
            iterations = garmin_step.get("numberOfIterations", 1)
            substeps = []
            
            # Converti i substep
            for substep in garmin_step.get("workoutSteps", []):
                converted = self.convert_garmin_step(substep)
                if converted:
                    substeps.append(converted)
            
            return {"repeat": iterations, "steps": substeps}
        
        # Step normale
        end_condition_key = garmin_step.get("endCondition", {}).get("conditionTypeKey", "lap.button")
        end_value = garmin_step.get("endConditionValue")
        description = garmin_step.get("description", "")
        
        # Formatta la condizione di fine
        formatted_end = self.format_garmin_end_condition(end_condition_key, end_value, garmin_step)
        
        # Formatta il target
        target_type_key = garmin_step.get("targetType", {}).get("workoutTargetTypeKey", "no.target")
        target_value_one = garmin_step.get("targetValueOne")
        target_value_two = garmin_step.get("targetValueTwo")
        zone_number = garmin_step.get("zoneNumber")
        
        formatted_target = self.format_garmin_target(target_type_key, target_value_one, target_value_two, zone_number)
        
        # Costruisci il dettaglio dello step
        step_detail = formatted_end
        
        if formatted_target:
            step_detail += " " + formatted_target
        
        if description:
            step_detail += f" -- {description}"
        
        return {step_type_key: step_detail}
    
    def format_garmin_end_condition(self, condition_key, value, step):
        """Formatta la condizione di fine dal formato Garmin"""
        if condition_key == "lap.button":
            return "lap-button"
        elif condition_key == "time":
            # Converti i secondi in formato mm:ss o hh:mm:ss
            if value is None:
                return "lap-button"
            
            if value < 3600:
                minutes = value // 60
                seconds = value % 60
                return f"{minutes}min"
            else:
                hours = value // 3600
                minutes = (value % 3600) // 60
                seconds = value % 60
                return f"{hours}h{minutes}min"
        
        elif condition_key == "distance":
            # Converti i metri in km o m
            if value is None:
                return "lap-button"
            
            if value >= 1000:
                km = value / 1000
                return f"{km}km"
            else:
                return f"{value}m"
        
        elif condition_key == "iterations":
            return str(value)
        
        # Default
        return "lap-button"
    
    def format_garmin_target(self, target_type, value_one, value_two, zone):
        """Formatta il target dal formato Garmin"""
        if target_type == "no.target":
            return ""
        
        elif target_type == "pace.zone":
            # Converti m/s in ritmo (min/km)
            if value_one is not None and value_two is not None:
                try:
                    from planner.utils import ms_to_pace
                    pace_one = ms_to_pace(value_one)
                    pace_two = ms_to_pace(value_two)
                    
                    # Cerca se corrisponde a una zona definita
                    for name, value in self.workout_config.get('paces', {}).items():
                        if '-' in value:
                            pace_range = value.split('-')
                            if pace_one == pace_range[0] and pace_two == pace_range[1]:
                                return f"@ {name}"
                    
                    # Se non corrisponde a una zona, usa il valore diretto
                    avg_pace = (value_one + value_two) / 2
                    return f"@ {ms_to_pace(avg_pace)}"
                except:
                    # Se fallisce la conversione, prova con una zona predefinita
                    if zone is not None:
                        return f"@ Z{zone}"
            
            # Se abbiamo solo la zona
            if zone is not None:
                return f"@ Z{zone}"
        
        elif target_type == "speed.zone":
            # Converti m/s in km/h
            if value_one is not None and value_two is not None:
                speed_one = round(value_one * 3.6, 1)
                speed_two = round(value_two * 3.6, 1)
                
                # Cerca se corrisponde a una zona definita
                for name, value in self.workout_config.get('speeds', {}).items():
                    if '-' in value:
                        speed_range = value.split('-')
                        if abs(speed_one - float(speed_range[0])) < 0.5 and abs(speed_two - float(speed_range[1])) < 0.5:
                            return f"@spd {name}"
                
                # Se non corrisponde a una zona, usa il valore diretto
                avg_speed = (value_one + value_two) / 2
                return f"@spd {round(avg_speed * 3.6, 1)}"
            
            # Se abbiamo solo la zona
            if zone is not None:
                return f"@spd Z{zone}"
        
        elif target_type == "heart.rate.zone":
            # Frequenza cardiaca
            if value_one is not None and value_two is not None:
                hr_one = int(value_one)
                hr_two = int(value_two)
                
                # Cerca se corrisponde a una zona definita
                for name, value in self.workout_config.get('heart_rates', {}).items():
                    if isinstance(value, str) and '-' in value:
                        hr_range = value.split('-')
                        if hr_one == int(hr_range[0]) and hr_two == int(hr_range[1]):
                            return f"@hr {name}"
                
                # Se non corrisponde a una zona, usa il valore diretto
                return f"@hr {hr_one}-{hr_two}"
            
            # Se abbiamo solo la zona
            if zone is not None:
                return f"@hr Z{zone}_HR"
        
        # Default (nessun target)
        return ""
    
    def on_login(self, client):
        """Gestisce l'evento di login completato"""
        self.garmin_client = client
        self.sync_button['state'] = 'normal'
        
        # Aggiorna l'interfaccia
        self.status_var.set("Connesso a Garmin Connect")
    
    def on_logout(self):
        """Gestisce l'evento di logout"""
        self.garmin_client = None
        self.sync_button['state'] = 'disabled'
        
        # Aggiorna l'interfaccia
        self.status_var.set("Non connesso a Garmin Connect")



    def create_workout_editor(self, parent):
        """Crea l'editor per l'allenamento selezionato"""
        # Frame per le proprietà dell'allenamento
        properties_frame = ttk.Frame(parent)
        properties_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Griglia per le proprietà
        ttk.Label(properties_frame, text="Nome:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(properties_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=(0, 5), pady=5)
        
        # Settimana e sessione
        ttk.Label(properties_frame, text="Settimana:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.week_var = tk.StringVar(value="01")
        week_entry = ttk.Entry(properties_frame, textvariable=self.week_var, width=5)
        week_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        
        ttk.Label(properties_frame, text="Sessione:").grid(row=1, column=2, sticky=tk.W, padx=(10, 5), pady=5)
        self.session_var = tk.StringVar(value="01")
        session_entry = ttk.Entry(properties_frame, textvariable=self.session_var, width=5)
        session_entry.grid(row=1, column=3, sticky=tk.W, padx=(0, 5), pady=5)
        
        ttk.Label(properties_frame, text="Descrizione:").grid(row=1, column=4, sticky=tk.W, padx=(10, 5), pady=5)
        self.description_var = tk.StringVar()
        description_entry = ttk.Entry(properties_frame, textvariable=self.description_var, width=20)
        description_entry.grid(row=1, column=5, sticky=tk.W+tk.E, padx=(0, 5), pady=5)
        
        # Tipo di sport
        ttk.Label(properties_frame, text="Sport:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        self.sport_var = tk.StringVar(value="running")
        sport_combo = ttk.Combobox(properties_frame, textvariable=self.sport_var, 
                                  values=["running", "cycling", "swimming"],
                                  width=15, state="readonly")
        sport_combo.grid(row=2, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        sport_combo.bind("<<ComboboxSelected>>", self.on_sport_change)
        
        # Data pianificata
        ttk.Label(properties_frame, text="Data:").grid(row=2, column=2, sticky=tk.W, padx=(10, 5), pady=5)
        self.date_var = tk.StringVar()
        date_entry = ttk.Entry(properties_frame, textvariable=self.date_var, width=12)
        date_entry.grid(row=2, column=3, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Pulsante calendario
        calendar_button = ttk.Button(properties_frame, text="📅", width=3, 
                                    command=self.show_calendar)
        calendar_button.grid(row=2, column=4, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Configurazione colonne
        properties_frame.columnconfigure(1, weight=1)
        properties_frame.columnconfigure(5, weight=2)
        
        planning_frame = ttk.LabelFrame(parent, text="Opzioni di pianificazione")
        planning_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        planning_grid = ttk.Frame(planning_frame, padding=5)
        planning_grid.pack(fill=tk.X, expand=True)
        
        # Data della gara
        ttk.Label(planning_grid, text="Data gara:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Imposta come default una data a 3 mesi da oggi
        default_race_day = (datetime.datetime.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        self.race_date_var = tk.StringVar(value=default_race_day)
        
        date_entry = ttk.Entry(planning_grid, textvariable=self.race_date_var, width=15)
        date_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Pulsante calendario
        race_calendar_button = ttk.Button(planning_grid, text="📅", width=3, 
                                        command=self.show_race_calendar)
        race_calendar_button.grid(row=0, column=2, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Giorni preferiti per l'allenamento
        ttk.Label(planning_grid, text="Giorni preferiti:").grid(row=0, column=3, sticky=tk.W, padx=(20, 5), pady=5)
        
        # Frame per i checkbox dei giorni
        days_frame = ttk.Frame(planning_grid)
        days_frame.grid(row=0, column=4, columnspan=4, sticky=tk.W, padx=(0, 5), pady=5)
        
        days_of_week = [("L", 0), ("M", 1), ("M", 2), ("G", 3), ("V", 4), ("S", 5), ("D", 6)]
        
        # Crea variabili e checkbox per ogni giorno
        self.preferred_days_vars = {}
        
        for i, (day_label, day_value) in enumerate(days_of_week):
            var = tk.BooleanVar(value=False)
            self.preferred_days_vars[day_value] = var  # 0 = Lunedì, 6 = Domenica
            
            cb = ttk.Checkbutton(days_frame, text=day_label, variable=var, width=3)
            cb.pack(side=tk.LEFT, padx=2)
        
        # Imposta valori di default comuni (mar, gio, dom)
        self.preferred_days_vars[1].set(True)  # Martedì
        self.preferred_days_vars[3].set(True)  # Giovedì
        self.preferred_days_vars[6].set(True)  # Domenica
        
        # Pulsante pianifica
        self.plan_button = ttk.Button(planning_grid, text="Pianifica", 
                                    command=self.schedule_workouts_direct)
        self.plan_button.grid(row=0, column=8, padx=(10, 0), pady=5)
        
        # Canvas per visualizzare graficamente i passi (esistente)
        canvas_frame = ttk.LabelFrame(parent, text="Anteprima allenamento")
        canvas_frame.pack(fill=tk.X, expand=False, pady=(0, 10))
        
        # Crea il canvas
        self.canvas = tk.Canvas(canvas_frame, bg=COLORS["bg_light"], highlightthickness=0, height=140)
        self.canvas.pack(fill=tk.X, expand=True, padx=5, pady=5)
        
        # Aggiungi i binding per drag and drop
        self.canvas.bind("<ButtonPress-1>", self.on_canvas_press)
        self.canvas.bind("<B1-Motion>", self.on_canvas_motion)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        
        # Inizializza i dati di trascinamento del canvas con una struttura completa
        self.canvas_drag_data = {
            "item": None,
            "index": -1,
            "start_x": 0,
            "start_y": 0,
            "current_x": 0,
            "current_y": 0,
            "type": "",
            "color": ""
        }
        
        # Frame per gli step dell'allenamento
        steps_frame = ttk.LabelFrame(parent, text="Passi dell'allenamento")
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Toolbar per gli step
        steps_toolbar = ttk.Frame(steps_frame)
        steps_toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Pulsanti per gestire gli step
        self.add_step_button = ttk.Button(steps_toolbar, text="Aggiungi passo", 
                                        command=self.add_step)
        self.add_step_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.add_repeat_button = ttk.Button(steps_toolbar, text="Aggiungi ripetizione", 
                                          command=self.add_repeat)
        self.add_repeat_button.pack(side=tk.LEFT, padx=5)
        
        self.edit_step_button = ttk.Button(steps_toolbar, text="Modifica", 
                                         command=self.edit_step)
        self.edit_step_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_step_button = ttk.Button(steps_toolbar, text="Elimina", 
                                           command=self.delete_step)
        self.delete_step_button.pack(side=tk.LEFT, padx=5)
        
        self.move_up_button = ttk.Button(steps_toolbar, text="↑", width=3, 
                                       command=self.move_step_up)
        self.move_up_button.pack(side=tk.LEFT, padx=5)
        
        self.move_down_button = ttk.Button(steps_toolbar, text="↓", width=3, 
                                         command=self.move_step_down)
        self.move_down_button.pack(side=tk.LEFT, padx=5)
        
        # Lista degli step
        steps_list_frame = ttk.Frame(steps_frame)
        steps_list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea la treeview per gli step
        columns = ("index", "type", "details")
        self.steps_tree = ttk.Treeview(steps_list_frame, columns=columns, show="headings", 
                                     selectmode="browse")
        
        # Definisci le intestazioni
        self.steps_tree.heading("index", text="#")
        self.steps_tree.heading("type", text="Tipo")
        self.steps_tree.heading("details", text="Dettagli")
        
        # Definisci le larghezze delle colonne
        self.steps_tree.column("index", width=30)
        self.steps_tree.column("type", width=100)
        self.steps_tree.column("details", width=400)
        
        # Aggiungi scrollbar
        scrollbar = ttk.Scrollbar(steps_list_frame, orient=tk.VERTICAL, 
                                command=self.steps_tree.yview)
        self.steps_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        self.steps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Aggiungi binding per drag and drop sulla TreeView
        self.steps_tree.bind("<ButtonPress-1>", self.on_tree_press)
        self.steps_tree.bind("<B1-Motion>", self.on_tree_motion)
        self.steps_tree.bind("<ButtonRelease-1>", self.on_tree_release)
        
        # Inizializza i dati per il drag and drop nella TreeView
        self.tree_drag_data = {"item": None, "index": -1}
        
        # Associa eventi
        self.steps_tree.bind("<Double-1>", self.on_step_double_click)
        self.steps_tree.bind("<<TreeviewSelect>>", self.on_step_select)
        
        # Frame per le azioni
        action_frame = ttk.Frame(parent)
        action_frame.pack(fill=tk.X, pady=(5, 0))
        
        # Pulsanti per salvare/annullare
        self.save_button = ttk.Button(action_frame, text="Salva allenamento", 
                                    style="Success.TButton", 
                                    command=self.save_workout)
        self.save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.cancel_button = ttk.Button(action_frame, text="Annulla modifiche", 
                                      command=self.cancel_edit)
        self.cancel_button.pack(side=tk.LEFT, padx=5)
        
        # Stato iniziale: disabilitato
        self.disable_editor()


    def show_race_calendar(self):
        """Mostra un selettore di data per la data della gara"""
        try:
            from tkcalendar import Calendar
            
            # Crea una finestra top-level
            top = tk.Toplevel(self)
            top.title("Seleziona data della gara")
            top.geometry("350x300")
            top.transient(self)
            top.grab_set()
            
            # Data iniziale
            if self.race_date_var.get():
                try:
                    initial_date = datetime.datetime.strptime(self.race_date_var.get(), "%Y-%m-%d").date()
                except ValueError:
                    initial_date = datetime.date.today()
            else:
                initial_date = datetime.date.today()
            
            # Crea il calendario
            cal = Calendar(top, selectmode='day', year=initial_date.year, 
                          month=initial_date.month, day=initial_date.day,
                          date_pattern="yyyy-mm-dd")
            cal.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Funzione per selezionare la data
            def select_date():
                self.race_date_var.set(cal.get_date())
                top.destroy()
            
            # Pulsante per confermare
            ttk.Button(top, text="Seleziona", command=select_date).pack(pady=10)
            
        except ImportError:
            # Se tkcalendar non è disponibile, usa un semplice dialogo
            from tkinter import simpledialog
            date_str = simpledialog.askstring("Data", "Inserisci la data della gara (YYYY-MM-DD):", 
                                            parent=self, initialvalue=self.race_date_var.get())
            if date_str:
                try:
                    # Verifica che sia una data valida
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    self.race_date_var.set(date_str)
                except ValueError:
                    show_error("Errore", "Formato data non valido. Usa YYYY-MM-DD.", parent=self)


    def schedule_workouts_direct(self):
        """Pianifica gli allenamenti direttamente usando i dati del form principale"""
        # Verifica che ci siano allenamenti
        if not self.workouts:
            messagebox.showwarning("Nessun allenamento", 
                                 "Non ci sono allenamenti da pianificare.", 
                                 parent=self)
            return
        
        # Ottieni la data della gara
        race_date_str = self.race_date_var.get().strip()
        try:
            race_date = datetime.datetime.strptime(race_date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Errore", "La data della gara non è valida. Usa il formato YYYY-MM-DD.", parent=self)
            return
        
        # Ottieni i giorni preferiti
        preferred_days = [day for day, var in self.preferred_days_vars.items() if var.get()]
        if not preferred_days:
            messagebox.showerror("Errore", "Seleziona almeno un giorno preferito per l'allenamento.", parent=self)
            return
        
        # Pianifica gli allenamenti
        try:
            # Importa le funzioni di pianificazione
            from garmin_planner_gui.gui.scheduling import (
                schedule_workouts_by_week, 
                apply_scheduled_dates
            )
            
            # Pianifica gli allenamenti
            scheduled_dates = schedule_workouts_by_week(
                self.workouts, 
                race_date, 
                preferred_days
            )
            
            # Se non sono state assegnate date
            if not scheduled_dates:
                messagebox.showwarning("Nessuna data pianificata", 
                                     "Non è stato possibile pianificare gli allenamenti. "
                                     "Verifica che ci siano allenamenti nel formato corretto (W00S00).", 
                                     parent=self)
                return
            
            # Applica le date pianificate
            self.workouts = apply_scheduled_dates(self.workouts, scheduled_dates)
            
            # Aggiorna la lista
            self.refresh_workout_list()
            
            # Aggiorna la configurazione con i dati di pianificazione
            self.save_planning_config(race_date_str, preferred_days)
            
            # Mostra messaggio di conferma
            messagebox.showinfo("Pianificazione completata", 
                              f"Sono stati pianificati {len(scheduled_dates)} allenamenti.", 
                              parent=self)
            
        except Exception as e:
            logging.error(f"Errore nella pianificazione degli allenamenti: {str(e)}")
            messagebox.showerror("Errore", 
                              f"Si è verificato un errore durante la pianificazione:\n{str(e)}", 
                              parent=self)

    def save_planning_config(self, race_date, preferred_days):
        """Salva la configurazione di pianificazione nella configurazione globale"""
        # Assicurati che workout_config esista
        if 'workout_config' not in self.controller.config:
            self.controller.config['workout_config'] = {}
        
        # Salva i dati di pianificazione
        self.controller.config['workout_config']['race_day'] = race_date
        self.controller.config['workout_config']['preferred_days'] = preferred_days
        
        # Aggiorna la configurazione locale
        self.workout_config = self.controller.config['workout_config']
        
        # Salva la configurazione
        from garmin_planner_gui.gui.utils import save_config
        save_config(self.controller.config)
        
        # Log
        logging.info(f"Configurazione di pianificazione salvata: race_day={race_date}, preferred_days={preferred_days}")

    def load_planning_config(self):
        """Carica la configurazione di pianificazione dalla configurazione globale"""
        # Se workout_config esiste, carica i dati di pianificazione
        if 'workout_config' in self.controller.config:
            race_day = self.controller.config['workout_config'].get('race_day')
            preferred_days = self.controller.config['workout_config'].get('preferred_days')
            
            # Imposta la data della gara se presente
            if race_day and hasattr(self, 'race_date_var'):
                self.race_date_var.set(race_day)
            
            # Imposta i giorni preferiti se presenti
            if preferred_days and hasattr(self, 'preferred_days_vars'):
                # Reset tutti i giorni
                for day in range(7):
                    self.preferred_days_vars[day].set(False)
                
                # Imposta i giorni preferiti
                if isinstance(preferred_days, list):
                    for day in preferred_days:
                        if 0 <= day <= 6:  # Validazione per sicurezza
                            self.preferred_days_vars[day].set(True)
                elif isinstance(preferred_days, str):
                    # Prova a interpretare la stringa come lista
                    try:
                        # Rimuovi le parentesi quadre e dividi per virgole
                        clean_str = preferred_days.strip('[]').replace(' ', '')
                        day_list = [int(d) for d in clean_str.split(',') if d.isdigit()]
                        
                        for day in day_list:
                            if 0 <= day <= 6:
                                self.preferred_days_vars[day].set(True)
                    except Exception as e:
                        logging.warning(f"Errore nel parsing dei giorni preferiti: {str(e)}")
            
            logging.info(f"Configurazione di pianificazione caricata: race_day={race_day}, preferred_days={preferred_days}")


    def on_canvas_press(self, event):
        """Gestisce il click sul canvas per iniziare il drag-and-drop"""
        # Canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Se il canvas non è ancora inizializzato correttamente, forza l'aggiornamento
        if width <= 1 or height <= 1:
            self.canvas.update_idletasks()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
        
        margin = 5
        draw_width = width - 2 * margin
        
        # Calcola il centro e la zona cliccabile
        center_y = height // 2
        click_zone_height = 80  # Zona cliccabile più ampia
        
        # Verifica che ci siano step
        if not self.current_steps or len(self.current_steps) == 0:
            return
        
        # Verifica se il click è nella zona degli step (fascia centrale)
        if center_y - click_zone_height/2 <= event.y <= center_y + click_zone_height/2:
            # Calcola la larghezza di ciascun blocco e determina quale è stato cliccato
            base_width = draw_width / len(self.current_steps)
            
            # Calcola l'indice dello step cliccato (correzione per i margini)
            relative_x = event.x - margin
            step_index = int(relative_x / base_width)
            
            # Verifica e limita l'indice per sicurezza
            if 0 <= step_index < len(self.current_steps):
                # Seleziona anche nella TreeView
                try:
                    tree_item = self.steps_tree.get_children()[step_index]
                    self.steps_tree.selection_set(tree_item)
                    self.steps_tree.see(tree_item)
                except:
                    pass
                
                # Memorizza i dettagli dell'elemento per il trascinamento
                step = self.current_steps[step_index]
                
                # Inizializza i dati di trascinamento
                self.canvas_drag_data = {
                    "item": step,
                    "index": step_index,
                    "start_x": event.x,
                    "start_y": event.y,
                    "current_x": event.x,
                    "current_y": event.y
                }
                
                # Determina tipo e colore
                if isinstance(step, dict):
                    if 'repeat' in step and 'steps' in step:
                        self.canvas_drag_data["type"] = "repeat"
                        self.canvas_drag_data["color"] = COLORS["repeat"]
                    elif len(step) == 1:
                        step_type = list(step.keys())[0]
                        self.canvas_drag_data["type"] = step_type
                        self.canvas_drag_data["color"] = COLORS.get(step_type, COLORS["other"])
                
                # Ridisegna con l'elemento evidenziato
                self.draw_workout(highlight_index=step_index)
                return
        
        # Se arriviamo qui, nessuno step è stato selezionato
        self.canvas_drag_data = {
            "item": None,
            "index": -1,
            "start_x": 0,
            "start_y": 0,
            "current_x": 0,
            "current_y": 0,
            "type": "",
            "color": ""
        }

    def on_canvas_motion(self, event):
        """Gestisce il movimento del mouse durante il drag-and-drop nel canvas"""
        # Solo se abbiamo un elemento selezionato
        if self.canvas_drag_data["item"] is not None:
            # Aggiorna la posizione corrente
            self.canvas_drag_data["current_x"] = event.x
            self.canvas_drag_data["current_y"] = event.y
            
            # Canvas dimensions
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            margin = 5
            draw_width = width - 2 * margin
            
            # Calcola la larghezza di base per ogni step
            base_width = draw_width / max(1, len(self.current_steps))
            
            # Determina la nuova posizione in base alla coordinata x
            x = event.x
            new_index = int((x - margin) / base_width)
            
            # Limita l'indice all'intervallo valido
            new_index = max(0, min(new_index, len(self.current_steps) - 1))
            
            # Ridisegna il grafico con l'indicatore di trascinamento
            self.draw_workout(drag_from=self.canvas_drag_data["index"], drag_to=new_index, event_x=event.x, event_y=event.y)

    def on_canvas_release(self, event):
        """Gestisce il rilascio del mouse per completare il drag-and-drop nel canvas"""
        # Solo se abbiamo un elemento selezionato
        if self.canvas_drag_data["item"] is not None:
            # Canvas dimensions
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            margin = 5
            draw_width = width - 2 * margin
            
            # Calcola la larghezza di base per ogni step
            base_width = draw_width / max(1, len(self.current_steps))
            
            # Determina la nuova posizione in base alla coordinata x
            x = event.x
            new_index = int((x - margin) / base_width)
            
            # Limita l'indice all'intervallo valido
            new_index = max(0, min(new_index, len(self.current_steps) - 1))
            
            # Sposta l'elemento solo se la posizione è cambiata
            if new_index != self.canvas_drag_data["index"]:
                source_index = self.canvas_drag_data["index"]
                
                # Esegui lo spostamento nella lista di step
                item = self.current_steps.pop(source_index)
                self.current_steps.insert(new_index, item)
                
                # Aggiorna la lista
                self.update_steps_tree()
                
                # Seleziona l'elemento spostato nella lista
                try:
                    target_item = self.steps_tree.get_children()[new_index]
                    self.steps_tree.selection_set(target_item)
                    self.steps_tree.see(target_item)
                except:
                    pass
            else:
                # Se non c'è stato spostamento, ridisegna semplicemente senza evidenziazione
                self.draw_workout()
                
            # Resetta i dati di trascinamento
            self.canvas_drag_data = {
                "item": None,
                "index": -1,
                "start_x": 0,
                "start_y": 0,
                "current_x": 0,
                "current_y": 0,
                "type": "",
                "color": ""
            }

    def on_tree_press(self, event):
        """Gestisce il click sulla treeview per iniziare il drag-and-drop"""
        # Ottieni l'elemento cliccato
        item = self.steps_tree.identify_row(event.y)
        if item:
            # Salva i dettagli dell'elemento
            self.tree_drag_data = {"item": item, "index": self.steps_tree.index(item)}

    def on_tree_motion(self, event):
        """Gestisce il movimento del mouse durante il drag-and-drop nella treeview"""
        # Solo se abbiamo un elemento selezionato
        if self.tree_drag_data["item"]:
            # Ottieni la posizione target
            target_item = self.steps_tree.identify_row(event.y)
            if target_item and target_item != self.tree_drag_data["item"]:
                # Feedback visivo - potrebbe essere aggiunto in futuro
                pass

    def on_tree_release(self, event):
        """Gestisce il rilascio del mouse per completare il drag-and-drop nella treeview"""
        # Solo se abbiamo un elemento selezionato
        if self.tree_drag_data["item"]:
            # Ottieni la posizione target
            target_item = self.steps_tree.identify_row(event.y)
            if target_item and target_item != self.tree_drag_data["item"]:
                # Ottieni gli indici sorgente e destinazione
                target_index = self.steps_tree.index(target_item)
                source_index = self.tree_drag_data["index"]
                
                # Sposta l'elemento nella lista degli step
                item = self.current_steps.pop(source_index)
                self.current_steps.insert(target_index, item)
                
                # Aggiorna la lista
                self.update_steps_tree()
                
                # Seleziona l'elemento spostato
                self.steps_tree.selection_set(self.steps_tree.get_children()[target_index])
            
            # Resetta i dati di trascinamento
            self.tree_drag_data = {"item": None, "index": -1}

    def on_step_select(self, event):
        """Gestisce la selezione di uno step"""
        selection = self.steps_tree.selection()
        if selection:
            # Ottieni l'indice dello step selezionato
            index = self.steps_tree.index(selection[0])
            # Ridisegna con l'elemento evidenziato
            self.draw_workout(highlight_index=index)
        else:
            # Ridisegna senza evidenziazione
            self.draw_workout()

    def draw_workout(self, highlight_index=None, drag_from=None, drag_to=None, event_x=None, event_y=None):
        """Disegna una rappresentazione visiva dell'allenamento sul canvas"""
        self.canvas.delete("all")
        
        # Canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        if width <= 1 or height <= 1:  # Canvas not yet realized
            self.canvas.update_idletasks()
            width = self.canvas.winfo_width()
            height = self.canvas.winfo_height()
            
            # If still not realized, use default dimensions
            if width <= 1:
                width = 700
            if height <= 1:
                height = 150
        
        # Margin
        margin = 5
        
        # Available drawing area
        draw_width = width - 2 * margin
        
        # Se non ci sono step da disegnare
        if not self.current_steps:
            # Disegna un messaggio di istruzioni
            self.canvas.create_text(
                width // 2, height // 2,
                text="Aggiungi passi all'allenamento per visualizzarli qui",
                fill=COLORS["text_dark"],
                font=("Arial", 10)
            )
            return
        
        # Calcola la larghezza di base per ogni step
        base_width = draw_width / len(self.current_steps)
        
        # Posizione Y centrale
        y = height // 2
        
        # Se stiamo trascinando, disegna un indicatore per la posizione target
        if drag_from is not None and drag_to is not None:
            # Calcola la posizione x dell'indicatore di trascinamento
            indicator_x = margin + drag_to * base_width
            
            # Disegna una linea verticale per indicare dove verrà inserito l'elemento
            self.canvas.create_line(
                indicator_x, y - 30, 
                indicator_x, y + 30,
                fill=COLORS["accent"], width=2, dash=(6, 4)
            )
        
        # Numerazione progressiva degli step
        step_number = 1
        
        # Disegna gli step
        for i, step in enumerate(self.current_steps):
            x = margin + i * base_width
            
            # Calcola se questo step deve essere evidenziato
            is_highlighted = (i == highlight_index)
            
            # Salta temporaneamente il disegno dell'elemento che stiamo trascinando
            if i == drag_from and event_x is not None and event_y is not None:
                continue
            
            outline_width = 2 if is_highlighted else 0
            outline_color = COLORS["accent"] if is_highlighted else ""
            
            if isinstance(step, dict):
                if 'repeat' in step and 'steps' in step:
                    # Repeat step
                    iterations = step['repeat']
                    substeps = step['steps']
                    
                    # Larghezza per la ripetizione
                    repeat_width = base_width
                    
                    # Draw repeat box
                    repeat_x = x
                    repeat_y = y - 30
                    self.canvas.create_rectangle(
                        repeat_x, repeat_y, 
                        repeat_x + repeat_width, repeat_y + 60,
                        outline=COLORS["repeat"], width=2, dash=(5, 2)
                    )
                    
                    # Draw repeat label
                    self.canvas.create_text(
                        repeat_x + 10, repeat_y - 10,
                        text=f"{STEP_ICONS['repeat']} {iterations}x",
                        fill=COLORS["repeat"], 
                        font=("Arial", 10, "bold"),
                        anchor=tk.W
                    )
                    
                    # Draw substeps
                    sub_width = repeat_width / max(1, len(substeps))
                    sub_x = x
                    sub_number = 1
                    
                    for substep in substeps:
                        if isinstance(substep, dict) and len(substep) == 1:
                            substep_type = list(substep.keys())[0]
                            
                            # Color for this type
                            color = COLORS.get(substep_type, COLORS["other"])
                            
                            # Draw box
                            self.canvas.create_rectangle(
                                sub_x, y - 20, sub_x + sub_width, y + 20,
                                fill=color, outline=outline_color, width=outline_width
                            )
                            
                            # Draw text
                            self.canvas.create_text(
                                sub_x + sub_width // 2, y,
                                text=f"{STEP_ICONS.get(substep_type, '📝')} {sub_number}",
                                fill=COLORS["text_light"],
                                font=("Arial", 9, "bold")
                            )
                            
                            # Disegna separatore tra substep (eccetto l'ultimo)
                            if sub_number < len(substeps):
                                self.canvas.create_line(
                                    sub_x + sub_width, y - 20,
                                    sub_x + sub_width, y + 20,
                                    fill="white", width=1
                                )
                            
                            sub_x += sub_width
                            sub_number += 1
                    
                    step_number += 1
                
                elif len(step) == 1:
                    # Regular step
                    step_type = list(step.keys())[0]
                    
                    # Color for this type
                    color = COLORS.get(step_type, COLORS["other"])
                    
                    # Draw box
                    self.canvas.create_rectangle(
                        x, y - 20, x + base_width, y + 20,
                        fill=color, outline=outline_color, width=outline_width
                    )
                    
                    # Draw text
                    self.canvas.create_text(
                        x + base_width // 2, y,
                        text=f"{STEP_ICONS.get(step_type, '📝')} {step_number}",
                        fill=COLORS["text_light"],
                        font=("Arial", 9, "bold")
                    )
                    
                    step_number += 1
            
            # Disegna separatori tra step (linea verticale)
            if i < len(self.current_steps) - 1:
                self.canvas.create_line(
                    x + base_width, y - 22,
                    x + base_width, y + 22,
                    fill="#333333", width=1, dash=(2, 2)
                )
        
        # Se stiamo trascinando, disegna l'elemento trascinato sotto il cursore
        if drag_from is not None and event_x is not None and event_y is not None and self.canvas_drag_data.get("type"):
            block_width = base_width
            block_height = 40
            
            # Disegna un rettangolo semitrasparente che rappresenta l'elemento trascinato
            element_type = self.canvas_drag_data["type"]
            color = self.canvas_drag_data["color"]
            
            # Per ottenere un effetto semitrasparente, usiamo un colore leggermente più chiaro
            light_color = self.lighten_color(color)
            
            # Disegna il rettangolo centrato sul cursore
            self.canvas.create_rectangle(
                event_x - block_width/2, event_y - block_height/2,
                event_x + block_width/2, event_y + block_height/2,
                fill=light_color, outline=COLORS["accent"], width=2
            )
            
            # Aggiunge anche un'icona all'elemento trascinato
            if element_type == "repeat":
                icon = STEP_ICONS["repeat"]
            else:
                icon = STEP_ICONS.get(element_type, '📝')
            
            self.canvas.create_text(
                event_x, event_y,
                text=f"{icon} {drag_from + 1}",
                fill=COLORS["text_dark"],
                font=("Arial", 9, "bold")
            )

    def lighten_color(self, hex_color):
        """Rende più chiaro un colore hexadecimale mescolandolo con bianco"""
        # Converte hex_color in componenti RGB
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        
        # Mescola con bianco (255,255,255) con un rapporto 40/60
        r = r * 0.6 + 255 * 0.4
        g = g * 0.6 + 255 * 0.4
        b = b * 0.6 + 255 * 0.4
        
        # Converte in hex e restituisce
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"