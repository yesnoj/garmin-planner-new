#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Punto di ingresso principale per l'applicazione Garmin Planner GUI
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
import json
import datetime
import yaml
import re

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Importa i moduli dell'applicazione
from garmin_planner_gui.gui.styles import setup_styles, COLORS
from garmin_planner_gui.gui.login_frame import LoginFrame
from garmin_planner_gui.gui.workout_editor_frame import WorkoutEditorFrame
from garmin_planner_gui.gui.calendar_frame import CalendarFrame
from garmin_planner_gui.gui.import_export_frame import ImportExportFrame
from garmin_planner_gui.gui.settings_frame import SettingsFrame
from garmin_planner_gui.gui.utils import center_window, load_config, save_config

class GarminPlannerApp(tk.Tk):
    """Applicazione principale per Garmin Planner"""
    
    def __init__(self):
        super().__init__()
        
        self.title("Garmin Planner")
        self.geometry("1024x768")
        self.minsize(800, 600)
        
        # Configura gli stili
        setup_styles()
        
        # Carica la configurazione
        self.config = load_config()
        
        # Verifica se esiste una sessione salvata
        self.garmin_client = None
        self.logged_in = False
        
        # Crea il frame principale
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crea il notebook (schede)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Crea le varie schede
        self.login_frame = LoginFrame(self.notebook, self)
        self.workout_editor_frame = WorkoutEditorFrame(self.notebook, self)
        self.calendar_frame = CalendarFrame(self.notebook, self)
        self.import_export_frame = ImportExportFrame(self.notebook, self)
        self.settings_frame = SettingsFrame(self.notebook, self)
        
        # Aggiungi le schede al notebook
        self.notebook.add(self.login_frame, text="Login")
        self.notebook.add(self.workout_editor_frame, text="Allenamenti")
        self.notebook.add(self.calendar_frame, text="Calendario")
        self.notebook.add(self.import_export_frame, text="Import/Export")
        self.notebook.add(self.settings_frame, text="Impostazioni")
        
        # Barra di stato
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(self.status_frame, text="Pronto", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, padx=5, pady=2)
        
        self.login_status_label = ttk.Label(self.status_frame, text="Non connesso", anchor=tk.E)
        self.login_status_label.pack(side=tk.RIGHT, padx=5, pady=2)
        
        # Centra la finestra
        center_window(self)
        
        # Collegamento alla chiusura dell'applicazione
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Verifica se c'è un token OAuth salvato e prova a usarlo
        self.try_auto_login()
    
    def try_auto_login(self):
        """Tenta un login automatico se è disponibile un token OAuth"""
        oauth_dir = self.config.get('oauth_folder', '~/.garth')
        oauth_dir = os.path.expanduser(oauth_dir)
        
        if os.path.exists(oauth_dir):
            try:
                from planner.garmin_client import GarminClient
                self.garmin_client = GarminClient(oauth_dir)
                # Verifica se il client è valido tentando una richiesta
                _ = self.garmin_client.list_workouts()
                self.logged_in = True
                self.update_login_status("Connesso a Garmin Connect")
                self.login_frame.update_ui_after_login()
                
                # Passa alla seconda scheda (Allenamenti) dopo il login
                self.notebook.select(1)
            except Exception as e:
                logging.error(f"Errore nel login automatico: {str(e)}")
                self.login_frame.show_login_error(f"Errore nel login automatico: {str(e)}")
    
    def set_status(self, message):
        """Imposta il messaggio nella barra di stato"""
        self.status_label.config(text=message)
        self.update_idletasks()
    
    def update_login_status(self, message):
        """Aggiorna il messaggio di stato del login"""
        self.login_status_label.config(text=message)
        self.update_idletasks()
    
    def on_login(self, client):
        """Gestisce l'evento di login completato"""
        self.garmin_client = client
        self.logged_in = True
        self.update_login_status("Connesso a Garmin Connect")
        
        # Aggiorna le altre schede
        self.workout_editor_frame.on_login(client)
        self.calendar_frame.on_login(client)
        self.import_export_frame.on_login(client)
        
        # Passa alla seconda scheda (Allenamenti) dopo il login
        self.notebook.select(1)
    
    def on_logout(self):
        """Gestisce l'evento di logout"""
        self.garmin_client = None
        self.logged_in = False
        self.update_login_status("Non connesso")
        
        # Aggiorna le altre schede
        self.workout_editor_frame.on_logout()
        self.calendar_frame.on_logout()
        self.import_export_frame.on_logout()
    
    def on_close(self):
        """Gestisce la chiusura dell'applicazione"""
        # Salva la configurazione
        save_config(self.config)
        
        # Chiudi l'applicazione
        self.destroy()

def main():
    app = GarminPlannerApp()
    app.mainloop()

if __name__ == "__main__":
    main()