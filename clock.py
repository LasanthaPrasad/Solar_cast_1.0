#from apscheduler.schedulers.blocking import BlockingScheduler
#from app.solcast_api import fetch_solcast_data

#sched = BlockingScheduler()

#@sched.scheduled_job('cron', hour='6-18')
#def scheduled_job():
#    fetch_solcast_data()

#sched.start()

""" 
from apscheduler.schedulers.blocking import BlockingScheduler
from app.forecast_service import ForecastService

sched = BlockingScheduler()
forecast_service = ForecastService()

@sched.scheduled_job('cron', hour='6-18')
def scheduled_job():
    forecast_service.update_forecasts()

sched.start()
 """
from app import create_app
from app.scheduler import update_forecast_locations

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        update_forecast_locations()
        