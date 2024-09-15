from flask_wtf import FlaskForm
#from wtforms import StringField, PasswordField, BooleanField, SubmitField
#from wtforms.validators import DataRequired, Email, EqualTo, Length
from .models import User
from wtforms import StringField, FloatField, SelectField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Email, EqualTo, Length,  ValidationError, Optional
import re
from flask_wtf.file import FileField, FileAllowed, FileAllowed, FileRequired





class BulkUploadForm(FlaskForm):
    file = FileField('CSV File', validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    data_type = SelectField('Data Type', choices=[
        ('forecast_locations', 'Forecast Locations'),
        ('grid_substations', 'Grid Substations'),
        ('feeders', 'Feeders'),
        ('solar_plants', 'Solar Plants')
    ])
    submit = SubmitField('Upload')


FORECAST_PROVIDERS = [
    ('solcast', 'Solcast'),
    #('visualcrossing', 'Visual Crossing'),
    ('geoclipz', 'GeoClipz Forecast'),
    #('openweather', 'OpenWeather')
    ]






def password_check(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError('Password must be at least 8 characters long.')
    if not re.search("[a-z]", password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    if not re.search("[A-Z]", password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search("[0-9]", password):
        raise ValidationError('Password must contain at least one number.')
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValidationError('Password must contain at least one special character.')

""" class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8), password_check])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')
       """  

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class ForecastLocationForm(FlaskForm):
    provider_name = SelectField('Provider Name', choices=FORECAST_PROVIDERS, validators=[DataRequired()])
    latitude = FloatField('Latitude', validators=[DataRequired(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[DataRequired(), NumberRange(min=-180, max=180)])
    api_key = StringField('API Key')



def int_or_empty(value):
    if value == '':
        return None
    return int(value)

class SolarPlantForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    latitude = FloatField('Latitude', validators=[DataRequired(), NumberRange(min=-90, max=90)])
    longitude = FloatField('Longitude', validators=[DataRequired(), NumberRange(min=-180, max=180)])
    grid_substation = SelectField('Grid Substation', coerce=int, validators=[DataRequired()])
    feeder = SelectField('Feeder', coerce=int_or_empty, validators=[Optional()])
    forecast_location = SelectField('Forecast Location', coerce=int, validators=[DataRequired()])
    installed_capacity = FloatField('Installed Capacity (MW)', validators=[DataRequired(), NumberRange(min=0)])
    panel_capacity = FloatField('Panel Capacity (MW)', validators=[DataRequired(), NumberRange(min=0)])
    inverter_capacity = FloatField('Inverter Capacity (MW)', validators=[DataRequired(), NumberRange(min=0)])
    plant_angle = FloatField('Plant Angle', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    api_status = SelectField('API Status', choices=[('enabled', 'Enabled'), ('disabled', 'Disabled')], validators=[DataRequired()])
    plant_efficiency = FloatField('Plant Efficiency', validators=[DataRequired(), NumberRange(min=0, max=1)])
    coefficient_factor = FloatField('Coefficient Factor', validators=[DataRequired(), NumberRange(min=0, max=1)])
    submit = SubmitField('Submit')