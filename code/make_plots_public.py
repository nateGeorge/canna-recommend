import json
import requests
from requests.auth import HTTPBasicAuth
import plotly
import os
plotly.tools.set_config_file(world_readable=True, sharing='public')

username = os.environ['PLOTLY_UNAME'] # Replace with YOUR USERNAME
api_key = os.environ['PLOTLY_PASS'] # Replace with YOUR API KEY

auth = HTTPBasicAuth(username, api_key)
headers = {'Plotly-Client-Platform': 'python'}

page_size = 500
