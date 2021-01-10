# Pull Your Strava Data
Use the Strava api to pull your activity data. 

## How To

Clone the repository, activate venv, and install requirements:
```
git clone https://github.com/davidherook/strava.git
python3 venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Find your Client ID from Strava here: https://www.strava.com/settings/api and use it to get your stats when you run the script:
```
python main.py --client_id [Client ID]
```

You will be prompted to visit the authorization page. Copy and paste the link into your browser and click the authorize button which will pop up. Copy the `code` from the resulting url and paste it back into terminal:

```
To authorize, visit:
http://www.strava.com/oauth/authorize?client_id=52233&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=profile:read_all,activity:read_all,read_all
Then, paste the code you get from the resulting url below:

```

This will write all activity and stream data to `output/activity_data.csv` so that you can make a [dashboard of all your activities](https://public.tableau.com/profile/david.herook#!/vizhome/PandemicRuns/PandemicRuns)

