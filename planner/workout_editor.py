#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import re
import copy
import logging
import datetime
from common import COLORS, STEP_ICONS, DEFAULT_CONFIG, TKCALENDAR_AVAILABLE
from utils import lighten_color, get_step_visual_length, get_step_display_text
from step_dialog import StepDialog
from repeat_dialog import RepeatDialog
from tkcalendar import DateEntry

class WorkoutEditor(tk.Toplevel):
    """Main workout editor window"""
    
    def __init__(self, parent, workout_name=None, workout_steps=None, sport_type=None, config=None):
        super().__init__(parent)
        self.parent = parent
        self.result = None
        self.config = config if config else copy.deepcopy(DEFAULT_CONFIG)
        
        self.title("Editor Allenamento")
        self.geometry("800x700")
        self.configure(bg=COLORS["bg_main"])
        
        # Stato dell'editor
        self.workout_name = workout_name if workout_name else "Nuovo allenamento"
        self.workout_steps = workout_steps if workout_steps else []
        
        # Sport type (default from config or passed parameter)
        self.sport_type = sport_type if sport_type else self.config.get('sport_type', 'running')
        
        # Inizializza l'interfaccia
        self.init_ui()
        
        # Carica passi se disponibili
        self.load_steps()
        
        # Centra la finestra
        self.center_window()
        
        # Rendi la finestra principale
        self.wait_window()
    
    # ... altri metodi di WorkoutEditor ...