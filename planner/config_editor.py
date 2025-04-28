#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import copy
from common import COLORS, DEFAULT_CONFIG, TKCALENDAR_AVAILABLE
from tkcalendar import DateEntry

class ConfigEditorDialog(tk.Toplevel):
    """Dialog for editing paces, heart rates, speeds, and other configuration options"""
    
    def __init__(self, parent, config=None):
        super().__init__(parent)
        self.parent = parent
        # Usa la configurazione fornita o quella predefinita
        self.config = config if config else copy.deepcopy(DEFAULT_CONFIG)
        
        self.title("Configurazione Allenamenti")
        self.geometry("800x600")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi la finestra modale
        self.transient(parent)
        self.grab_set()
        
        # Crea il notebook per le schede
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scheda per i ritmi (paces) - corsa
        self.paces_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.paces_frame, text="Ritmi (Corsa)")
        
        # Scheda per velocità (speeds) - ciclismo
        self.speeds_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.speeds_frame, text="Velocità (Ciclismo)")
        
        # Scheda per ritmi (swim_paces) - nuoto
        self.swim_paces_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.swim_paces_frame, text="Ritmi (Nuoto)")
        
        # Scheda per le frequenze cardiache (heart rates)
        self.hr_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.hr_frame, text="Frequenze Cardiache")
        
        # Scheda per i margini
        self.margins_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.margins_frame, text="Margini")
        
        # Scheda generale per il tipo di sport e nome atleta
        self.general_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.general_frame, text="Generale")
        
        # Inizializza le schede
        self.init_paces_tab()
        self.init_speeds_tab()
        self.init_swim_paces_tab()
        self.init_hr_tab()
        self.init_margins_tab()
        self.init_general_tab()
        
        # Bottoni
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Annulla", command=self.on_cancel).pack(side=tk.RIGHT, padx=5)
        
        # Centra la finestra
        self.center_window()
        
        # Carica i dati
        self.load_data()
        
        # Attendi la chiusura della finestra
        self.wait_window()

    # ... altri metodi di ConfigEditorDialog ...