#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pacchetto planner - Core per la gestione degli allenamenti Garmin

Questo pacchetto fornisce le funzionalità di base per interagire con Garmin Connect,
creare e modificare allenamenti, e pianificare sessioni di allenamento.
"""

import os
import sys

# Assicurati che il progetto principale sia nel path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)