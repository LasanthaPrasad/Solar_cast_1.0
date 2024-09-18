import os
import requests
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from .models import IrradiationForecast
from zoneinfo import ZoneInfo



class BaseForecastProvider(ABC):
    @abstractmethod
    def fetch_forecast(self, location):
        pass

    @abstractmethod
    def parse_forecast(self, data):
        pass

class SolcastProvider(BaseForecastProvider):
    def fetch_forecast(self, location):
        print(f"SolcastProvider: Fetching forecast for location {location.id}")
        url = "https://api.solcast.com.au/world_radiation/forecasts"
        api_key = location.api_key or os.environ.get('SOLCAST_API_KEY')

        params = {
            'latitude': location.latitude,
            'longitude': location.longitude,
            'api_key': api_key,
            'format': 'json',
            'hours': 72  # 3 days
        }
        response = requests.get(url, params=params)
        print(f"SolcastProvider: API response status code: {response}")
        response.raise_for_status()
        return response.json()



    def parse_forecast(self, data):
        print("SolcastProvider: Parsing forecast data")
        forecasts = []
        for forecast in data['forecasts']:
            # Convert to datetime and adjust to start of the hour
            timestamp = datetime.fromisoformat(forecast['period_end'].replace('Z', '+00:00'))
            #timestamp = timestamp.replace(minute=0, second=0, microsecond=0)
            
            forecasts.append(IrradiationForecast(
                timestamp=timestamp,
                ghi=forecast['ghi'],
                dni=forecast['dni'],
                dhi=forecast['dhi'],
                air_temp=forecast.get('air_temp'),
                cloud_opacity=forecast.get('cloud_opacity')
            ))
        print(f"SolcastProvider: Parsed {len(forecasts)} forecast entries")
        return forecasts





"""     def parse_forecast(self, data):
        print("SolcastProvider: Parsing forecast data")
        forecasts = []
        for forecast in data['forecasts']:
            forecasts.append(IrradiationForecast(
                timestamp=datetime.fromisoformat(forecast['period_end'].replace('Z', '+00:00')),
                ghi=forecast['ghi'],
                dni=forecast['dni'],
                dhi=forecast['dhi'],
                air_temp=forecast.get('air_temp'),
                cloud_opacity=forecast.get('cloud_opacity')
            ))
        print(f"SolcastProvider: Parsed {len(forecasts)} forecast entries")
        return forecasts
 """




class VisualCrossingProvider(BaseForecastProvider):
    def fetch_forecast(self, location):
        print(f"VisualCrossingProvider: Fetching forecast for location {location.id}")
        coordinates = f"{location.latitude}%2C%20{location.longitude}"
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{coordinates}"
        api_key = location.api_key or os.environ.get('VISUAL_CROSSING_API_KEY')
        params = {
            'key': api_key,
            'include': 'hours',
            'elements': 'datetime,solarradiation,temp,cloudcover',
            'unitGroup': 'metric',
            'contentType': 'json'
        }
        response = requests.get(url, params=params)
        print(f"VisualCrossingProvider: API response status code: {response}")
        response.raise_for_status()
        return response.json()


    def parse_forecast(self, data):
        print("VisualCrossingProvider: Parsing forecast data")
        forecasts = []
        local_timezone = ZoneInfo(data['timezone'])
        for day in data['days']:
            date = datetime.strptime(day['datetime'], '%Y-%m-%d').date()
            for hour in day['hours']:
                time = datetime.strptime(hour['datetime'], '%H:%M:%S').time()
                local_dt = datetime.combine(date, time)
                local_dt = local_dt.replace(tzinfo=local_timezone)
                utc_dt = local_dt.astimezone(timezone.utc)
                
                forecasts.append(IrradiationForecast(
                    timestamp=utc_dt,
                    ghi=hour['solarradiation'],
                    air_temp=hour['temp'],
                    cloud_opacity=hour['cloudcover'] / 100  # Convert to 0-1 scale
                ))
        print(f"VisualCrossingProvider: Parsed {len(forecasts)} forecast entries")
        return forecasts




"""     def parse_forecast(self, data):
        print("VisualCrossingProvider: Parsing forecast data")
        forecasts = []
        timezone = ZoneInfo(data['timezone'])
        for day in data['days']:
            date = datetime.strptime(day['datetime'], '%Y-%m-%d').date()
            for hour in day['hours']:
                time = datetime.strptime(hour['datetime'], '%H:%M:%S').time()
                local_dt = datetime.combine(date, time)
                local_dt = local_dt.replace(tzinfo=timezone)
                utc_dt = local_dt.astimezone(ZoneInfo('UTC'))
                
                forecasts.append(IrradiationForecast(
                    timestamp=utc_dt,
                    ghi=hour['solarradiation'],
                    air_temp=hour['temp'],
                    cloud_opacity=hour['cloudcover'] / 100  # Convert to 0-1 scale
                ))
        print(f"VisualCrossingProvider: Parsed {len(forecasts)} forecast entries")
        return forecasts """


class GeoclipzProvider(BaseForecastProvider):
    def fetch_forecast(self, location):
        print(f"GeoClipzProvider: Fetching forecast for location {location.id}")
        coordinates = f"{location.latitude}%2C%20{location.longitude}"
        url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{coordinates}"
        api_key = location.api_key or os.environ.get('VISUAL_CROSSING_API_KEY')
        params = {
            'key': api_key,
            'include': 'hours',
            'elements': 'datetime,solarradiation,temp,cloudcover',
            'unitGroup': 'metric',
            'contentType': 'json'
        }
        response = requests.get(url, params=params)
        print(f"GeoClipzProvider: API response status code: {response}")
        response.raise_for_status()
        return response.json()



    def parse_forecast(self, data):
        print("GeoClipzProvider: Parsing forecast data")
        forecasts = []
        local_timezone = ZoneInfo(data['timezone'])
        for day in data['days']:
            date = datetime.strptime(day['datetime'], '%Y-%m-%d').date()
            for hour in day['hours']:
                time = datetime.strptime(hour['datetime'], '%H:%M:%S').time()
                local_dt = datetime.combine(date, time)
                local_dt = local_dt.replace(tzinfo=local_timezone)
                utc_dt = local_dt.astimezone(timezone.utc)
                
                forecasts.append(IrradiationForecast(
                    timestamp=utc_dt,
                    ghi=hour['solarradiation'],
                    air_temp=hour['temp'],
                    cloud_opacity=hour['cloudcover'] / 100  # Convert to 0-1 scale
                ))
        print(f"GeoClipzProvider: Parsed {len(forecasts)} forecast entries")
        return forecasts






""" 
    def parse_forecast(self, data):
        print("GeoClipzProvider: Parsing forecast data")
        forecasts = []
        timezone = ZoneInfo(data['timezone'])
        for day in data['days']:
            date = datetime.strptime(day['datetime'], '%Y-%m-%d').date()
            for hour in day['hours']:
                time = datetime.strptime(hour['datetime'], '%H:%M:%S').time()
                local_dt = datetime.combine(date, time)
                local_dt = local_dt.replace(tzinfo=timezone)
                utc_dt = local_dt.astimezone(ZoneInfo('UTC'))
                
                forecasts.append(IrradiationForecast(
                    timestamp=utc_dt,
                    ghi=hour['solarradiation'],
                    air_temp=hour['temp'],
                    cloud_opacity=hour['cloudcover'] / 100  # Convert to 0-1 scale
                ))
        print(f"GeoClipzProvider: Parsed {len(forecasts)} forecast entries")
        return forecasts """