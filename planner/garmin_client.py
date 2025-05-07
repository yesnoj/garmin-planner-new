#! /usr/bin/env python

import json
import logging
import garth
from getpass import getpass

class GarminClient():

  def __init__(self, oauth_folder='oauth-folder'):
    garth.resume(oauth_folder)
    self.logged_in = True

  def list_workouts(self):
    response = garth.connectapi(
        '/workout-service/workouts',
        params={'start': 1, 'limit': 999, 'myWorkoutsOnly': True})
    return response


  def add_workout(self, workout):
      """
      Versione semplificata che utilizza valori hardcoded per le zone HR
      """
      import logging
      import json
      
      # Converti in JSON
      workout_json = workout.garminconnect_json()
      
      # Forza manualmente specifici step a usare heart.rate.zone con valori appropriati
      for segment in workout_json.get("workoutSegments", []):
          for step in segment.get("workoutSteps", []):
              step_type = step.get("stepType", {}).get("stepTypeKey", "")
              
              # Forza HR per step warmup e cooldown
              if step_type in ["warmup", "cooldown"]:
                  step["targetType"]["workoutTargetTypeKey"] = "heart.rate.zone"
                  step["targetType"]["workoutTargetTypeId"] = 4  # ID per heart.rate.zone
                  
                  # Valori hardcoded per Z1_HR
                  hr_min = 110.0
                  hr_max = 125.0
                  step["targetValueOne"] = hr_min
                  step["targetValueTwo"] = hr_max
                  
                  logging.info(f"Forzato target a heart.rate.zone per step {step_type} con valori {hr_min}-{hr_max} bpm")
      
      # Invia a Garmin Connect
      response = garth.connectapi(
        '/workout-service/workout', method="POST",
        json=workout_json)
      
      return response

  def _load_config(self):
      """Carica la configurazione da un file."""
      import os
      import json
      
      # Percorso del file di configurazione
      config_file = os.path.join(os.path.dirname(__file__), '..', 'config.json')
      
      try:
          if os.path.exists(config_file):
              with open(config_file, 'r', encoding='utf-8') as f:
                  config = json.load(f)
                  # Assicurati che workout_config esista
                  return config.get('workout_config', {})
          return {}
      except Exception as e:
          logging.error(f"Errore nel caricamento della configurazione: {str(e)}")
          return {}

  def delete_workout(self, workout_id):
    logging.info(f'deleting workout {workout_id}')
    response = garth.connectapi(
      '/workout-service/workout/' + workout_id, method="DELETE")
    return response 

  def get_workout(self, workout_id):
    logging.info(f'getting workout {workout_id}')
    response = garth.connectapi(
      '/workout-service/workout/' + str(workout_id), method="GET")
    return response 

  def update_workout(self, workout_id, workout):
    logging.info(f'updating workout {workout_id}')
    wo_json = workout.garminconnect_json()
    wo_json['workoutId'] = workout_id
    response = garth.connectapi(
      '/workout-service/workout/' + str(workout_id), method="PUT", json=wo_json)
    print(response)
    return response 


  def get_calendar(self, year, month):
      if not isinstance(month, int) or month < 1 or month > 12:
          logging.error(f"Invalid month value: {month}. Must be between 1 and 12.")
          raise ValueError(f"Month must be between 1 and 12, got {month}")
      
      # Garmin API uses 0-based month indexing, so January = 0
      garmin_month = month - 1
      
      logging.info(f'getting calendar. Year: {year}, month: {month} (Garmin month index: {garmin_month})')
      
      try:
          response = garth.connectapi(
              f'/calendar-service/year/{year}/month/{garmin_month}')
          
          # Add some debugging information
          if response and 'calendarItems' in response:
              calendar_items = response.get('calendarItems', [])
              workout_items = [item for item in calendar_items if item.get('itemType') == 'workout']
              logging.info(f"Calendar response for {year}-{month} contains {len(calendar_items)} items total, {len(workout_items)} workouts")
          else:
              logging.warning(f"Calendar response for {year}-{month} does not contain 'calendarItems' key")
              
          return response
      except Exception as e:
          logging.error(f"Error getting calendar for {year}-{month}: {str(e)}")
          raise

  def get_activities(self, start_date=None, end_date=None, limit=20):
      """
      Ottiene le attività dell'utente da Garmin Connect.
      
      Args:
          start_date (str, optional): Data di inizio nel formato 'YYYY-MM-DD'
          end_date (str, optional): Data di fine nel formato 'YYYY-MM-DD'
          limit (int, optional): Numero massimo di attività da recuperare. Default 20.
          
      Returns:
          list: Lista delle attività
      """
      import datetime
      
      logging.info(f'Ottengo attività da Garmin Connect. Limit: {limit}')
      
      # Se le date non sono specificate, usa gli ultimi 30 giorni
      if not start_date:
          start_date = (datetime.datetime.now() - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
      if not end_date:
          end_date = datetime.datetime.now().strftime('%Y-%m-%d')
          
      try:
          # Utilizziamo l'endpoint corretto con i parametri adeguati
          # Basato sul codice C# che hai fornito
          start = 0  # Iniziamo dalla prima pagina
          
          # Costruiamo l'URL con i parametri
          url = '/activitylist-service/activities/search/activities'
          params = {
              'startDate': start_date,
              'endDate': end_date,
              'start': start,
              'limit': limit
          }
          
          logging.info(f"Chiamata API attività con parametri: {params}")
          response = garth.connectapi(url, params=params)
          
          if response:
              logging.info(f"Trovate {len(response)} attività nel periodo {start_date} - {end_date}")
          else:
              logging.warning(f"Nessuna attività trovata nel periodo {start_date} - {end_date}")
              
          return response
              
      except Exception as e:
          logging.error(f"Errore nel recupero delle attività: {str(e)}")
          # In caso di errore, ritorniamo una lista vuota invece di propagare l'errore
          return []

  def schedule_workout(self, workout_id, date):
    date_formatted = date
    if type(date_formatted) is not str:
      date_formatted = date.strftime('%Y-%m-%d')
    response = garth.connectapi(
      f'/workout-service/schedule/{workout_id}', method="POST",
      json={'date' :date_formatted})
    return response 

  def unschedule_workout(self, schedule_id):
    response = garth.connectapi(
      f'/workout-service/schedule/{schedule_id}', method="DELETE")
    return response 

  def cmd_login(args):
      email = input('Enter email address: ')
      password = getpass('Enter password: ')
      garth.login(email, password)
      garth.save(args.oauth_folder)
      
def add_workout_from_yaml(self, workout_name, steps, sport_type=None, config=None):
    """
    Crea un allenamento dai passi in formato YAML e lo carica su Garmin Connect.
    
    Args:
        workout_name: Nome dell'allenamento
        steps: Lista di passi in formato YAML
        sport_type: Tipo di sport (opzionale, sarà estratto dai passi)
        config: Configurazione con paces, heart_rates, etc.
        
    Returns:
        Risposta dall'API di Garmin Connect
    """
    from planner.workout import Workout
    
    # Prepara i dati di configurazione
    paces = {}
    heart_rates = {}
    swim_paces = {}
    
    if config and 'workout_config' in config:
        workout_config = config['workout_config']
        if 'paces' in workout_config:
            paces = workout_config['paces']
            print(f"Using paces configuration: {paces}")
        if 'heart_rates' in workout_config:
            heart_rates = workout_config['heart_rates']
            print(f"Using heart_rates configuration: {heart_rates}")
        if 'swim_paces' in workout_config:
            swim_paces = workout_config['swim_paces']
            print(f"Using swim_paces configuration: {swim_paces}")
    
    # Stampa per debug
    print(f"Creating workout: {workout_name}")
    print(f"Sport type: {sport_type}")
    print(f"Steps: {steps}")
    
    # Crea l'allenamento usando il nuovo metodo 
    workout = Workout.from_yaml_steps(
        workout_name, 
        steps,
        sport_type=sport_type,
        paces=paces,
        heart_rates=heart_rates
    )
    
    # Converti distanza a tempo se necessario (per tapis roulant)
    workout.dist_to_time()
    
    # Stampa l'allenamento in formato JSON per debug
    import json
    wo_json = workout.garminconnect_json()
    print(f"Workout JSON for Garmin Connect: {json.dumps(wo_json, indent=2)}")
    
    # Aggiungi l'allenamento a Garmin Connect
    return self.add_workout(workout)