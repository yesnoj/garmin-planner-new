#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pacchetto garmin_planner_gui - Interfaccia grafica per la gestione degli allenamenti Garmin

Questo pacchetto fornisce un'interfaccia grafica completa per gestire allenamenti
di corsa, ciclismo e nuoto, sincronizzandoli con Garmin Connect.
"""

import os
import sys

# Assicurati che il pacchetto planner sia nel path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Esporta la funzione main per facilitare l'importazione dall'esterno
from .main import main

__version__ = "0.1.0"