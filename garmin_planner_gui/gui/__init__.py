#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sottopacchetto GUI per Garmin Planner

Questo pacchetto contiene tutti i componenti dell'interfaccia grafica
per l'applicazione Garmin Planner GUI.
"""

import os
import sys

# Assicurati che i percorsi siano corretti per le importazioni
package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

# Assicurati che la directory parent sia nel path
project_dir = os.path.dirname(package_dir)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)