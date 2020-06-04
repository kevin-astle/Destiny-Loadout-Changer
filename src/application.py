import json
from threading import Thread
import time
import webbrowser

from flask import Flask

from src.api import API
from src.profile import Profile
from twitchio.ext import commands


class Application:
    """
    Application class which holds a lot of shared data and has methods to start the flask webserver
    and the bot. An instance of this class will be created and inserted into the global namespace
    to allow the event decorator (for the bot) and the route decorator (for the flask webserver) to
    be accessed in other modules. This is a little weird, but makes it so that the code can be
    organized in a more logical way.
    """

    def __init__(self):
        self.flask_app = Flask(__name__)  # Flask application

        self.config = json.load(open('config.json'))  # Contains credentials and settings

        self.bot = commands.Bot(  # The Twitch bot
            irc_token=self.config['tmi_token'],
            client_id=self.config['client_id'],
            nick=self.config['bot_nickname'],
            prefix=self.config['bot_prefix'],
            initial_channels=[self.config['channel']]
        )

        # Oauth code which will needs to be provided every time the script is run
        self.oauth_code = None

        self._api = None

    @property
    def api(self):
        """
        Returns an API object which can be used to perform API operations. oauth_code must be set
        before this can be used.
        """
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
        """
        Link to the page with the oauth approval prompt
        """
        return 'https://www.bungie.net/en/OAuth/Authorize?client_id={}&response_type=code'.format(
            self.config['oauth_client_id'])

    @property
    def oauth_port(self):
        """
        Port to host the flask webserver on
        """
        return self.config['oauth_port']

    @property
    def profile(self):
        """
        Returns player Profile object, which can be used to perform account-level API operations
        """
        return Profile(self.api)

    def start_flask(self):
        """
        Start the flask server, which will serve the oauth redirect endpoint to capture the oauth
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
        Open the oauth authentication page in the default system web browser, and wait for the user
        to authenticate and for the oauth code to be received by the flask server.
        """
        webbrowser.open(self.oauth_link)

    def wait_for_oauth_approval(self):
        """
        Wait until the oauth code has been received by the flask webserver and stored in oauth_code
        """
        while self.oauth_code is None:
            time.sleep(.25)
