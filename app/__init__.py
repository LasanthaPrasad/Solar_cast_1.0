from flask import Flask

##from apscheduler.schedulers.background import BackgroundScheduler

from .models import User, Role

from .extensions import db, security, mail, CustomUserDatastore

from flask_security import SQLAlchemyUserDatastore



from .routes import main as main_blueprint
from flask_mail import Mail





from datetime import datetime, timedelta, timezone


from .models import ForecastLocation
from .scheduler import init_app as init_scheduler



from .scheduler import init_app as init_scheduler

#db = SQLAlchemy()
##scheduler = BackgroundScheduler()

#user_datastore = None


#, static_folder='assets', static_url_path='/assets'






def create_app():
    """     app = Flask(__name__) """
    app = Flask(__name__, static_folder='assets', static_url_path='/assets')
    app.config.from_object('config.Config')
    app.config['MAIL_SERVER'] = 'smtp.cloudmta.net'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = '419506dea731b2f9'
    app.config['MAIL_PASSWORD'] = 'hTaBwGSQbfNVdin9WrdeMJnt'
    app.config['SECURITY_EMAIL_SENDER'] = 'no_reply@geoclipz.com'
    app.config['SECURITY_EMAIL_TEMPLATES'] = 'security/email'
    app.config['SECURITY_EMAIL_SUBJECT_PASSWORD_RESET'] = 'GeoClipz Password Reset Instructions'
    app.config['SECURITY_LOGIN_USER_TEMPLATE'] = 'security/login_user.html'
    #app.config['SECURITY_REGISTER_USER_TEMPLATE'] = 'register.html'
    app.config['SECURITY_FORGOT_PASSWORD_TEMPLATE'] = 'security/forgot_password.html'
    app.config['SECURITY_RESET_PASSWORD_TEMPLATE'] = 'security/reset_password.html'

    db.init_app(app)

    mail.init_app(app)
    


    user_datastore = CustomUserDatastore(db, User, Role)
    #user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore)

    # Store user_datastore in app.extensions for global access
    app.extensions['user_datastore'] = user_datastore


#user_datastore = CustomUserDatastore(db, User, Role)
#security = Security(app, user_datastore)
    #@app.before_first_request
    #def create_user():
    #    db.create_all()
    #    user_datastore.find_or_create_role(name='user', description='Regular user')
    #    user_datastore.find_or_create_role(name='moderator', description='Moderator')
    #    user_datastore.find_or_create_role(name='admin', description='Administrator')
    #    db.session.commit()



    with app.app_context():
        from . import models
        db.create_all()  # Create tables if they don't exist
        
 #       # Create roles
#        user_role = user_datastore.find_or_create_role(name='user', description='Regular user')
 #       admin_role = user_datastore.find_or_create_role(name='admin', description='Administrator')
        
        # Create users
 #       if not user_datastore.get_user('praasad@geoclipz.com'):
 #           user_datastore.create_user(email='praasad@geoclipz.com', password='admin', roles=[admin_role])
  #      if not user_datastore.get_user('ee.prasad@gmail.com'):
   #         user_datastore.create_user(email='ee.prasad@gmail.com', password='userq', roles=[user_role])
        
        # Start the scheduler

        # Initialize the scheduler last
        init_scheduler(app)
        # Import and register blueprints/routes here
        from .routes import main as main_blueprint
        app.register_blueprint(main_blueprint)
    


    return app

