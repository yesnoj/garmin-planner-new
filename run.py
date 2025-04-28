#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script per avviare Garmin Planner GUI
"""

import os
import sys

# Assicurati che la directory padre sia nel path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Importa e avvia l'applicazione
from garmin_planner_gui import main

if __name__ == "__main__":
    main()