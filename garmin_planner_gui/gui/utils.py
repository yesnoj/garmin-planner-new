#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Funzioni di utilità per Garmin Planner GUI
"""

import os
import json
import tkinter as tk
from tkinter import messagebox
import logging
import re
import datetime
import yaml

# Costanti
CONFIG_DIR = os.path.expanduser("~/.garmin_planner")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_CONFIG = {
    "oauth_folder": os.path.expanduser("~/.garth"),
    "workout_config": {
        "paces": {
            "Z1": "6:30",
            "Z2": "6:00",
            "Z3": "5:30",
            "Z4": "5:00",
            "Z5": "4:30",
            "recovery": "7:00",
            "threshold": "5:10",
            "marathon": "5:20",
            "race_pace": "5:10",
        },
        "speeds": {
            "Z1": "15.0",
            "Z2": "20.0",
            "Z3": "25.0",
            "Z4": "30.0",
            "Z5": "35.0",
            "recovery": "12.0",
            "threshold": "28.0",
            "ftp": "32.0",
        },
        "swim_paces": {
            "Z1": "2:30",
            "Z2": "2:15",
            "Z3": "2:00",
            "Z4": "1:45",
            "Z5": "1:30",
            "recovery": "2:45",
            "threshold": "1:55",
            "sprint": "1:25",
        },
        "heart_rates": {
            "max_hr": 180,
            "Z1_HR": "110-125",
            "Z2_HR": "125-140",
            "Z3_HR": "140-155",
            "Z4_HR": "155-165",
            "Z5_HR": "165-180",
        },
        "margins": {
            "faster": "0:03",
            "slower": "0:03",
            "faster_spd": "2.0",
            "slower_spd": "2.0",
            "hr_up": 5,
            "hr_down": 5
        },
        "name_prefix": "",
        "sport_type": "running"
    },
    "ui_preferences": {
        "theme": "default",
        "font_size": "medium",
        "window_size": "1280x800"
    },
    "athlete_name": "",
    "recent_files": []
}

def ensure_config_dir():
    """Assicura che la directory di configurazione esista"""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def load_config():
    """Carica la configurazione dell'applicazione
    
    Returns:
        dict: La configurazione caricata o quella predefinita in caso di errore
    """
    # Assicurati che la directory esista
    try:
        ensure_config_dir()
    except Exception as e:
        logging.error(f"Errore nella creazione della directory di configurazione: {str(e)}")
        return DEFAULT_CONFIG.copy()
    
    # Se il file esiste, prova a caricarlo
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Verifica che sia un dizionario
            if not isinstance(config, dict):
                logging.error("Il file di configurazione non contiene un dizionario valido.")
                return DEFAULT_CONFIG.copy()
            
            # Aggiorna la configurazione con eventuali nuove chiavi
            merged_config = DEFAULT_CONFIG.copy()
            deep_update(merged_config, config)
            
            logging.info("Configurazione caricata con successo.")
            return merged_config
            
        except json.JSONDecodeError as e:
            logging.error(f"Errore di formato nel file di configurazione: {str(e)}")
            
            # Salva una copia del file corrotto
            try:
                import shutil
                backup_file = f"{CONFIG_FILE}.bak"
                shutil.copy2(CONFIG_FILE, backup_file)
                logging.info(f"Creato backup del file di configurazione corrotto: {backup_file}")
            except Exception as backup_err:
                logging.error(f"Impossibile creare backup del file di configurazione: {str(backup_err)}")
            
            return DEFAULT_CONFIG.copy()
            
        except Exception as e:
            logging.error(f"Errore nel caricamento della configurazione: {str(e)}")
            return DEFAULT_CONFIG.copy()
    else:
        logging.info("File di configurazione non trovato. Utilizzo configurazione predefinita.")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Salva la configurazione dell'applicazione
    
    Args:
        config (dict): La configurazione da salvare
        
    Returns:
        bool: True se il salvataggio è riuscito, False altrimenti
    """
    if not isinstance(config, dict):
        logging.error("Tentativo di salvare una configurazione non valida. Deve essere un dizionario.")
        return False
    
    # Assicurati che la directory esista
    try:
        ensure_config_dir()
    except Exception as e:
        logging.error(f"Errore nella creazione della directory di configurazione: {str(e)}")
        return False
    
    # Salva prima in un file temporaneo per evitare la corruzione
    temp_file = f"{CONFIG_FILE}.tmp"
    
    try:
        # Serializza la configurazione
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        # Sostituisci il file originale
        if os.path.exists(CONFIG_FILE):
            os.replace(temp_file, CONFIG_FILE)
        else:
            os.rename(temp_file, CONFIG_FILE)
        
        logging.info("Configurazione salvata con successo.")
        return True
        
    except Exception as e:
        logging.error(f"Errore nel salvataggio della configurazione: {str(e)}")
        
        # Pulisci i file temporanei
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
                
        return False

def deep_update(d, u):
    """Aggiorna ricorsivamente un dizionario con un altro
    
    Args:
        d: Il dizionario da aggiornare
        u: Il dizionario con i nuovi valori
        
    Returns:
        Il dizionario aggiornato (lo stesso oggetto d)
    """
    if not isinstance(d, dict) or not isinstance(u, dict):
        return u
        
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = deep_update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def center_window(window):
    """Centra una finestra sullo schermo"""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f'{width}x{height}+{x}+{y}')

def hhmmss_to_seconds(s):
    """Converte una stringa di tempo nel formato hh:mm:ss in secondi"""
    if not s:
        return 0
    
    parts = s.split(':')
    if len(parts) == 1:
        return int(parts[0])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    else:
        raise ValueError(f"Formato tempo non valido: {s}")

def seconds_to_mmss(seconds):
    """Converte un numero di secondi in una stringa nel formato mm:ss"""
    if not seconds:
        return "00:00"
    
    minutes = int(seconds / 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def seconds_to_hhmmss(seconds):
    """Converte un numero di secondi in una stringa nel formato hh:mm:ss"""
    if not seconds:
        return "00:00:00"
    
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def get_today_date_str():
    """Restituisce la data odierna nel formato YYYY-MM-DD"""
    return datetime.datetime.now().strftime("%Y-%m-%d")

def is_valid_date_str(date_str):
    """Verifica se una stringa è una data valida nel formato YYYY-MM-DD"""
    if not date_str:
        return False
    
    try:
        datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def parse_date_str(date_str, format="%Y-%m-%d"):
    """Converte una stringa data in un oggetto datetime"""
    try:
        return datetime.datetime.strptime(date_str, format)
    except ValueError:
        return None

def validate_pace(pace):
    """Valida il formato del ritmo (mm:ss)"""
    if not pace:
        return False
    
    pattern = r'^\d{1,2}:\d{2}$'
    return bool(re.match(pattern, pace))

def validate_speed(speed):
    """Valida il formato della velocità (km/h)"""
    if not speed:
        return False
    
    try:
        float(speed)
        return True
    except ValueError:
        return False

def validate_heart_rate(hr):
    """Valida il formato della frequenza cardiaca"""
    if not hr:
        return False
    
    # Formato semplice (es. 150)
    if hr.isdigit():
        return True
    
    # Formato intervallo (es. 140-160)
    pattern = r'^\d{2,3}-\d{2,3}$'
    if re.match(pattern, hr):
        return True
    
    # Formato percentuale (es. 70-80% max_hr)
    pattern = r'^\d{1,3}-\d{1,3}%\s+\w+$'
    if re.match(pattern, hr):
        return True
    
    return False

def format_workout_name(week, session, description):
    """Formatta il nome dell'allenamento nel formato standard"""
    week_str = str(week).zfill(2)
    session_str = str(session).zfill(2)
    return f"W{week_str}S{session_str} {description}"

def parse_workout_name(name):
    """Estrae settimana, sessione e descrizione da un nome di allenamento"""
    pattern = r'^W(\d{2})S(\d{2})\s+(.+)$'
    match = re.match(pattern, name)
    
    if match:
        week = int(match.group(1))
        session = int(match.group(2))
        description = match.group(3)
        return week, session, description
    
    return None, None, name

def load_yaml_file(file_path):
    """Carica un file YAML"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"Errore nel caricamento del file YAML: {str(e)}")
        return None

def save_yaml_file(data, file_path):
    """Salva dati in un file YAML"""
    try:
        with open(file_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        return True
    except Exception as e:
        logging.error(f"Errore nel salvataggio del file YAML: {str(e)}")
        return False

def show_error(title, message, parent=None):
    """Mostra una finestra di errore"""
    return messagebox.showerror(title, message, parent=parent)

def show_warning(title, message, parent=None):
    """Mostra una finestra di avviso"""
    return messagebox.showwarning(title, message, parent=parent)

def show_info(title, message, parent=None):
    """Mostra una finestra informativa"""
    return messagebox.showinfo(title, message, parent=parent)

def ask_yes_no(title, message, parent=None):
    """Mostra una finestra di conferma Sì/No"""
    return messagebox.askyesno(title, message, parent=parent)

def create_scrollable_frame(parent):
    """Crea un frame con barre di scorrimento"""
    # Crea un canvas con scrollbar
    canvas = tk.Canvas(parent)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    return scrollable_frame