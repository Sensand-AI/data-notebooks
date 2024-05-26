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

    def fetch_weather_data(self, latitude, longitude, start_date, end_date, daily, hourly, historical=False):
        """
        Fetch weather data using the Open Meteo API client.
        """
        # Define API endpoints
        historical_url = "https://archive-api.open-meteo.com/v1/archive"
        current_url = "https://api.open-meteo.com/v1/bom"
        url = historical_url if historical else current_url

        # Define the parameters for the API call
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": hourly,
            "daily": daily
        }

        # Make the API request using the configured client
        response = self.client.weather_api(url, params=params)
        return response
