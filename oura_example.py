import requests
import json
from urllib.parse import urlencode
import webbrowser

from dotenv import load_dotenv
import os

load_dotenv()
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")

# TODO:
# 1. capture authorization code through listening process
# 2. capture access_token
# 3. capture refresh_token
# 4. authentication process to check and see if access_token and refresh_token are valid
# 5. read access and refresh token from environment
# 6. update environment access and refresh token from script
# 7. Make data call for visualization

# Make Data Access Call
headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
sleep_data = requests.get(
    "https://api.ouraring.com/v2/usercollection/sleep",
    headers=headers,
    params={"start_date": "2025-01-01", "end_date": "2025-01-07"})

print(sleep_data.text)



# Your OAuth2 application credentials
CLIENT_ID = "RAELOBHOLLY7C4JX"
CLIENT_SECRET = "IHUJGLBETFJVR35CSEINTKI3ELQIIUQR"
REDIRECT_URI = "https://zechariah-distichous-alberto.ngrok-free.dev"

# Step 1: Direct user to authorization page
auth_params = {
    "client_id": CLIENT_ID,
    "redirect_uri": REDIRECT_URI,
    "response_type": "code",
    "scope": "daily heartrate personal"
}
auth_url = f"https://cloud.ouraring.com/oauth/authorize?{urlencode(auth_params)}"
print(f"Please visit this URL to authorize: {auth_url}")
webbrowser.open(auth_url)

# Step 2: Exchange authorization code for access token
# After user authorizes, they'll be redirected to your redirect URI with a code parameter
auth_code = input("Enter the authorization code from the redirect URL: ")

token_url = "https://api.ouraring.com/oauth/token"
token_data = {
    "grant_type": "authorization_code",
    "code": auth_code,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI
}
response = requests.post(token_url, data=token_data)
tokens = response.json()
print(tokens)
access_token = tokens["access_token"]
refresh_token = tokens["refresh_token"]

# Step 3: Use the access token to make API calls
headers = {"Authorization": f"Bearer {access_token}"}
sleep_data = requests.get(
    "https://api.ouraring.com/v2/usercollection/sleep",
    headers=headers,
    params={"start_date": "2025-01-01", "end_date": "2025-01-07"}
)
print(json.dumps(sleep_data.json(), indent=2))

# Step 4: Refresh the token when it expires
def refresh_access_token(refresh_token):
    token_data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(token_url, data=token_data)
    new_tokens = response.json()
    return new_tokens["access_token"], new_tokens["refresh_token"]

