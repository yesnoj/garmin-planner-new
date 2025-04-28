#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Definizione degli stili per l'interfaccia Garmin Planner GUI
"""

import tkinter as tk
from tkinter import ttk
import os
import sys

# Colori moderni (ispirati a Garmin Connect)
COLORS = {
    "bg_main": "#f5f5f5",
    "bg_header": "#333333",
    "bg_light": "#ffffff",
    "accent": "#0076c0",  # Blu Garmin
    "accent_dark": "#005486",
    "accent_light": "#66a3d2",  # Versione più chiara del blu Garmin
    "text_light": "#ffffff",
    "text_dark": "#333333",
    "warmup": "#52b69a",   # Verde acqua 
    "interval": "#e07a5f", # Arancione 
    "recovery": "#81b29a", # Verde chiaro
    "cooldown": "#3d5a80", # Blu scuro
    "rest": "#98c1d9",     # Azzurro
    "repeat": "#5e548e",   # Viola
    "other": "#bdbdbd",    # Grigio
    "running": "#e63946",  # Rosso per la corsa
    "cycling": "#1d3557",  # Blu scuro per il ciclismo
    "swimming": "#457b9d", # Blu-verde per il nuoto
    "success": "#2a9d8f",  # Verde per successo
    "warning": "#f4a261",  # Arancione per warning
    "error": "#e76f51",    # Rosso per errore
}

# Icone per i diversi tipi di passi (emoji Unicode)
STEP_ICONS = {
    "warmup": "🔥",     # Fiamma per riscaldamento
    "interval": "⚡",   # Fulmine per intervallo
    "recovery": "🌊",   # Onda per recupero
    "cooldown": "❄️",   # Fiocco di neve per defaticamento
    "rest": "⏸️",       # Pausa per riposo
    "repeat": "🔄",     # Frecce circolari per ripetizione
    "other": "📝"       # Note per altro
}

# Icone per i diversi tipi di sport (emoji Unicode)
SPORT_ICONS = {
    "running": "🏃",    # Persona che corre
    "cycling": "🚴",    # Persona in bicicletta
    "swimming": "🏊"    # Persona che nuota
}

def setup_styles(config=None):
    """Configura gli stili dell'applicazione"""
    # Usa la configurazione predefinita se non fornita
    if config is None:
        config = {'ui_preferences': {'theme': 'default', 'font_size': 'medium'}}
    
    ui_prefs = config.get('ui_preferences', {})
    theme = ui_prefs.get('theme', 'default')
    font_size = ui_prefs.get('font_size', 'medium')
    
    # Determina le dimensioni del font
    if font_size == 'small':
        default_font = ('Arial', 9)
        heading_font = ('Arial', 12, 'bold')
        subheading_font = ('Arial', 11)
        button_font = ('Arial', 9)
        small_font = ('Arial', 8)
    elif font_size == 'large':
        default_font = ('Arial', 12)
        heading_font = ('Arial', 16, 'bold')
        subheading_font = ('Arial', 14)
        button_font = ('Arial', 12)
        small_font = ('Arial', 10)
    else:  # medium
        default_font = ('Arial', 10)
        heading_font = ('Arial', 14, 'bold')
        subheading_font = ('Arial', 12)
        button_font = ('Arial', 10)
        small_font = ('Arial', 9)
    
    style = ttk.Style()
    
    # Imposta il tema di base
    try:
        # Prova a utilizzare il tema "clam" che è più moderno
        style.theme_use("clam")
    except tk.TclError:
        # Se non disponibile, usa il tema predefinito
        pass
    
    # Colori in base al tema
    if theme == 'light':
        bg_color = COLORS["bg_light"]
        fg_color = COLORS["text_dark"]
        accent_color = COLORS["accent"]
    elif theme == 'dark':
        bg_color = COLORS["bg_header"]
        fg_color = COLORS["text_light"]
        accent_color = COLORS["accent_light"]
    else:  # default
        bg_color = COLORS["bg_main"]
        fg_color = COLORS["text_dark"]
        accent_color = COLORS["accent"]
    
    # Stile per il frame principale
    style.configure("TFrame", background=bg_color)
    
    # Stile per le etichette
    style.configure("TLabel", 
                   font=default_font,
                   background=bg_color, 
                   foreground=fg_color)
    
    # Stile per i bottoni
    style.configure("TButton", 
                   font=button_font, 
                   background=accent_color,
                   foreground=COLORS["text_light"])
    
    # Stile per i bottoni accentuati
    style.configure("Accent.TButton", 
                   font=button_font, 
                   background=COLORS["accent"],
                   foreground=COLORS["text_light"])
    
    # Stile per i bottoni di successo
    style.configure("Success.TButton", 
                   font=button_font, 
                   background=COLORS["success"],
                   foreground=COLORS["text_light"])
    
    # Stile per i bottoni di warning
    style.configure("Warning.TButton", 
                   font=button_font, 
                   background=COLORS["warning"],
                   foreground=COLORS["text_dark"])
    
    # Stile per i bottoni di errore
    style.configure("Error.TButton", 
                   font=button_font, 
                   background=COLORS["error"],
                   foreground=COLORS["text_light"])
    
    # Stile per le caselle di testo
    style.configure("TEntry", font=default_font)
    
    # Stile per i combobox
    style.configure("TCombobox", font=default_font)
    
    # Stile per le schede
    style.configure("TNotebook", background=bg_color)
    style.configure("TNotebook.Tab", 
                   font=button_font,
                   padding=[10, 5])
    
    # Stile per le barre di scorrimento
    style.configure("TScrollbar", background=bg_color)
    
    # Stile per i progressbar
    style.configure("TProgressbar", 
                   background=accent_color,
                   troughcolor=COLORS["bg_light"])
    
    # Stile per i separatori
    style.configure("TSeparator", background=COLORS["bg_header"])
    
    # Stile per i pannelli
    style.configure("TLabelframe", 
                   background=bg_color,
                   font=button_font)
    style.configure("TLabelframe.Label", 
                   background=bg_color,
                   font=button_font)
    
    # Stile per intestazioni
    style.configure("Heading.TLabel", 
                   font=heading_font,
                   background=bg_color)
    
    # Stile per sottotitoli
    style.configure("Subheading.TLabel", 
                   font=subheading_font,
                   background=bg_color)
    
    # Stile per il testo di stato
    style.configure("Status.TLabel", 
                   font=small_font,
                   background=bg_color)
    
    # Stile per il testo di istruzioni
    style.configure("Instructions.TLabel", 
                   font=default_font,
                   background=bg_color)
    
    # Stile per le tabelle (Treeview)
    style.configure("Treeview", 
                   font=default_font,
                   background=COLORS["bg_light"],
                   fieldbackground=COLORS["bg_light"])
    style.configure("Treeview.Heading", 
                   font=button_font)
                   
    # Stili specifici per il calendario
    style.configure("Today.TFrame", 
                    background=accent_color,
                    relief="raised")
    style.configure("Today.TLabel", 
                    background=accent_color,
                    foreground=COLORS["text_light"],
                    font=button_font)