"""
Weather service for interacting with external weather APIs.
"""

import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from solace_ai_connector.common.log import log


class WeatherService:
    """Service for fetching weather data from external APIs."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.openweathermap.org/data/2.5"):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.log_identifier = "[WeatherService]"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
            log.info(f"{self.log_identifier} HTTP session closed")
    
    async def get_current_weather(self, location: str, units: str = "metric") -> Dict[str, Any]:
        """
        Get current weather for a location.
        
        Args:
            location: City name, state code, and country code (for example, "London,UK")
            units: Temperature units (metric, imperial, kelvin)
        
        Returns:
            Dictionary containing current weather data
        """
        log.info(f"{self.log_identifier} Fetching current weather for: {location}")
        
        session = await self._get_session()
        url = f"{self.base_url}/weather"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": units
        }
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    log.info(f"{self.log_identifier} Successfully fetched weather for {location}")
                    return self._format_current_weather(data)
                elif response.status == 404:
                    raise ValueError(f"Location '{location}' not found")
                else:
                    error_data = await response.json()
                    raise Exception(f"Weather API error: {error_data.get('message', 'Unknown error')}")
        
        except aiohttp.ClientError as e:
            log.error(f"{self.log_identifier} Network error fetching weather: {e}")
            raise Exception(f"Network error: {str(e)}")
    
    async def get_weather_forecast(self, location: str, days: int = 5, units: str = "metric") -> Dict[str, Any]:
        """
        Get weather forecast for a location.
        
        Args:
            location: City name, state code, and country code
            days: Number of days for forecast (1-5)
            units: Temperature units
        
        Returns:
            Dictionary containing forecast data
        """
        log.info(f"{self.log_identifier} Fetching {days}-day forecast for: {location}")
        
        session = await self._get_session()
        url = f"{self.base_url}/forecast"
        params = {
            "q": location,
            "appid": self.api_key,
            "units": units,
            "cnt": min(days * 8, 40)  # API returns 3-hour intervals, max 40 entries
        }
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    log.info(f"{self.log_identifier} Successfully fetched forecast for {location}")
                    return self._format_forecast_data(data, days)
                elif response.status == 404:
                    raise ValueError(f"Location '{location}' not found")
                else:
                    error_data = await response.json()
                    raise Exception(f"Weather API error: {error_data.get('message', 'Unknown error')}")
        
        except aiohttp.ClientError as e:
            log.error(f"{self.log_identifier} Network error fetching forecast: {e}")
            raise Exception(f"Network error: {str(e)}")
    
    def _format_current_weather(self, data: Dict) -> Dict[str, Any]:
        """Format current weather data for consistent output."""
        return {
            "location": f"{data['name']}, {data['sys']['country']}",
            "temperature": data['main']['temp'],
            "feels_like": data['main']['feels_like'],
            "humidity": data['main']['humidity'],
            "pressure": data['main']['pressure'],
            "description": data['weather'][0]['description'].title(),
            "wind_speed": data.get('wind', {}).get('speed', 0),
            "wind_direction": data.get('wind', {}).get('deg', 0),
            "visibility": data.get('visibility', 0) / 1000,  # Convert to km
            "timestamp": datetime.fromtimestamp(data['dt']).isoformat(),
            "sunrise": datetime.fromtimestamp(data['sys']['sunrise']).isoformat(),
            "sunset": datetime.fromtimestamp(data['sys']['sunset']).isoformat()
        }
    
    def _format_forecast_data(self, data: Dict, days: int) -> Dict[str, Any]:
        """Format forecast data for consistent output."""
        forecasts = []
        current_date = None
        daily_data = []
        
        for item in data['list'][:days * 8]:
            forecast_date = datetime.fromtimestamp(item['dt']).date()
            
            if current_date != forecast_date:
                if daily_data:
                    forecasts.append(self._aggregate_daily_forecast(daily_data))
                current_date = forecast_date
                daily_data = []
            
            daily_data.append(item)
        
        # Add the last day's data
        if daily_data:
            forecasts.append(self._aggregate_daily_forecast(daily_data))
        
        return {
            "location": f"{data['city']['name']}, {data['city']['country']}",
            "forecasts": forecasts[:days]
        }
    
    def _aggregate_daily_forecast(self, daily_data: List[Dict]) -> Dict[str, Any]:
        """Aggregate 3-hour forecasts into daily summary."""
        if not daily_data:
            return {}
        
        # Get temperatures for min/max calculation
        temps = [item['main']['temp'] for item in daily_data]
        
        # Use the forecast closest to noon for general conditions
        noon_forecast = min(daily_data, key=lambda x: abs(
            datetime.fromtimestamp(x['dt']).hour - 12
        ))
        
        return {
            "date": datetime.fromtimestamp(daily_data[0]['dt']).date().isoformat(),
            "temperature_min": min(temps),
            "temperature_max": max(temps),
            "description": noon_forecast['weather'][0]['description'].title(),
            "humidity": noon_forecast['main']['humidity'],
            "wind_speed": noon_forecast.get('wind', {}).get('speed', 0),
            "precipitation_probability": noon_forecast.get('pop', 0) * 100
        }