"""
Writes a strava user's activity data to output/activity_data.csv for easier use
e.g. {tableau link} # TODO
"""

import os
import json
# import argparse
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from time import sleep

URL_AUTH = 'https://www.strava.com/oauth/token'
URL_ACTIVITIES = 'https://www.strava.com/api/v3/athlete/activities'
URL_ROUTE = 'https://www.strava.com/api/v3/activities/{activity_id}/streams/latlng,altitude,time'

ACTIVITIES_JSON_PATH = 'output/activity_data.json'
ACTIVITIES_CSV_PATH = 'output/activity_data.csv'

ROUTE_JSON_PATH = 'output/activity_streams/activity_stream_{activity_id}.json'

STRAVA_CLIENT_ID = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

class RateLimitExceeded(Exception):
    pass

def get_access_token(code):
    res = requests.post(
            url = URL_AUTH,
            data = {
                'client_id': STRAVA_CLIENT_ID,
                'client_secret': STRAVA_CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code'}
        )
    return res.json()['access_token']

def get_user_activities(access_token, save_to = None) -> List[Dict[Any, Any]]:
    data = requests.get(URL_ACTIVITIES,
        headers = {'Authorization': 'Bearer ' + access_token},
        params = {'per_page': 200, 'page': 1})
    if data.status_code == 429:
        raise RateLimitExceeded("\nExceeded Strava's rate limit. Response:\n {}".format(data.json()))
    if save_to:
        print(f"Writing user activities to {save_to}...")
        with open(save_to, 'w') as f:
            json.dump(data.json(), f)
    return data.json()

def get_route(access_token, activity_id, save_to = None):
    data = requests.get(URL_ROUTE.format(activity_id = activity_id),
        headers = {'Authorization': 'Bearer ' + access_token},
        params = {'per_page': 200, 'page': 1})
    if data.status_code == 429:
        raise RateLimitExceeded("\nExceeded Strava's rate limit. Response:\n {}".format(data.json()))
    if save_to:
        print(f'Writing activity stream {activity_id} to json...')
        with open(ROUTE_JSON_PATH.format(activity_id = activity_id), 'w') as f:
            json.dump(data.json(), f)
    return data.json()

def make_route_df(json_data: Dict[Any, Any]) -> pd.DataFrame:
    df = pd.DataFrame(json_data).set_index('type')
    data_latlng = df.loc['latlng']['data']
    data_time = df.loc['time']['data']
    assert len(data_latlng) == len(data_time)
    df = pd.DataFrame(data_latlng, columns=['lat','lng'])
    df['latlng_time'] = data_time
    return df

def meters_to_miles(meters: float) -> float:
    return meters / 1609.344

def mps_to_mph(meters_per_second: float) -> float:
    return meters_per_second * 2.23694

def mps_to_kph(meters_per_second: float) -> float:
    return meters_per_second * 3.6

def get_existing_activities(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        print('No existing strava data was found...')
        return None

def get_new_activities(existing_ids: List[int], all_ids: List[int]) -> List[int]:
    if existing_ids is None:
        return all_ids
    return list(set(all_ids) - set(existing_ids))

if __name__ == '__main__':

    # parser = argparse.ArgumentParser()
    # args = vars(parser.parse_args())

    url = f"http://www.strava.com/oauth/authorize?client_id={STRAVA_CLIENT_ID}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all,read_all"
    code = input(f'To authorize, visit:\n{url}\nThen, paste the code you get from the resulting url below:\n')
    access_token = get_access_token(code)

    print('\nGetting activities...')
    activities = get_user_activities(access_token)

    data = {
        'id': [],
        'date': [],
        'name': [],
        'type': [],
        'distance': [],
        'distance_miles': [],
        'moving_time': [],
        'moving_time_hrs': [],
        'city': [],
        'max_speed_mph': []
    }

    # Process each activity and populate the lists
    for a in activities:
        data['id'].append(a['id'])
        data['date'].append(a['start_date_local'])
        data['name'].append(a['name'])
        data['type'].append(a['type'])
        distance = a['distance']
        data['distance'].append(distance)
        data['distance_miles'].append(meters_to_miles(distance))
        data['moving_time'].append(a['moving_time'])
        data['moving_time_hrs'].append(a['moving_time'] / 3600)
        data['city'].append(a['location_city'])
        data['max_speed_mph'].append(mps_to_mph(a['max_speed']))

    # Create the DataFrame from the dictionary
    df = pd.DataFrame(data).set_index('id')
    df['mph'] = df['distance_miles'] / df['moving_time_hrs']

    # Get historical data
    df_historical = get_existing_activities(path = ACTIVITIES_CSV_PATH)
    existing_ids = list(df_historical['activity_id'].unique()) if df_historical is not None else None
    new_activity_ids = get_new_activities(existing_ids = existing_ids, all_ids = data['id'])

    print(f"Getting {len(new_activity_ids)} new activity streams...")
    all_dfs = []
    for i in new_activity_ids:
        try:
            route = get_route(access_token, i)
            df_route = make_route_df(route)
            df_route['activity_id'] = i
            all_dfs.append(df_route)
            sleep(0.1)
        except RateLimitExceeded as e:
            print(f"Rate limit exceeded. Got {len(all_dfs)} routes but cannot get more.")
            break
    streams = pd.concat(all_dfs)
    streams['activity_id'] = streams['activity_id'].astype(int)

    new_data = pd.merge(streams, df, how = 'left', left_on = 'activity_id', right_index = True)

    updated = pd.concat([df_historical, new_data])
    updated.to_csv(ACTIVITIES_CSV_PATH, index = False)
    print(f"Wrote updated activity routes to {ACTIVITIES_CSV_PATH}")
