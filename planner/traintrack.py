#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TrainTrack - Gestore di Allenamenti Sportivi

Un'applicazione per la creazione, modifica e pianificazione di allenamenti per
diversi sport (corsa, ciclismo, nuoto), con funzionalità di esportazione in Excel.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import copy
import logging
import webbrowser
import sys

from common import COLORS, DEFAULT_CONFIG, APP_VERSION, SPORT_ICONS
from workout_editor import WorkoutEditor
from config_editor import ConfigEditorDialog
from calendar_view import CalendarView, AutoScheduleDialog
from import_export import ImportDialog, ExcelExportDialog

class MainApplication(tk.Tk):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        self.title(f"TrainTrack - Gestore di Allenamenti Sportivi v{APP_VERSION}")
        self.geometry("1200x800")
        self.configure(bg=COLORS["bg_main"])
        
        # Program state
        self.workouts = []  # List of (name, steps) tuples
        self.config = copy.deepcopy(DEFAULT_CONFIG)
        self.current_file = None
        self.modified = False
        
        # Setup UI
        self.init_ui()
        self.update_title()
        
        # Attempt to load default config file
        default_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traintrack_config.json')
        if os.path.isfile(default_config_file):
            try:
                with open(default_config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                logging.info(f"Loaded default config from {default_config_file}")
            except Exception as e:
                logging.error(f"Error loading default config: {str(e)}")
        
        # Check command line args for file to open
        if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
            self.open_file(sys.argv[1])
    
    # ... altri metodi di MainApplication ...

if __name__ == "__main__":
    app = MainApplication()
    app.mainloop()