#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Dialog per pianificare automaticamente gli allenamenti
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import logging
import re

class ScheduleDialog(tk.Toplevel):
    """Dialog per pianificare automaticamente gli allenamenti"""
    
    def __init__(self, parent, workouts=None):
        super().__init__(parent)
        self.parent = parent
        self.workouts = workouts or []
        self.result = None
        
        # Analisi degli allenamenti per determinare il numero di settimane e sessioni
        self.max_week, self.max_sessions_per_week = self.analyze_workouts()
        
        # Configurazione del dialog
        self.title("Pianificazione automatica allenamenti")
        self.geometry("550x400")
        self.configure(bg="#f5f5f5")
        
        # Rendi il dialog modale
        self.transient(parent)
        self.grab_set()
        
        # Inizializza l'interfaccia
        self.init_ui()
        
        # Centra il dialog
        self.center_window()
        
        # Attendi la chiusura
        self.wait_window()
    
    def analyze_workouts(self):
        """Analizza gli allenamenti per determinare numero di settimane e sessioni max per settimana"""
        max_week = 0
        sessions_by_week = {}
        
        for name, _ in self.workouts:
            match = re.match(r'W(\d{2})S(\d{2})\s', name)
            if match:
                week = int(match.group(1))
                session = int(match.group(2))
                
                if week > max_week:
                    max_week = week
                
                if week not in sessions_by_week:
                    sessions_by_week[week] = set()
                
                sessions_by_week[week].add(session)
        
        # Determina il numero massimo di sessioni in una settimana
        max_sessions = 0
        for week, sessions in sessions_by_week.items():
            if len(sessions) > max_sessions:
                max_sessions = len(sessions)
        
        logging.info(f"Analisi allenamenti: {max_week} settimane, max {max_sessions} sessioni per settimana")
        return max_week, max_sessions
    
    def center_window(self):
        """Centra il dialog sullo schermo"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Descrizione
        ttk.Label(main_frame, text="Pianificazione automatica degli allenamenti", 
                  font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        description = (
            f"Questo programma di allenamento contiene {self.max_week} settimane "
            f"con un massimo di {self.max_sessions_per_week} sessioni per settimana.\n\n"
            "Seleziona la data della gara e i giorni di allenamento preferiti."
        )
        ttk.Label(main_frame, text=description, wraplength=500, justify="left").pack(pady=(0, 20))
        
        # Frame per la data della gara
        race_frame = ttk.LabelFrame(main_frame, text="Data della gara")
        race_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Grid per la data della gara
        race_grid = ttk.Frame(race_frame, padding=10)
        race_grid.pack(fill=tk.X)
        
        ttk.Label(race_grid, text="Data gara:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        
        # Imposta come default una data a 3 mesi da oggi
        default_race_day = (datetime.datetime.today() + datetime.timedelta(days=90)).strftime("%Y-%m-%d")
        self.race_date_var = tk.StringVar(value=default_race_day)
        
        date_entry = ttk.Entry(race_grid, textvariable=self.race_date_var, width=15)
        date_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Pulsante calendario
        calendar_button = ttk.Button(race_grid, text="📅", width=3, 
                                    command=self.show_calendar)
        calendar_button.grid(row=0, column=2, sticky=tk.W, padx=(0, 5), pady=5)
        
        # Frame per i giorni preferiti
        days_frame = ttk.LabelFrame(main_frame, text="Giorni preferiti per l'allenamento")
        days_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Testo informativo
        ttk.Label(days_frame, text=f"Seleziona fino a {self.max_sessions_per_week} giorni per gli allenamenti:",
                  padding=(10, 5)).pack(anchor=tk.W)
        
        # Grid per i giorni
        days_grid = ttk.Frame(days_frame, padding=10)
        days_grid.pack(fill=tk.X)
        
        days_of_week = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        
        # Crea variabili e checkbox per ogni giorno
        self.day_vars = {}
        
        for i, day in enumerate(days_of_week):
            var = tk.BooleanVar(value=False)
            self.day_vars[i] = var  # 0 = Lunedì, 6 = Domenica
            
            ttk.Checkbutton(days_grid, text=day, variable=var, 
                           command=self.check_max_days).grid(
                row=i // 4, column=i % 4, sticky=tk.W, padx=10, pady=5)
        
        # Imposta valori di default comuni (mar, gio, dom)
        self.day_vars[1].set(True)  # Martedì
        self.day_vars[3].set(True)  # Giovedì
        self.day_vars[6].set(True)  # Domenica
        
        # Pulsanti per salvare/annullare
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Pianifica", 
                  command=self.on_ok, style="Accent.TButton").pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(button_frame, text="Annulla", 
                  command=self.on_cancel).pack(side=tk.LEFT, padx=5)
    
    def check_max_days(self):
        """Controlla che non siano selezionati più giorni del necessario"""
        selected_days = self.get_preferred_days()
        
        # Se sono selezionati troppi giorni
        if len(selected_days) > self.max_sessions_per_week:
            # Trova l'ultimo giorno selezionato
            for i in range(6, -1, -1):
                if i in selected_days:
                    # Deseleziona questo giorno
                    self.day_vars[i].set(False)
                    break
                    
            # Avvisa l'utente
            messagebox.showwarning("Troppi giorni", 
                                  f"Puoi selezionare al massimo {self.max_sessions_per_week} giorni di allenamento.", 
                                  parent=self)
    
    def show_calendar(self):
        """Mostra un selettore di data"""
        try:
            from tkcalendar import Calendar
            
            # Crea una finestra top-level
            top = tk.Toplevel(self)
            top.title("Seleziona data")
            top.geometry("350x300")
            top.transient(self)
            top.grab_set()
            
            # Data iniziale
            if self.race_date_var.get():
                try:
                    initial_date = datetime.datetime.strptime(self.race_date_var.get(), "%Y-%m-%d").date()
                except ValueError:
                    initial_date = datetime.date.today()
            else:
                initial_date = datetime.date.today()
            
            # Crea il calendario
            cal = Calendar(top, selectmode='day', year=initial_date.year, 
                          month=initial_date.month, day=initial_date.day,
                          date_pattern="yyyy-mm-dd")
            cal.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Funzione per selezionare la data
            def select_date():
                self.race_date_var.set(cal.get_date())
                top.destroy()
            
            # Pulsante per confermare
            ttk.Button(top, text="Seleziona", command=select_date).pack(pady=10)
            
        except ImportError:
            # Se tkcalendar non è disponibile, usa un semplice dialogo
            from tkinter import simpledialog
            
            date_str = simpledialog.askstring("Data", "Inserisci la data (YYYY-MM-DD):", 
                                            parent=self, initialvalue=self.race_date_var.get())
            if date_str:
                try:
                    # Verifica che sia una data valida
                    datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    self.race_date_var.set(date_str)
                except ValueError:
                    messagebox.showerror("Errore", "Formato data non valido. Usa YYYY-MM-DD.", parent=self)
                    self.show_calendar()
    
    def get_preferred_days(self):
        """Restituisce i giorni preferiti (0 = Lunedì, 6 = Domenica)"""
        return [day for day, var in self.day_vars.items() if var.get()]
    
    def validate_inputs(self):
        """Valida gli input del dialog"""
        # Controlla la data della gara
        race_date_str = self.race_date_var.get().strip()
        try:
            race_date = datetime.datetime.strptime(race_date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Errore", "La data della gara non è valida. Usa il formato YYYY-MM-DD.", parent=self)
            return False
        
        # Controlla che ci sia almeno un giorno selezionato
        if not self.get_preferred_days():
            messagebox.showerror("Errore", "Seleziona almeno un giorno preferito per l'allenamento.", parent=self)
            return False
        
        # Controlla che non ci siano più giorni del necessario
        if len(self.get_preferred_days()) > self.max_sessions_per_week:
            messagebox.showerror("Errore", 
                               f"Puoi selezionare al massimo {self.max_sessions_per_week} giorni di allenamento.", 
                               parent=self)
            return False
        
        # Tutto ok
        return True
    
    def on_ok(self):
        """Gestisce il pulsante OK"""
        if not self.validate_inputs():
            return
        
        # Ottieni i valori
        race_date = datetime.datetime.strptime(self.race_date_var.get().strip(), "%Y-%m-%d").date()
        preferred_days = self.get_preferred_days()
        
        # Crea il risultato
        self.result = {
            "race_date": race_date,
            "weeks": self.max_week,
            "preferred_days": preferred_days
        }
        
        # Chiudi il dialog
        self.destroy()
    
    def on_cancel(self):
        """Gestisce il pulsante Annulla"""
        self.result = None
        self.destroy()