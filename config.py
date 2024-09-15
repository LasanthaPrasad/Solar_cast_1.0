import os
#from dotenv import load_dotenv

#load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or '11541514185144'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://') or 'sqlite:///solar_forecast.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SOLCAST_API_KEY = os.environ.get('SOLCAST_API_KEY') or 'your-solcast-api-key'
    VISUAL_CROSSING_API_KEY = os.environ.get('VISUAL_CROSSING_API_KEY')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')


    # Flask-Security config
    SECURITY_PASSWORD_SALT = 'your-password-salt'
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_UNAUTHORIZED_VIEW = None
    SECURITY_RECOVERABLE = True
    SECURITY_RESET_PASSWORD_WITHIN = '1 day'  # User has 5 days to reset password

    SECURITY_CONFIRMABLE = True
    SECURITY_SEND_REGISTER_EMAIL = True
    SECURITY_EMAIL_SUBJECT_REGISTER = "Welcome to GeoClipz Forecast Platform - Confirm Your Account"
    MAIL_DEFAULT_SENDER = 'GeoClipz <noreply@geoclipz.com>'    


 
