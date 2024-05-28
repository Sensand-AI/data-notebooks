from datetime import datetime

import pandas as pd
import pytz
import requests_cache
from openmeteo_requests import Client
from retry_requests import retry


def setup_session():
    """
    Set up a session with caching and retries.
    """
    cache = requests_cache.CachedSession('.cache', expire_after=3600)  # Cache for 1 hour
    retry_strategy = retry(
        cache,
        retries=5,
        backoff_factor=0.2
    )
    return retry_strategy

def convert_epoch_to_timezone(data, column_names, timezone='Australia/Sydney'):
    """
    Convert epoch times in specified columns of a DataFrame to datetime objects localized to UTC,
    then converted to a specified timezone.

    Args:
    data (pd.DataFrame): DataFrame containing columns with epoch times.
    column_names (list of str): List of column names containing epoch times to be converted.
    timezone (str): String representing the target timezone (default is 'Australia/Sydney').

    Returns:
    pd.DataFrame: DataFrame with specified columns converted to the specified timezone.
    """
    # Define the timezone objects
    utc_timezone = pytz.timezone('UTC')
    target_timezone = pytz.timezone(timezone)

    for column in column_names:
        # Convert epoch times to naive UTC datetime
        data[column] = pd.to_datetime(data[column], unit='s', utc=False)

        # Localize the naive datetime to UTC
        data[column] = data[column].dt.tz_localize(utc_timezone)

        # Convert from UTC to the target timezone
        data[column] = data[column].dt.tz_convert(target_timezone)

    return data

def calculate_days_between(date_str1: str, date_str2: str, format = "%Y-%m-%d") -> int:
    """
    Calculate the number of days between two dates given as strings.

    Parameters:
    - date_str1 (str): The first date string.
    - date_str2 (str): The second date string.

    Returns:
    - int: The difference in days between the two dates.
    
    Example:
    ```python
    days_difference = calculate_days_between('2024-05-01', '2024-04-25')
    print(f"The difference in days is: {days_difference}")
        
    """
    # convert the date strings into datetime objects
    date_format = format  # allow for custom date formats because merica
    datetime1 = datetime.strptime(date_str1, date_format)
    datetime2 = datetime.strptime(date_str2, date_format)
    
    # calculate the difference in days
    delta = datetime1 - datetime2
    return abs(delta.days)  # use abs to ensure a non-negative results

class OpenMeteoAPI:
    """
    A client for the Open Meteo API.    
		"""
    def __init__(self):
        """
        Initialize the OpenMeteoAPI client.
        """
        session = setup_session()
        self.client = Client(session=session)

    def fetch_weather_data(
        self,
        latitude,
        longitude,
        start_date,
        end_date,
        daily,
        timezone,
        hourly=None,
        historical=False,
        **kwargs
    ):
        """
        Fetch weather data using the Open Meteo API client.
        """
        # Define API endpoints
        historical_url = "https://archive-api.open-meteo.com/v1/archive"
        #current_url = "https://api.open-meteo.com/v1/bom"
        current_url = "https://api.open-meteo.com/v1/forecast"
        url = historical_url if historical else current_url

        # Define the parameters for the API call
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": hourly,
            "daily": daily,
            "timezone": timezone,
            **kwargs
        }

        # Make the API request using the configured client
        response = self.client.weather_api(url, params=params)
        return response
