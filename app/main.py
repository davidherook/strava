############################################################################
# https://www.strava.com/settings/api
#
# client id: 52233
# client secret: 1d12c3246ca75bda2e6601b3be3566a6972e13dc
#
#
# curl -X GET "https://www.strava.com/api/v3/athlete" "Authorization: Bearer [[token]]"
#
#
#
#
#
#
#
#
#
#
#
#
############################################################################
import os
import json 
import requests
import pandas as pd

def example_function():
    return 'a'

# def get_access_token():
#     url = 'https://www.strava.com/api/v3/oauth/token'
#     payload = {
#         'client_id': "52233",
#         'client_secret': "1d12c3246ca75bda2e6601b3be3566a6972e13dc",
#         'refresh_token': "2e225b1066d00c6edcce6647b11ac86b5d735a93",
#         'grant_type': "refresh_token",
#         'scope': 'activity:read_all',
#         'f': "json"
#     }
#     res = requests.post(url, data=payload, verify=False)
#     access_token = res.json()['access_token']
#     return access_token

# def get_code():

#     return code


def get_access_token(code):
    res = requests.post(
            url='https://www.strava.com/oauth/token',
            data={
                'client_id': 52233,
                'client_secret': "1d12c3246ca75bda2e6601b3be3566a6972e13dc",
                'code': code,
                'grant_type': 'authorization_code'
        }
    )
    return res.json()['access_token']

# def get_code():
#     url = 'https://www.strava.com/oauth/authorize'
#     # Enter this into browser, authorize, and store the code in the get_user_activities function
#     # http://www.strava.com/oauth/authorize?client_id=52233&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all
#     payload = {
#         'client_id': 52233,
#         'response_type': 'code',
#         'redirect_uri':'http://localhost/exchange_token',
#         'approval_prompt': 'force',
#         'scope': 'profile:read_all,activity:read_all'
#     }
#     res = requests.get(url, data=payload)
#     return res.url

def get_user_activities(access_token, save_json=True):
    url = 'https://www.strava.com/api/v3/athlete/activities'
    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    data = requests.get(url, headers=header, params=param)
    if save_json:
        with open('data/activities.json', 'w') as f:
            json.dump(data.json(), f)
    return data

# def convert_json_to_df(json_data_path):
#     json_data = pd.read

#     return pd.from_json(json_data)

def get_route(access_token, activity_id, save_json=True):
    url = f'https://www.strava.com/api/v3/activities/{activity_id}/streams/latlng,altitude,time'
    header = {'Authorization': 'Bearer ' + access_token}
    param = {'per_page': 200, 'page': 1}
    data = requests.get(url, headers=header, params=param)
    if save_json:
        print(f'Writing activity {activity_id} to json...')
        with open(f'data/activity_streams/activity_stream_{activity_id}.json', 'w') as f:
            json.dump(data.json(), f)
    return data.json()

def activity_stream_as_df(f):
    df = pd.read_json(f)
    df.set_index('type', inplace=True)
    data = df.loc['latlng']['data']
    df1 = pd.DataFrame(data, columns=['lat','lng'])
    # d1.to_csv('data/lat_long.csv')
    return df1

def make_route_df(json_data):
    df = pd.DataFrame(json_data)
    df.set_index('type', inplace=True)
    data = df.loc['latlng']['data']
    df1 = pd.DataFrame(data, columns=['lat','lng'])
    return df1


if __name__ == '__main__':



    # Using activities file, get all ids
    # with open('data/activities.json', 'r') as f:
    #     activities = json.loads(f.read())
    
    # activity_ids = [a['id'] for a in activities]
    # activity_ids.remove(3928170027)

    # Authorize
    url = 'http://www.strava.com/oauth/authorize?client_id=52233&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all,read_all'
    code = input(f'To authorise, visit:\n{url}\nThen, paste the code you get from the resulting url below:\n')
    access_token = get_access_token(code)

    # Get activities
    activities = get_user_activities(access_token, save_json=False)
    activities = json.loads(activities.text)

    names = [a['name'] for a in activities]
    ids = [a['id'] for a in activities]
    dates = [a['start_date_local'] for a in activities]
    distance = [a['distance'] for a in activities]
    moving_time = [a['moving_time'] for a in activities]
    city = [a['location_city'] for a in activities]

    df = pd.DataFrame({'date': dates, 'name': names, 'distance': distance, 
        'moving_time': moving_time, 'city': city}, index=ids)

    # Make DF of every activity stream
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


    


    

