import json
import os
from threading import Thread
import time
import webbrowser

from flask import Flask, request

from src.destiny_api import API
from twitchio.ext import commands


class LoadoutChanger:
    app = Flask(__name__)

    config = json.load(open('config.json'))

    bot = commands.Bot(
        irc_token=config['tmi_token'],
        client_id=config['client_id'],
        nick=config['bot_nickname'],
        prefix=config['bot_prefix'],
        initial_channels=[config['channel']]
    )

    oauth_code = None

    def __init__(self):
        self._api = None

    def start_flask(self):
        Thread(target=LoadoutChanger.app.run, kwargs={
               'host': '0.0.0.0', 'port': 4949, 'ssl_context': 'adhoc'}).start()

    def start_bot(self):
        Thread(target=LoadoutChanger.bot.run).start()

    @property
    def api(self):
        if LoadoutChanger.oauth_code is None:
            return None
        if self._api is None:
            self._api = API(LoadoutChanger.config['bungie_api_key'],
                            LoadoutChanger.config['oauth_client_id'],
                            LoadoutChanger.config['oauth_client_secret'],
                            LoadoutChanger.oauth_code,
                            LoadoutChanger.config['bungie_membership_type'])
        return self._api


@LoadoutChanger.app.route('/oauth', methods=['GET'])
def oauth_redirect():
    """
    Endpoint to accept oauth code
    """
    LoadoutChanger.oauth_code = request.args['code']
    return 'Thank you for authenticating, your twitch bot can now perform actions on your account.'


@LoadoutChanger.bot.event
async def event_ready():
    await LoadoutChanger.bot._ws.send_privmsg(
        LoadoutChanger.config['channel'],
        'If you have not done so already, authenticate this bot with Bungie using this url: '
        'https://www.bungie.net/en/OAuth/Authorize?client_id={}&response_type=code'.format(
            LoadoutChanger.config['oauth_client_id']))


@LoadoutChanger.bot.command(name='help')
async def test(ctx):
    await ctx.send('Available commands:')
    await ctx.send('!equip primary random: equip a random weapon in the primary weapon slot')
    await ctx.send('!equip energy random: equip a random weapon in the energy weapon slot')
    await ctx.send('!equip heavy random: equip a random weapon in the heavy weapon slot')


@LoadoutChanger.bot.command(name='equip')
async def equip(ctx):
    words = ctx.content.split()[1:]  # Drop first word (!equip)


if __name__ == '__main__':
    loadout_changer = LoadoutChanger()
    loadout_changer.start_flask()
    loadout_changer.start_bot()
    webbrowser.open(
        'https://www.bungie.net/en/OAuth/Authorize?client_id={}&response_type=code'.format(
            LoadoutChanger.config['oauth_client_id']))
    while loadout_changer.oauth_code is None:
        time.sleep(1)
    items = loadout_changer.api.get_active_character()

    while True:
        time.sleep(1)
