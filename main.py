from authorization import *
from database import *
from dashboard import *

from configparser import ConfigParser
from dotenv import load_dotenv
import os
import subprocess

if __name__ == '__main__':

    # load config
    load_dotenv()
    CONFIG_PATH = os.getenv("OURA_SLEEP_CONFIG_PATH")
    config = ConfigParser()
    config.read(CONFIG_PATH)
    config.set('user', 'refresh_token', os.getenv("REFRESH_TOKEN"))
    config.set('user', 'access_token', os.getenv("ACCESS_TOKEN"))
    config.set('user', 'client_id', os.getenv("CLIENT_ID"))
    config.set('user', 'client_secret', os.getenv("CLIENT_SECRET"))
    config.set('user', 'redirect_uri', os.getenv("REDIRECT_URI"))

    # make sure authorization is set
    authorize(config)
    # create or update databases
    update_database(config)
    # launch_dashboard()
    launch_dashboard(config)
