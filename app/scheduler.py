from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime

def update_forecast_locations():
    print("update_forecast_locations function called")
    from .forecast_service import ForecastService
    forecast_service = ForecastService()
    forecast_service.update_forecasts()

def start_scheduler(app):
    print("start_scheduler function called")
    scheduler = BackgroundScheduler()
    
    def run_job():
        with app.app_context():
            update_forecast_locations()

    scheduler.add_job(
        func=run_job,
        trigger=CronTrigger(hour="*/1"),
        id="update_forecasts",
        name="Update forecast locations every hour",
        replace_existing=True,
    )
    
    
    # Run immediately when the scheduler starts
    scheduler.add_job(
        func=run_job,
        trigger='date',
        run_date=datetime.now(),
        id="initial_update",
        name="Initial forecast update",
    )
    
    scheduler.start()
    print("Scheduler started")

def init_app(app):
    print("init_app function called")
    start_scheduler(app)