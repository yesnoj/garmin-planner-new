#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog per l'aggiunta e modifica delle sezioni di ripetizioni negli allenamenti
"""

import tkinter as tk
from tkinter import ttk, messagebox
import copy
from .styles import COLORS, STEP_ICONS
from .workout_step_dialog import StepDialog

class RepeatDialog(tk.Toplevel):
    """Dialog per la definizione di una sezione di ripetizioni"""
    
    def __init__(self, parent, iterations=None, steps=None, sport_type="running"):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.sport_type = sport_type  # Conserviamo il tipo di sport
        
        # Inizializza i valori prima di chiamare init_ui
        self.iterations = iterations if iterations is not None else 4
        self.repeat_steps = steps if steps is not None else []
        
        # Configurazione del dialog
        self.title("Definizione ripetizioni")
        self.geometry("600x500")  # Dimensione aumentata per visualizzare tutto
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi il dialog modale
        self.transient(parent)
        self.grab_set()
        
        # Ora che i valori sono inizializzati, possiamo chiamare init_ui
        self.init_ui()
        
        # Carica i passi se disponibili
        self.load_steps()
        
        # Centra il dialog
        self.center_window()
        
        # Attendi la chiusura
        self.wait_window()

    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame per l'intestazione
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Numero di ripetizioni
        ttk.Label(header_frame, text="Numero di ripetizioni:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Spinner per il numero
        self.iterations_var = tk.StringVar(value=str(self.iterations))
        iterations_spinbox = ttk.Spinbox(header_frame, from_=1, to=100, 
                                        textvariable=self.iterations_var, width=5)
        iterations_spinbox.pack(side=tk.LEFT)
        
        # Label informativa
        ttk.Label(header_frame, text=f"{STEP_ICONS['repeat']} Definisci i passi da ripetere", 
                 style="Instructions.TLabel").pack(side=tk.RIGHT)
        
        # Frame per la lista dei passi
        steps_frame = ttk.LabelFrame(main_frame, text="Passi da ripetere")
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Toolbar per i passi
        toolbar = ttk.Frame(steps_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        
        # Pulsanti per gestire i passi
        ttk.Button(toolbar, text="Aggiungi passo", command=self.add_step).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Modifica passo", command=self.edit_step).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Elimina passo", command=self.delete_step).pack(side=tk.LEFT, padx=5)  # Corretto il nome del metodo
        ttk.Button(toolbar, text="Sposta su", command=self.move_step_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Sposta giù", command=self.move_step_down).pack(side=tk.LEFT, padx=5)
        
        # Lista dei passi con scrollbar
        list_frame = ttk.Frame(steps_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea la treeview per la lista dei passi
        columns = ("index", "type", "details")
        self.steps_tree = ttk.Treeview(list_frame, columns=columns, show="headings", 
                                      selectmode="browse")
        
        # Intestazioni
        self.steps_tree.heading("index", text="#")
        self.steps_tree.heading("type", text="Tipo")
        self.steps_tree.heading("details", text="Dettagli")
        
        # Larghezze colonne
        self.steps_tree.column("index", width=30)
        self.steps_tree.column("type", width=100)
        self.steps_tree.column("details", width=400)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.steps_tree.yview)
        self.steps_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.steps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click per modificare
        self.steps_tree.bind("<Double-1>", lambda e: self.edit_step())
        
        # Esempio di blocco di ripetizione tipico
        example_frame = ttk.LabelFrame(main_frame, text="Esempi comuni")
        example_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Pulsanti per esempi tipici
        if self.sport_type == "running":
            ttk.Button(example_frame, text="400m x recupero", 
                      command=lambda: self.add_example("running_400m")).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(example_frame, text="800m x recupero", 
                      command=lambda: self.add_example("running_800m")).pack(side=tk.LEFT, padx=5)
            ttk.Button(example_frame, text="1km x recupero", 
                      command=lambda: self.add_example("running_1km")).pack(side=tk.LEFT, padx=5)
        elif self.sport_type == "cycling":
            ttk.Button(example_frame, text="1min x recupero", 
                      command=lambda: self.add_example("cycling_1min")).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(example_frame, text="5min x recupero", 
                      command=lambda: self.add_example("cycling_5min")).pack(side=tk.LEFT, padx=5)
            ttk.Button(example_frame, text="Interval + recovery", 
                      command=lambda: self.add_example("cycling_interval")).pack(side=tk.LEFT, padx=5)
        elif self.sport_type == "swimming":
            ttk.Button(example_frame, text="100m x recupero", 
                      command=lambda: self.add_example("swimming_100m")).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(example_frame, text="4x25m @ ripetuta", 
                      command=lambda: self.add_example("swimming_25m")).pack(side=tk.LEFT, padx=5)
            ttk.Button(example_frame, text="Tecnica + nuotata", 
                      command=lambda: self.add_example("swimming_drill")).pack(side=tk.LEFT, padx=5)
        
        # Pulsanti OK e Annulla
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Annulla", command=self.on_cancel).pack(side=tk.LEFT)
    
    def center_window(self):
        """Centra il dialog sullo schermo"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def add_step(self):
        """Aggiunge un nuovo passo"""
        # Ottieni la configurazione dal parent se possibile
        workout_config = None
        if hasattr(self.parent, "controller") and self.parent.controller:
            workout_config = self.parent.controller.config.get('workout_config', {})
        
        # Passa la configurazione a StepDialog
        dialog = StepDialog(self, sport_type=self.sport_type, workout_config=workout_config)
        
        if dialog.result:
            step_type, step_detail = dialog.result
            
            # Aggiungi lo step alla lista
            if not hasattr(self, 'repeat_steps'):
                self.repeat_steps = []
            
            self.repeat_steps.append({step_type: step_detail})
            self.load_steps()
    
    def edit_step(self):
        """Edit the selected step"""
        selection = self.steps_tree.selection()
        
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona un passo da modificare", parent=self)
            return
        
        # Get the selected step
        index = self.steps_tree.index(selection[0])
        step = self.repeat_steps[index]
        
        # Get step type and detail
        if isinstance(step, dict) and len(step) == 1:
            step_type = list(step.keys())[0]
            step_detail = step[step_type]
            
            # Ottieni la configurazione dal parent se possibile
            workout_config = None
            if hasattr(self.parent, "controller") and self.parent.controller:
                workout_config = self.parent.controller.config.get('workout_config', {})
            
            # Open the step dialog passing the sport_type and workout_config
            dialog = StepDialog(self, step_type=step_type, step_detail=step_detail, 
                               sport_type=self.sport_type, workout_config=workout_config)
            
            if dialog.result:
                new_type, new_detail = dialog.result
                self.repeat_steps[index] = {new_type: new_detail}
                self.load_steps()
        else:
            messagebox.showinfo("Formato non supportato", 
                               "Questo passo ha un formato che non può essere modificato direttamente.\n"
                               "Ti suggeriamo di eliminarlo e ricrearlo.", parent=self)
    
    def remove_step(self):
        """Alias per delete_step per compatibilità"""
        self.delete_step()
        
    def delete_step(self):
        """Elimina il passo selezionato"""
        selection = self.steps_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", "Seleziona un passo da eliminare", parent=self)
            return
        
        # Ottieni l'indice
        index = self.steps_tree.index(selection[0])
        
        # Chiedi conferma
        if messagebox.askyesno("Conferma eliminazione", 
                              "Sei sicuro di voler eliminare questo passo?", 
                              parent=self):
            # Elimina il passo
            self.repeat_steps.pop(index)
            self.load_steps()
    
    def move_step_up(self):
        """Sposta il passo selezionato verso l'alto"""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice
        index = self.steps_tree.index(selection[0])
        
        # Non si può spostare il primo elemento in alto
        if index == 0:
            return
        
        # Scambia gli step
        self.repeat_steps[index], self.repeat_steps[index-1] = self.repeat_steps[index-1], self.repeat_steps[index]
        
        # Aggiorna la lista
        self.load_steps()
        
        # Seleziona lo step spostato
        new_selection = self.steps_tree.get_children()[index-1]
        self.steps_tree.selection_set(new_selection)
        self.steps_tree.see(new_selection)
    
    def move_step_down(self):
        """Sposta il passo selezionato verso il basso"""
        selection = self.steps_tree.selection()
        if not selection:
            return
        
        # Ottieni l'indice
        index = self.steps_tree.index(selection[0])
        
        # Non si può spostare l'ultimo elemento in basso
        if index >= len(self.repeat_steps) - 1:
            return
        
        # Scambia gli step
        self.repeat_steps[index], self.repeat_steps[index+1] = self.repeat_steps[index+1], self.repeat_steps[index]
        
        # Aggiorna la lista
        self.load_steps()
        
        # Seleziona lo step spostato
        new_selection = self.steps_tree.get_children()[index+1]
        self.steps_tree.selection_set(new_selection)
        self.steps_tree.see(new_selection)
    
    def add_example(self, example_type):
        """Aggiunge un esempio predefinito"""
        # Esempi per la corsa
        if example_type == "running_400m":
            self.repeat_steps = [
                {"interval": "400m @ Z4"},
                {"recovery": "1min @ Z1_HR"}
            ]
        elif example_type == "running_800m":
            self.repeat_steps = [
                {"interval": "800m @ Z3"},
                {"recovery": "2min @ Z1_HR"}
            ]
        elif example_type == "running_1km":
            self.repeat_steps = [
                {"interval": "1km @ Z4"},
                {"recovery": "3min @ Z1_HR"}
            ]
        
        # Esempi per il ciclismo
        elif example_type == "cycling_1min":
            self.repeat_steps = [
                {"interval": "1min @spd Z4"},
                {"recovery": "1min @hr Z1_HR"}
            ]
        elif example_type == "cycling_5min":
            self.repeat_steps = [
                {"interval": "5min @spd Z3"},
                {"recovery": "2min @hr Z1_HR"}
            ]
        elif example_type == "cycling_interval":
            self.repeat_steps = [
                {"interval": "2min @spd Z5"},
                {"recovery": "30s @hr Z1_HR"},
                {"interval": "1min @spd Z4"},
                {"recovery": "1min @hr Z1_HR"}
            ]
        
        # Esempi per il nuoto
        elif example_type == "swimming_100m":
            self.repeat_steps = [
                {"interval": "100m @ Z4"},
                {"recovery": "30s @ Z1_HR"}
            ]
        elif example_type == "swimming_25m":
            self.repeat_steps = [
                {"interval": "25m @ Z5 -- Sprint"},
                {"recovery": "15s @ Z1_HR"}
            ]
        elif example_type == "swimming_drill":
            self.repeat_steps = [
                {"interval": "50m @ Z2 -- Tecnica"},
                {"interval": "50m @ Z4 -- Nuotata completa"}
            ]
        
        # Aggiorna la lista
        self.load_steps()
    
    def on_ok(self):
        """Gestisce il pulsante OK"""
        # Verifica i dati
        if not self.iterations_var.get():
            messagebox.showerror("Errore", "Inserisci il numero di ripetizioni", parent=self)
            return
        
        try:
            iterations = int(self.iterations_var.get())
            if iterations <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Errore", "Il numero di ripetizioni deve essere un intero positivo", parent=self)
            return
        
        if not hasattr(self, 'repeat_steps') or not self.repeat_steps:
            messagebox.showerror("Errore", "Aggiungi almeno un passo alla ripetizione", parent=self)
            return
        
        # Imposta il risultato
        self.result = (iterations, self.repeat_steps)
        
        # Chiudi il dialog
        self.destroy()
    
    def on_cancel(self):
        """Gestisce il pulsante Annulla"""
        self.destroy()

    def load_steps(self):
        """Carica i passi nella treeview"""
        # Pulisci la lista attuale
        for item in self.steps_tree.get_children():
            self.steps_tree.delete(item)
        
        # Se non ci sono passi, esci
        if not hasattr(self, 'repeat_steps') or not self.repeat_steps:
            return
        
        # Aggiungi i passi alla treeview
        for i, step in enumerate(self.repeat_steps):
            if isinstance(step, dict) and len(step) == 1:
                step_type = list(step.keys())[0]
                step_detail = step[step_type]
                
                # Aggiungi alla treeview
                self.steps_tree.insert("", "end", values=(i+1, step_type, step_detail))