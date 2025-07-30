import os
import logging
import json

logging.basicConfig(filename='weather_app.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

PREFERENCES_FILE = 'user_preferences.json'

def load_preferences():
    if os.path.exists(PREFERENCES_FILE):
        try:
            with open(PREFERENCES_FILE, 'r') as file:
                preferences = json.load(file)
                logging.info("Loaded user preferences successfully.")
                return preferences
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.error(f"Error loading preferences: {e}")
            return {}
    else:
        logging.info("No preferences file found; loading defaults.")
        return {}

def save_preferences(preferences):
    try:
        with open(PREFERENCES_FILE, 'w') as file:
            json.dump(preferences, file)
            logging.info("User preferences saved successfully.")
    except IOError as e:
        logging.error(f"Error saving preferences: {e}")

def display_weather(preferences):
    unit = preferences.get('temperature_unit', 'Celsius')
    language = preferences.get('display_language', 'English')
    location = preferences.get('preferred_location', 'your area')

    # Simulated weather data
    weather_data = {
        'temperature': 22,  # degrees Celsius
        'condition': 'Sunny'
    }
    
    if unit == 'Fahrenheit':
        weather_data['temperature'] = weather_data['temperature'] * 9/5 + 32
        
    print(f"Weather in {location}: {weather_data['temperature']:.1f}°{unit[0]} - {weather_data['condition']}")

def update_user_preferences(preferences):
    print("Update your preferences:")
    
    temperature_unit = input("Select temperature unit (Celsius/Fahrenheit): ")
    if temperature_unit not in ['Celsius', 'Fahrenheit']:
        logging.warning("Invalid temperature unit selected.")
        print("Invalid selection for temperature unit; defaulting to Celsius.")
        temperature_unit = 'Celsius'
    
    display_language = input("Select display language (English/Other): ")
    if display_language not in ['English', 'Other']:
        logging.warning("Invalid language selected.")
        print("Invalid selection for language; defaulting to English.")
        display_language = 'English'
    
    preferred_location = input("Enter your preferred location: ")
    
    preferences['temperature_unit'] = temperature_unit
    preferences['display_language'] = display_language
    preferences['preferred_location'] = preferred_location

    save_preferences(preferences)

def main():
    logging.info("Weather app started.")
    preferences = load_preferences()
    
    while True:
        action = input("Would you like to (1) view weather or (2) update preferences? Enter 'q' to quit: ")
        if action == '1':
            display_weather(preferences)
        elif action == '2':
            update_user_preferences(preferences)
        elif action.lower() == 'q':
            logging.info("Exiting the weather app.")
            break
        else:
            print("Invalid selection. Please try again.")

if __name__ == '__main__':
    main()