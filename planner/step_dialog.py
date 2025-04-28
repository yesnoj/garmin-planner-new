#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import re
from common import COLORS, DEFAULT_CONFIG

class StepDialog(tk.Toplevel):
    """Dialog per aggiungere/modificare un passo dell'allenamento"""
    
    def __init__(self, parent, step_type=None, step_detail=None, sport_type="running"):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.sport_type = sport_type
        
        # Verifica se stiamo tentando di modificare un metadato
        metadata_keys = ["sport_type", "date"]
        if step_type in metadata_keys:
            messagebox.showinfo("Informazione", f"I metadati di tipo '{step_type}' non possono essere modificati in questa schermata.")
            self.destroy()
            return
        
        self.title("Dettagli del passo")
        self.geometry("500x300")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi la finestra modale
        self.transient(parent)
        self.grab_set()
        
        # Tipo di passo
        type_frame = ttk.Frame(self)
        type_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(type_frame, text="Tipo di passo:").grid(row=0, column=0, padx=5, pady=5)
        
        # Aggiungi "drill" per il nuoto
        step_types = ["warmup", "interval", "recovery", "cooldown", "rest", "drill", "other"]
        self.step_type = tk.StringVar(value=step_type if step_type and step_type not in ["sport_type", "date"] else "interval")
        
        # Usa un combobox
        step_type_combo = ttk.Combobox(type_frame, textvariable=self.step_type, values=step_types, state="readonly", width=15)
        step_type_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Quando cambia il tipo, aggiorna l'interfaccia
        step_type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        
        # Dettaglio del passo
        detail_frame = ttk.LabelFrame(self, text="Definisci il passo")
        detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Per la durata/distanza
        measure_frame = ttk.Frame(detail_frame)
        measure_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(measure_frame, text="Durata/Distanza:").grid(row=0, column=0, padx=5, pady=5)
        self.measure_var = tk.StringVar()
        self.measure_entry = ttk.Entry(measure_frame, textvariable=self.measure_var, width=10)
        self.measure_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Unità adattate al tipo di sport
        unit_values = ["min", "km", "m", "lap-button"]
        if sport_type == "swimming":
            # Per il nuoto aggiungiamo le "yards" e le vasche (lengths)
            unit_values = ["min", "m", "yd", "lengths", "lap-button"]
            
        self.unit_var = tk.StringVar(value="min")
        self.unit_combo = ttk.Combobox(measure_frame, textvariable=self.unit_var, values=unit_values, width=10, state="readonly")
        self.unit_combo.grid(row=0, column=2, padx=5, pady=5)
        self.unit_combo.bind('<<ComboboxSelected>>', self.on_unit_change)
        
        # Per la zona (ritmo, velocità o FC)
        zone_frame = ttk.Frame(detail_frame)
        zone_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Cambia le etichette in base al tipo di sport
        if sport_type == "cycling":
            pace_label = "Velocità"
        elif sport_type == "swimming":
            pace_label = "Ritmo nuoto"
        else:  # running
            pace_label = "Ritmo"
            
        self.zone_type = tk.StringVar(value="pace")
        ttk.Radiobutton(zone_frame, text=pace_label, variable=self.zone_type, value="pace", 
                        command=self.update_zone_options).grid(row=0, column=0, padx=5, pady=5)
        ttk.Radiobutton(zone_frame, text="Frequenza Cardiaca", variable=self.zone_type, value="hr", 
                        command=self.update_zone_options).grid(row=0, column=1, padx=5, pady=5)
        ttk.Radiobutton(zone_frame, text="Nessuna", variable=self.zone_type, value="none", 
                        command=self.update_zone_options).grid(row=0, column=2, padx=5, pady=5)
        
        # Frame per le opzioni della zona
        self.zone_options_frame = ttk.Frame(detail_frame)
        self.zone_options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Lista vuota per i valori di zona
        self.zone_var = tk.StringVar()
        self.zone_combo = ttk.Combobox(self.zone_options_frame, textvariable=self.zone_var, width=15)
        self.zone_combo.pack(side=tk.LEFT, padx=5)
        
        # Aggiornamento delle opzioni di zona
        self.update_zone_options()
        
        # Descrizione (opzionale)
        desc_frame = ttk.LabelFrame(detail_frame, text="Descrizione (opzionale)")
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.description_var = tk.StringVar()
        ttk.Entry(desc_frame, textvariable=self.description_var, width=50).pack(fill=tk.X, padx=5, pady=5)
        
        # Bottoni
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Annulla", command=self.on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Se abbiamo dei dettagli, popola i campi
        if step_detail:
            self.populate_from_detail(step_detail)
            
        # Centra la finestra sullo schermo
        self.center_window()
        
        # Attendi che la finestra sia chiusa
        self.wait_window()
    
    def center_window(self):
        """Center the window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_type_change(self, event):
        """Handle step type change"""
        # Adatta l'interfaccia in base al tipo selezionato
        step_type = self.step_type.get()
        
        # Verifica se è un metadato
        metadata_keys = ["sport_type", "date"]
        if step_type in metadata_keys:
            messagebox.showinfo("Informazione", f"I metadati di tipo '{step_type}' non possono essere selezionati.")
            # Reimposta il tipo a un valore accettabile
            self.step_type.set("interval")
            return
        
        # Aggiorna le unità di default
        if step_type in ["warmup", "cooldown", "recovery"]:
            self.unit_var.set("min")
        elif step_type == "interval":
            if self.sport_type == "swimming":
                self.unit_var.set("m")  # Per il nuoto, usa metri come default
            else:
                self.unit_var.set("km")
        elif step_type == "drill" and self.sport_type == "swimming":
            self.unit_var.set("lengths")  # Per esercizi di nuoto, default a vasche
        elif step_type == "rest":
            # Per i passi di riposo, mostra anche lap-button come opzione
            self.unit_var.set("min")
        
    def on_unit_change(self, event):
        """Handle unit change"""
        if self.unit_var.get() == "lap-button":
            # Disabilita il campo misura
            self.measure_var.set("")
            self.measure_entry.configure(state="disabled")
            # Imposta zona a none
            self.zone_type.set("none")
            self.update_zone_options()
        else:
            # Riabilita il campo misura
            self.measure_entry.configure(state="normal")
    
    def update_zone_options(self):
        """Update zone options based on the selected zone type"""
        zone_type = self.zone_type.get()
        
        # Pulisci le opzioni correnti
        for widget in self.zone_options_frame.winfo_children():
            widget.destroy()
        
        if zone_type == "pace":
            # In base al tipo di sport, carica le opzioni appropriate
            if self.sport_type == "cycling":
                # Carica le opzioni per la velocità
                speed_zones = list(DEFAULT_CONFIG.get('speeds', {}).keys())
                
                self.zone_var = tk.StringVar()
                self.zone_combo = ttk.Combobox(self.zone_options_frame, textvariable=self.zone_var, values=speed_zones, width=15)
                self.zone_combo.pack(side=tk.LEFT, padx=5)
                
                # Aggiungi simbolo @spd per velocità
                ttk.Label(self.zone_options_frame, text="@spd").pack(side=tk.LEFT)
                
                # Il primo valore come default
                if speed_zones:
                    self.zone_var.set(speed_zones[0])
            elif self.sport_type == "swimming":
                # Carica le opzioni per il nuoto
                swim_zones = list(DEFAULT_CONFIG.get('swim_paces', {}).keys())
                
                self.zone_var = tk.StringVar()
                self.zone_combo = ttk.Combobox(self.zone_options_frame, textvariable=self.zone_var, values=swim_zones, width=15)
                self.zone_combo.pack(side=tk.LEFT, padx=5)
                
                # Aggiungi simbolo @swim per nuoto
                ttk.Label(self.zone_options_frame, text="@swim").pack(side=tk.LEFT)
                
                # Il primo valore come default
                if swim_zones:
                    self.zone_var.set(swim_zones[0])
            else:  # running
                # Carica le opzioni per il ritmo
                pace_zones = list(DEFAULT_CONFIG.get('paces', {}).keys())
                
                self.zone_var = tk.StringVar()
                self.zone_combo = ttk.Combobox(self.zone_options_frame, textvariable=self.zone_var, values=pace_zones, width=15)
                self.zone_combo.pack(side=tk.LEFT, padx=5)
                
                # Aggiungi simbolo @
                ttk.Label(self.zone_options_frame, text="@").pack(side=tk.LEFT)
                
                # Il primo valore come default
                if pace_zones:
                    self.zone_var.set(pace_zones[0])
                
        elif zone_type == "hr":
            # Carica le opzioni per la frequenza cardiaca
            hr_zones = list(DEFAULT_CONFIG.get('heart_rates', {}).keys())
            
            # Filtra "_HR" per le zone che hanno il suffisso
            hr_zones = [zone for zone in hr_zones if "_HR" in zone or zone == "max_hr"]
            
            self.zone_var = tk.StringVar()
            self.zone_combo = ttk.Combobox(self.zone_options_frame, textvariable=self.zone_var, values=hr_zones, width=15)
            self.zone_combo.pack(side=tk.LEFT, padx=5)
            
            # Aggiungi simbolo @hr
            ttk.Label(self.zone_options_frame, text="@hr").pack(side=tk.LEFT)
            
            # Il primo valore come default
            if hr_zones:
                self.zone_var.set(hr_zones[0])
        
        else:  # none - nessuna zona
            # Non mostrare opzioni di zona
            pass
            
        # Gestione speciale per lap-button
        if self.unit_var.get() == "lap-button":
            # Disabilita il campo misura
            self.measure_var.set("")
            self.measure_entry.configure(state="disabled")
    

    def populate_from_detail(self, detail):
        """Populate fields from step detail"""
        # [Continua il resto dei metodi...]

    def on_ok(self):
        """Handle OK button click"""
        # [Continua il resto dei metodi...]
    
    def on_cancel(self):
        """Handle Cancel button click"""
        self.destroy()