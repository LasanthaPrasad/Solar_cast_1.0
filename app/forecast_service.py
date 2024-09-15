from .forecast_providers import SolcastProvider, VisualCrossingProvider, GeoclipzProvider
from .models import ForecastLocation, IrradiationForecast
from .extensions import db
import logging

logger = logging.getLogger(__name__)

class ForecastService:
    def __init__(self):
        print("ForecastService: Initializing")
        self.providers = {
            'solcast': SolcastProvider(),
            'visualcrossing': VisualCrossingProvider(),
            'geoclipz': GeoclipzProvider(),
        }
        print(f"ForecastService: Initialized with providers: {', '.join(self.providers.keys())}")


    def fetch_and_save_forecasts(self, location):
        print(f"Fetching forecasts for new location {location.id}")
        provider = self.providers.get(location.provider_name.lower())
        if not provider:
            raise ValueError(f"Unsupported provider: {location.provider_name}")

        try:
            data = provider.fetch_forecast(location)
            forecasts = provider.parse_forecast(data)
            
            # Clear existing forecasts for this location (if any)
            IrradiationForecast.query.filter_by(forecast_location_id=location.id).delete()
            
            # Add new forecasts
            for forecast in forecasts:
                forecast.forecast_location_id = location.id
                db.session.add(forecast)
            
            db.session.commit()
            print(f"Successfully fetched and saved forecasts for location {location.id}")
        except Exception as e:
            db.session.rollback()
            print(f"Error fetching forecasts for location {location.id}: {str(e)}")
            raise


    def fetch_forecasts(self, location):
        print(f"ForecastService: Fetching forecasts for location {location.id}")
        provider = self.providers.get(location.provider_name.lower())
        if not provider:
            print(f"ForecastService: Unsupported provider: {location.provider_name}")
            raise ValueError(f"Unsupported provider: {location.provider_name}")

        data = provider.fetch_forecast(location)
        forecasts = provider.parse_forecast(data)
        print(f"ForecastService: Fetched {len(forecasts)} forecasts for location {location.id}")
        return forecasts

    def update_forecasts(self):
        print("ForecastService: Starting forecast update process")
        locations = ForecastLocation.query.all()
        print(f"ForecastService: Found {len(locations)} locations to update")
        for location in locations:
            try:
                print(f"ForecastService: Processing location {location.id} ({location.provider_name})")
                forecasts = self.fetch_forecasts(location)
                
                print(f"ForecastService: Clearing existing forecasts for location {location.id}")
                IrradiationForecast.query.filter_by(forecast_location_id=location.id).delete()
                
                print(f"ForecastService: Adding {len(forecasts)} new forecasts for location {location.id}")
                for forecast in forecasts:
                    forecast.forecast_location_id = location.id
                    db.session.add(forecast)
                
                db.session.commit()
                print(f"ForecastService: Successfully updated forecasts for location {location.id}")
            except Exception as e:
                db.session.rollback()
                print(f"ForecastService: Error updating forecasts for location {location.id}: {str(e)}")
                logger.error(f"Error updating forecasts for location {location.id}: {str(e)}")
        
        print("ForecastService: Forecast update process complete")