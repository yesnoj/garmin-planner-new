#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import os
import re
import datetime

# Versione dell'applicazione
APP_VERSION = "1.0.0"

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='traintrack.log'
)

# Controlla le dipendenze opzionali
try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("openpyxl non disponibile. Alcune funzionalità di Excel saranno disabilitate.")

try:
    from tkcalendar import Calendar, DateEntry
    TKCALENDAR_AVAILABLE = True
except ImportError:
    TKCALENDAR_AVAILABLE = False
    print("tkcalendar non disponibile. Verrà utilizzato un selettore di date semplificato.")

# Colori moderni
COLORS = {
    "bg_main": "#f5f5f5",
    "bg_header": "#333333",
    "bg_light": "#ffffff",
    "accent": "#0076c0",  # Blu principale
    "accent_dark": "#005486",
    "accent_light": "#66a3d2",
    "text_light": "#ffffff",
    "text_dark": "#333333",
    
    # Colori specifici per sport
    "running": "#e07a5f",    # Arancione/Rosso
    "cycling": "#52b69a",    # Verde acqua
    "swimming": "#3d5a80",   # Blu marino
    
    # Colori per tipi di passo
    "warmup": "#52b69a",   # Verde acqua 
    "interval": "#e07a5f", # Arancione 
    "recovery": "#81b29a", # Verde chiaro
    "cooldown": "#3d5a80", # Blu scuro
    "rest": "#98c1d9",     # Azzurro
    "drill": "#ffcb77",    # Giallo intenso
    "repeat": "#5e548e",   # Viola
    "other": "#bdbdbd"     # Grigio
}

# Icone per i diversi tipi di passi (emoji Unicode)
STEP_ICONS = {
    "warmup": "🔥",     # Fiamma per riscaldamento
    "interval": "⚡",    # Fulmine per intervallo
    "recovery": "🌊",    # Onda per recupero
    "cooldown": "❄️",    # Fiocco di neve per defaticamento
    "rest": "⏸️",        # Pausa per riposo
    "drill": "🏋️",       # Esercizio
    "repeat": "🔄",      # Frecce circolari per ripetizione
    "other": "📝"        # Note per altro
}

# Icone per i diversi sport
SPORT_ICONS = {
    "running": "🏃",     # Persona che corre
    "cycling": "🚴",     # Persona in bicicletta
    "swimming": "🏊",    # Persona che nuota
    "general": "📊"      # Generico
}

# Configurazione di default
DEFAULT_CONFIG = {
    'paces': {
        'Z1': '6:30',
        'Z2': '6:00',
        'Z3': '5:30',
        'Z4': '5:00',
        'Z5': '4:30',
        'recovery': '7:00',
        'threshold': '5:10',
        'marathon': '5:20',
        'race_pace': '5:10',
    },
    'speeds': {
        'Z1': '15.0',
        'Z2': '20.0',
        'Z3': '25.0',
        'Z4': '30.0',
        'Z5': '35.0',
        'recovery': '12.0',
        'threshold': '28.0',
        'ftp': '32.0',
    },
    'swim_paces': {
        'Z1': '2:30',
        'Z2': '2:15',
        'Z3': '2:00',
        'Z4': '1:45',
        'Z5': '1:30',
        'recovery': '2:45',
        'threshold': '1:50',
        'race_pace': '1:40',
    },
    'heart_rates': {
        'max_hr': 180,
        'Z1_HR': '62-76% max_hr',
        'Z2_HR': '76-85% max_hr',
        'Z3_HR': '85-91% max_hr',
        'Z4_HR': '91-95% max_hr',
        'Z5_HR': '95-100% max_hr',
    },
    'margins': {
        'faster': '0:03',
        'slower': '0:03',
        'faster_spd': '2.0',
        'slower_spd': '2.0',
        'faster_swim': '0:05',
        'slower_swim': '0:05',
        'hr_up': 5,
        'hr_down': 5
    },
    'name_prefix': '',
    'athlete_name': 'Atleta',
    'sport_type': 'running',  # Default sport type
    'race_day': (datetime.datetime.now() + datetime.timedelta(days=90)).strftime('%Y-%m-%d'),
}