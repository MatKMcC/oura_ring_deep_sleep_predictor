import datetime as dt
from dateutil import relativedelta
import pandas as pd
import requests
import psycopg2
from dateutil.relativedelta import relativedelta


def create_conn(config):
    # Connect and Collect
    conn = psycopg2.connect(
        host=config['db']['host']
        , user=config['db']['username']
        , connect_timeout=1
        , password=""
        , database=config['db']['dbname'])
    return conn

def create_connection_string(config):
    dbtype= config['db']['dbtype']
    host = config['db']['host']
    username = config['db']['username']
    dbname = config['db']['dbname']
    return f'{dbtype}+psycopg2://{username}@{host}:5432/{dbname}'

def retrieve_query(config, query):
    conn = create_conn(config)
    cursor = conn.cursor()
    cursor.execute(query)
    data = cursor.fetchall()
    column_names = [i[0] for i in cursor.description]
    df = pd.DataFrame(data, columns=column_names)
    conn.close()

    # decode binary data
    for el in df:
        if type(df[el][0]) == bytearray:
            df[el] = df[el].apply(lambda el: el.decode('utf-8') if el is not None else el)

    return df

def execute_query(config, query):
    conn = create_conn(config)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()

def update_daily_activity(config, headers, params):
    response = requests.get(config['api']['base_url'] + 'daily_activity', headers=headers, params=params)
    response = response.json()
    daily_activity_data = []
    for el in response['data']:
        feature_dict = {}
        feature_dict['id'] = el['id']
        feature_dict['date'] = el['day']
        feature_dict['timestamp'] = el['timestamp']
        feature_dict['steps'] = el['steps']
        feature_dict['sedentary_time'] = el['sedentary_time']
        feature_dict['resting_time'] = el['resting_time']
        feature_dict['high_activity_time'] = el['high_activity_time']
        feature_dict['low_activity_time'] = el['low_activity_time']
        feature_dict['medium_activity_time'] = el['medium_activity_time']
        feature_dict['active_calories'] = el['active_calories']
        feature_dict['total_calories'] = el['total_calories']
        feature_dict['inactivity_alerts'] = el['inactivity_alerts']
        daily_activity_data.append(feature_dict)
    daily_activity_data = pd.DataFrame(daily_activity_data)
    daily_activity_data.to_sql('daily_activity', create_connection_string(config), index=False, if_exists='replace')

def update_daily_readiness(config, headers, params):
    # Create Daily Readiness Data
    response = requests.get(config['api']['base_url'] + 'daily_readiness', headers=headers, params=params)
    response = response.json()
    daily_readiness_data = []
    for el in response['data']:
        feature_dict = {}
        feature_dict['id'] = el['id']
        feature_dict['date'] = el['day']
        feature_dict['timestamp'] = el['timestamp']
        feature_dict['score'] = el['score']
        feature_dict['temperature_deviation'] = el['temperature_deviation']
        feature_dict['body_temperature'] = el['contributors']['body_temperature']
        feature_dict['hrv_balance'] = el['contributors']['hrv_balance']
        daily_readiness_data.append(feature_dict)
    daily_readiness_data = pd.DataFrame(daily_readiness_data)
    _ = daily_readiness_data.to_sql('daily_readiness', create_connection_string(config), index=False, if_exists='replace')

def update_daily_stress(config, headers, params):
    response = requests.get(config['api']['base_url'] + 'daily_stress', headers=headers, params=params)
    response = response.json()
    daily_stress_data = []
    for el in response['data']:
        feature_dict = {}
        feature_dict['id'] = el['id']
        feature_dict['date'] = el['day']
        feature_dict['recovery_high'] = el['recovery_high']
        feature_dict['stress_high'] = el['stress_high']
        feature_dict['day_summary'] = el['day_summary']
        daily_stress_data.append(feature_dict)
    daily_stress_data = pd.DataFrame(daily_stress_data)
    _ = daily_stress_data.to_sql('daily_stress', create_connection_string(config), index=False, if_exists='replace')

def update_sleep(config, headers, params):
    response = requests.get(config['api']['base_url'] + 'sleep', headers=headers, params=params)
    response = response.json()
    sleep_data = []
    for el in response['data']:
        feature_dict = {}
        feature_dict['id'] = el['id']
        feature_dict['date'] = el['day']
        feature_dict['bedtime_start'] = el['bedtime_start']
        feature_dict['deep_sleep_duration'] = el['deep_sleep_duration']
        feature_dict['light_sleep_duration'] = el['light_sleep_duration']
        feature_dict['rem_sleep_duration'] = el['rem_sleep_duration']
        feature_dict['total_sleep_duration'] = el['total_sleep_duration']
        feature_dict['lowest_heart_rate'] = el['lowest_heart_rate']
        feature_dict['average_heart_rate'] = el['average_heart_rate']
        feature_dict['average_breath'] = el['average_breath']
        feature_dict['average_hrv'] = el['average_hrv']
        feature_dict['sleep_algorithm_version'] = el['sleep_algorithm_version']
        feature_dict['sleep_analysis_reason'] = el['sleep_analysis_reason']
        feature_dict['type'] = el['type']
        feature_dict['low_battery_alert'] = el['low_battery_alert']
        sleep_data.append(feature_dict)
    sleep_data = pd.DataFrame(sleep_data)
    _ = sleep_data.to_sql('sleep', create_connection_string(config), index=False, if_exists='replace')

def update_database(config):

    headers = {
        "Authorization": f"Bearer {config['user']['access_token']}",
        "Content-Type": "application/json",
    }

    params = {
        'start_date': config['user']['start_date']
      , 'end_date':  (dt.date.today() + relativedelta(days=1)).strftime('%Y-%m-%d')
    }

    print("Updating database...")
    print('-- Updating Daily Activity')
    update_daily_activity(config, headers, params)
    print('-- Updating Daily Readiness')
    update_daily_readiness(config, headers, params)
    print('-- Updating Daily Stress')
    update_daily_stress(config, headers, params)
    print('-- Updating Sleep')
    update_sleep(config, headers, params)
    print('Database Update Successful')