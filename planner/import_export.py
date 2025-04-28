#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import yaml
import re
import copy
import logging
import traceback
from common import COLORS, DEFAULT_CONFIG, OPENPYXL_AVAILABLE

class ImportDialog(tk.Toplevel):
    """Dialog for importing workouts from Excel or YAML"""
    
    def __init__(self, parent, config=None):
        super().__init__(parent)
        self.parent = parent
        self.config = config if config else copy.deepcopy(DEFAULT_CONFIG)
        self.result = None
        
        self.title("Importa Allenamenti")
        self.geometry("500x500")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi la finestra modale
        self.transient(parent)
        self.grab_set()
        
        # Setup UI
        self.init_ui()
        
        # Centra e mostra
        self.center_window()
        self.wait_window()
    
    # ... altri metodi di ImportDialog ...

class ExcelExportDialog(tk.Toplevel):
    """Dialog for exporting workouts to Excel"""
    
    def __init__(self, parent, workouts, config=None):
        super().__init__(parent)
        self.parent = parent
        self.workouts = workouts
        self.config = config if config else copy.deepcopy(DEFAULT_CONFIG)
        self.result = None
        
        self.title("Esporta in Excel")
        self.geometry("500x500")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi la finestra modale
        self.transient(parent)
        self.grab_set()
        
        # Verifica openpyxl
        if not OPENPYXL_AVAILABLE:
            messagebox.showerror("Errore", "Libreria openpyxl non disponibile.\nInstalla openpyxl per esportare in Excel.", parent=self)
            self.destroy()
            return
        
        # Setup UI
        self.init_ui()
        
        # Centra e mostra
        self.center_window()
        self.wait_window()
    
    # ... altri metodi di ExcelExportDialog ...