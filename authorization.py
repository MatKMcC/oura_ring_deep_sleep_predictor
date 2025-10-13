# this script launches all authorization end points
# To Do
# -- update refresh token and authorization end points
# -- automagically grab oath token
# -- launch oath server
# -- function to authorize

# load config file
#

import webbrowser
from urllib.parse import urlencode
import requests
from dotenv import load_dotenv
import os


def update_env_variable(file_path, key, value):
    """
    Updates or adds an environment variable in a .env file.
    If the key exists, its value is updated. If not, a new entry is added.
    """
    lines = []
    found_key = False
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip().startswith(f"{key} = "):
                    lines.append(f"{key} = {value}\n")
                    found_key = True
                else:
                    lines.append(line)
    except FileNotFoundError:
        # If the file doesn't exist, start with an empty list of lines
        pass

    if not found_key:
        lines.append(f"{key} = {value}\n")

    with open(file_path, 'w') as f:
        f.writelines(lines)

# auth_url = f"https://cloud.ouraring.com/oauth/authorize?{urlencode(auth_params)}"
# print(f"Please visit this URL to authorize: {auth_url}")
# webbrowser.open(auth_url)

def authorize(config):

    print('Authorizing...')
    # step through authorization flow

    # check if the access_token exist / is valid
    # try:
    # check if the access_token exist / is valid
    headers = {
        "Authorization": f"Bearer {config['user']['access_token']}"
    }
    response = requests.get(config['api']['base_url'] + 'sleep', headers=headers)
    print(f'-- Trying Access Token: status code {response.status_code}')
    print(f'-- {str(response.json()):.150}')

    # if access_token is valid the log success
    if response.status_code == 200:
        print('Authorization Successful')

    # if access_token is not valid then fallback to refresh token or oauth
    elif response.status_code == 401:

        params = {
            'grant_type': 'refresh_token'
          , 'refresh_token': config['user']['refresh_token']
          , 'client_id': config['user']['client_id']
          , 'client_secret': config['user']['client_secret']
        }

        # check if the refresh_token exist / is valid
        response = requests.post('https://api.ouraring.com/oauth/token', params=urlencode(params))

        print(f'---- Trying Refresh Token: status code {response.status_code}')
        print(f'-- {str(response.json()):.150}')

        # if authorization successful, update params and log success
        if response.status_code == 200:

            print('Authorization Successful')
            print(response.json())

            # update access and refresh token
            response = response.json()
            config.set('user', 'access_token', response['access_token'])
            update_env_variable('.env', 'ACCESS_TOKEN', response['access_token'])
            config.set('user', 'refresh_token', response['refresh_token'])
            update_env_variable('.env', 'REFRESH_TOKEN', response['refresh_token'])

        # launch Oauth authorization process
        else:
            params = auth_params = {
                "client_id": config['user']['client_id'],
                "redirect_uri": config['user']['redirect_uri'],
                "response_type": "code",
            }
            auth_url = f"https://cloud.ouraring.com/oauth/authorize?{urlencode(params)}"
            webbrowser.open(auth_url)

            # get value from ngrok endpoint
            auth_code = input("Enter the authorization code from the redirect URL: ")
            params = {
                'grant_type': 'authorization_code'
              , 'code': auth_code
              , 'client_id': config['user']['client_id']
              , 'client_secret': config['user']['client_secret']
              , 'redirect_uri': config['user']['redirect_uri']
            }

            response = requests.post('https://api.ouraring.com/oauth/token', params=urlencode(params))
            # authenticate through URL
            # authorize application
            # capture code from endpoint

            print(f'------ Trying OAuth: {response.status_code}')
            print(f'-- {str(response.json()):.150}')

            if response.status_code == 200:

                # update access and refresh token:
                response = response.json()
                config.set('user', 'access_token', os.getenv("ACCESS_TOKEN"))
                update_env_variable('.env', 'ACCESS_TOKEN', response['access_token'])
                config.set('user', 'refresh_token', response['refresh_token'])
                update_env_variable('.env', 'REFRESH_TOKEN', response['refresh_token'])
