#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Modulo per la pianificazione automatica degli allenamenti
"""

import datetime
import re
import logging


def schedule_workouts_by_week(workouts, race_date, preferred_days):
    """
    Pianifica automaticamente gli allenamenti a partire dalla data della gara.
    
    Args:
        workouts: lista di tuple (name, steps) degli allenamenti da pianificare
        race_date: data della gara (datetime.date)
        preferred_days: lista dei giorni preferiti (0=lunedì, 6=domenica)
        
    Returns:
        dict: dizionario con le date assegnate a ciascun allenamento (workout_name -> data)
    """
    logging.info(f"Pianificazione allenamenti: {len(workouts)} allenamenti, gara il {race_date}")
    
    # Ordina i giorni preferiti
    preferred_days = sorted(preferred_days)
    
    # Identifica gli allenamenti con pattern W00S00
    pattern = re.compile(r'W(\d{2})S(\d{2})\s')
    workout_list = []
    
    for name, steps in workouts:
        match = pattern.match(name)
        if match:
            week = int(match.group(1))
            session = int(match.group(2))
            workout_list.append((name, week, session, steps))
    
    # Ordina gli allenamenti per settimana e sessione
    workout_list.sort(key=lambda x: (x[1], x[2]))
    
    # Se non ci sono allenamenti con il pattern corretto, esci
    if not workout_list:
        logging.warning("Nessun allenamento con il pattern W00S00 trovato")
        return {}
    
    # Determina il numero di allenamenti da pianificare
    num_workouts = len(workout_list)
    
    # Calcola quante settimane sono necessarie per pianificare tutti gli allenamenti
    # considerando i giorni preferiti disponibili per settimana
    days_per_week = len(preferred_days)
    
    # Se race_date è in uno dei giorni preferiti, rimuovilo per questa settimana
    race_day_of_week = race_date.weekday()
    if race_day_of_week in preferred_days:
        days_in_race_week = len([d for d in preferred_days if d != race_day_of_week and d < race_day_of_week])
    else:
        days_in_race_week = len([d for d in preferred_days if d < race_day_of_week])
    
    # Calcola quante settimane sono necessarie (arrotondando per eccesso)
    weeks_needed = (num_workouts - days_in_race_week + days_per_week - 1) // days_per_week + 1
    
    # Calcola il lunedì della settimana della gara
    race_monday = race_date - datetime.timedelta(days=race_date.weekday())
    
    # Calcola la data di inizio (lunedì della prima settimana)
    start_date = race_monday - datetime.timedelta(days=7 * (weeks_needed - 1))
    logging.info(f"Data inizio piano: {start_date} (lunedì)")
    
    # Dizionario per memorizzare le date assegnate
    assigned_dates = {}
    
    # Pianifica ogni allenamento
    for i, (name, week, session, steps) in enumerate(workout_list):
        # Calcola in quale settimana pianificare questo allenamento
        target_week = i // days_per_week
        day_in_week = i % days_per_week
        
        # Calcola la data di questa settimana
        week_start = start_date + datetime.timedelta(days=7 * target_week)
        
        # Calcola il giorno specifico nella settimana
        day_offset = preferred_days[day_in_week]
        workout_date = week_start + datetime.timedelta(days=day_offset)
        
        # Verifica che la data non sia uguale o successiva alla data della gara
        if workout_date >= race_date:
            logging.warning(f"Allenamento {name} cadrebbe nel giorno o dopo la gara ({workout_date}), non pianificato.")
            continue
        
        # Assegna la data
        assigned_dates[name] = workout_date
        logging.info(f"Assegnato: {name} a {workout_date}")
    
    logging.info(f"Pianificazione completata: {len(assigned_dates)} allenamenti pianificati")
    return assigned_dates

def apply_scheduled_dates(workouts, scheduled_dates):
    """
    Applica le date pianificate agli allenamenti.
    
    Args:
        workouts: lista di tuple (name, steps) degli allenamenti
        scheduled_dates: dizionario con le date assegnate (workout_name -> data)
        
    Returns:
        list: nuova lista di allenamenti con le date aggiornate
    """
    logging.info(f"Applicazione date: {len(scheduled_dates)} date da applicare a {len(workouts)} allenamenti")
    
    updated_workouts = []
    updated_count = 0
    
    for name, steps in workouts:
        # Copia gli step
        new_steps = steps.copy()
        
        # Se c'è una data pianificata per questo allenamento
        if name in scheduled_dates:
            date_str = scheduled_dates[name].strftime("%Y-%m-%d")
            
            # Cerca un elemento "date" esistente negli step
            date_found = False
            for i, step in enumerate(new_steps):
                if isinstance(step, dict) and "date" in step:
                    new_steps[i] = {"date": date_str}
                    date_found = True
                    break
            
            # Se non è stato trovato, aggiungi un nuovo elemento "date"
            if not date_found:
                # Conserva gli elementi di metadati all'inizio (ad es. sport_type)
                metadata_count = 0
                for step in new_steps:
                    if isinstance(step, dict) and any(key in step for key in ["sport_type"]):
                        metadata_count += 1
                    else:
                        break
                
                # Inserisci dopo i metadati
                new_steps.insert(metadata_count, {"date": date_str})
            
            updated_count += 1
        
        updated_workouts.append((name, new_steps))
    
    logging.info(f"Aggiornati {updated_count} allenamenti con nuove date")
    return updated_workouts


def clear_workout_dates(workouts, selected_indices=None):
    """
    Rimuove le date pianificate dagli allenamenti selezionati.
    
    Args:
        workouts: lista di tuple (name, steps) degli allenamenti
        selected_indices: lista degli indici degli allenamenti selezionati (se None, tutti)
        
    Returns:
        list: nuova lista di allenamenti con le date rimosse
    """
    if selected_indices is None:
        selected_indices = range(len(workouts))
    
    logging.info(f"Rimozione date: {len(selected_indices)} allenamenti selezionati")
    
    updated_workouts = []
    removed_count = 0
    
    for i, (name, steps) in enumerate(workouts):
        if i in selected_indices:
            # Copia gli step rimuovendo gli elementi "date"
            new_steps = [step for step in steps if not (isinstance(step, dict) and "date" in step)]
            
            # Se abbiamo rimosso qualcosa
            if len(new_steps) < len(steps):
                removed_count += 1
            
            updated_workouts.append((name, new_steps))
        else:
            # Mantieni invariato
            updated_workouts.append((name, steps))
    
    logging.info(f"Rimosse date da {removed_count} allenamenti")
    return updated_workouts