""" import os
import requests
from datetime import datetime
from . import db
from .models import ForecastLocation, IrradiationForecast

SOLCAST_API_KEY = os.environ.get('SOLCAST_API_KEY')
SOLCAST_BASE_URL = 'https://api.solcast.com.au/world_radiation/forecasts'

def fetch_solcast_forecasts():
    if not SOLCAST_API_KEY:
        print("Error: SOLCAST_API_KEY environment variable is not set")
        return False

    try:
        locations = ForecastLocation.query.all()
        for location in locations:
            params = {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'api_key': SOLCAST_API_KEY,
                'format': 'json',
                'hours': 72  # 3 days
            }

            response = requests.get(SOLCAST_BASE_URL, params=params)
            
            if response.status_code == 200:
                forecasts = response.json()['forecasts']
                for forecast in forecasts:
                    timestamp = datetime.fromisoformat(forecast['period_end'].replace('Z', '-05:30'))
                    
                    existing_forecast = IrradiationForecast.query.filter_by(
                        forecast_location_id=location.id,
                        timestamp=timestamp
                    ).first()

                    if existing_forecast:
                        existing_forecast.ghi = forecast['ghi']
                        existing_forecast.dni = forecast['dni']
                        existing_forecast.dhi = forecast['dhi']
                        existing_forecast.air_temp = forecast['air_temp']
                        existing_forecast.cloud_opacity = forecast['cloud_opacity']
                    else:
                        new_forecast = IrradiationForecast(
                            forecast_location_id=location.id,
                            timestamp=timestamp,
                            ghi=forecast['ghi'],
                            dni=forecast['dni'],
                            dhi=forecast['dhi'],
                            air_temp=forecast['air_temp'],
                            cloud_opacity=forecast['cloud_opacity']
                        )
                        db.session.add(new_forecast)

                db.session.commit()
            else:
                print(f"Error fetching forecast for location {location.id}: {response.status_code}")

        print("Forecast update completed")
        return True
    except Exception as e:
        print(f"Error updating forecasts: {str(e)}")
        return False """