#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script di installazione per Garmin Planner GUI
"""

import os
import sys
import subprocess
from setuptools import setup, find_packages

REQUIRED_PACKAGES = [
    'garth',
    'pyyaml',
    'pandas',
    'openpyxl',
    'tk',  # o 'tkinter' su alcune distribuzioni
]

OPTIONAL_PACKAGES = {
    'calendar': ['tkcalendar'],
}

def main():
    # Crea la directory gui se non esiste
    if not os.path.exists('gui'):
        os.makedirs('gui')
    
    setup(
        name="garmin_planner_gui",
        version="0.1.0",
        author="Garmin Planner GUI Developers",
        author_email="example@example.com",
        description="GUI for managing workouts with Garmin Connect",
        packages=find_packages(),
        install_requires=REQUIRED_PACKAGES,
        extras_require=OPTIONAL_PACKAGES,
        entry_points={
            'console_scripts': [
                'garmin-planner-gui=garmin_planner_gui:main',
            ],
        },
    )

if __name__ == "__main__":
    main()