
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app,Response
#from . import db
from .models import ForecastLocation, IrradiationForecast, SolarPlant, GridSubstation, Feeder, User, Role
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import joinedload
import uuid
from .auth import require_api_key
from flask_security import login_required, roles_required, roles_accepted, login_user, current_user

from flask import render_template, redirect, url_for, request, flash

from flask_security.views import reset_password, forgot_password
from flask_security.utils import hash_password
from flask_security.confirmable import confirm_user

#from flask_wtf import FlaskForm
#from wtforms import StringField, FloatField, SelectField, PasswordField, BooleanField, SubmitField
#from wtforms.validators import DataRequired, NumberRange, Email, EqualTo, Length
from .forecast_service import ForecastService
#from . import user_datastore  # Assuming user_datastore is defined in __init__.py

from .forms import RegistrationForm, LoginForm, ForecastLocationForm, SolarPlantForm


#from config import FORECAST_PROVIDERS  # or from wherever you defined the providers

    # config.py or a new file like providers.py

#from .extensions import db, security, user_datastore
from .extensions import db, security
import string
import random




from flask import render_template, flash, redirect, url_for, current_app
#from . import db
#from .models import User
#from .forms import RegistrationForm
#from flask_security import current_user
from sqlalchemy import text

import csv
import io
#from flask import request, flash
#from flask_security import roles_required
from .forms import BulkUploadForm
#from .models import ForecastLocation, GridSubstation, Feeder, SolarPlant

import pandas as pd
from io import StringIO, BytesIO
import logging

logger = logging.getLogger(__name__)

from .utils import calculate_distance

main = Blueprint('main', __name__)



from flask import jsonify, current_app
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

import pandas as pd


@main.route('/api/aggregate_forecast')
def aggregate_forecast():
    now = datetime.now(timezone.utc)
    start_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=12)
    end_time = start_time + timedelta(hours=24)

    print(f"Current UTC time: {now}")
    print(f"Fetching forecasts from {start_time} to {end_time}")

    substations = GridSubstation.query.all()
    print(f"Found {len(substations)} substations")

    hourly_data = {start_time + timedelta(hours=i): {'sum': 0.0, 'count': 0} for i in range(25)}

    for substation in substations:
        forecasts = IrradiationForecast.query.filter(
            IrradiationForecast.forecast_location_id == substation.forecast_location,
            IrradiationForecast.timestamp >= start_time,
            IrradiationForecast.timestamp <= end_time
        ).order_by(IrradiationForecast.timestamp).all()

        print(f"Found {len(forecasts)} forecasts for substation {substation.id}")

        for forecast in forecasts:
            hour_key = forecast.timestamp.replace(minute=0, second=0, microsecond=0)
            if forecast.ghi is not None and substation.installed_solar_capacity is not None:
                estimated_mw = (forecast.ghi / 150) * float(substation.installed_solar_capacity) * 0.15
                
                hourly_data[hour_key]['sum'] += estimated_mw
                hourly_data[hour_key]['count'] += 1

                print(f"Substation {substation.id}, Hour: {hour_key}, GHI: {forecast.ghi}, Capacity: {substation.installed_solar_capacity}, Estimated MW: {estimated_mw}")
            else:
                print(f"Invalid data for substation {substation.id}, forecast_location_id: {substation.forecast_location}, GHI: {forecast.ghi}, Installed capacity: {substation.installed_solar_capacity}")

    # Calculate the average for each hour
    final_hourly_data = {}
    for hour, data in hourly_data.items():
        if data['count'] > 0:
            final_hourly_data[hour] = data['sum'] / data['count']
        else:
            final_hourly_data[hour] = 0.0

    print(f"Hourly data after processing: {final_hourly_data}")

    # Convert to pandas Series for easy resampling and interpolation
    s = pd.Series(final_hourly_data)
    s = s.resample('30T').interpolate(method='cubic')  # Resample to 30-minute intervals and interpolate

    result = {
        'current_utc_time': now.isoformat(),
        'timestamps': s.index.strftime('%Y-%m-%dT%H:%M:%S%z').tolist(),
        'total_estimated_mw': s.tolist(),
        'hourly_data': {k.isoformat(): v for k, v in final_hourly_data.items()}  # Include original hourly data
    }

    print(f"Final result: {result}")
    return jsonify(result)



""" 

@main.route('/api/aggregate_forecast')
def aggregate_forecast():
    now = datetime.now(timezone.utc)
    start_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    end_time = start_time + timedelta(hours=24)  # 4 hours of hourly data

    print(f"Current UTC time: {now}")
    print(f"Fetching forecasts from {start_time} to {end_time}")

    substations = GridSubstation.query.all()
    print(f"Found {len(substations)} substations")

    hourly_data = {start_time + timedelta(hours=i): 0.0 for i in range(5)}

    for substation in substations:
        forecasts = IrradiationForecast.query.filter(
            IrradiationForecast.forecast_location_id == substation.forecast_location,
            IrradiationForecast.timestamp >= start_time,
            IrradiationForecast.timestamp <= end_time
        ).order_by(IrradiationForecast.timestamp).all()

        print(f"Found {len(forecasts)} forecasts for substation {substation.id}")

        for forecast in forecasts:
            hour_key = forecast.timestamp.replace(minute=0, second=0, microsecond=0)
            if hour_key not in hourly_data:
                print(f"Unexpected hour key: {hour_key}")
                hourly_data[hour_key] = 0.0
            if forecast.ghi is not None and substation.installed_solar_capacity is not None:
                estimated_mw = (forecast.ghi / 150) * float(substation.installed_solar_capacity) * 0.15
                # Check the forecast provider and handle accordingly
                if substation.forecast_location_rel.provider_name.lower() == 'solcast':
                    # For Solcast, we'll average the two 30-minute readings
                    hourly_data[hour_key]['sum'] += estimated_mw
                    hourly_data[hour_key]['count'] += 1
                else:
                    # For hourly data, we'll just use the value as-is
                    hourly_data[hour_key]['sum'] = estimated_mw
                    hourly_data[hour_key]['count'] = 1


                print(f"Substation {substation.id}, Hour: {hour_key}, GHI: {forecast.ghi}, Capacity: {substation.installed_solar_capacity}, Estimated MW: {estimated_mw}")
            else:
                print(f"Invalid data for substation {substation.id}, forecast_location_id: {substation.forecast_location}, GHI: {forecast.ghi}, Installed capacity: {substation.installed_solar_capacity}")

    print(f"Hourly data before processing: {hourly_data}")



    # Calculate the final hourly values
    final_hourly_data = {}
    for hour, data in hourly_data.items():
        if data['count'] > 0:
            final_hourly_data[hour] = data['sum'] / data['count']
        else:
            final_hourly_data[hour] = 0.0

    print(f"Hourly data after processing: {final_hourly_data}")

    # Convert to pandas Series for interpolation
    s = pd.Series(final_hourly_data)
    s = s.resample('30T').interpolate(method='cubic')  # Resample to 30-minute intervals and interpolate





    result = {
        'current_utc_time': now.isoformat(),
        'timestamps': s.index.strftime('%Y-%m-%dT%H:%M:%S%z').tolist(),
        'total_estimated_mw': s.tolist(),
        'hourly_data': {k.isoformat(): v for k, v in hourly_data.items()}  # Include original hourly data
    }

    print(f"Final result: {result}")
    return jsonify(result)

 """


















""" 
@main.route('/api/aggregate_forecast')
def aggregate_forecast():
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=24)

    print(f"Current UTC time: {now}")
    print(f"Fetching forecasts from {start_time} to {end_time}")

    # Query all substations
    substations = GridSubstation.query.all()
    print(f"Found {len(substations)} substations")

    aggregated_data = {}

    for substation in substations:
        # Get forecast data for this substation's location
        forecasts = IrradiationForecast.query.filter(
            IrradiationForecast.forecast_location_id == substation.forecast_location,
            IrradiationForecast.timestamp >= start_time,
            IrradiationForecast.timestamp <= end_time
        ).order_by(IrradiationForecast.timestamp).all()

        print(f"Found {len(forecasts)} forecasts for substation {substation.id}")

        for forecast in forecasts:
            timestamp = forecast.timestamp.isoformat()
            if timestamp not in aggregated_data:
                aggregated_data[timestamp] = 0

            if forecast.ghi is not None and substation.installed_solar_capacity is not None:
                estimated_mw = (forecast.ghi / 150) * float(substation.installed_solar_capacity) * 0.15
                aggregated_data[timestamp] += estimated_mw
                print(f"Substation {substation.id}, Timestamp: {timestamp}, GHI: {forecast.ghi}, Capacity: {substation.installed_solar_capacity}, Estimated MW: {estimated_mw}")
            else:
                print(f"Invalid data for substation {substation.id}, forecast_location_id: {substation.forecast_location}, GHI: {forecast.ghi}, Installed capacity: {substation.installed_solar_capacity}")

    # Sort the data and prepare the response
    sorted_data = sorted(aggregated_data.items())
    result = {
        'current_utc_time': now.isoformat(),
        'timestamps': [item[0] for item in sorted_data],
        'total_estimated_mw': [item[1] for item in sorted_data]
    }

    current_app.logger.info(f"Final result: {result}")
    return jsonify(result)
 """

""" 




@main.route('/api/aggregate_forecast')
def aggregate_forecast():
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=1)
    end_time = now + timedelta(hours=2)

    current_app.logger.info(f"Fetching forecasts from {start_time} to {end_time}")

    forecasts = IrradiationForecast.query.filter(
        IrradiationForecast.timestamp >= start_time,
        IrradiationForecast.timestamp <= end_time
    ).all()

    current_app.logger.info(f"Found {len(forecasts)} forecasts")

    aggregated_data = {}
    for forecast in forecasts:
        timestamp = forecast.timestamp.isoformat()
        if timestamp not in aggregated_data:
            aggregated_data[timestamp] = 0
        
        substation = GridSubstation.query.filter_by(forecast_location=forecast.forecast_location_id).first()
        if substation and substation.installed_solar_capacity and forecast.ghi:
            estimated_mw = (forecast.ghi / 1000) * substation.installed_solar_capacity * 0.15
            aggregated_data[timestamp] += estimated_mw
            current_app.logger.info(f"Timestamp: {timestamp}, GHI: {forecast.ghi}, Capacity: {substation.installed_solar_capacity}, Estimated MW: {estimated_mw}")
        else:
            current_app.logger.warning(f"Invalid data for forecast_location_id: {forecast.forecast_location_id}, GHI: {forecast.ghi}, Substation capacity: {substation.installed_solar_capacity if substation else 'N/A'}")

    current_app.logger.info(f"Aggregated data: {aggregated_data}")

    if all(value == 0 for value in aggregated_data.values()):
        current_app.logger.warning("All aggregated values are zero")

    sorted_data = sorted(aggregated_data.items())
    result = {
        'timestamps': [item[0] for item in sorted_data],
        'total_estimated_mw': [item[1] for item in sorted_data]
    }
    current_app.logger.info(f"Final result: {result}")
    return jsonify(result)

 """




""" 

@main.route('/api/aggregate_forecast')
def aggregate_forecast():
    now = datetime.now(timezone.utc)
    start_time = now
    end_time = now + timedelta(hours=2)

    forecasts = IrradiationForecast.query.filter(
        IrradiationForecast.timestamp >= start_time,
        IrradiationForecast.timestamp <= end_time
    ).all()

    print(f"FFFFF Plantdfgdfgdfgdfg {forecasts}")
    aggregated_data = {}
    for forecast in forecasts:
        timestamp = forecast.timestamp.isoformat()
        #if timestamp not in aggregated_data:
        #    aggregated_data[timestamp] = 0
        
        substation = GridSubstation.query.filter_by(forecast_location=forecast.forecast_location_id).first()
        print(f"substations: {substation}")      

        if substation:
            # Use the same calculation as in the individual forecast
            estimated_mw = (forecast.ghi / 1000) * float(substation.installed_solar_capacity) * 0.15
            aggregated_data[timestamp] += estimated_mw
    print(f"FFFFF Plantdfgdfgdfgdfg {estimated_mw}")

    sorted_data = sorted(aggregated_data.items())
    print(f"FFFFF Plantdfgdfgdfgdfg {sorted_data}")
    return jsonify({
        'timestamps': [item[0] for item in sorted_data],
        'total_estimated_mw': [item[1] for item in sorted_data]
    })

 """

@main.route('/admin/download/<entity_type>')
@roles_required('admin')
def download_csv(entity_type):
    if entity_type == 'forecast_locations':
        data = ForecastLocation.query.all()
        fieldnames = ['provider_name', 'latitude', 'longitude', 'api_key']
    elif entity_type == 'grid_substations':
        data = GridSubstation.query.all()
        fieldnames = ['name', 'code', 'latitude', 'longitude', 'installed_solar_capacity', 'api_status', 'forecast_location']
    elif entity_type == 'feeders':
        data = Feeder.query.all()
        fieldnames = ['name', 'code', 'grid_substation', 'installed_solar_capacity', 'status']
    elif entity_type == 'solar_plants':
        data = SolarPlant.query.all()
        fieldnames = ['name', 'latitude', 'longitude', 'grid_substation', 'feeder', 'forecast_location', 
                      'installed_capacity', 'panel_capacity', 'inverter_capacity', 'plant_angle', 
                      'company', 'api_status', 'plant_efficiency', 'coefficient_factor']
    else:
        return "Invalid entity type", 400

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for item in data:
        row = {field: getattr(item, field) for field in fieldnames}
        writer.writerow(row)

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={entity_type}.csv"}
    )




@main.route('/assign_forecast_locations', methods=['POST'])
@roles_required('admin')  # Ensure only admins can trigger this
def trigger_assign_forecast_locations():
    try:
        assign_nearest_forecast_locations()
        return jsonify({"message": "Successfully assigned nearest forecast locations to all grid substations."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

def assign_nearest_forecast_locations():
    grid_substations = GridSubstation.query.all()
    forecast_locations = ForecastLocation.query.all()

    for substation in grid_substations:
        nearest_location = None
        min_distance = float('inf')

        for location in forecast_locations:
            distance = calculate_distance(
                substation.latitude, substation.longitude,
                location.latitude, location.longitude
            )

            if distance < min_distance:
                min_distance = distance
                nearest_location = location

        if nearest_location:
            substation.forecast_location = nearest_location.id
            print(f"Assigned forecast location {nearest_location.id} to substation {substation.id}")

    db.session.commit()
    print("Finished assigning nearest forecast locations to all grid substations.")




def check_for_errors(data_type, csv_data):
    df = pd.read_csv(StringIO(csv_data))
    errors = []

    if data_type == 'solar_plants':
        # Check for duplicate locations
        duplicates = df[df.duplicated(subset=['latitude', 'longitude'], keep=False)]
        for index, row in duplicates.iterrows():
            errors.append(f"Row {index + 2}: Duplicate location ({row['latitude']}, {row['longitude']})")

        # Check for invalid grid substation IDs
        valid_substation_ids = set(GridSubstation.query.with_entities(GridSubstation.id).all())
        invalid_substations = df[~df['grid_substation'].isin(valid_substation_ids)]
        for index, row in invalid_substations.iterrows():
            errors.append(f"Row {index + 2}: Invalid grid substation ID {row['grid_substation']}")

    elif data_type == 'grid_substations':
        # Check for duplicate names
        duplicates = df[df.duplicated(subset=['name'], keep=False)]
        for index, row in duplicates.iterrows():
            errors.append(f"Row {index + 2}: Duplicate substation name '{row['name']}'")

        # Check for duplicate locations
        duplicates = df[df.duplicated(subset=['latitude', 'longitude'], keep=False)]
        for index, row in duplicates.iterrows():
            errors.append(f"Row {index + 2}: Duplicate location ({row['latitude']}, {row['longitude']})")

    # Add more checks for other data types as needed

    return errors

def create_error_report(errors):
    df = pd.DataFrame(errors, columns=['Error'])
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8')
    output.seek(0)
    return output.getvalue()







@main.route('/admin/sample_csv/<data_type>')
@roles_required('admin')
def sample_csv(data_type):
    if data_type == 'forecast_locations':
        csv_data = "provider_name,latitude,longitude,api_key\nsolcast,40.7128,-74.0060,your_api_key_here\n"
    elif data_type == 'grid_substations':
        csv_data = "name,code,latitude,longitude,installed_solar_capacity,api_status\nSubstation A,SUB001,40.7128,-74.0060,100.5,disabled\n"
    elif data_type == 'feeders':
        csv_data = "name,code,grid_substation,installed_solar_capacity,status\nFeeder A,FDR001,1,50.25,active\n"

    elif data_type == 'solar_plants':
        csv_data = "name,latitude,longitude,grid_substation,feeder,forecast_location,installed_capacity,panel_capacity,inverter_capacity,plant_angle,company,api_status,plant_efficiency,coefficient_factor\nPlant1,40.7128,-74.0060,1,1,1,100.5,110.0,95.0,30.0,Company A,enabled,0.85,0.9\nPlant2,34.0522,-118.2437,2,2,2,75.3,80.0,70.0,25.0,Company B,enabled,0.83,0.88\n"

    else:
        return "Invalid data type", 400

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition":
                 f"attachment; filename={data_type}_sample.csv"}
    )



@main.route('/admin/bulk_upload', methods=['GET', 'POST'])
@roles_required('admin')
def admin_bulk_upload():
    form = BulkUploadForm()
    if form.validate_on_submit():
        csv_file = request.files['file']
        data_type = form.data_type.data
        
        if csv_file:
            try:
                csv_data = csv_file.stream.read().decode("UTF-8")
                current_app.logger.info(f"CSV Data: {csv_data}")  # Log the CSV data
                csv_file = StringIO(csv_data)
                csv_reader = csv.DictReader(csv_file)
                df = pd.read_csv(csv_file)

                if data_type == 'forecast_locations':
                    process_forecast_locations(csv_reader)
                elif data_type == 'grid_substations':
                    process_grid_substations(csv_reader)
                elif data_type == 'feeders':
                    process_feeders(csv_reader)
                elif data_type == 'solar_plants':
                    process_solar_plants(df)
                





               # Log the first few rows of the CSV
                for i, row in enumerate(csv_reader):
                    if i < 5:  # Log only the first 5 rows
                        current_app.logger.info(f"Row {i+1}: {row}")
                    else:
                        break
                csv_file.seek(0)  # Reset the file pointer to the beginning











                flash(f'Bulk upload for {data_type} completed successfully!', 'success')
            except Exception as e:
                current_app.logger.error(f'Error during bulk upload: {str(e)}', exc_info=True)
                flash(f'Error during bulk upload: {str(e)}', 'error')
        
    return render_template('admin/bulk_upload.html', form=form)



""" 


@main.route('/admin/bulk_upload', methods=['GET', 'POST'])
@roles_required('admin')
def admin_bulk_upload():
    form = BulkUploadForm()
    if form.validate_on_submit():
        csv_file = request.files['file']
        data_type = form.data_type.data
        
        if csv_file:
            csv_file = csv_file.read().decode('utf-8')
            csv_data = csv.DictReader(io.StringIO(csv_file))
            
            try:
                if data_type == 'forecast_locations':
                    process_forecast_locations(csv_data)
                elif data_type == 'grid_substations':
                    process_grid_substations(csv_data)
                elif data_type == 'feeders':
                    process_feeders(csv_data)
                elif data_type == 'solar_plants':
                    process_solar_plants(csv_data)
                
                flash(f'Bulk upload for {data_type} completed successfully!', 'success')
            except Exception as e:
                flash(f'Error during bulk upload: {str(e)}', 'error')
        
    return render_template('admin/bulk_upload.html', form=form)

 """
def process_forecast_locations(csv_reader):
    for row in csv_reader:
        location = ForecastLocation(
            provider_name=row['provider_name'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            api_key=row.get('api_key')
        )
        db.session.add(location)
    db.session.commit()

def process_grid_substations(csv_reader):
    for row in csv_reader:
        substation = GridSubstation(
            name=row['name'],
            code=row['code'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            installed_solar_capacity=float(row['installed_solar_capacity']),
            api_status=row['api_status']
        )
        db.session.add(substation)
    db.session.commit()

def process_feeders(csv_reader):
    for row in csv_reader:
        feeder = Feeder(
            name=row['name'],
            code=row['code'],
            grid_substation=int(row['grid_substation']),
            installed_solar_capacity=float(row['installed_solar_capacity']),
            status=row['status']
        )
        db.session.add(feeder)
    db.session.commit()


def process_solar_plants(csv_reader):
    for row in csv_reader:
        try:
            plant = SolarPlant(
                name=row['name'],
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                grid_substation=int(row['grid_substation']),
                feeder=int(row['feeder']),
                forecast_location=int(row['forecast_location']),
                installed_capacity=float(row['installed_capacity']),
                panel_capacity=float(row['panel_capacity']),
                inverter_capacity=float(row['inverter_capacity']),
                plant_angle=float(row['plant_angle']),
                company=row['company'],
                api_status=row['api_status'],
                plant_efficiency=float(row['plant_efficiency']),
                coefficient_factor=float(row['coefficient_factor'])
            )
            db.session.add(plant)
        except KeyError as e:
            current_app.logger.error(f"Missing column in CSV: {str(e)}")
            db.session.rollback()
            raise ValueError(f"Missing column in CSV: {str(e)}")
        except ValueError as e:
            current_app.logger.error(f"Invalid data in CSV: {str(e)}")
            db.session.rollback()
            raise ValueError(f"Invalid data in CSV: {str(e)}")
    db.session.commit()




""" 
def process_solar_plants(csv_data):
    for row in csv_data:
        plant = SolarPlant(
            name=row['name'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            grid_substation=int(row['grid_substation']),
            feeder=int(row['feeder']),
            forecast_location=int(row['forecast_location']),
            installed_capacity=float(row['installed_capacity']),
            panel_capacity=float(row['panel_capacity']),
            inverter_capacity=float(row['inverter_capacity']),
            plant_angle=float(row['plant_angle']),
            company=row['company'],
            api_status=row['api_status']
        )
        db.session.add(plant)
    db.session.commit()

 """
def process_solar_plants(csv_data):
    df = pd.read_csv(StringIO(csv_data))
    for _, row in df.iterrows():
        plant = SolarPlant(
            name=row['name'],
            latitude=float(row['latitude']),
            longitude=float(row['longitude']),
            grid_substation=int(row['grid_substation']),
            feeder=int(row['feeder']),
            forecast_location=int(row['forecast_location']),
            installed_capacity=float(row['installed_capacity']),
            panel_capacity=float(row['panel_capacity']),
            inverter_capacity=float(row['inverter_capacity']),
            plant_angle=float(row['plant_angle']),
            company=row['company'],
            api_status=row['api_status'],
            plant_efficiency=float(row['plant_efficiency']),
            coefficient_factor=float(row['coefficient_factor'])
        )
        db.session.add(plant)
    db.session.commit()











@main.route('/register', methods=['GET', 'POST'])
def register():
    current_app.logger.info("Entering register route")
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    current_app.logger.info(f"Form created: {form}")
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        flash('A confirmation email has been sent to your email address. Please check your inbox to activate your account.', 'info')
        return redirect(url_for('main.login'))
    current_app.logger.info(f"Rendering template with form: {form}")
    return render_template('register.html', title='Register', form=form)




@main.route('/confirm/<token>')
def confirm_email(token):
    user_datastore = current_app.extensions['user_datastore']
    try:
        user = confirm_user(token)
        if user:
            user_datastore.commit()
            flash('Thank you for confirming your email address. Your account is now active.', 'success')
            return redirect(url_for('security.login'))
        else:
            flash('The confirmation link is invalid or has expired.', 'danger')
    except Exception as e:
        flash('An error occurred while confirming your email.', 'danger')
    return redirect(url_for('main.index'))


@main.route('/view_data')
@login_required
def view_data():
    # All logged in users can view this
    return render_template('view_data.html')

@main.route('/edit_data')
@roles_accepted('moderator', 'admin')
def edit_data():
    # Only moderators and admins can access this
    return render_template('edit_data.html')

@main.route('/manage_users')
#@roles_required('admin')
def manage_users():
    # Only admins can access this
    users = User.query.all()
    return render_template('manage_users.html', users=users)



""" 
@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('A confirmation email has been sent to your email address. Please check your inbox to activate your account.', 'info')
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

 """

""" 

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        user.set_password_confirm(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('A confirmation email has been sent to your email address. Please check your inbox to activate your account.', 'info')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

 """
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.confirmed_at:
                flash('Please confirm your account. Check your email for the confirmation link.', 'warning')
                return redirect(url_for('main.login'))
            login_user(user, remember=form.remember_me.data)
            return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password', 'danger')
    return render_template('login.html', title='Sign In', form=form)






@main.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@roles_required('admin')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    db.session.commit()
    status = 'activated' if user.active else 'deactivated'
    flash(f'User {user.email} has been {status}', 'success')
    return redirect(url_for('main.manage_users'))

@main.route('/reset_user_password/<int:user_id>', methods=['POST'])
@roles_required('admin')
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    user.password = hash_password(new_password)
    db.session.commit()
    
    # Here you would typically send an email to the user with their new password
    # For this example, we'll just flash it (not secure for production!)
    flash(f'Password for {user.email} has been reset. New password: {new_password}', 'success')
    return redirect(url_for('main.manage_users'))

# Update the existing change_user_role function
@main.route('/change_user_role/<int:user_id>', methods=['POST'])
@roles_required('admin')
def change_user_role(user_id):
    user_datastore = current_app.extensions['user_datastore']
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in ['user', 'moderator', 'admin']:
        # Remove all existing roles
        for role in user.roles:
            user_datastore.remove_role_from_user(user, role)
        # Add the new role
        role = Role.query.filter_by(name=new_role).first()
        if role:
            user_datastore.add_role_to_user(user, role)
            db.session.commit()
            flash(f'Role updated for user {user.email} to {new_role}', 'success')
        else:
            flash(f'Role {new_role} not found', 'error')
    else:
        flash(f'Invalid role specified', 'error')
    return redirect(url_for('main.manage_users'))






def init_routes(app):

    user_datastore = current_app.extensions['user_datastore']
    @app.route('/reset', methods=['GET', 'POST'])
    def reset():
        return security.forgot_password_view()

    @app.route('/reset/<token>', methods=['GET', 'POST'])
    def reset_with_token(token):
        return security.reset_password_view(token)

    @app.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        if request.method == 'POST':
            password = request.form.get('password')
            if password:
                current_user.password = hash_password(password)
                user_datastore.put(current_user)
                db.session.commit()
                flash('Password updated successfully.', 'success')
                return redirect(url_for('profile'))
        return render_template('change_password.html')



def init_app(app):
    init_routes(app)







#@main.route('/forgot-password', endpoint='security_forgot_password')
#def forgot_password():
#    return security_forgot_password()



@main.route('/profile')
@login_required
def profile():
    """User profile page route"""
    return render_template('profile.html', user=current_user)

@main.route('/admin')
@roles_required('admin')
def admin():
    """Admin dashboard route"""
    # Here you might want to fetch some admin-specific data
    form = BulkUploadForm()
    return render_template('admin.html', form=form)

















@main.route('/solar_plants/<int:id>/generate_api_key', methods=['POST'])
def generate_solar_plant_api_key(id):
    plant = SolarPlant.query.get_or_404(id)
    plant.api_key = str(uuid.uuid4())
    db.session.commit()
    flash('New API key generated for Solar Plant', 'success')
    return redirect(url_for('main.solar_plants'))



















@main.route('/grid_substations')
def grid_substations():
    substations = GridSubstation.query.order_by(GridSubstation.name).all()
    substations_data = [{
        'id': s.id,
        'name': s.name,
        'code': s.code,
        'latitude': float(s.latitude),
        'longitude': float(s.longitude),
        'installed_solar_capacity': float(s.installed_solar_capacity),
        'api_key': s.api_key,
        'api_status': s.api_status,
        'forecast_location': s.forecast_location
    } for s in substations]
    return render_template('grid_substations.html', substations=substations, substations_data=substations_data)



""" 

@main.route('/api/substation_forecast/<int:substation_id>')
def get_substation_forecast(substation_id):
    substation = GridSubstation.query.get_or_404(substation_id)
    forecasts = calculate_substation_forecasts(substation)
    return jsonify(forecasts)

def calculate_substation_forecasts(substation):
    now = datetime.now(timezone.utc)
    three_days_later = now + timedelta(days=3)

    # Get the forecast location for this substation
    forecast_location = ForecastLocation.query.get(substation.forecast_location)

    if not forecast_location:
        return {"error": "No forecast location associated with this substation"}

    forecasts = IrradiationForecast.query.filter_by(forecast_location_id=forecast_location.id).filter(            
        IrradiationForecast.timestamp >= now,
        IrradiationForecast.timestamp <= three_days_later
    ).order_by(IrradiationForecast.timestamp).all()

    if not forecasts:
        return {"error": "No forecast data available"}

    substation_forecasts = []
    for forecast in forecasts:
        # This is a simplified calculation. You might need a more complex model.
        estimated_mw = (forecast.ghi / 150) * substation.installed_solar_capacity * 0.15  # Assuming 15% efficiency
        substation_forecasts.append({
            'timestamp': forecast.timestamp.isoformat(),
            'estimated_mw': estimated_mw
        })

    return {
        'timestamps': [f['timestamp'] for f in substation_forecasts],
        'estimated_mw': [f['estimated_mw'] for f in substation_forecasts]
    }


 """





@main.route('/api/plant_forecast')
@require_api_key
def get_plant_forecast(plant_id):
    plant = SolarPlant.query.get_or_404(plant_id)
    forecasts = calculate_plant_forecasts(plant)
    return jsonify(forecasts)


def calculate_plant_forecasts(plant):
        
        now = datetime.now(timezone.utc)
        three_days_later = now + timedelta(days=1)


        forecasts = IrradiationForecast.query.filter_by(forecast_location_id=plant.forecast_location).filter(            
            IrradiationForecast.timestamp >= now,
            IrradiationForecast.timestamp <= three_days_later
        ).order_by(IrradiationForecast.timestamp).all()

        #print(f"FFFFF Plantdfgdfgdfgdfg {forecasts}")


        if not forecasts:
            return jsonify({'error': 'No forecast data available'}), 404



        plant_forecasts = []
        for forecast in forecasts:
        # This is a simplified calculation. You might need a more complex model.
            estimated_mw = (forecast.ghi / 150) * plant.installed_capacity * 0.15  # Assuming 15% efficiency
            plant_forecasts.append({
            'timestamp': forecast.timestamp.isoformat(),
            'estimated_mw': estimated_mw
        })

        return plant_forecasts



@main.route('/api/plant_forecast/<int:plant_id>')
def get_plant_forecast1(plant_id):
    plant = SolarPlant.query.get_or_404(plant_id)
    forecasts = calculate_plant_forecasts(plant)
    return jsonify(forecasts)


@main.route('/api/check_forecasts/<int:location_id>')
def check_forecasts(location_id):

    now = datetime.now(timezone.utc)
    three_days_later = now + timedelta(days=1)
        
    forecasts = IrradiationForecast.query.filter(
            IrradiationForecast.forecast_location_id == location_id,
            IrradiationForecast.timestamp >= now,
            IrradiationForecast.timestamp <= three_days_later
        ).order_by(IrradiationForecast.timestamp).all()



    #forecasts = IrradiationForecast.query.filter_by(forecast_location_id=location_id).limit(100).all()
    return jsonify([{
        'timestamp': f.timestamp.isoformat(),
        'ghi': f.ghi,
        'dni': f.dni,
        'dhi': f.dhi
    } for f in forecasts])


@main.route('/api/location_forecast/<int:location_id>')
def get_location_forecast(location_id):
    try:
        now = datetime.now(timezone.utc)
        three_days_later = now + timedelta(days=3)
        
        forecasts = IrradiationForecast.query.filter(
            IrradiationForecast.forecast_location_id == location_id,
            IrradiationForecast.timestamp >= now,
            IrradiationForecast.timestamp <= three_days_later
        ).order_by(IrradiationForecast.timestamp).all()

        if not forecasts:
            return jsonify({'error': 'No forecast data available'}), 404

        timestamps = [f.timestamp.isoformat() for f in forecasts]
        ghi_values = [f.ghi for f in forecasts]
        dni_values = [f.dni for f in forecasts]
        dhi_values = [f.dhi for f in forecasts]

        return jsonify({
            'timestamps': timestamps,
            'ghi': ghi_values,
            'dni': dni_values,
            'dhi': dhi_values
        })
    except Exception as e:
        print(f"Error in get_location_forecast: {str(e)}")  # Server-side logging
        return jsonify({'error': str(e)}), 500







def recalculate_all_substation_capacities():
    substations = GridSubstation.query.all()
    for substation in substations:
        substation.update_installed_capacity()
    db.session.commit()



#@app.route('/')
#def index():
#    total_mw = db.session.query(db.func.sum(SolarPlant.installed_capacity)).scalar() or 0
#    total_capacity = db.session.query(db.func.sum(GridSubstation.installed_solar_capacity)).scalar() or 0
#    return render_template('index.html', total_mw=total_mw, total_capacity=total_capacity)


@main.route('/')
def index():
    total_mw = db.session.query(db.func.sum(SolarPlant.installed_capacity)).scalar() or 0
    total_capacity = db.session.query(db.func.sum(GridSubstation.installed_solar_capacity)).scalar() or 0
    forecast_locations = ForecastLocation.query.all()
    
    # Add this print statement for debugging
    print(f"Number of forecast locations: {len(forecast_locations)}")
    
    return render_template('index.html', 
                           total_mw=total_mw, 
                           total_capacity=total_capacity,
                           forecast_locations=forecast_locations)







# Forecast Locations
@main.route('/forecast_locations')
def forecast_locations():

    locations = ForecastLocation.query.order_by(ForecastLocation.id).all()

    return render_template('forecast_locations.html', locations=locations)











@main.route('/forecast_locations/create', methods=['GET', 'POST'])
def create_forecast_location():
    form = ForecastLocationForm()
    if form.validate_on_submit():
        location = ForecastLocation(
            provider_name=form.provider_name.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            api_key=form.api_key.data
        )
        db.session.add(location)
        db.session.commit()


        forecast_service = ForecastService()
        try:
            forecast_service.fetch_and_save_forecasts(location)
            flash('Forecast location created and initial forecast data fetched successfully', 'success')
        except Exception as e:
            flash(f'Forecast location created, but failed to fetch initial forecast data: {str(e)}', 'warning')



        flash('Forecast location created successfully', 'success')
        return redirect(url_for('main.forecast_locations'))
    return render_template('create_forecast_location.html', form=form)

@main.route('/forecast_locations/<int:id>/edit', methods=['GET', 'POST'])
def edit_forecast_location(id):
    location = ForecastLocation.query.get_or_404(id)
    form = ForecastLocationForm(obj=location)
    if form.validate_on_submit():
        form.populate_obj(location)
        db.session.commit()
        forecast_service = ForecastService()
        try:
            forecast_service.fetch_and_save_forecasts(location)
            flash('Forecast location created and initial forecast data fetched successfully', 'success')
        except Exception as e:
            flash(f'Forecast location created, but failed to fetch initial forecast data: {str(e)}', 'warning')



        flash('Forecast location updated successfully', 'success')
        return redirect(url_for('main.forecast_locations'))
    return render_template('edit_forecast_location.html', form=form, location=location)




@main.route('/forecast_locations/<int:location_id>/delete', methods=['POST'])
def delete_forecast_location(location_id):
    location = ForecastLocation.query.get_or_404(location_id)
    try:
        # First, delete all associated irradiation forecasts
        IrradiationForecast.query.filter_by(forecast_location_id=location_id).delete()
        
        # Then delete the forecast location
        db.session.delete(location)
        db.session.commit()
        flash('Forecast location and associated forecasts deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting forecast location: {str(e)}', 'error')
    return redirect(url_for('main.forecast_locations'))






@main.route('/grid_substations/<int:id>/generate_api_key', methods=['POST'])
def generate_grid_substation_api_key(id):
    substation = GridSubstation.query.get_or_404(id)
    substation.api_key = str(uuid.uuid4())
    db.session.commit()
    flash('New API key generated for Grid Substation', 'success')
    return redirect(url_for('main.grid_substations'))










@main.route('/api/substation_forecast/<int:substation_id>')
def get_substation_forecast(substation_id):
    substation = GridSubstation.query.get_or_404(substation_id)
    print(f"substation ID : {substation_id}")
    forecasts = calculate_substation_forecasts(substation)
    return jsonify(forecasts)

#@main.route('/api/check_forecasts_sub/<substation>')
def calculate_substation_forecasts(substation):
    now = datetime.now(timezone.utc)
    three_days_later = now + timedelta(days=1)

    # Get the forecast location for this substation
    """ 
    forecast_location = ForecastLocation.query.get(substation.forecast_location)
    print(f"FFFFF Location {forecast_location}")




    if not forecast_location:
        return {"error": "No forecast location associated with this substation"}

    """
    forecasts = IrradiationForecast.query.filter_by(forecast_location_id=substation.forecast_location).filter(            
        IrradiationForecast.timestamp >= now,
        IrradiationForecast.timestamp <= three_days_later
    ).order_by(IrradiationForecast.timestamp).all()

   # print(f"FFFFF Locationdfgdfgdfgdfg {forecasts}")

    if not forecasts:
        return {"error": "No forecast data available"}
    
    substation_forecasts = []
    for forecast in forecasts:
    # This is a simplified calculation. You might need a more complex model.
        estimated_mw = (forecast.ghi / 150) *  float(substation.installed_solar_capacity) * 0.15  # Assuming 15% efficiency
        substation_forecasts.append({
        'timestamp': forecast.timestamp.isoformat(),
        'estimated_mw': estimated_mw
    })

    #print(f" return forecast  {substation_forecasts}")
    return substation_forecasts




"""     substation_forecasts = []
    for forecast in forecasts:
        # Simple calculation: GHI * installed capacity * efficiency factor
        estimated_mw = (forecast.ghi / 1000) * substation.installed_solar_capacity * 0.15  # Assuming 15% efficiency
        substation_forecasts.append({
            'timestamp': forecast.timestamp.isoformat(),
            'estimated_mw': estimated_mw
        })

    return {
        'timestamps': [f['timestamp'] for f in substation_forecasts],
        'estimated_mw': [f['estimated_mw'] for f in substation_forecasts]
    } """






@main.route('/grid_substations/create', methods=['GET', 'POST'])
def create_grid_substation():
    if request.method == 'POST':
        substation = GridSubstation(
            name=request.form['name'],
            code=request.form['code'],
            latitude=float(request.form['latitude']),
            longitude=float(request.form['longitude']),
            installed_solar_capacity=float(request.form['installed_solar_capacity']),
            forecast_location = int(request.form['forecast_location']),
            api_status=request.form['api_status']
        )
        db.session.add(substation)
        db.session.commit()
        flash('Grid Substation created successfully!', 'success')
        return redirect(url_for('main.grid_substations'))
    forecast_locations = ForecastLocation.query.all()
    return render_template('create_grid_substation.html', forecast_locations=forecast_locations)



@main.route('/grid_substations/<int:id>/edit', methods=['GET', 'POST'])
def edit_grid_substation(id):
    substation = GridSubstation.query.get_or_404(id)
    if request.method == 'POST':
        substation.name = request.form['name']
        substation.code = request.form['code']
        substation.latitude = float(request.form['latitude'])
        substation.longitude = float(request.form['longitude'])
        substation.installed_solar_capacity = float(request.form['installed_solar_capacity'])
        substation.forecast_location = int(request.form['forecast_location'])
        substation.api_status=request.form['api_status']

        db.session.commit()
        flash('Grid Substation updated successfully!', 'success')
        return redirect(url_for('main.grid_substations'))

    forecast_locations = ForecastLocation.query.all()
    return render_template('edit_grid_substation.html', substation=substation, forecast_locations=forecast_locations)

@main.route('/grid_substations/<int:id>/delete', methods=['POST'])
def delete_grid_substation(id):
    substation = GridSubstation.query.get_or_404(id)
    db.session.delete(substation)
    db.session.commit()
    flash('Grid Substation deleted successfully!', 'success')
    return redirect(url_for('main.grid_substations'))



@main.route('/feeders/create', methods=['GET', 'POST'])
def create_feeder():
    if request.method == 'POST':
        try:
            feeder = Feeder(
                name=request.form['name'],
                code=request.form['code'],
                grid_substation=int(request.form['grid_substation']),
                installed_solar_capacity=float(request.form['installed_solar_capacity']),
                status=request.form['status']
            )
            db.session.add(feeder)
            db.session.commit()
            
            # Update Grid Substation capacity
            substation = GridSubstation.query.get(feeder.grid_substation)
            substation.update_installed_capacity()
            
            flash('Feeder created successfully!', 'success')
            return redirect(url_for('main.feeders'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating Feeder: {str(e)}', 'danger')

    substations = GridSubstation.query.all()
    return render_template('create_feeder.html', substations=substations)

@main.route('/feeders/<int:id>/edit', methods=['GET', 'POST'])
def edit_feeder(id):
    feeder = Feeder.query.get_or_404(id)
    old_status = feeder.status
    old_substation_id = feeder.grid_substation

    if request.method == 'POST':
        try:
            feeder.name = request.form['name']
            feeder.code = request.form['code']
            feeder.grid_substation = int(request.form['grid_substation'])
            feeder.installed_solar_capacity = float(request.form['installed_solar_capacity'])
            feeder.status = request.form['status']
            db.session.commit()
            
            # Update old Grid Substation capacity if changed
            if old_substation_id != feeder.grid_substation or old_status != feeder.status:
                old_substation = GridSubstation.query.get(old_substation_id)
                old_substation.update_installed_capacity()
            
            # Update new Grid Substation capacity
            new_substation = GridSubstation.query.get(feeder.grid_substation)
            new_substation.update_installed_capacity()
            
            flash('Feeder updated successfully!', 'success')
            return redirect(url_for('main.feeders'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating Feeder: {str(e)}', 'danger')

    substations = GridSubstation.query.order_by(GridSubstation.name).all()
    return render_template('edit_feeder.html', feeder=feeder, substations=substations)

@main.route('/feeders/<int:id>/delete', methods=['POST'])
def delete_feeder(id):
    feeder = Feeder.query.get_or_404(id)
    try:
        substation = GridSubstation.query.get(feeder.grid_substation)
        db.session.delete(feeder)
        db.session.commit()
        
        # Update Grid Substation capacity
        substation.update_installed_capacity()
        
        flash('Feeder deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting Feeder: {str(e)}', 'danger')
    return redirect(url_for('main.feeders'))





# Feeders
@main.route('/feeders')
def feeders():
    feeders = Feeder.query.options(db.joinedload(Feeder.grid_substation_rel)).order_by(Feeder.name).all()
    return render_template('feeders.html', feeders=feeders)



@main.route('/solar_plants')
def solar_plants():
    plants = SolarPlant.query.options(
        joinedload(SolarPlant.grid_substation_rel),
        joinedload(SolarPlant.feeder_rel)
    ).order_by(SolarPlant.id).all()
    return render_template('solar_plants.html', plants=plants)

# Solar Plants
#@app.route('/solar_plants')
#def solar_plants():
#    plants = SolarPlant.query.all()
#    return render_template('solar_plants.html', plants=plants)







@main.route('/solar_plants/create', methods=['GET', 'POST'])
def create_solar_plant():
    form = SolarPlantForm()

    substations = GridSubstation.query.order_by(GridSubstation.name).all()
    print(f"Number of Gridss : {len(substations)}")

    form.grid_substation.choices = [(s.id, s.name) for s in substations]
    form.forecast_location.choices = [(f.id, f"{f.provider_name} ({f.latitude}, {f.longitude})") for f in ForecastLocation.query.all()]
    print(f"Grid substation choices: {form.grid_substation.choices}")
    # Initialize feeder choices with an empty option
    form.feeder.choices = [('', 'Select a Grid Substation first')]


    if form.validate_on_submit():
        try:
            plant = SolarPlant(
                name=form.name.data,
                latitude=form.latitude.data,
                longitude=form.longitude.data,
                grid_substation=form.grid_substation.data,
                feeder=form.feeder.data if form.feeder.data is not None else None,
                forecast_location=form.forecast_location.data,
                installed_capacity=form.installed_capacity.data,
                panel_capacity=form.panel_capacity.data,
                inverter_capacity=form.inverter_capacity.data,
                plant_angle=form.plant_angle.data,
                company=form.company.data,
                api_status=form.api_status.data,
                plant_efficiency=form.plant_efficiency.data,
                coefficient_factor=form.coefficient_factor.data
            )
            db.session.add(plant)
            db.session.commit()
            flash('Solar Plant created successfully!', 'success')
            return redirect(url_for('main.solar_plants'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating Solar Plant: {str(e)}', 'danger')
        

    return render_template('create_solar_plant.html', form=form)






""" 
@main.route('/solar_plants/create', methods=['GET', 'POST'])
def create_solar_plant():
    form = SolarPlantForm()

    substations = GridSubstation.query.all()
    print(f"Number of Gridss : {len(substations)}")
    form.grid_substation.choices = [(s.id, s.name) for s in substations]
    current_app.logger.info(f"Grid substation choices: {form.grid_substation.choices}")
    print(f"Grid substation choices: {form.grid_substation.choices}")

    form.forecast_location.choices = [(f.id, f"{f.provider_name} ({f.latitude}, {f.longitude})") for f in ForecastLocation.query.all()]
   

    # Populate the choices for grid_substation and forecast_location
    form.grid_substation.choices = [(s.id, s.name) for s in GridSubstation.query.all()]
    form.forecast_location.choices = [(f.id, f"{f.provider_name} ({f.latitude}, {f.longitude})") for f in ForecastLocation.query.all()]


    # Initialize feeder choices with an empty option
    form.feeder.choices = [('', 'Select a Grid Substation first')]
    print("feeders route")


    if form.validate_on_submit():
        plant = SolarPlant(
            name=form.name.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            grid_substation=form.grid_substation.data,
            feeder=form.feeder.data,
            forecast_location=form.forecast_location.data,
            installed_capacity=form.installed_capacity.data,
            panel_capacity=form.panel_capacity.data,
            inverter_capacity=form.inverter_capacity.data,
            plant_angle=form.plant_angle.data,
            company=form.company.data,
            api_status=form.api_status.data,
            plant_efficiency=form.plant_efficiency.data,
            coefficient_factor=form.coefficient_factor.data
        )
        db.session.add(plant)
        db.session.commit()
        flash('Solar Plant created successfully!', 'success')
        return redirect(url_for('main.solar_plants'))
    
    return render_template('create_solar_plant.html', form=form)

 """
@main.route('/get_feeders/<int:substation_id>')
def get_feeders(substation_id):
    current_app.logger.info(f"Fetching feeders for substation ID: {substation_id}")
    print("feeders route 12348444")
    # Get the SQL query as a string
    query = Feeder.query.filter_by(grid_substation=substation_id).statement
    current_app.logger.info(f"SQL Query: {query}")
    #print(f"SQL Query: {query}") 
    feeders = Feeder.query.filter_by(grid_substation=substation_id).all()
    current_app.logger.info(f"Found {len(feeders)} feeders")
    #print(f"Found {len(feeders)} feeders")
    feeder_list = [{'id': f.id, 'name': f.name} for f in feeders]
    current_app.logger.info(f"Feeder list: {feeder_list}")
    return jsonify(feeder_list)



@main.route('/solar_plants/<int:id>/edit', methods=['GET', 'POST'])
def edit_solar_plant(id):
    plant = SolarPlant.query.get_or_404(id)
    form = SolarPlantForm(obj=plant)

    # Populate the choices for grid_substation and forecast_location
    form.grid_substation.choices = [(s.id, s.name) for s in GridSubstation.query.all()]
    form.forecast_location.choices = [(f.id, f"{f.provider_name} ({f.latitude}, {f.longitude})") for f in ForecastLocation.query.all()]
    
    # Initially populate feeder choices based on the current grid substation
    if plant.grid_substation:
        feeders = Feeder.query.filter_by(grid_substation=plant.grid_substation).all()
        form.feeder.choices = [(f.id, f.name) for f in feeders]
    else:
        form.feeder.choices = [('', 'Select a Grid Substation first')]

    if form.validate_on_submit():
        try:
            form.populate_obj(plant)
            db.session.commit()
            flash('Solar Plant updated successfully!', 'success')
            return redirect(url_for('main.solar_plants'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating Solar Plant: {str(e)}', 'danger')

    return render_template('edit_solar_plant.html', form=form, plant=plant)










@main.route('/solar_plants/<int:id>/delete', methods=['POST'])
def delete_solar_plant(id):
    plant = SolarPlant.query.get_or_404(id)
    db.session.delete(plant)
    db.session.commit()
    flash('Solar Plant deleted successfully!', 'success')
    return redirect(url_for('main.solar_plants'))


