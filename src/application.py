import json
from threading import Thread
import time
import webbrowser

from flask import Flask

from src.api import API
from src.profile import Profile
from twitchio.ext import commands


class Application:

    def __init__(self, oauth_port=4949):
        self.oauth_port = oauth_port
        self.flask_app = Flask(__name__)
        self.config = json.load(open('config.json'))
        self.bot = commands.Bot(
            irc_token=self.config['tmi_token'],
            client_id=self.config['client_id'],
            nick=self.config['bot_nickname'],
            prefix=self.config['bot_prefix'],
            initial_channels=[self.config['channel']]
        )
        self.oauth_code = None

        self._api = None

    @property
    def api(self):
        if self.oauth_code is None:
            return None
        if self._api is None:
            self._api = API(self.config['bungie_api_key'],
                            self.config['oauth_client_id'],
                            self.config['oauth_client_secret'],
                            self.oauth_code,
                            self.config['bungie_membership_type'])
        return self._api

    @property
    def oauth_link(self):
        return 'https://www.bungie.net/en/OAuth/Authorize?client_id={}&response_type=code'.format(
            self.config['oauth_client_id'])

    @property
    def profile(self):
        return Profile(self.api)

    def start_flask(self):
        """
        Start the flask server, which will serve the OAUTH redirect endpoint to capture the oauth 
        code which will be used to make restricted api calls.

        This must run with ssl, because Bungie oauth does not allow redirect to http. Because adhoc
        does not use an officially signed cert, there will be a warning shown in the browser when
        the user is redirected to this endpoint.
        """
        Thread(target=self.flask_app.run,
               kwargs={'host': '0.0.0.0', 'port': self.oauth_port, 'ssl_context': 'adhoc'}).start()

    def start_bot(self):
        """
        Connect the Twitch bot to the channel
        """
        Thread(target=self.bot.run).start()

    def open_oauth_page(self):
        """
        Open the OAUTH authentication page in the default system web browser, and wait for the user
        to authenticate and for the oauth code to be received by the flask server.
        """
        webbrowser.open(self.oauth_link)

    def wait_for_oauth_approval(self):
        while self.oauth_code is None:
            time.sleep(.25)
