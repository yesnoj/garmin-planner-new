#!/usr/bin/env python
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import re
import copy
import datetime
import logging
from common import COLORS, SPORT_ICONS, DEFAULT_CONFIG, TKCALENDAR_AVAILABLE
from tkcalendar import Calendar, DateEntry

class WorkoutSelector(tk.Toplevel):
    """Dialog for selecting a workout from a list"""
    
    def __init__(self, parent, workouts):
        super().__init__(parent)
        self.parent = parent
        self.workouts = workouts
        self.result = None
        
        self.title("Seleziona Allenamento")
        self.geometry("600x400")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi la finestra modale
        self.transient(parent)
        self.grab_set()
        
        # Setup UI
        self.init_ui()
        
        # Centra e mostra
        self.center_window()
        self.wait_window()
    
    # ... altri metodi di WorkoutSelector ...

class AutoScheduleDialog(tk.Toplevel):
    """Dialog for auto-scheduling settings"""
    
    def __init__(self, parent, config=None):
        super().__init__(parent)
        self.parent = parent
        self.config = config if config else copy.deepcopy(DEFAULT_CONFIG)
        self.result = None
        
        self.title("Pianificazione Automatica")
        self.geometry("500x400")
        self.configure(bg=COLORS["bg_light"])
        
        # Rendi la finestra modale
        self.transient(parent)
        self.grab_set()
        
        # Setup UI
        self.init_ui()
        
        # Centra e mostra
        self.center_window()
        self.wait_window()
    
    # ... altri metodi di AutoScheduleDialog ...

class CalendarView(tk.Toplevel):
    """Calendar view for scheduling workouts"""
    
    def __init__(self, parent, workouts, config=None):
        super().__init__(parent)
        self.parent = parent
        self.workouts = workouts
        self.config = config if config else copy.deepcopy(DEFAULT_CONFIG)
        self.result = None
        
        self.title("Calendario Allenamenti")
        self.geometry("1000x700")
        self.configure(bg=COLORS["bg_light"])
        
        # Current date and selected date
        self.current_date = datetime.datetime.now().date()
        self.selected_date = self.current_date
        self.selected_workout = None
        
        # Calendar mode: month or week
        self.calendar_mode = "month"
        
        # Setup UI
        self.init_ui()
        
        # Rendi la finestra principale
        self.update_calendar()
        self.center_window()
        self.wait_window()
    
    # ... altri metodi di CalendarView ...