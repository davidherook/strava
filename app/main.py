######################################
# https://www.strava.com/settings/api
#
# python app/main.py
######################################

import os
import json 
import requests
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

def get_access_token(code):
    res = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': 52233,
                'client_secret': "1d12c3246ca75bda2e6601b3be3566a6972e13dc",
                'code': code,
                'grant_type': 'authorization_code'}
        )
    return res.json()['access_token']

def get_user_activities(access_token, save_json=True):
    url = 'https://www.strava.com/api/v3/athlete/activities'
    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    data = requests.get(url, headers=header, params=param)
    if save_json:
        print(f'Writing user activities to data/activities.json...')
        with open('data/activities.json', 'w') as f:
            json.dump(data.json(), f)
    return data

def get_route(access_token, activity_id, save_json=True):
    url = f'https://www.strava.com/api/v3/activities/{activity_id}/streams/latlng,altitude,time'
    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    data = requests.get(url, headers=header, params=param)
    if save_json:
        print(f'Writing activity stream {activity_id} to json...')
        with open(f'data/activity_streams/activity_stream_{activity_id}.json', 'w') as f:
            json.dump(data.json(), f)
    return data.json()

def make_route_df(json_data):
    df = pd.DataFrame(json_data)
    df.set_index('type', inplace=True)
    data = df.loc['latlng']['data']
    df1 = pd.DataFrame(data, columns=['lat','lng'])
    return df1

def meters_to_miles(meters):
    return meters / 1609.344

# def scale_column(col):
#     return MinMaxScaler().fit_transform(col)



if __name__ == '__main__':

    url = 'http://www.strava.com/oauth/authorize?client_id=52233&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all,read_all'
    code = input(f'To authorise, visit:\n{url}\nThen, paste the code you get from the resulting url below:\n')
    access_token = get_access_token(code)

    # Get activities
    print('\nGetting activities...')
    activities = get_user_activities(access_token, save_json=False)
    activities = json.loads(activities.text)

    names = [a['name'] for a in activities]
    ids = [a['id'] for a in activities]
    dates = [a['start_date_local'] for a in activities]
    distance = [a['distance'] for a in activities]
    distance_miles = [meters_to_miles(d) for d in distance]
    moving_time = [a['moving_time'] for a in activities]
    moving_time_hrs = [s / (60*60) for s in moving_time]

    city = [a['location_city'] for a in activities]

    df = pd.DataFrame({'date': dates, 'name': names, 'distance': distance, 'distance_miles': distance_miles,
        'moving_time': moving_time, 'moving_time_hrs': moving_time_hrs, 'city': city}, index=ids)
    df['mph'] = df['distance_miles'] / df['moving_time_hrs']

    scaler = MinMaxScaler()
    t = scaler.fit_transform(df[['distance_miles','moving_time_hrs','mph']])
    df[['distance_miles_scaled','moving_time_hrs_scaled','mph_scaled']] = t


    # df['distance_miles_scaled'] = scale_column(df['distance_miles'].reshape(-1, 1))
    # df['moving_time_hrs_scaled'] = scale_column(df['moving_time_hrs'].reshape(-1, 1))
    # df['mph_scaled'] = scale_column(df['mph'].reshape(-1, 1))

    # Get activity streams
    print('Getting activity streams...')
    all_dfs = []
    for i in ids: 
        route = get_route(access_token, i, save_json=False)
        df_route = make_route_df(route)
        df_route['activity_id'] = i
        all_dfs.append(df_route)
    streams = pd.concat(all_dfs)
    streams['activity_id'] = streams['activity_id'].astype(int)

    merged = pd.merge(streams, df, how='left', left_on='activity_id', right_index=True)
    merged.to_csv('data/activity_data.csv')


    


    

