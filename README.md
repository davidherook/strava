# strava
Use the Strava api to pull your activity data

# Pull Data

Run:

```
python app/main.py
```

You will then be promted to visit the authorization page. Click the authorize button and paste the `code` from the url:

```
To authorise, visit:
http://www.strava.com/oauth/authorize?client_id=52233&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all,read_all
Then, paste the code you get from the resulting url below:

```

This will write all activity and stream data to `data/activity_data.csv`

# Map Routes

