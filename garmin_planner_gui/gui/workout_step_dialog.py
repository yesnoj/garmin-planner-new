#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog per l'aggiunta e modifica di passi negli allenamenti
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from .styles import COLORS, STEP_ICONS

class StepDialog(tk.Toplevel):
    """Dialog per la definizione di un passo di allenamento"""
    
    def __init__(self, parent, step_type=None, step_detail=None, sport_type="running", workout_config=None):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.sport_type = sport_type
        
        # Configurazione del dialog
        self.title("Dettagli del passo")
        self.geometry("550x400")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi il dialog modale
        self.transient(parent)
        self.grab_set()
        
        # Carica la configurazione - gestisci diverse fonti di configurazione
        if workout_config is not None:
            # Usa la configurazione passata esplicitamente
            self.workout_config = workout_config
        elif hasattr(parent, 'controller') and parent.controller and hasattr(parent.controller, 'config'):
            # Ottieni la configurazione dal controller del parent
            self.workout_config = parent.controller.config.get('workout_config', {})
        else:
            # Usa una configurazione vuota con valori predefiniti
            self.workout_config = {
                'paces': {
                    "Z1": "6:30", "Z2": "6:00", "Z3": "5:30", "Z4": "5:00", "Z5": "4:30",
                    "recovery": "7:00", "threshold": "5:10", "marathon": "5:20"
                },
                'speeds': {
                    "Z1": "15.0", "Z2": "20.0", "Z3": "25.0", "Z4": "30.0", "Z5": "35.0",
                    "recovery": "12.0", "threshold": "28.0", "ftp": "32.0"
                },
                'swim_paces': {
                    "Z1": "2:30", "Z2": "2:15", "Z3": "2:00", "Z4": "1:45", "Z5": "1:30",
                    "recovery": "2:45", "threshold": "1:55", "sprint": "1:25"
                },
                'heart_rates': {
                    "Z1_HR": "110-125", "Z2_HR": "125-140", "Z3_HR": "140-155", 
                    "Z4_HR": "155-165", "Z5_HR": "165-180"
                }
            }
        
        # Inizializza l'interfaccia
        self.init_ui()
        
        # Se ci sono dati pre-esistenti, popola i campi
        if step_type and step_detail:
            self.populate_from_detail(step_type, step_detail)
        
        # Centra il dialog
        self.center_window()
        
        # Attendi la chiusura
        self.wait_window()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tipo di passo
        type_frame = ttk.Frame(main_frame)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(type_frame, text="Tipo di passo:").pack(side=tk.LEFT, padx=(0, 10))
        
        # Lista dei tipi di passo
        step_types = ["warmup", "interval", "recovery", "cooldown", "rest", "other"]
        self.step_type_var = tk.StringVar(value=step_types[0] if not step_types else step_types[0])
        
        # Crea un combobox per i tipi di passo
        self.step_type_combo = ttk.Combobox(type_frame, textvariable=self.step_type_var, 
                                          values=step_types, state="readonly", width=15)
        self.step_type_combo.pack(side=tk.LEFT)
        
        # Aggiunge un binding per il cambio di tipo
        self.step_type_combo.bind("<<ComboboxSelected>>", self.on_type_change)
        
        # Sezione durata/distanza
        duration_frame = ttk.LabelFrame(main_frame, text="Durata o distanza")
        duration_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Opzioni per la durata/distanza
        self.duration_type_var = tk.StringVar(value="time")
        
        # Grid per opzioni
        ttk.Radiobutton(duration_frame, text="Tempo", variable=self.duration_type_var, 
                       value="time", command=self.update_duration_ui).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Radiobutton(duration_frame, text="Distanza", variable=self.duration_type_var, 
                       value="distance", command=self.update_duration_ui).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Radiobutton(duration_frame, text="Pulsante Lap", variable=self.duration_type_var, 
                       value="lap", command=self.update_duration_ui).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame per i valori di durata
        self.duration_values_frame = ttk.Frame(duration_frame)
        self.duration_values_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Variabili per i valori
        self.time_min_var = tk.StringVar()
        self.time_sec_var = tk.StringVar()
        self.distance_var = tk.StringVar()
        self.distance_unit_var = tk.StringVar(value="m")
        
        # Chiama la funzione per aggiornare l'interfaccia
        self.update_duration_ui()
        
        # Sezione target (pace, velocità, frequenza cardiaca)
        target_frame = ttk.LabelFrame(main_frame, text="Target")
        target_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Opzioni per il target
        self.target_type_var = tk.StringVar(value="none")
        
        # Etichette specifiche per tipo di sport
        if self.sport_type == "running":
            pace_label = "Ritmo"
        elif self.sport_type == "cycling":
            pace_label = "Velocità"
        elif self.sport_type == "swimming":
            pace_label = "Passo vasca"
        else:
            pace_label = "Ritmo/Velocità"
        
        # Grid per opzioni
        ttk.Radiobutton(target_frame, text="Nessuno", variable=self.target_type_var, 
                       value="none", command=self.update_target_ui).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Radiobutton(target_frame, text=pace_label, variable=self.target_type_var, 
                       value="pace", command=self.update_target_ui).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Radiobutton(target_frame, text="Frequenza cardiaca", variable=self.target_type_var, 
                       value="hr", command=self.update_target_ui).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame per i valori di target
        self.target_values_frame = ttk.Frame(target_frame)
        self.target_values_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Variabili per i valori
        self.pace_var = tk.StringVar()
        self.hr_var = tk.StringVar()
        
        # Chiama la funzione per aggiornare l'interfaccia
        self.update_target_ui()
        
        # Descrizione (opzionale)
        desc_frame = ttk.LabelFrame(main_frame, text="Descrizione (opzionale)")
        desc_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.description_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.description_var, width=50).pack(fill=tk.X, padx=5, pady=5)
        
        # Pulsanti
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
    
    def on_type_change(self, event):
        """Gestisce il cambio di tipo di passo"""
        # Imposta valori di default in base al tipo di passo
        step_type = self.step_type_var.get()
        
        if step_type in ["warmup", "cooldown"]:
            # Default per riscaldamento e defaticamento: tempo e nessun target
            self.duration_type_var.set("time")
            self.time_min_var.set("10")
            self.time_sec_var.set("00")
            self.target_type_var.set("none")
        
        elif step_type == "interval":
            # Default per intervallo: distanza e target di ritmo/velocità
            self.duration_type_var.set("distance")
            
            if self.sport_type == "running":
                self.distance_var.set("400")
                self.distance_unit_var.set("m")
            elif self.sport_type == "cycling":
                self.distance_var.set("1")
                self.distance_unit_var.set("km")
            elif self.sport_type == "swimming":
                self.distance_var.set("100")
                self.distance_unit_var.set("m")
            
            self.target_type_var.set("pace")
            
            # Valore di default per il target
            if self.sport_type == "running":
                self.pace_var.set("Z4")
            elif self.sport_type == "cycling":
                self.pace_var.set("Z4")
            elif self.sport_type == "swimming":
                self.pace_var.set("Z4")
        
        elif step_type == "recovery":
            # Default per recupero: tempo e target FC bassa
            self.duration_type_var.set("time")
            self.time_min_var.set("1")
            self.time_sec_var.set("00")
            self.target_type_var.set("hr")
            self.hr_var.set("Z1_HR")
        
        elif step_type == "rest":
            # Default per riposo: pulsante lap e nessun target
            self.duration_type_var.set("lap")
            self.target_type_var.set("none")
        
        # Aggiorna l'interfaccia
        self.update_duration_ui()
        self.update_target_ui()
    
    def update_duration_ui(self):
        """Aggiorna l'interfaccia per la durata in base al tipo selezionato"""
        # Pulisci il frame
        for widget in self.duration_values_frame.winfo_children():
            widget.destroy()
        
        duration_type = self.duration_type_var.get()
        
        if duration_type == "time":
            # Tempo in minuti e secondi
            ttk.Label(self.duration_values_frame, text="Durata:").pack(side=tk.LEFT, padx=(0, 5))
            
            # Minuti
            ttk.Entry(self.duration_values_frame, textvariable=self.time_min_var, width=3).pack(side=tk.LEFT)
            ttk.Label(self.duration_values_frame, text="min").pack(side=tk.LEFT, padx=(0, 5))
            
            # Secondi (non necessari, rimossi per semplicità)
            # ttk.Label(self.duration_values_frame, text=":").pack(side=tk.LEFT)
            # ttk.Entry(self.duration_values_frame, textvariable=self.time_sec_var, width=3).pack(side=tk.LEFT)
            # ttk.Label(self.duration_values_frame, text="sec").pack(side=tk.LEFT)
        
        elif duration_type == "distance":
            # Distanza in metri o chilometri
            ttk.Label(self.duration_values_frame, text="Distanza:").pack(side=tk.LEFT, padx=(0, 5))
            ttk.Entry(self.duration_values_frame, textvariable=self.distance_var, width=6).pack(side=tk.LEFT)
            
            # Unità
            unit_combo = ttk.Combobox(self.duration_values_frame, textvariable=self.distance_unit_var, 
                                     values=["m", "km"], state="readonly", width=5)
            unit_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        elif duration_type == "lap":
            # Nessun valore, usa il pulsante lap
            ttk.Label(self.duration_values_frame, 
                    text="Pressione del pulsante Lap richiesta per passare al passo successivo").pack(side=tk.LEFT)
    
    def update_target_ui(self):
        """Aggiorna l'interfaccia per il target in base al tipo selezionato"""
        # Pulisci il frame
        for widget in self.target_values_frame.winfo_children():
            widget.destroy()
        
        target_type = self.target_type_var.get()
        
        if target_type == "pace":
            # Target di ritmo/velocità
            if self.sport_type == "running":
                # Ritmo per corsa
                ttk.Label(self.target_values_frame, text="Ritmo:").pack(side=tk.LEFT, padx=(0, 5))
                
                # Lista di zone di ritmo
                paces = self.workout_config.get('paces', {})
                pace_values = list(paces.keys())
                
                # Se non ci sono zone definite, usa alcune di default
                if not pace_values:
                    pace_values = ["Z1", "Z2", "Z3", "Z4", "Z5", "recovery", "threshold", "marathon"]
                
                pace_combo = ttk.Combobox(self.target_values_frame, textvariable=self.pace_var, 
                                        values=pace_values, width=15)
                pace_combo.pack(side=tk.LEFT)
                
                # Mostra il prefisso
                ttk.Label(self.target_values_frame, text="@").pack(side=tk.LEFT, padx=(5, 0))
            
            elif self.sport_type == "cycling":
                # Velocità per ciclismo
                ttk.Label(self.target_values_frame, text="Velocità:").pack(side=tk.LEFT, padx=(0, 5))
                
                # Lista di zone di velocità
                speeds = self.workout_config.get('speeds', {})
                speed_values = list(speeds.keys())
                
                # Se non ci sono zone definite, usa alcune di default
                if not speed_values:
                    speed_values = ["Z1", "Z2", "Z3", "Z4", "Z5", "recovery", "threshold", "ftp"]
                
                speed_combo = ttk.Combobox(self.target_values_frame, textvariable=self.pace_var, 
                                         values=speed_values, width=15)
                speed_combo.pack(side=tk.LEFT)
                
                # Mostra il prefisso
                ttk.Label(self.target_values_frame, text="@spd").pack(side=tk.LEFT, padx=(5, 0))
            
            elif self.sport_type == "swimming":
                # Passo vasca per nuoto
                ttk.Label(self.target_values_frame, text="Passo vasca:").pack(side=tk.LEFT, padx=(0, 5))
                
                # Lista di zone di passo vasca
                swim_paces = self.workout_config.get('swim_paces', {})
                swim_pace_values = list(swim_paces.keys())
                
                # Se non ci sono zone definite, usa alcune di default
                if not swim_pace_values:
                    swim_pace_values = ["Z1", "Z2", "Z3", "Z4", "Z5", "recovery", "threshold", "sprint"]
                
                swim_pace_combo = ttk.Combobox(self.target_values_frame, textvariable=self.pace_var, 
                                             values=swim_pace_values, width=15)
                swim_pace_combo.pack(side=tk.LEFT)
                
                # Mostra il prefisso
                ttk.Label(self.target_values_frame, text="@").pack(side=tk.LEFT, padx=(5, 0))
        
        elif target_type == "hr":
            # Target di frequenza cardiaca
            ttk.Label(self.target_values_frame, text="FC:").pack(side=tk.LEFT, padx=(0, 5))
            
            # Lista di zone di FC
            heart_rates = self.workout_config.get('heart_rates', {})
            hr_values = [k for k in heart_rates.keys() if k.endswith("_HR") or k in ["Z1_HR", "Z2_HR", "Z3_HR", "Z4_HR", "Z5_HR"]]
            
            # Se non ci sono zone definite, usa alcune di default
            if not hr_values:
                hr_values = ["Z1_HR", "Z2_HR", "Z3_HR", "Z4_HR", "Z5_HR"]
            
            hr_combo = ttk.Combobox(self.target_values_frame, textvariable=self.hr_var, 
                                   values=hr_values, width=15)
            hr_combo.pack(side=tk.LEFT)
            
            # Mostra il prefisso
            ttk.Label(self.target_values_frame, text="@hr").pack(side=tk.LEFT, padx=(5, 0))
    
    def populate_from_detail(self, step_type, step_detail):
        """Popola i campi del dialog con i dettagli del passo esistente"""
        # Imposta il tipo di passo
        self.step_type_var.set(step_type)
        
        # Caso speciale per lap-button
        if step_detail == "lap-button" or step_detail.startswith("lap-button"):
            self.duration_type_var.set("lap")
            
            # Estrai la descrizione se presente
            if " -- " in step_detail:
                _, description = step_detail.split(" -- ", 1)
                self.description_var.set(description.strip())
            
            # Nessun target
            self.target_type_var.set("none")
            
            # Aggiorna l'interfaccia
            self.update_duration_ui()
            self.update_target_ui()
            return
        
        # Estrai la descrizione
        if " -- " in step_detail:
            step_detail, description = step_detail.split(" -- ", 1)
            self.description_var.set(description.strip())
        
        # Gestione per target di velocità (ciclismo)
        if " @spd " in step_detail:
            parts = step_detail.split(" @spd ", 1)
            duration_part = parts[0].strip()
            pace_part = parts[1].strip()
            
            # Imposta il target
            self.target_type_var.set("pace")
            self.pace_var.set(pace_part)
            
            # Estrai la durata/distanza
            self._extract_duration(duration_part)
        
        # Gestione per target di frequenza cardiaca
        elif " @hr " in step_detail:
            parts = step_detail.split(" @hr ", 1)
            duration_part = parts[0].strip()
            hr_part = parts[1].strip()
            
            # Imposta il target
            self.target_type_var.set("hr")
            self.hr_var.set(hr_part)
            
            # Estrai la durata/distanza
            self._extract_duration(duration_part)
        
        # Gestione per target di ritmo
        elif " @ " in step_detail:
            parts = step_detail.split(" @ ", 1)
            duration_part = parts[0].strip()
            pace_part = parts[1].strip()
            
            # Imposta il target
            self.target_type_var.set("pace")
            self.pace_var.set(pace_part)
            
            # Estrai la durata/distanza
            self._extract_duration(duration_part)
        
        # Se non c'è target, estrai solo la durata/distanza
        else:
            self._extract_duration(step_detail)
            self.target_type_var.set("none")
        
        # Aggiorna l'interfaccia
        self.update_duration_ui()
        self.update_target_ui()
    
    def _extract_duration(self, duration_part):
        """Estrae i valori di durata o distanza da una stringa"""
        # Verifica se è un tempo
        if "min" in duration_part:
            self.duration_type_var.set("time")
            value = duration_part.replace("min", "").strip()
            
            # Gestisci formato mm:ss
            if ":" in value:
                m, s = value.split(":")
                self.time_min_var.set(m)
                self.time_sec_var.set(s)
            else:
                # Solo minuti
                self.time_min_var.set(value)
                self.time_sec_var.set("00")
        
        # Verifica se è una distanza in km
        elif "km" in duration_part:
            self.duration_type_var.set("distance")
            value = duration_part.replace("km", "").strip()
            self.distance_var.set(value)
            self.distance_unit_var.set("km")
        
        # Verifica se è una distanza in m
        elif "m" in duration_part and not "min" in duration_part:
            self.duration_type_var.set("distance")
            value = duration_part.replace("m", "").strip()
            self.distance_var.set(value)
            self.distance_unit_var.set("m")
        
        # Se non è nessuna di queste, prova come valore numerico
        else:
            try:
                # Se è un numero, assumiamo che sia tempo in minuti
                int(duration_part)
                self.duration_type_var.set("time")
                self.time_min_var.set(duration_part)
                self.time_sec_var.set("00")
            except ValueError:
                # Altrimenti imposta lap-button
                self.duration_type_var.set("lap")
    
    def on_ok(self):
        """Gestisce il pulsante OK"""
        # Ottieni il tipo di passo
        step_type = self.step_type_var.get()
        
        # Costruisci il dettaglio in base ai valori
        duration_type = self.duration_type_var.get()
        
        if duration_type == "lap":
            # Pulsante lap
            step_detail = "lap-button"
        
        elif duration_type == "time":
            # Tempo in minuti e secondi
            minutes = self.time_min_var.get().strip()
            # seconds = self.time_sec_var.get().strip()
            
            # Validazione
            if not minutes:
                messagebox.showerror("Errore", "Inserisci un valore per i minuti", parent=self)
                return
            
            try:
                int(minutes)
                # int(seconds)
            except ValueError:
                messagebox.showerror("Errore", "I valori di tempo devono essere numeri interi", parent=self)
                return
            
            # Formatta il tempo
            # step_detail = f"{minutes}:{seconds.zfill(2)}min"
            step_detail = f"{minutes}min"
        
        elif duration_type == "distance":
            # Distanza in metri o chilometri
            distance = self.distance_var.get().strip()
            unit = self.distance_unit_var.get()
            
            # Validazione
            if not distance:
                messagebox.showerror("Errore", "Inserisci un valore per la distanza", parent=self)
                return
            
            try:
                float(distance)
            except ValueError:
                messagebox.showerror("Errore", "Il valore della distanza deve essere un numero", parent=self)
                return
            
            # Formatta la distanza
            step_detail = f"{distance}{unit}"
        
        # Aggiungi il target se presente
        target_type = self.target_type_var.get()
        
        if target_type == "pace":
            pace_value = self.pace_var.get().strip()
            
            # Validazione
            if not pace_value:
                messagebox.showerror("Errore", "Inserisci un valore per il ritmo/velocità", parent=self)
                return
            
            # Prefisso in base al tipo di sport
            if self.sport_type == "cycling":
                step_detail += f" @spd {pace_value}"
            else:
                step_detail += f" @ {pace_value}"
        
        elif target_type == "hr":
            hr_value = self.hr_var.get().strip()
            
            # Validazione
            if not hr_value:
                messagebox.showerror("Errore", "Inserisci un valore per la frequenza cardiaca", parent=self)
                return
            
            step_detail += f" @hr {hr_value}"
        
        # Aggiungi la descrizione se presente
        description = self.description_var.get().strip()
        if description:
            step_detail += f" -- {description}"
        
        # Imposta il risultato
        self.result = (step_type, step_detail)
        
        # Chiudi il dialog
        self.destroy()
    
    def on_cancel(self):
        """Gestisce il pulsante Annulla"""
        self.destroy()