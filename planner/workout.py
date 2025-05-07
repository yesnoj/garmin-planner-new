import logging
import re
import datetime
import calendar
import yaml
from planner.garmin_client import GarminClient


SPORT_TYPES = {
    "running": 1,
    "cycling": 2,
    "swimming": 4,
}

STEP_TYPES = {"warmup": 1, "cooldown": 2, "interval": 3, "recovery": 4, "rest": 5, "repeat":6, "other": 7}

END_CONDITIONS = {
    "lap.button": 1,
    "time": 2,
    "distance": 3,
    "iterations": 7,
}

TARGET_TYPES = {
    "no.target": 1,
    "power.zone": 2,
    "cadence.zone": 3,
    "heart.rate.zone": 4,
    "speed.zone": 5,
    "pace.zone": 6,  # meters per second
}

class Workout:
    def __init__(self, sport_type, name, description=None):
        self.sport_type = sport_type
        self.workout_name = name
        self.description = description
        self.workout_steps = []

    def add_step(self, step):
        if step.order == 0:
            step.order = len(self.workout_steps) + 1
        self.workout_steps.append(step)

    def dist_to_time(self):
        for ws in self.workout_steps:
            ws.dist_to_time()


    def garminconnect_json(self):
        return {
            "sportType": {
                "sportTypeId": SPORT_TYPES[self.sport_type],
                "sportTypeKey": self.sport_type,
            },
            "workoutName": self.workout_name,
            "description": self.description,
            "workoutSegments": [
                {
                    "segmentOrder": 1,
                    "sportType": {
                        "sportTypeId": SPORT_TYPES[self.sport_type],
                        "sportTypeKey": self.sport_type,
                    },
                    "workoutSteps": [step.garminconnect_json() for step in self.workout_steps],
                }
            ],
        }
        
    @classmethod
    def from_yaml_steps(cls, name, steps, sport_type=None, paces=None, heart_rates=None):
        """
        Crea un allenamento dai passi in formato YAML.
        
        Args:
            name: Nome dell'allenamento
            steps: Lista di passi in formato YAML
            sport_type: Tipo di sport (opzionale, sarà estratto dai passi)
            paces: Dizionario dei valori di ritmo (opzionale)
            heart_rates: Dizionario delle zone di frequenza cardiaca (opzionale)
            
        Returns:
            Oggetto Workout
        """
        # Extract sport type from steps if not provided
        if not sport_type:
            for step in steps:
                if isinstance(step, dict) and "sport_type" in step:
                    sport_type = step["sport_type"]
                    break
            
            # Default to running if not found
            if not sport_type:
                sport_type = "running"
        
        # Create a new workout
        workout = cls(sport_type, name)
        
        # Extract date if present
        workout_date = None
        for step in steps:
            if isinstance(step, dict) and "date" in step:
                workout_date = step["date"]
                break
        
        # Process steps
        order = 1
        for step in steps:
            # Skip metadata steps
            if isinstance(step, dict) and (
                "sport_type" in step or 
                "date" in step
            ):
                continue
            
            # Handle repeat steps
            if isinstance(step, dict) and "repeat" in step and "steps" in step:
                repeat_count = step["repeat"]
                repeat_steps = step["steps"]
                
                # Create the repeat step
                repeat_step = WorkoutStep(
                    order=order,
                    step_type="repeat",
                    end_condition="iterations",
                    end_condition_value=repeat_count
                )
                order += 1
                
                # Process substeps
                substep_order = 1
                for substep in repeat_steps:
                    # Get the step type and detail
                    if isinstance(substep, dict) and len(substep) == 1:
                        substep_type = list(substep.keys())[0]
                        substep_detail = substep[substep_type]
                        
                        # Create and add the substep
                        step_obj = create_workout_step_from_text(
                            substep_type, 
                            substep_detail,
                            paces=paces,
                            heart_rates=heart_rates,
                            sport_type=sport_type,
                            order=substep_order
                        )
                        repeat_step.add_step(step_obj)
                        substep_order += 1
                
                # Add the repeat step to the workout
                workout.add_step(repeat_step)
            
            # Handle regular steps
            elif isinstance(step, dict) and len(step) == 1:
                step_type = list(step.keys())[0]
                step_detail = step[step_type]
                
                # Create and add the step
                step_obj = create_workout_step_from_text(
                    step_type, 
                    step_detail,
                    paces=paces,
                    heart_rates=heart_rates,
                    sport_type=sport_type,
                    order=order
                )
                workout.add_step(step_obj)
                order += 1
        
        return workout

class WorkoutStep:
    def __init__(
        self,
        order,
        step_type,
        description = '',
        end_condition="lap.button",
        end_condition_value=None,
        target=None,
    ):
        """Valid end condition values:
        - distance: '2.0km', '1.125km', '1.6km'
        - time: 0:40, 4:20
        - lap.button
        """
        self.order = order
        self.step_type = step_type
        self.description = description
        self.end_condition = end_condition
        self.end_condition_value = end_condition_value
        
        # Se il target è None, crea un target vuoto
        if target is None:
            self.target = Target()
        else:
            # Verifica se il target contiene informazioni di frequenza cardiaca
            if hasattr(target, 'from_value') and isinstance(target.from_value, str) and '_HR' in target.from_value:
                # Forza il tipo di target a heart.rate.zone
                target.target = "heart.rate.zone"
            
            # Stesso controllo per to_value
            if hasattr(target, 'to_value') and isinstance(target.to_value, str) and '_HR' in target.to_value:
                # Forza il tipo di target a heart.rate.zone
                target.target = "heart.rate.zone"
                
            self.target = target
            
        self.child_step_id = 1 if self.step_type == 'repeat' else None
        self.workout_steps = []

    def add_step(self, step):
        step.child_step_id = self.child_step_id
        if step.order == 0:
            step.order = len(self.workout_steps) + 1
        self.workout_steps.append(step)

    def end_condition_unit(self):
        if self.end_condition and isinstance(self.end_condition_value, str) and self.end_condition_value.endswith("km"):
            return {"unitKey": "kilometer"}
        else:
            return None

    def parsed_end_condition_value(self):
        """
        Parse and return the end condition value in the appropriate units.
        
        Returns:
            Numeric value of the end condition (e.g., meters for distance, seconds for time)
        """
        # distance
        if self.end_condition == 'distance' and self.end_condition_value and isinstance(self.end_condition_value, str) and self.end_condition_value.endswith("km"):
            return int(float(self.end_condition_value.replace("km", "")) * 1000)
        elif self.end_condition == 'distance' and self.end_condition_value and isinstance(self.end_condition_value, str) and self.end_condition_value.endswith("m"):
            return int(float(self.end_condition_value.replace("m", "")))
        # time
        elif self.end_condition == 'time' and self.end_condition_value and isinstance(self.end_condition_value, str) and ":" in self.end_condition_value:
            m, s = [int(x) for x in self.end_condition_value.split(":")]
            return m * 60 + s
        elif self.end_condition == 'time' and self.end_condition_value and isinstance(self.end_condition_value, str) and self.end_condition_value.endswith("min"):
            return int(float(self.end_condition_value.replace("min", "")) * 60)
        elif self.end_condition == 'time' and self.end_condition_value and isinstance(self.end_condition_value, str) and self.end_condition_value.endswith("s"):
            return int(float(self.end_condition_value.replace("s", "")))
        else:
            # If it's already a numeric value or we can't parse it, return as is
            try:
                return float(self.end_condition_value) if self.end_condition_value is not None else None
            except (ValueError, TypeError):
                return self.end_condition_value


    def garminconnect_json(self):
        """
        Versione che forza specifici step a usare heart.rate.zone
        """
        import logging
        import inspect
        
        # Tenta di ottenere informazioni sullo step che contiene questo target
        parent_step = None
        frame = inspect.currentframe()
        try:
            while frame:
                if 'self' in frame.f_locals and hasattr(frame.f_locals['self'], 'step_type'):
                    parent_step = frame.f_locals['self']
                    break
                frame = frame.f_back
        finally:
            del frame  # Evita reference cycles
        
        # Decidi il tipo di target in base al tipo di step
        target_type = self.target
        
        # Se abbiamo trovato lo step genitore, usa il suo tipo per decidere
        if parent_step and hasattr(parent_step, 'step_type'):
            step_type = parent_step.step_type
            step_order = parent_step.order if hasattr(parent_step, 'order') else 0
            
            logging.info(f"Esaminando target per step tipo={step_type}, ordine={step_order}")
            
            # Forza HR per step 1 e 3 (warmup e cooldown)
            if (step_type == 'warmup' or step_type == 'cooldown'):
                target_type = "heart.rate.zone"
                logging.info(f"Forzato target a heart.rate.zone per step tipo={step_type}")
        
        # Prepara il risultato JSON
        result = {
            "targetType": {
                "workoutTargetTypeId": TARGET_TYPES.get(target_type, TARGET_TYPES["no.target"]),
                "workoutTargetTypeKey": target_type,
            },
            "targetValueOne": self.from_value,
            "targetValueTwo": self.to_value,
            "zoneNumber": self.zone,
        }
        
        logging.info(f"Target finale JSON per {target_type}: {result}")
        return result


    def dist_to_time(self):
        """
        Convert steps with distance end condition and pace target to time end
        condition. This is better for treadmill runs, where the pace is hard to
        estimate.
        """
        import logging
        
        # Log per debug
        logging.info(f"dist_to_time: step_type={self.step_type}, target_type={getattr(self.target, 'target', 'None')}")
        
        # Verifica esplicitamente se è un target di frequenza cardiaca esaminando i valori
        is_hr_target = False
        if hasattr(self.target, 'from_value'):
            if isinstance(self.target.from_value, str) and "_HR" in self.target.from_value:
                is_hr_target = True
                logging.info(f"Rilevato HR in from_value: {self.target.from_value}")
        if hasattr(self.target, 'to_value'):
            if isinstance(self.target.to_value, str) and "_HR" in self.target.to_value:
                is_hr_target = True
                logging.info(f"Rilevato HR in to_value: {self.target.to_value}")
                
        # Se il target ha un tipo che contiene "heart"
        if hasattr(self.target, 'target') and isinstance(self.target.target, str):
            if "heart" in self.target.target.lower():
                is_hr_target = True
                logging.info(f"Rilevato HR nel tipo di target: {self.target.target}")
        
        # Se è un target HR, imposta esplicitamente il tipo e interrompi l'esecuzione
        if is_hr_target:
            logging.info("Rilevato target HR, impostazione tipo a heart.rate.zone")
            self.target.target = "heart.rate.zone"
            return
        
        # Procedi solo se è un target di ritmo e l'end condition è distance
        if self.end_condition == 'distance' and hasattr(self.target, 'target') and self.target.target == 'pace.zone':
            try:
                # Verifica ulteriore che non sia un target HR
                if ((hasattr(self.target, 'from_value') and isinstance(self.target.from_value, str) and '_HR' in self.target.from_value) or
                    (hasattr(self.target, 'to_value') and isinstance(self.target.to_value, str) and '_HR' in self.target.to_value)):
                    logging.info("Rilevato HR durante la conversione, impostazione tipo a heart.rate.zone")
                    self.target.target = "heart.rate.zone"
                    return
                    
                # Controllo aggiuntivo sui valori numerici - se non possono essere convertiti, potrebbe essere un target HR
                from_value = self.target.from_value
                to_value = self.target.to_value
                
                if not isinstance(from_value, (int, float)) or not isinstance(to_value, (int, float)):
                    logging.info(f"Valori non numerici: {from_value}/{to_value}, possibile target HR")
                    return
                    
                # Procedi con la conversione solo per target di ritmo con valori numerici validi
                target_pace_ms = (from_value + to_value) / 2
                end_condition_sec = int(self.parsed_end_condition_value()) / target_pace_ms
                
                # Round it to the nearest 10 seconds
                end_condition_sec = int(round(end_condition_sec/10, 0) * 10)
                
                # Update end condition
                self.end_condition = 'time'
                self.end_condition_value = f'{end_condition_sec:.0f}'
                
                logging.info(f"Convertito da distanza a tempo: {end_condition_sec} secondi")
                
            except Exception as e:
                logging.error(f"Errore durante la conversione dist_to_time: {str(e)}")
                # In caso di errore, non modificare lo step
                return
                
        elif self.end_condition == 'iterations' and len(self.workout_steps) > 0:
            # Per i repeat step, applica la conversione ai suoi substep
            for ws in self.workout_steps:
                ws.dist_to_time()

    def garminconnect_json(self):
        base_json = {
            "type": 'RepeatGroupDTO' if self.step_type == 'repeat' else 'ExecutableStepDTO',
            "stepId": None,
            "stepOrder": self.order,
            "childStepId": self.child_step_id,
            "stepType": {
                "stepTypeId": STEP_TYPES[self.step_type],
                "stepTypeKey": self.step_type,
            },
            "endCondition": {
                "conditionTypeKey": self.end_condition,
                "conditionTypeId": END_CONDITIONS[self.end_condition],
            },
            "endConditionValue": self.parsed_end_condition_value(),
        }

        if len(self.workout_steps) > 0:
            base_json["workoutSteps"] = [step.garminconnect_json() for step in self.workout_steps]

        if self.step_type == 'repeat':
            base_json['smartRepeat'] = True
            base_json['numberOfIterations'] = self.end_condition_value
        else:
            # Aggiorna con i dati del target
            base_json.update({
                "description": self.description,
                "preferredEndConditionUnit": self.end_condition_unit(),
                "endConditionCompare": None,
                "endConditionZone": None,
                **self.target.garminconnect_json(),
            })
        return base_json

class Target:
    def __init__(self, target="no.target", from_value=None, to_value=None, zone=None):
        self.target = target
        self.from_value = from_value
        self.to_value = to_value
        self.zone = zone
        
        # Aggiungi un flag per identificare i target di frequenza cardiaca
        self.is_heart_rate = False
        
        # Verifica se il target è di frequenza cardiaca
        if isinstance(self.from_value, str) and "_HR" in self.from_value:
            self.is_heart_rate = True
        elif isinstance(self.to_value, str) and "_HR" in self.to_value:
            self.is_heart_rate = True
        elif self.target == "heart.rate.zone":
            self.is_heart_rate = True

    def garminconnect_json(self):
        import logging
        
        # Log dello stato iniziale
        logging.info(f"Target iniziale: {self.target}, from={self.from_value}, to={self.to_value}, zone={self.zone}, is_heart_rate={self.is_heart_rate}")
        
        # Se è un target di frequenza cardiaca, imposta il tipo corretto
        target_type = self.target
        if self.is_heart_rate:
            target_type = "heart.rate.zone"
            logging.info(f"Forzato target_type in heart.rate.zone perché is_heart_rate=True")
        
        result = {
            "targetType": {
                "workoutTargetTypeId": TARGET_TYPES.get(target_type, TARGET_TYPES["no.target"]),
                "workoutTargetTypeKey": target_type,
            },
            "targetValueOne": self.from_value,
            "targetValueTwo": self.to_value,
            "zoneNumber": self.zone,
        }
        
        logging.info(f"Target finale JSON: {result}")
        return result

def create_workout_step_from_text(step_type, step_detail, paces=None, heart_rates=None, sport_type="running", order=0):
    """
    Crea un oggetto WorkoutStep a partire da una descrizione testuale.
    
    Args:
        step_type: Tipo di passo (es. 'interval', 'warmup')
        step_detail: Dettagli del passo (es. '5km @Z3')
        paces: Dizionario dei valori di ritmo (opzionale)
        heart_rates: Dizionario delle zone di frequenza cardiaca (opzionale)
        sport_type: Tipo di sport (running, cycling, swimming)
        order: Ordine del passo
        
    Returns:
        Oggetto WorkoutStep
    """
    # Default values
    description = ""
    end_condition = "lap.button"
    end_condition_value = None
    target = Target()  # Default target
    
    # Extract description if present
    if " -- " in step_detail:
        parts = step_detail.split(" -- ", 1)
        step_detail = parts[0].strip()
        description = parts[1].strip()
    
    # Extract duration/distance
    duration_match = re.match(r'^([\d\.]+)(km|m|min|s|h)(?:\s+(.*))?$', step_detail)
    if duration_match:
        value = float(duration_match.group(1))
        unit = duration_match.group(2)
        remainder = duration_match.group(3) if duration_match.group(3) else ""
        
        # Determine end condition type and value
        if unit in ['km', 'm']:
            end_condition = "distance"
            end_condition_value = f"{value}{unit}"
        else:
            end_condition = "time"
            if unit == 'h':
                minutes = int(value * 60)
                end_condition_value = f"{minutes}:00"
            elif unit == 'min':
                end_condition_value = f"{int(value)}:00"
            elif unit == 's':
                minutes = int(value) // 60
                seconds = int(value) % 60
                end_condition_value = f"{minutes}:{seconds:02d}"
        
        # Parse target zone if present
        if '@' in remainder:
            # Determine if this is a heart rate target
            is_hr = '@hr' in remainder.lower()
            
            # Extract zone name
            zone_match = re.search(r'@(?:hr\s+)?([A-Za-z0-9_]+)', remainder)
            if zone_match:
                zone_name = zone_match.group(1)
                
                # Heart rate zone
                if is_hr or '_HR' in zone_name:
                    target = create_heart_rate_target(zone_name, heart_rates)
                
                # Pace zone for running
                elif sport_type == "running" and not zone_name.endswith('_HR'):
                    target = create_pace_target(zone_name, paces, sport_type)
                
                # Power zone for cycling
                elif sport_type == "cycling" and zone_name.startswith('Z') and not zone_name.endswith('_HR'):
                    target = create_power_target(zone_name)
                
                # Swim pace for swimming
                elif sport_type == "swimming" and zone_name.startswith('Z') and not zone_name.endswith('_HR'):
                    target = create_swim_pace_target(zone_name, paces)
    
    # Handle lap-button for rest steps
    elif step_type == 'rest' and 'lap-button' in step_detail.lower():
        end_condition = "lap.button"
        end_condition_value = None
        
        # Check if there's a target for the lap-button rest
        if '@' in step_detail:
            # Same target parsing logic as above
            is_hr = '@hr' in step_detail.lower()
            zone_match = re.search(r'@(?:hr\s+)?([A-Za-z0-9_]+)', step_detail)
            if zone_match:
                zone_name = zone_match.group(1)
                
                if is_hr or '_HR' in zone_name:
                    target = create_heart_rate_target(zone_name, heart_rates)
                elif sport_type == "running" and not zone_name.endswith('_HR'):
                    target = create_pace_target(zone_name, paces, sport_type)
                elif sport_type == "cycling" and zone_name.startswith('Z') and not zone_name.endswith('_HR'):
                    target = create_power_target(zone_name)
                elif sport_type == "swimming" and zone_name.startswith('Z') and not zone_name.endswith('_HR'):
                    target = create_swim_pace_target(zone_name, paces)
    
    # Create the workout step
    return WorkoutStep(
        order=order,
        step_type=step_type,
        description=description,
        end_condition=end_condition,
        end_condition_value=end_condition_value,
        target=target
    )

def create_heart_rate_target(zone_name, heart_rates=None):
    """
    Crea un target per la frequenza cardiaca.
    
    Args:
        zone_name: Nome della zona (es. 'Z1_HR')
        heart_rates: Dizionario delle zone di frequenza cardiaca
        
    Returns:
        Oggetto Target
    """
    # Get zone number if it's in format Z1_HR, Z2_HR, etc.
    zone_number_match = re.match(r'Z(\d+)(?:_HR)?', zone_name)
    if not zone_number_match:
        return Target("heart.rate.zone", 150, 130, None)
        
    zone_number = int(zone_number_match.group(1))
    zone_key = f"Z{zone_number}_HR"
    
    # DEBUG LOG
    print(f"Processing HR zone: {zone_name}, looking for {zone_key} in {heart_rates}")
    
    # Look up HR values if available
    if heart_rates and zone_key in heart_rates:
        hr_value = heart_rates[zone_key]
        print(f"Found HR value: {hr_value}")
        
        # Parse HR range (e.g., "140-160" or "62-76% max_hr")
        hr_range_match = re.match(r'(\d+)-(\d+)(?:%\s*max_hr)?', str(hr_value))
        if hr_range_match:
            from_value = float(hr_range_match.group(1))
            to_value = float(hr_range_match.group(2))
            
            # Check if it's percentage of max_hr
            if '%' in str(hr_value) and heart_rates.get('max_hr'):
                max_hr = float(heart_rates['max_hr'])
                from_value = (from_value / 100) * max_hr
                to_value = (to_value / 100) * max_hr
                
            print(f"Setting HR range: {from_value}-{to_value}")
            return Target("heart.rate.zone", to_value, from_value, zone_number)
            
        # Parse single HR value
        elif str(hr_value).replace('.', '', 1).isdigit():
            value = float(hr_value)
            # Create a range around the single value (+/- 5%)
            from_value = value * 0.95
            to_value = value * 1.05
            return Target("heart.rate.zone", to_value, from_value, zone_number)
    
    # Use default values based on image 4 in your screenshots
    # These are expressed as percentages of max_hr: "62-76% max_hr", etc.
    default_hr_zones = {
        1: (62, 76),  # Z1_HR: 62-76% max_hr
        2: (76, 85),  # Z2_HR: 76-85% max_hr 
        3: (85, 91),  # Z3_HR: 85-91% max_hr
        4: (91, 95),  # Z4_HR: 91-95% max_hr
        5: (95, 100)  # Z5_HR: 95-100% max_hr
    }
    
    if zone_number in default_hr_zones and heart_rates and 'max_hr' in heart_rates:
        try:
            max_hr = float(heart_rates['max_hr'])
            from_percent, to_percent = default_hr_zones[zone_number]
            from_value = (from_percent / 100) * max_hr
            to_value = (to_percent / 100) * max_hr
            print(f"Using default %max_hr: {from_percent}%-{to_percent}% of {max_hr} = {from_value}-{to_value}")
            return Target("heart.rate.zone", to_value, from_value, zone_number)
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error calculating default HR: {e}")
    
    # Absolute fallback values if nothing else works
    base_hr = 120 + (zone_number - 1) * 10
    return Target("heart.rate.zone", base_hr + 10, base_hr, zone_number)

def create_pace_target(zone_name, paces=None, sport_type="running"):
    """
    Crea un target per il ritmo di corsa.
    
    Args:
        zone_name: Nome della zona (es. 'Z3')
        paces: Dizionario dei valori di ritmo
        sport_type: Tipo di sport
        
    Returns:
        Oggetto Target
    """
    # Get zone number
    zone_number = None
    if re.match(r'Z\d+', zone_name):
        zone_number = int(zone_name[1:])
    
    # If we have pace values
    if paces and zone_name in paces:
        pace_value = paces[zone_name]
        
        # Convert MM:SS format to meters per second
        if isinstance(pace_value, str) and ":" in pace_value:
            parts = pace_value.split(":")
            if len(parts) == 2:
                try:
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    total_seconds = minutes * 60 + seconds
                    meters_per_second = 1000 / total_seconds if total_seconds > 0 else 0
                    
                    # DEBUG LOG
                    print(f"Converting pace zone {zone_name}: {pace_value} = {meters_per_second} m/s")
                    
                    # Creating pace range using margins (default +/- 5% if not specified)
                    # For pace, LOWER numeric value (slower pace) = from_value
                    # HIGHER numeric value (faster pace) = to_value
                    # We adjust this correctly for Garmin Connect
                    slow_pace = meters_per_second * 0.95  # -5% = slower pace (lower m/s)
                    fast_pace = meters_per_second * 1.05  # +5% = faster pace (higher m/s)
                    
                    return Target("pace.zone", fast_pace, slow_pace, zone_number)
                except (ValueError, ZeroDivisionError) as e:
                    print(f"Error converting pace: {e}")
    
    # Default pace values if not found - based on image 3 in your screenshots
    if zone_number:
        default_paces = {
            1: "6:30",  # Z1
            2: "6:00",  # Z2
            3: "5:30",  # Z3
            4: "5:00",  # Z4
            5: "4:30",  # Z5
        }
        
        if zone_number in default_paces:
            default_pace = default_paces[zone_number]
            parts = default_pace.split(":")
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = int(parts[1])
                total_seconds = minutes * 60 + seconds
                meters_per_second = 1000 / total_seconds if total_seconds > 0 else 0
                
                # Use same margin as above
                slow_pace = meters_per_second * 0.95
                fast_pace = meters_per_second * 1.05
                
                return Target("pace.zone", fast_pace, slow_pace, zone_number)
    
    # Fallback default values
    return Target("pace.zone", 3.3, 3.0, None)

def create_power_target(zone_name):
    """
    Crea un target per la potenza nel ciclismo.
    
    Args:
        zone_name: Nome della zona (es. 'Z3')
        
    Returns:
        Oggetto Target
    """
    # Extract zone number
    zone_number_match = re.match(r'Z(\d+)', zone_name)
    if not zone_number_match:
        return Target("power.zone", 250, 200, None)
        
    zone_number = int(zone_number_match.group(1))
    
    # Define power ranges based on zone number
    power_ranges = {
        1: (100, 150),  # Z1: 55-75% FTP
        2: (150, 200),  # Z2: 75-90% FTP
        3: (200, 250),  # Z3: 90-105% FTP
        4: (250, 300),  # Z4: 105-120% FTP
        5: (300, 350)   # Z5: 120%+ FTP
    }
    
    if zone_number in power_ranges:
        from_value, to_value = power_ranges[zone_number]
        return Target("power.zone", to_value, from_value, zone_number)
    
    # Default for unknown zone numbers
    return Target("power.zone", 250, 200, zone_number)

def create_swim_pace_target(zone_name, swim_paces=None):
    """
    Crea un target per il ritmo nel nuoto.
    
    Args:
        zone_name: Nome della zona (es. 'Z3')
        swim_paces: Dizionario dei valori di ritmo nel nuoto
        
    Returns:
        Oggetto Target
    """
    # Get zone number
    zone_number = None
    if re.match(r'Z\d+', zone_name):
        zone_number = int(zone_name[1:])
    
    # If we have pace values
    if swim_paces and zone_name in swim_paces:
        pace_value = swim_paces[zone_name]
        
        # Convert MM:SS format to meters per second
        if isinstance(pace_value, str) and ":" in pace_value:
            parts = pace_value.split(":")
            if len(parts) == 2:
                try:
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    total_seconds = minutes * 60 + seconds
                    # Base is 100m in swimming
                    meters_per_second = 100 / total_seconds if total_seconds > 0 else 0
                    
                    # Create a range with margin
                    from_value = meters_per_second * 0.95
                    to_value = meters_per_second * 1.05
                    
                    return Target("pace.zone", to_value, from_value, zone_number)
                except (ValueError, ZeroDivisionError):
                    pass
    
    # Default swim pace values if not found
    if zone_number:
        # Default pace values for zones 1-5 (in m/s)
        base_paces = {
            1: 0.6,  # ~2:46 min/100m
            2: 0.7,  # ~2:22 min/100m
            3: 0.8,  # ~2:05 min/100m
            4: 0.9,  # ~1:51 min/100m
            5: 1.0   # ~1:40 min/100m
        }
        
        if zone_number in base_paces:
            base_pace = base_paces[zone_number]
            from_value = base_pace * 0.95
            to_value = base_pace * 1.05
            return Target("pace.zone", to_value, from_value, zone_number)
    
    # Fallback default values
    return Target("pace.zone", 0.8, 0.7, None)