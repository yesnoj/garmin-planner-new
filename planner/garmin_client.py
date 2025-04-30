#! /usr/bin/env python

import json
import logging
import garth
from getpass import getpass

class GarminClient():

  def __init__(self, oauth_folder='oauth-folder'):
    garth.resume(oauth_folder)

  def list_workouts(self):
    response = garth.connectapi(
        '/workout-service/workouts',
        params={'start': 1, 'limit': 999, 'myWorkoutsOnly': True})
    return response

  def add_workout(self, workout):
    response = garth.connectapi(
      '/workout-service/workout', method="POST",
      json=workout.garminconnect_json())
    return response 

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
      """
      Gets the calendar for the specified year and month.
      
      Important: The Garmin Connect API uses 0-based month indexing (January = 0),
      but this function expects 1-based month indexing (January = 1) and converts internally.
      
      Args:
          year (int): The year
          month (int): The month (1-12)
          
      Returns:
          dict: The calendar data from Garmin Connect
      """
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