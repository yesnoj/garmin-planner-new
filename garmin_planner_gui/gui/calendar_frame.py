#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Frame per la gestione del calendario di allenamenti
"""

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import calendar
import re
import logging
from .styles import COLORS, SPORT_ICONS
import json
import webbrowser

class CalendarFrame(ttk.Frame):
    """Frame per la gestione del calendario di allenamenti"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.garmin_client = None
        self.scheduled_workouts = []
        self.activities = []  # Nuova lista per memorizzare le attività
        
        # Mese e anno correnti per la visualizzazione
        self.current_month = datetime.datetime.now().month
        self.current_year = datetime.datetime.now().year
        
        # Flag per mostrare o nascondere le attività nel calendario
        self.show_activities = tk.BooleanVar(value=True)
        
        # Inizializza l'interfaccia
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia utente"""
        # Frame principale con padding
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Frame superiore per i controlli di navigazione
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Pulsanti per cambiare mese/anno
        ttk.Button(nav_frame, text="<<", width=3, command=self.prev_year).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text="<", width=3, command=self.prev_month).pack(side=tk.LEFT, padx=2)
        
        # Etichetta per mese/anno
        self.date_var = tk.StringVar()
        ttk.Label(nav_frame, textvariable=self.date_var, 
                 style="Heading.TLabel").pack(side=tk.LEFT, padx=10)
        
        # Pulsanti per cambiare mese/anno (avanti)
        ttk.Button(nav_frame, text=">", width=3, command=self.next_month).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_frame, text=">>", width=3, command=self.next_year).pack(side=tk.LEFT, padx=2)
        
        # Pulsante per tornare al mese corrente
        ttk.Button(nav_frame, text="Oggi", command=self.goto_today).pack(side=tk.LEFT, padx=(10, 0))
        
        # Checkbox per mostrare/nascondere le attività
        ttk.Checkbutton(nav_frame, text="Mostra attività", 
                       variable=self.show_activities, 
                       command=self.on_toggle_activities).pack(side=tk.LEFT, padx=(10, 0))
        
        # Pulsante per sincronizzare con Garmin Connect
        self.sync_button = ttk.Button(nav_frame, text="Sincronizza calendario", 
                                     command=self.sync_calendar)
        self.sync_button.pack(side=tk.RIGHT, padx=5)
        
        # Disabilitato fino al login
        self.sync_button['state'] = 'disabled'
        
        # Frame per il calendario
        calendar_frame = ttk.Frame(main_frame)
        calendar_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Intestazioni dei giorni della settimana
        day_headers = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
        
        # Frame per i nomi dei giorni
        days_frame = ttk.Frame(calendar_frame)
        days_frame.pack(fill=tk.X)
        
        # Grid per i giorni della settimana
        for i, day in enumerate(day_headers):
            day_label = ttk.Label(days_frame, text=day, anchor=tk.CENTER)
            day_label.grid(row=0, column=i, sticky=tk.W+tk.E)
            days_frame.columnconfigure(i, weight=1)
        
        # Frame per i giorni del mese
        self.month_frame = ttk.Frame(calendar_frame)
        self.month_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configura le colonne
        for i in range(7):
            self.month_frame.columnconfigure(i, weight=1)
        
        # Frame per i dettagli dell'allenamento selezionato
        details_frame = ttk.LabelFrame(main_frame, text="Dettagli allenamento")
        details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid per i dettagli
        self.details_grid = ttk.Frame(details_frame)
        self.details_grid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Etichette per i dettagli
        ttk.Label(self.details_grid, text="Data:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.detail_date_var = tk.StringVar()
        ttk.Label(self.details_grid, textvariable=self.detail_date_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(self.details_grid, text="Allenamento:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.detail_name_var = tk.StringVar()
        ttk.Label(self.details_grid, textvariable=self.detail_name_var).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(self.details_grid, text="Sport:").grid(row=2, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.detail_sport_var = tk.StringVar()
        ttk.Label(self.details_grid, textvariable=self.detail_sport_var).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(self.details_grid, text="ID:").grid(row=3, column=0, sticky=tk.W, padx=(0, 5), pady=2)
        self.detail_id_var = tk.StringVar()
        ttk.Label(self.details_grid, textvariable=self.detail_id_var).grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Pulsanti per gestire l'allenamento
        button_frame = ttk.Frame(details_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancella programmazione", 
                                      command=self.cancel_scheduled_workout)
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.move_button = ttk.Button(button_frame, text="Sposta a...", 
                                    command=self.move_scheduled_workout)
        self.move_button.pack(side=tk.LEFT, padx=5)
        
        # Disabilita inizialmente i pulsanti
        self.cancel_button['state'] = 'disabled'
        self.move_button['state'] = 'disabled'
        
        # Frame per la lista degli allenamenti
        workouts_frame = ttk.LabelFrame(main_frame, text="Allenamenti disponibili")
        workouts_frame.pack(fill=tk.BOTH, expand=True)
        
        # Filtro per la lista
        filter_frame = ttk.Frame(workouts_frame)
        filter_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        
        ttk.Label(filter_frame, text="Filtro:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_var = tk.StringVar()
        filter_entry = ttk.Entry(filter_frame, textvariable=self.filter_var, width=30)
        filter_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        # Associa evento di modifica del filtro
        self.filter_var.trace_add("write", lambda *args: self.update_workout_list())
        
        # Tipo di sport
        ttk.Label(filter_frame, text="Sport:").pack(side=tk.LEFT, padx=(10, 5))
        
        self.sport_filter_var = tk.StringVar(value="Tutti")
        sport_combo = ttk.Combobox(filter_frame, textvariable=self.sport_filter_var, 
                                  values=["Tutti", "Corsa", "Ciclismo", "Nuoto"], 
                                  width=10, state="readonly")
        sport_combo.pack(side=tk.LEFT)
        
        # Associa evento di modifica del filtro sport
        sport_combo.bind("<<ComboboxSelected>>", lambda e: self.update_workout_list())
        
        # Lista degli allenamenti
        list_frame = ttk.Frame(workouts_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Crea il treeview
        columns = ("name", "sport", "date")
        self.workouts_tree = ttk.Treeview(list_frame, columns=columns, show="headings", 
                                        selectmode="extended")
        
        # Intestazioni
        self.workouts_tree.heading("name", text="Nome")
        self.workouts_tree.heading("sport", text="Sport")
        self.workouts_tree.heading("date", text="Data")
        
        # Larghezze colonne
        self.workouts_tree.column("name", width=400)
        self.workouts_tree.column("sport", width=100)
        self.workouts_tree.column("date", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.workouts_tree.yview)
        self.workouts_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.workouts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pulsanti per gestire gli allenamenti
        workouts_buttons = ttk.Frame(workouts_frame)
        workouts_buttons.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.schedule_button = ttk.Button(workouts_buttons, text="Pianifica per...", 
                                        command=self.schedule_workout)
        self.schedule_button.pack(side=tk.LEFT, padx=(0, 5))
        
        self.refresh_button = ttk.Button(workouts_buttons, text="Aggiorna lista", 
                                       command=self.refresh_workouts)
        self.refresh_button.pack(side=tk.RIGHT)
        
        # Disabilita il pulsante di pianificazione fino al login
        self.schedule_button['state'] = 'disabled'
        
        self.delete_workout_button = ttk.Button(workouts_buttons, text="Elimina da Garmin", 
                                             command=self.delete_workout)
        self.delete_workout_button.pack(side=tk.LEFT, padx=5)

        self.delete_workout_button['state'] = 'disabled'

        # Associa evento di doppio click
        self.workouts_tree.bind("<Double-1>", lambda e: self.schedule_workout())
        
        # Aggiorna l'etichetta della data
        self.update_date_label()
        
        # Disegna il calendario
        self.draw_calendar()

    def debug_activities(self):
        """Visualizza informazioni di debug sulle attività nel mese corrente"""
        if not hasattr(self, 'activities') or not self.activities:
            logging.error("Nessuna attività disponibile per il debug")
            return
            
        # Crea una finestra di dialogo per visualizzare le informazioni
        debug_dialog = tk.Toplevel(self)
        debug_dialog.title("Debug Attività")
        debug_dialog.geometry("800x600")
        debug_dialog.transient(self)
        
        # Frame principale con padding
        main_frame = ttk.Frame(debug_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Intestazione
        ttk.Label(main_frame, text=f"Attività per {self.current_year}-{self.current_month}", 
                 style="Heading.TLabel").pack(pady=(0, 10))
        
        # Area di testo per le informazioni
        text_area = tk.Text(main_frame, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_area, orient=tk.VERTICAL, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Inserisci informazioni sulle attività
        text_area.insert(tk.END, f"Numero totale di attività: {len(self.activities)}\n\n")
        
        # Raggruppa le attività per data
        activities_by_date = {}
        for activity in self.activities:
            if 'startTimeLocal' in activity:
                date_str = activity.get('startTimeLocal', '').split('T')[0]
                if date_str not in activities_by_date:
                    activities_by_date[date_str] = []
                activities_by_date[date_str].append(activity)
        
        # Visualizza attività raggruppate per data
        for date_str, day_activities in sorted(activities_by_date.items()):
            text_area.insert(tk.END, f"\nData: {date_str} ({len(day_activities)} attività)\n")
            for i, activity in enumerate(day_activities):
                text_area.insert(tk.END, f"  {i+1}. Nome: {activity.get('activityName', 'Sconosciuto')}\n")
                text_area.insert(tk.END, f"     Tipo: {activity.get('activityType', {}).get('typeKey', 'Sconosciuto')}\n")
                text_area.insert(tk.END, f"     ID: {activity.get('activityId', 'Sconosciuto')}\n")
                text_area.insert(tk.END, f"     Inizio: {activity.get('startTimeLocal', 'Sconosciuto')}\n")
        
        # Informazioni sulla struttura delle attività
        if self.activities:
            text_area.insert(tk.END, "\n\nStruttura della prima attività:\n")
            first_activity = self.activities[0]
            for key, value in first_activity.items():
                text_area.insert(tk.END, f"  {key}: {value}\n")
        
        # Rendi l'area di testo di sola lettura
        text_area.configure(state=tk.DISABLED)
        
        # Pulsante per chiudere
        ttk.Button(main_frame, text="Chiudi", command=debug_dialog.destroy).pack(pady=(10, 0))

    def on_toggle_activities(self):
        """Gestisce il toggle per mostrare/nascondere le attività"""
        show = self.show_activities.get()
        logging.info(f"Toggle attività: {show}")
        
        # Se abbiamo attivato le attività e siamo loggati, sincronizza il calendario
        if show and self.garmin_client:
            self.sync_calendar(show_messages=False)
        else:
            # Altrimenti ridisegna semplicemente il calendario
            self.draw_calendar()

    def fetch_activities(self):
        """Recupera le attività da Garmin Connect"""
        if not self.garmin_client:
            logging.error("Nessun client Garmin disponibile")
            return
        
        logging.info("Recupero attività...")
        
        try:
            # Calcola le date di inizio e fine per il mese corrente
            start_date = datetime.date(self.current_year, self.current_month, 1)
            _, last_day = calendar.monthrange(self.current_year, self.current_month)
            end_date = datetime.date(self.current_year, self.current_month, last_day)
            
            # Formatta le date
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')
            
            logging.info(f"Ricerca attività dal {start_str} al {end_str}")
            
            # Recupera le attività
            activities = self.garmin_client.get_activities(
                start_date=start_str,
                end_date=end_str,
                limit=100  # Limite alto per recuperare più attività possibili
            )
            
            # Imposta le attività recuperate
            self.activities = activities if activities else []
            
            logging.info(f"Recuperate {len(self.activities)} attività")
            
            # Log dettagli delle attività
            for activity in self.activities[:5]:  # Log solo prime 5 per brevità
                activity_date = activity.get('startTimeLocal', '').split('T')[0] if 'startTimeLocal' in activity else 'Sconosciuta'
                activity_name = activity.get('activityName', 'Sconosciuta')
                activity_type = activity.get('activityType', {}).get('typeKey', 'Sconosciuto')
                logging.info(f"Attività: {activity_name} ({activity_type}) il {activity_date}")
            
            if len(self.activities) > 5:
                logging.info(f"... e altre {len(self.activities) - 5} attività")
                
        except Exception as e:
            logging.error(f"Errore nel recupero delle attività: {str(e)}")
            self.activities = []

    def update_date_label(self):
        """Aggiorna l'etichetta con mese e anno correnti"""
        month_name = calendar.month_name[self.current_month]
        self.date_var.set(f"{month_name} {self.current_year}")
    
    def prev_month(self):
        """Passa al mese precedente"""
        self.current_month -= 1
        if self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        
        self.update_date_label()
        
        # Se è attiva l'opzione "Mostra attività", sincronizza automaticamente il calendario
        if hasattr(self, 'show_activities') and self.show_activities.get() and self.garmin_client:
            self.sync_calendar(show_messages=False)
        else:
            self.draw_calendar()
    
    def next_month(self):
        """Passa al mese successivo"""
        self.current_month += 1
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        
        self.update_date_label()
        
        # Se è attiva l'opzione "Mostra attività", sincronizza automaticamente il calendario
        if hasattr(self, 'show_activities') and self.show_activities.get() and self.garmin_client:
            self.sync_calendar(show_messages=False)
        else:
            self.draw_calendar()
    
    def prev_year(self):
        """Passa all'anno precedente"""
        self.current_year -= 1
        self.update_date_label()
        
        # Se è attiva l'opzione "Mostra attività", sincronizza automaticamente il calendario
        if hasattr(self, 'show_activities') and self.show_activities.get() and self.garmin_client:
            self.sync_calendar(show_messages=False)
        else:
            self.draw_calendar()

    def next_year(self):
        """Passa all'anno successivo"""
        self.current_year += 1
        self.update_date_label()
        
        # Se è attiva l'opzione "Mostra attività", sincronizza automaticamente il calendario
        if hasattr(self, 'show_activities') and self.show_activities.get() and self.garmin_client:
            self.sync_calendar(show_messages=False)
        else:
            self.draw_calendar()
    
    def goto_today(self):
        """Torna al mese e anno correnti"""
        today = datetime.datetime.now()
        self.current_month = today.month
        self.current_year = today.year
        
        self.update_date_label()
        
        # Se è attiva l'opzione "Mostra attività", sincronizza automaticamente il calendario
        if hasattr(self, 'show_activities') and self.show_activities.get() and self.garmin_client:
            self.sync_calendar(show_messages=False)
        else:
            self.draw_calendar()
    
    def draw_calendar(self):
        """Disegna il calendario del mese corrente"""
        logging.info(f"Drawing calendar for {self.current_year}-{self.current_month}")
        
        # Pulisci il frame attuale
        for widget in self.month_frame.winfo_children():
            widget.destroy()
        
        # Ottieni il primo giorno del mese
        first_day = datetime.date(self.current_year, self.current_month, 1)
        
        # Ottieni il numero di giorni nel mese
        _, num_days = calendar.monthrange(self.current_year, self.current_month)
        
        # Ottieni il giorno della settimana del primo giorno (0 = lunedì in calendar.monthrange)
        first_weekday = first_day.weekday()
        
        # Log workouts that should be in this month for debugging
        if self.scheduled_workouts:
            this_month_workouts = []
            for workout in self.scheduled_workouts:
                workout_date = workout.get('date', '')
                if workout_date.startswith(f"{self.current_year}-{self.current_month:02d}-"):
                    this_month_workouts.append(workout)
            
            logging.info(f"Found {len(this_month_workouts)} workouts for {self.current_year}-{self.current_month}")
            for workout in this_month_workouts:
                logging.info(f"  Workout in current month: {workout.get('title')} on {workout.get('date')}")
        else:
            logging.info("No scheduled workouts found for any month")
        
        # Disegna i giorni
        for day in range(1, num_days + 1):
            # Calcola riga e colonna
            row = (first_weekday + day - 1) // 7
            col = (first_weekday + day - 1) % 7
            
            # Crea un frame per il giorno
            day_frame = ttk.Frame(self.month_frame, borderwidth=1, relief="solid")
            day_frame.grid(row=row, column=col, sticky="nsew", padx=1, pady=1)
            
            # Assicurati che tutti i frame dei giorni abbiano la stessa altezza
            self.month_frame.rowconfigure(row, weight=1, minsize=80)
            
            # Crea l'etichetta con il numero del giorno
            day_label = ttk.Label(day_frame, text=str(day), anchor=tk.NW, padding=(5, 5, 0, 0))
            day_label.pack(fill=tk.X)
            
            # Formatta la data completa
            full_date = f"{self.current_year}-{self.current_month:02d}-{day:02d}"
            
            # Verifica se è oggi
            today = datetime.date.today()
            is_today = (self.current_year == today.year and 
                        self.current_month == today.month and
                        day == today.day)
            
            if is_today:
                day_frame.configure(style="Today.TFrame")
                day_label.configure(style="Today.TLabel")
            
            # Crea un frame per gli allenamenti
            workouts_container = ttk.Frame(day_frame)
            workouts_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
            
            # Aggiungi gli allenamenti programmati per questo giorno
            self.add_workouts_to_day(workouts_container, full_date)
            
            # Associa un evento di click al giorno
            day_frame.bind("<Button-1>", lambda e, d=full_date: self.on_day_click(d))
        
        logging.info("Calendar drawing completed")
    


    def add_workouts_to_day(self, container, date):
        """Aggiungi gli allenamenti programmati e le attività a un giorno"""
        # Filtra gli allenamenti per questa data
        day_workouts = [w for w in self.scheduled_workouts if w.get('date') == date]
        
        # Filtra le attività per questa data (se l'opzione è attiva)
        day_activities = []
        if hasattr(self, 'show_activities') and self.show_activities.get() and hasattr(self, 'activities') and self.activities:
            for activity in self.activities:
                # Le attività hanno una data in formato "2025-04-29 20:05:43"
                # Dobbiamo confrontare solo la parte della data (YYYY-MM-DD) con il formato del calendario
                activity_date = None
                if 'startTimeLocal' in activity:
                    # Estrai solo la parte della data (prima dello spazio)
                    activity_date = activity['startTimeLocal'].split(' ')[0]
                    
                # Confronta la data dell'attività con la data del calendario
                if activity_date == date:
                    day_activities.append(activity)
                    logging.debug(f"Aggiunta attività '{activity.get('activityName', 'Sconosciuta')}' per la data {date}")
        
        # Debug logging
        if day_workouts:
            logging.info(f"Aggiunta di {len(day_workouts)} allenamenti per {date}")
            for workout in day_workouts:
                logging.info(f"  Aggiunta allenamento: {workout.get('title')} (ID: {workout.get('workoutId')})")
            
        if day_activities:
            logging.info(f"Aggiunta di {len(day_activities)} attività per {date}")
            for activity in day_activities:
                activity_name = activity.get('activityName', 'Sconosciuta')
                activity_id = activity.get('activityId', 'Sconosciuto')
                logging.info(f"  Aggiunta attività: {activity_name} (ID: {activity_id})")
        
        # Combina gli elementi (allenamenti prima, poi attività)
        all_items = day_workouts + day_activities
        
        # Se non ci sono elementi, esci
        if not all_items:
            return
        
        # Aggiungi al massimo i primi 3 elementi, per non sovraffollare
        for i, item in enumerate(all_items[:3]):
            # Crea un frame per l'elemento
            item_frame = ttk.Frame(container)
            item_frame.pack(fill=tk.X, pady=1)
            
            # Determina se è un allenamento o un'attività
            is_activity = item in day_activities
            
            if is_activity:
                # È un'attività
                activity = item
                # Determina il tipo di sport
                sport_type = 'running'  # Default
                if 'activityType' in activity and 'typeKey' in activity['activityType']:
                    sport_type = activity['activityType']['typeKey'].lower()
                
                # Ottieni il nome dell'attività
                name = activity.get('activityName', 'Attività sconosciuta')
                if len(name) > 25:
                    name = name[:22] + "..."
                
                # Stile speciale per le attività (altro colore o icona diversa)
                icon = SPORT_ICONS.get(sport_type, "•")
                activity_label = ttk.Label(item_frame, text=f"✓ {icon} {name}", anchor=tk.W, foreground=COLORS["success"])
                activity_label.pack(fill=tk.X)
                
                # Associa evento di click
                item_frame.bind("<Button-1>", 
                             lambda e, a=activity: self.show_activity_details(a))
                activity_label.bind("<Button-1>", 
                                 lambda e, a=activity: self.show_activity_details(a))
            else:
                # È un allenamento programmato (codice esistente)
                workout = item
                sport_type = workout.get('sportTypeKey', 'running')
                icon = SPORT_ICONS.get(sport_type, "•")
                name = workout.get('title', 'Sconosciuto')
                
                if len(name) > 25:
                    name = name[:22] + "..."
                
                workout_label = ttk.Label(item_frame, text=f"{icon} {name}", anchor=tk.W)
                workout_label.pack(fill=tk.X)
                
                # Associa evento di click
                item_frame.bind("<Button-1>", 
                             lambda e, w=workout: self.show_workout_details(w))
                workout_label.bind("<Button-1>", 
                                 lambda e, w=workout: self.show_workout_details(w))
        
        # Se ci sono più di 3 elementi, mostra quanti ne mancano
        if len(all_items) > 3:
            more_label = ttk.Label(container, 
                                  text=f"+ altri {len(all_items) - 3}...", 
                                  anchor=tk.W)
            more_label.pack(fill=tk.X)


    def show_activity_details(self, activity):
        """Mostra i dettagli di un'attività"""
        # Creazione di una finestra di dialogo per i dettagli dell'attività
        details_dialog = tk.Toplevel(self)
        details_dialog.title("Dettagli attività")
        details_dialog.geometry("500x400")
        details_dialog.transient(self)
        details_dialog.grab_set()
        
        # Frame principale con padding
        main_frame = ttk.Frame(details_dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Intestazione con nome attività
        activity_name = activity.get('activityName', 'Attività sconosciuta')
        ttk.Label(main_frame, text=activity_name, style="Heading.TLabel").pack(fill=tk.X, pady=(0, 10))
        
        # Griglia per i dettagli
        details_frame = ttk.Frame(main_frame)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Data e ora
        start_time_local = activity.get('startTimeLocal', '')
        ttk.Label(details_frame, text="Data e ora:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(details_frame, text=start_time_local).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Tipo di sport
        sport_type = "Sconosciuto"
        if 'activityType' in activity and 'typeKey' in activity['activityType']:
            sport_type = activity['activityType']['typeKey']
        ttk.Label(details_frame, text="Sport:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=5)
        ttk.Label(details_frame, text=sport_type).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Distanza
        distance = activity.get('distance', 0)
        if distance:
            distance_km = round(distance / 1000, 2)
            ttk.Label(details_frame, text="Distanza:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=5)
            ttk.Label(details_frame, text=f"{distance_km} km").grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Durata
        duration = activity.get('duration', 0)
        if duration:
            # Formatta come ore:minuti:secondi
            hours = int(duration // 3600)
            minutes = int((duration % 3600) // 60)
            seconds = int(duration % 60)
            
            if hours > 0:
                duration_fmt = f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                duration_fmt = f"{minutes:02d}:{seconds:02d}"
                
            ttk.Label(details_frame, text="Durata:").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=5)
            ttk.Label(details_frame, text=duration_fmt).grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Frequenza cardiaca
        avg_hr = activity.get('averageHR')
        max_hr = activity.get('maxHR')
        if avg_hr or max_hr:
            hr_text = ""
            if avg_hr:
                hr_text += f"Media: {avg_hr} bpm"
            if max_hr:
                if hr_text:
                    hr_text += ", "
                hr_text += f"Max: {max_hr} bpm"
            
            ttk.Label(details_frame, text="Frequenza cardiaca:").grid(row=4, column=0, sticky=tk.W, padx=(0, 10), pady=5)
            ttk.Label(details_frame, text=hr_text).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # Calorie
        calories = activity.get('calories', 0)
        if calories:
            ttk.Label(details_frame, text="Calorie:").grid(row=5, column=0, sticky=tk.W, padx=(0, 10), pady=5)
            ttk.Label(details_frame, text=f"{calories} kcal").grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Informazioni specifiche per il nuoto
        if sport_type == 'lap_swimming':
            # Vasche
            active_lengths = activity.get('activeLengths')
            if active_lengths:
                ttk.Label(details_frame, text="Vasche:").grid(row=6, column=0, sticky=tk.W, padx=(0, 10), pady=5)
                ttk.Label(details_frame, text=str(active_lengths)).grid(row=6, column=1, sticky=tk.W, pady=5)
            
            # SWOLF
            avg_swolf = activity.get('averageSwolf')
            if avg_swolf:
                ttk.Label(details_frame, text="SWOLF medio:").grid(row=7, column=0, sticky=tk.W, padx=(0, 10), pady=5)
                ttk.Label(details_frame, text=str(avg_swolf)).grid(row=7, column=1, sticky=tk.W, pady=5)
        
        # Pulsante per visualizzare su Garmin Connect
        def open_in_browser():
            """Apre l'attività in Garmin Connect"""
            import webbrowser
            activity_id = activity.get('activityId')
            if activity_id:
                url = f"https://connect.garmin.com/modern/activity/{activity_id}"
                webbrowser.open(url)
        
        # Pulsanti
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        garmin_button = ttk.Button(button_frame, text="Visualizza su Garmin Connect", command=open_in_browser)
        garmin_button.pack(side=tk.LEFT, padx=(0, 5))
        
        close_button = ttk.Button(button_frame, text="Chiudi", command=details_dialog.destroy)
        close_button.pack(side=tk.LEFT)

    
    def on_day_click(self, date):
        """Gestisce il click su un giorno"""
        # Mostra gli allenamenti per questa data
        self.show_day_workouts(date)
    
    def show_day_workouts(self, date):
        """Mostra gli allenamenti per una data specifica"""
        # Filtra gli allenamenti per questa data
        day_workouts = [w for w in self.scheduled_workouts if w.get('date') == date]
        
        # Se non ci sono allenamenti, mostra un messaggio
        if not day_workouts:
            messagebox.showinfo("Nessun allenamento", 
                               f"Nessun allenamento programmato per {date}", 
                               parent=self)
            return
        
        # Se c'è un solo allenamento, mostra i dettagli
        if len(day_workouts) == 1:
            self.show_workout_details(day_workouts[0])
            return
        
        # Se ci sono più allenamenti, mostra una finestra di selezione
        select_dialog = tk.Toplevel(self)
        select_dialog.title(f"Allenamenti per {date}")
        select_dialog.geometry("400x300")
        select_dialog.transient(self)
        select_dialog.grab_set()
        
        # Frame per la lista
        list_frame = ttk.Frame(select_dialog, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Intestazione
        ttk.Label(list_frame, text=f"Allenamenti programmati per {date}:", 
                 style="Heading.TLabel").pack(pady=(0, 10))
        
        # Lista
        listbox = tk.Listbox(list_frame, height=10, width=50)
        listbox.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(listbox, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Aggiungi gli allenamenti
        for workout in day_workouts:
            sport_type = workout.get('sportTypeKey', 'running')
            icon = SPORT_ICONS.get(sport_type, "•")
            name = workout.get('title', 'Sconosciuto')
            
            listbox.insert(tk.END, f"{icon} {name}")
        
        # Associa evento di doppio click
        listbox.bind("<Double-1>", lambda e: on_select())
        
        # Pulsanti
        button_frame = ttk.Frame(select_dialog, padding=10)
        button_frame.pack(fill=tk.X)
        
        def on_select():
            # Ottieni l'indice selezionato
            selection = listbox.curselection()
            if not selection:
                return
            
            # Ottieni l'allenamento
            workout = day_workouts[selection[0]]
            
            # Chiudi il dialog
            select_dialog.destroy()
            
            # Mostra i dettagli
            self.show_workout_details(workout)
        
        ttk.Button(button_frame, text="Seleziona", command=on_select).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Annulla", 
                  command=select_dialog.destroy).pack(side=tk.LEFT)
    
    def show_workout_details(self, workout):
        """Mostra i dettagli di un allenamento"""
        # Aggiorna le variabili per i dettagli
        self.detail_date_var.set(workout.get('date', ''))
        self.detail_name_var.set(workout.get('title', 'Sconosciuto'))
        
        sport_type = workout.get('sportTypeKey', 'running')
        icon = SPORT_ICONS.get(sport_type, "•")
        self.detail_sport_var.set(f"{icon} {sport_type.capitalize()}")
        
        schedule_id = workout.get('id', '')
        workout_id = workout.get('workoutId', '')
        self.detail_id_var.set(f"Schedule: {schedule_id}, Workout: {workout_id}")
        
        # Abilita i pulsanti
        self.cancel_button['state'] = 'normal'
        self.move_button['state'] = 'normal'
        
        # Salva l'allenamento corrente
        self.current_workout = workout
    
    def cancel_scheduled_workout(self):
        """Cancella la programmazione di un allenamento"""
        # Verifica che sia selezionato un allenamento
        if not hasattr(self, 'current_workout'):
            return
        
        # Ottieni l'ID
        schedule_id = self.current_workout.get('id')
        name = self.current_workout.get('title', 'Sconosciuto')
        
        # Chiedi conferma
        if not messagebox.askyesno("Conferma cancellazione", 
                                 f"Sei sicuro di voler cancellare l'allenamento '{name}'?", 
                                 parent=self):
            return

        try:
            # Cancella la programmazione
            if self.garmin_client:
                self.garmin_client.unschedule_workout(schedule_id)
                
                # Aggiorna la lista
                self.fetch_scheduled_workouts()
                
                # Ridisegna il calendario
                self.draw_calendar()
                
                # Pulisci i dettagli
                self.clear_workout_details()
                
                # Mostra messaggio di conferma
                messagebox.showinfo("Operazione completata", 
                                   f"Allenamento '{name}' cancellato dal calendario", 
                                   parent=self)
            else:
                messagebox.showerror("Errore", 
                                    "Devi essere connesso a Garmin Connect", 
                                    parent=self)
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Impossibile cancellare l'allenamento: {str(e)}", 
                               parent=self)
    
    def move_scheduled_workout(self):
        """Sposta un allenamento programmato a un'altra data"""
        # Verifica che sia selezionato un allenamento
        if not hasattr(self, 'current_workout'):
            return
        
        # Ottieni i dati
        schedule_id = self.current_workout.get('id')
        workout_id = self.current_workout.get('workoutId')
        name = self.current_workout.get('title', 'Sconosciuto')
        current_date = self.current_workout.get('date', '')
        
        # Chiedi la nuova data
        new_date = self.ask_for_date(f"Nuova data per '{name}'",
                                   f"Inserisci la nuova data per l'allenamento (attualmente {current_date}):",
                                   current_date)
        
        if not new_date:
            return
        
        try:
            # Cancella la programmazione attuale
            if self.garmin_client:
                self.garmin_client.unschedule_workout(schedule_id)
                
                # Programma di nuovo per la nuova data
                self.garmin_client.schedule_workout(workout_id, new_date)
                
                # Aggiorna la lista
                self.fetch_scheduled_workouts()
                
                # Ridisegna il calendario
                self.draw_calendar()
                
                # Pulisci i dettagli
                self.clear_workout_details()
                
                # Mostra messaggio di conferma
                messagebox.showinfo("Operazione completata", 
                                   f"Allenamento '{name}' spostato dal {current_date} al {new_date}", 
                                   parent=self)
            else:
                messagebox.showerror("Errore", 
                                    "Devi essere connesso a Garmin Connect", 
                                    parent=self)
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Impossibile spostare l'allenamento: {str(e)}", 
                               parent=self)
    
    def schedule_workout(self):
        """Pianifica un allenamento"""
        # Verifica che sia selezionato un allenamento
        selection = self.workouts_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", 
                                 "Seleziona un allenamento da pianificare", 
                                 parent=self)
            return
        
        # Ottieni l'allenamento
        item = selection[0]
        values = self.workouts_tree.item(item, "values")
        name = values[0]
        workout_id = self.workouts_tree.item(item, "tags")[0]
        
        # Chiedi la data
        date = self.ask_for_date("Data pianificazione", 
                               f"Inserisci la data per l'allenamento '{name}':")
        
        if not date:
            return
        
        try:
            # Programma l'allenamento
            if self.garmin_client:
                self.garmin_client.schedule_workout(workout_id, date)
                
                # Aggiorna la lista
                self.fetch_scheduled_workouts()
                
                # Ridisegna il calendario
                self.draw_calendar()
                
                # Mostra messaggio di conferma
                messagebox.showinfo("Operazione completata", 
                                   f"Allenamento '{name}' pianificato per {date}", 
                                   parent=self)
            else:
                messagebox.showerror("Errore", 
                                    "Devi essere connesso a Garmin Connect", 
                                    parent=self)
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Impossibile pianificare l'allenamento: {str(e)}", 
                               parent=self)
    
    def ask_for_date(self, title, prompt, initial_date=None):
        """Chiede una data utilizzando un calendario se disponibile, altrimenti un semplice input"""
        # Se non è specificata una data iniziale, usa oggi
        if not initial_date:
            initial_date = datetime.date.today().strftime("%Y-%m-%d")
        
        try:
            # Prova a utilizzare il widget Calendar
            from tkcalendar import Calendar
            
            date_dialog = tk.Toplevel(self)
            date_dialog.title(title)
            date_dialog.geometry("300x350")
            date_dialog.transient(self)
            date_dialog.grab_set()
            
            # Label con le istruzioni
            ttk.Label(date_dialog, text=prompt, 
                    wraplength=280).pack(pady=(10, 5), padx=10)
            
            # Estrai anno, mese e giorno
            try:
                year, month, day = map(int, initial_date.split("-"))
            except:
                today = datetime.date.today()
                year, month, day = today.year, today.month, today.day
            
            # Crea il calendario
            cal = Calendar(date_dialog, selectmode='day', 
                          year=year, month=month, day=day, 
                          date_pattern="yyyy-mm-dd")
            cal.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
            
            # Variabile per memorizzare il risultato
            result = {"date": None, "confirmed": False}
            
            # Funzione per confermare
            def on_ok():
                result["date"] = cal.get_date()
                result["confirmed"] = True
                date_dialog.destroy()
            
            # Funzione per annullare
            def on_cancel():
                date_dialog.destroy()
            
            # Pulsanti
            buttons = ttk.Frame(date_dialog)
            buttons.pack(pady=(0, 10), padx=10, fill=tk.X)
            
            ttk.Button(buttons, text="OK", command=on_ok).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(buttons, text="Annulla", command=on_cancel).pack(side=tk.LEFT)
            
            # Attendi la chiusura del dialog
            self.wait_window(date_dialog)
            
            # Restituisci la data se confermata
            if result["confirmed"]:
                return result["date"]
            return None
            
        except ImportError:
            # Se il widget Calendar non è disponibile, usa un semplice input
            from tkinter import simpledialog
            
            date = simpledialog.askstring(title, prompt, 
                                        parent=self, initialvalue=initial_date)
            
            # Verifica che sia una data valida
            if date:
                try:
                    # Prova a convertire in un oggetto data
                    year, month, day = map(int, date.split("-"))
                    datetime.date(year, month, day)
                    return date
                except:
                    messagebox.showerror("Formato data non valido", 
                                       "Inserisci la data nel formato YYYY-MM-DD", 
                                       parent=self)
                    return self.ask_for_date(title, prompt, initial_date)
            
            return None
    
    def clear_workout_details(self):
        """Pulisce i dettagli dell'allenamento"""
        self.detail_date_var.set("")
        self.detail_name_var.set("")
        self.detail_sport_var.set("")
        self.detail_id_var.set("")
        
        # Disabilita i pulsanti
        self.cancel_button['state'] = 'disabled'
        self.move_button['state'] = 'disabled'
        
        # Rimuovi l'allenamento corrente
        if hasattr(self, 'current_workout'):
            del self.current_workout


    def sync_calendar(self, show_messages=True):
        """Sincronizza il calendario con Garmin Connect"""
        logging.info(f"sync_calendar chiamato: garmin_client è {'presente' if self.garmin_client else 'assente'}")
        if not self.garmin_client:
            if show_messages:
                messagebox.showerror("Errore", 
                                   "Devi essere connesso a Garmin Connect", 
                                   parent=self)
            return
        
        # Mostra indicatore di progresso
        try:
            # Crea una finestra di progresso
            if show_messages:
                progress = tk.Toplevel(self)
                progress.title("Sincronizzazione in corso")
                progress.geometry("300x100")
                progress.transient(self)
                progress.grab_set()
                
                # Etichetta
                ttk.Label(progress, text="Sincronizzazione del calendario in corso...").pack(pady=(20, 10))
                
                # Barra di progresso
                progressbar = ttk.Progressbar(progress, mode='indeterminate')
                progressbar.pack(fill=tk.X, padx=20)
                progressbar.start()
                
                # Aggiorna la finestra
                progress.update()
            else:
                progress = None
            
            try:
                # TEST DIRECT CALENDAR ACCESS
                # Try to get calendar data for the current month
                current_month = datetime.datetime.now().month
                current_year = datetime.datetime.now().year
                
                logging.info(f"Trying direct calendar access for {current_year}-{current_month}")
                try:
                    direct_response = self.garmin_client.get_calendar(current_year, current_month)
                    logging.info(f"Direct calendar response: {json.dumps(direct_response, indent=2)}")
                    
                    # Check if there are any calendar items
                    calendar_items = direct_response.get('calendarItems', [])
                    workout_items = [item for item in calendar_items if item.get('itemType') == 'workout']
                    logging.info(f"Found {len(workout_items)} workout items directly in calendar")
                    
                    # Log details of each workout found
                    for item in workout_items:
                        workout_id = item.get('workoutId', 'Unknown')
                        workout_name = item.get('title', 'Untitled')
                        workout_date = item.get('date', 'No date')
                        logging.info(f"Found workout: {workout_name} (ID: {workout_id}) on {workout_date}")
                except Exception as e:
                    logging.error(f"Error in direct calendar access: {str(e)}")
                
                # Now we proceed with the normal scheduled workouts fetch
                logging.info("Recupero degli allenamenti programmati...")
                try:
                    self.fetch_scheduled_workouts()
                except Exception as sched_err:
                    logging.error(f"Errore nel recupero degli allenamenti programmati: {str(sched_err)}")
                    if show_messages:
                        messagebox.showerror("Errore", 
                                          f"Impossibile recuperare gli allenamenti programmati: {str(sched_err)}", 
                                          parent=self)
                    raise
                
                # Recupera anche le attività
                logging.info("Recupero delle attività...")
                try:
                    self.fetch_activities()
                except Exception as act_err:
                    logging.error(f"Errore nel recupero delle attività: {str(act_err)}")
                    if show_messages:
                        messagebox.showwarning("Avviso", 
                                            f"Impossibile recuperare le attività: {str(act_err)}", 
                                            parent=self)
                    # Continuiamo comunque, perché gli allenamenti programmati sono più importanti
                
                # Aggiorna la lista degli allenamenti disponibili
                logging.info("Recupero degli allenamenti disponibili...")
                try:
                    self.fetch_available_workouts()
                except Exception as avail_err:
                    logging.error(f"Errore nel recupero degli allenamenti disponibili: {str(avail_err)}")
                    if show_messages:
                        messagebox.showerror("Errore", 
                                          f"Impossibile recuperare gli allenamenti disponibili: {str(avail_err)}", 
                                          parent=self)
                    # Continuiamo comunque, perché gli allenamenti programmati sono più importanti
                
                # Ridisegna il calendario
                logging.info("Aggiornamento grafico del calendario...")
                try:
                    # Log how many workouts we're going to display
                    logging.info(f"Drawing calendar with {len(self.scheduled_workouts)} scheduled workouts and {len(self.activities)} activities")
                    self.draw_calendar()
                except Exception as draw_err:
                    logging.error(f"Errore nel ridisegno del calendario: {str(draw_err)}")
                    # Non blocchiamo l'operazione per un errore di disegno
                
                # Mostra messaggio di conferma solo se richiesto
                if show_messages:
                    messagebox.showinfo("Sincronizzazione completata", 
                                      "Calendario sincronizzato con Garmin Connect", 
                                      parent=self)
                
                logging.info("Sincronizzazione del calendario completata con successo")
                
            except Exception as e:
                logging.error(f"Errore durante la sincronizzazione del calendario: {str(e)}")
                if show_messages:
                    messagebox.showerror("Errore", 
                                       f"Impossibile sincronizzare il calendario: {str(e)}", 
                                       parent=self)
            
        finally:
            # Chiudi la finestra di progresso se è stata creata
            if show_messages and 'progress' in locals() and progress:
                try:
                    progress.destroy()
                except:
                    pass

    def fetch_scheduled_workouts(self):
        """Ottiene gli allenamenti programmati da Garmin Connect"""
        logging.info("Starting fetch_scheduled_workouts")
        if not self.garmin_client:
            logging.error("No Garmin client available")
            return
        
        # Crea una finestra di progresso
        progress = tk.Toplevel(self)
        progress.title("Caricamento in corso")
        progress.geometry("300x100")
        progress.transient(self)
        progress.grab_set()
        
        # Etichetta
        ttk.Label(progress, text="Recupero allenamenti programmati...").pack(pady=(20, 10))
        
        # Barra di progresso
        progressbar = ttk.Progressbar(progress, mode='indeterminate')
        progressbar.pack(fill=tk.X, padx=20)
        progressbar.start()
        
        # Aggiorna la finestra
        progress.update()
        
        try:
            # Periodo di ricerca: 3 mesi prima e 12 mesi dopo
            start_date = datetime.date.today() - datetime.timedelta(days=90)
            end_date = datetime.date.today() + datetime.timedelta(days=365)
            
            logging.info(f"Searching for workouts from {start_date} to {end_date}")
            
            self.scheduled_workouts = []
            seen_ids = set()  # Set per tenere traccia degli ID già visti
            
            # First, let's check if we can get the current month's data directly
            current_month_date = datetime.date.today()
            try:
                logging.info(f"Checking current month: {current_month_date.year}-{current_month_date.month}")
                current_response = self.garmin_client.get_calendar(current_month_date.year, current_month_date.month)
                
                # Log the raw response for debugging
                logging.debug(f"Current month response: {json.dumps(current_response, indent=2)}")
                
                if 'calendarItems' in current_response:
                    calendar_items = current_response.get('calendarItems', [])
                    logging.info(f"Current month has {len(calendar_items)} calendar items total")
                    
                    workout_items = [item for item in calendar_items if item.get('itemType') == 'workout']
                    logging.info(f"Current month has {len(workout_items)} workout items")
                    
                    # Log details of each workout found
                    for item in workout_items:
                        workout_id = item.get('workoutId', 'Unknown')
                        workout_name = item.get('title', 'Untitled')
                        workout_date = item.get('date', 'No date')
                        logging.info(f"Current month workout: {workout_name} (ID: {workout_id}) on {workout_date}")
                else:
                    logging.warning("No calendarItems found in the response for current month")
            except Exception as e:
                logging.error(f"Error checking current month: {str(e)}")
            
            # Now proceed with the regular month-by-month search
            # Ottieni il calendario per ogni mese nel periodo
            current_date = datetime.date(start_date.year, start_date.month, 1)
            end_month = datetime.date(end_date.year, end_date.month, 1)
            
            while current_date <= end_month:
                logging.info(f"Checking month: {current_date.year}-{current_date.month}")
                # Ottieni il calendario per questo mese
                response = self.garmin_client.get_calendar(current_date.year, current_date.month)
                
                # Cerca gli allenamenti
                found_workouts = 0  # Reset for this month
                if 'calendarItems' in response:
                    calendar_items = response.get('calendarItems', [])
                    logging.info(f"Month {current_date.year}-{current_date.month} has {len(calendar_items)} calendar items")
                    
                    workout_items = [item for item in calendar_items if item.get('itemType') == 'workout']
                    logging.info(f"Month {current_date.year}-{current_date.month} has {len(workout_items)} workout items")
                    
                    for item in calendar_items:
                        if item.get('itemType') == 'workout':
                            workout_name = item.get('title', '')
                            workout_id = item.get('workoutId', None)
                            schedule_id = item.get('id', None)
                            schedule_date = item.get('date', None)
                            
                            # Controlla se questo ID è già stato visto
                            item_id = item.get('id')
                            if item_id not in seen_ids:
                                seen_ids.add(item_id)
                                self.scheduled_workouts.append(item)
                                found_workouts += 1
                                logging.debug(f"Found workout: {workout_name} (ID: {workout_id}, Schedule ID: {schedule_id}) on {schedule_date}")
                else:
                    logging.warning(f"No calendarItems found in the response for {current_date.year}-{current_date.month}")
                
                logging.info(f"Found {found_workouts} workouts for {current_date.year}-{current_date.month}")
                
                # Passa al mese successivo
                if current_date.month == 12:
                    current_date = datetime.date(current_date.year + 1, 1, 1)
                else:
                    current_date = datetime.date(current_date.year, current_date.month + 1, 1)
                
                # Se non c'è una data di fine specifica e non sono stati trovati allenamenti in questo mese,
                # interrompi la ricerca (non ha senso continuare a cercare oltre)
                if not end_date and found_workouts == 0:
                    logging.info(f"No workouts found for {current_date.year}-{current_date.month}, stopping search")
                    break
            
            # Ordina per data
            self.scheduled_workouts.sort(key=lambda x: x.get('date', ''))
            logging.info(f"Total scheduled workouts found: {len(self.scheduled_workouts)}")
            
            # Log some details about what we found
            if self.scheduled_workouts:
                for workout in self.scheduled_workouts[:5]:  # Log first 5 for brevity
                    logging.info(f"Scheduled workout: {workout.get('title')} on {workout.get('date')}")
                if len(self.scheduled_workouts) > 5:
                    logging.info(f"... and {len(self.scheduled_workouts) - 5} more workouts")
            
        except Exception as e:
            logging.error(f"Error in fetch_scheduled_workouts: {str(e)}")
            # Chiudi la finestra di progresso
            progress.destroy()
            raise e
        
        # Chiudi la finestra di progresso
        progress.destroy()

        
    def fetch_available_workouts(self):
        """Ottiene gli allenamenti disponibili da Garmin Connect"""
        if not self.garmin_client:
            return
        
        try:
            # Ottieni la lista degli allenamenti
            self.available_workouts = self.garmin_client.list_workouts()
            
            # Aggiorna la lista
            self.update_workout_list()
            
        except Exception as e:
            messagebox.showerror("Errore", 
                               f"Impossibile ottenere gli allenamenti: {str(e)}", 
                               parent=self)
    
    def update_workout_list(self):
        """Aggiorna la lista degli allenamenti disponibili"""
        # Pulisci la lista attuale
        for item in self.workouts_tree.get_children():
            self.workouts_tree.delete(item)
        
        # Se non ci sono allenamenti, esci
        if not hasattr(self, 'available_workouts') or not self.available_workouts:
            return
        
        # Filtra gli allenamenti
        filter_text = self.filter_var.get().lower()
        sport_filter = self.sport_filter_var.get()
        
        # Converti il filtro sport
        if sport_filter == "Corsa":
            sport_filter = "running"
        elif sport_filter == "Ciclismo":
            sport_filter = "cycling"
        elif sport_filter == "Nuoto":
            sport_filter = "swimming"
        else:
            sport_filter = None
        
        # Aggiungi gli allenamenti filtrati
        for workout in self.available_workouts:
            # Ottieni il nome
            name = workout.get('workoutName', '')
            
            # Filtra per testo
            if filter_text and filter_text not in name.lower():
                continue
            
            # Filtra per sport
            if sport_filter and workout.get('sportType', {}).get('sportTypeKey') != sport_filter:
                continue
            
            # Formatta il tipo di sport
            sport_type = workout.get('sportType', {}).get('sportTypeKey', 'running')
            sport_display = sport_type.capitalize()
            
            # Ottieni la data di creazione
            created_date = workout.get('createdDate', '')
            if created_date:
                try:
                    # Convert timestamp to date
                    created_date = datetime.datetime.fromtimestamp(created_date / 1000.0).strftime('%Y-%m-%d')
                except:
                    created_date = ""
            
            # Aggiungi alla lista con l'ID come tag
            self.workouts_tree.insert("", "end", 
                                     values=(name, sport_display, created_date), 
                                     tags=(workout.get('workoutId'),))
    
    def refresh_workouts(self):
        """Aggiorna la lista degli allenamenti disponibili"""
        if self.garmin_client:
            self.fetch_available_workouts()
        else:
            messagebox.showerror("Errore", 
                               "Devi essere connesso a Garmin Connect", 
                               parent=self)
    
    def on_login(self, client):
        """Gestisce l'evento di login completato"""
        logging.info("on_login chiamato in CalendarFrame")
        
        if client is None:
            logging.error("Client Garmin è None in on_login di CalendarFrame")
        else:
            logging.info("Client Garmin valido ricevuto in on_login di CalendarFrame")
        
        self.garmin_client = client
        
        # Abilita i pulsanti
        self.sync_button['state'] = 'normal'
        self.schedule_button['state'] = 'normal'
        self.delete_workout_button['state'] = 'normal'
        
        # Ottieni gli allenamenti (sincronizza sempre in modo silenzioso)
        # Aggiungiamo un breve ritardo per assicurarci che l'interfaccia sia pronta
        self.after(500, lambda: self.sync_calendar(show_messages=False))

    # Modifica al metodo on_logout per rimuovere i pulsanti di debug
    def on_logout(self):
        """Gestisce l'evento di logout"""
        self.garmin_client = None
        
        # Disabilita i pulsanti
        self.sync_button['state'] = 'disabled'
        self.schedule_button['state'] = 'disabled'
        self.cancel_button['state'] = 'disabled'
        self.move_button['state'] = 'disabled'
        self.delete_workout_button['state'] = 'disabled'

        # Pulisci i dati
        self.scheduled_workouts = []
        if hasattr(self, 'available_workouts'):
            del self.available_workouts
        
        # Pulisci i dettagli
        self.clear_workout_details()
        
        # Aggiorna la lista
        self.update_workout_list()
        
        # Ridisegna il calendario
        self.draw_calendar()


    def schedule_test_workout(self):
        """Function to schedule a test workout for debugging purposes"""
        if not self.garmin_client:
            messagebox.showerror("Error", "Must be connected to Garmin Connect", parent=self)
            return
        
        try:
            # Create a simple test workout
            from planner.workout import Workout, WorkoutStep, Target
            
            # Get today's date
            today = datetime.date.today().strftime("%Y-%m-%d")
            
            # Create a simple test workout
            test_workout = Workout("running", "Test Workout")
            
            # Add a simple warmup step
            warmup_step = WorkoutStep(
                1,
                "warmup",
                "Warmup",
                end_condition="time",
                end_condition_value="5:00"
            )
            test_workout.add_step(warmup_step)
            
            # Add an interval step
            interval_step = WorkoutStep(
                2,
                "interval",
                "Interval",
                end_condition="time",
                end_condition_value="1:00",
                target=Target("pace.zone", 3.0, 3.5)
            )
            test_workout.add_step(interval_step)
            
            # Add a cooldown step
            cooldown_step = WorkoutStep(
                3,
                "cooldown",
                "Cooldown",
                end_condition="time",
                end_condition_value="5:00"
            )
            test_workout.add_step(cooldown_step)
            
            # Upload the workout to Garmin Connect
            response = self.garmin_client.add_workout(test_workout)
            
            if response and "workoutId" in response:
                workout_id = response["workoutId"]
                logging.info(f"Created test workout with ID: {workout_id}")
                
                # Schedule the workout for today
                schedule_response = self.garmin_client.schedule_workout(workout_id, today)
                logging.info(f"Scheduled test workout response: {schedule_response}")
                
                messagebox.showinfo("Success", f"Test workout scheduled for today ({today})", parent=self)
                
                # Refresh the calendar
                self.sync_calendar()
            else:
                logging.error(f"Failed to create test workout. Response: {response}")
                messagebox.showerror("Error", "Failed to create test workout", parent=self)
        
        except Exception as e:
            logging.error(f"Error scheduling test workout: {str(e)}")
            messagebox.showerror("Error", f"Error scheduling test workout: {str(e)}", parent=self)

    # Add a button to the calendar frame to call this function
    def add_test_workout_button(self):
        """Add a test workout button to the calendar frame"""
        # Add a test workout button below the sync button
        self.test_workout_button = ttk.Button(self.status_frame, text="Schedule Test Workout", 
                                           command=self.schedule_test_workout)
        self.test_workout_button.pack(side=tk.RIGHT, padx=5)
        
        # Initially disabled until login
        self.test_workout_button['state'] = 'disabled'
        
        # Add to the on_login method
        original_on_login = self.on_login
        
        def new_on_login(client):
            original_on_login(client)
            self.test_workout_button['state'] = 'normal'
        
        self.on_login = new_on_login
        
        # Add to the on_logout method
        original_on_logout = self.on_logout
        
        def new_on_logout():
            original_on_logout()
            self.test_workout_button['state'] = 'disabled'
        
        self.on_logout = new_on_logout


    def delete_workout(self):
        """Elimina uno o più allenamenti da Garmin Connect"""
        # Verifica che sia selezionato almeno un allenamento
        selection = self.workouts_tree.selection()
        if not selection:
            messagebox.showwarning("Nessuna selezione", 
                                 "Seleziona almeno un allenamento da eliminare", 
                                 parent=self)
            return
        
        # Se c'è un solo elemento selezionato
        if len(selection) == 1:
            # Ottieni l'allenamento
            item = selection[0]
            values = self.workouts_tree.item(item, "values")
            name = values[0]
            workout_id = self.workouts_tree.item(item, "tags")[0]
            
            # Chiedi conferma
            if not messagebox.askyesno("Conferma eliminazione", 
                                    f"Sei sicuro di voler eliminare l'allenamento '{name}' da Garmin Connect?", 
                                    parent=self):
                return
            
            try:
                # Elimina l'allenamento
                if self.garmin_client:
                    self.garmin_client.delete_workout(workout_id)
                    
                    # Aggiorna la lista
                    self.fetch_available_workouts()
                    
                    # Aggiorna anche gli allenamenti pianificati poiché l'eliminazione 
                    # potrebbe aver rimosso anche le pianificazioni
                    self.fetch_scheduled_workouts()
                    
                    # Ridisegna il calendario
                    self.draw_calendar()
                    
                    # Mostra messaggio di conferma
                    messagebox.showinfo("Operazione completata", 
                                        f"Allenamento '{name}' eliminato da Garmin Connect", 
                                        parent=self)
                else:
                    messagebox.showerror("Errore", 
                                        "Devi essere connesso a Garmin Connect", 
                                        parent=self)
            except Exception as e:
                messagebox.showerror("Errore", 
                                    f"Impossibile eliminare l'allenamento: {str(e)}", 
                                    parent=self)
        
        # Se ci sono più elementi selezionati
        else:
            # Ottieni i nomi degli allenamenti
            workout_names = []
            workout_ids = []
            for item in selection:
                values = self.workouts_tree.item(item, "values")
                name = values[0]
                workout_id = self.workouts_tree.item(item, "tags")[0]
                workout_names.append(name)
                workout_ids.append(workout_id)
            
            # Chiedi conferma
            if not messagebox.askyesno("Conferma eliminazione multipla", 
                                    f"Sei sicuro di voler eliminare {len(workout_names)} allenamenti selezionati da Garmin Connect?", 
                                    parent=self):
                return
            
            # Elimina gli allenamenti
            success_count = 0
            error_count = 0
            
            # Crea una finestra di progresso
            progress = tk.Toplevel(self)
            progress.title("Eliminazione in corso")
            progress.geometry("400x150")
            progress.transient(self)
            progress.grab_set()
            
            # Etichetta
            status_var = tk.StringVar(value="Eliminazione in corso...")
            status_label = ttk.Label(progress, textvariable=status_var)
            status_label.pack(pady=(20, 10))
            
            # Barra di progresso
            progressbar = ttk.Progressbar(progress, mode='determinate', length=300, maximum=len(workout_ids))
            progressbar.pack(pady=10)
            
            # Aggiorna la finestra
            progress.update()
            
            try:
                if self.garmin_client:
                    for i, (name, workout_id) in enumerate(zip(workout_names, workout_ids)):
                        try:
                            # Aggiorna lo stato
                            status_var.set(f"Eliminazione {i+1}/{len(workout_ids)}: {name}")
                            progressbar['value'] = i
                            progress.update()
                            
                            # Elimina l'allenamento
                            self.garmin_client.delete_workout(workout_id)
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            logging.error(f"Errore nell'eliminazione di '{name}': {str(e)}")
                    
                    # Aggiorna la lista
                    self.fetch_available_workouts()
                    
                    # Aggiorna anche gli allenamenti pianificati
                    self.fetch_scheduled_workouts()
                    
                    # Ridisegna il calendario
                    self.draw_calendar()
                    
                    # Mostra messaggio di conferma
                    messagebox.showinfo("Operazione completata", 
                                       f"Eliminati {success_count} allenamenti.\n"
                                       f"Errori: {error_count}", 
                                       parent=self)
                else:
                    progress.destroy()
                    messagebox.showerror("Errore", 
                                        "Devi essere connesso a Garmin Connect", 
                                        parent=self)
                    return
            except Exception as e:
                progress.destroy()
                messagebox.showerror("Errore", 
                                    f"Impossibile eliminare gli allenamenti: {str(e)}", 
                                    parent=self)
                return
            
            # Chiudi la finestra di progresso
            progress.destroy()