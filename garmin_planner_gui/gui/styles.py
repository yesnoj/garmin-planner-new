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

def setup_styles():
    """Configura gli stili dell'applicazione"""
    style = ttk.Style()
    
    # Imposta il tema di base
    try:
        # Prova a utilizzare il tema "clam" che è più moderno
        style.theme_use("clam")
    except tk.TclError:
        # Se non disponibile, usa il tema predefinito
        pass
    
    # Stile per il frame principale
    style.configure("TFrame", background=COLORS["bg_main"])
    
    # Stile per le etichette
    style.configure("TLabel", background=COLORS["bg_main"], font=("Arial", 10))
    
    # Stile per i bottoni
    style.configure("TButton", 
                   font=("Arial", 10), 
                   background=COLORS["accent"],
                   foreground=COLORS["text_light"])
    
    # Stile per i bottoni accentuati
    style.configure("Accent.TButton", 
                   font=("Arial", 10, "bold"), 
                   background=COLORS["accent"],
                   foreground=COLORS["text_light"])
    
    # Stile per i bottoni di successo
    style.configure("Success.TButton", 
                   font=("Arial", 10), 
                   background=COLORS["success"],
                   foreground=COLORS["text_light"])
    
    # Stile per i bottoni di warning
    style.configure("Warning.TButton", 
                   font=("Arial", 10), 
                   background=COLORS["warning"],
                   foreground=COLORS["text_dark"])
    
    # Stile per i bottoni di errore
    style.configure("Error.TButton", 
                   font=("Arial", 10), 
                   background=COLORS["error"],
                   foreground=COLORS["text_light"])
    
    # Stile per le caselle di testo
    style.configure("TEntry", font=("Arial", 10))
    
    # Stile per i combobox
    style.configure("TCombobox", font=("Arial", 10))
    
    # Stile per le schede
    style.configure("TNotebook", background=COLORS["bg_main"])
    style.configure("TNotebook.Tab", 
                   font=("Arial", 10, "bold"),
                   padding=[10, 5])
    
    # Stile per le barre di scorrimento
    style.configure("TScrollbar", background=COLORS["bg_light"])
    
    # Stile per i progressbar
    style.configure("TProgressbar", 
                   background=COLORS["accent"],
                   troughcolor=COLORS["bg_light"])
    
    # Stile per i separatori
    style.configure("TSeparator", background=COLORS["bg_header"])
    
    # Stile per i pannelli
    style.configure("TLabelframe", 
                   background=COLORS["bg_main"],
                   font=("Arial", 10, "bold"))
    style.configure("TLabelframe.Label", 
                   background=COLORS["bg_main"],
                   font=("Arial", 10, "bold"))
    
    # Stile per intestazioni
    style.configure("Heading.TLabel", 
                   font=("Arial", 14, "bold"),
                   background=COLORS["bg_main"])
    
    # Stile per sottotitoli
    style.configure("Subheading.TLabel", 
                   font=("Arial", 12),
                   background=COLORS["bg_main"])
    
    # Stile per il testo di stato
    style.configure("Status.TLabel", 
                   font=("Arial", 9),
                   background=COLORS["bg_main"])
    
    # Stile per il testo di istruzioni
    style.configure("Instructions.TLabel", 
                   font=("Arial", 10, "italic"),
                   background=COLORS["bg_main"])
    
    # Stile per le tabelle (Treeview)
    style.configure("Treeview", 
                   font=("Arial", 10),
                   background=COLORS["bg_light"],
                   fieldbackground=COLORS["bg_light"])
    style.configure("Treeview.Heading", 
                   font=("Arial", 10, "bold"))