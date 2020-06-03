from datetime import datetime
import time

import requests

from src.manifest import get_manifest_data


BASE_URL = 'https://www.bungie.net/Platform'


class API:
    def __init__(self, api_key, client_id, client_secret, oauth_code, bungie_membership_type):
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_code = oauth_code
        self.bungie_membership_type = bungie_membership_type
        self._membership_type = None
        self._access_token = None
        self._membership_id = None
        self._manifest_data = None
        self.expiration_date = None

    @property
    def access_token(self):
        if self._access_token is None:
            self.get_token()
        return self._access_token

    @property
    def refresh_token(self):
        if self._refresh_token is None:
            self.get_refresh_token()
        return self._refresh_token

    @property
    def membership_type(self):
        if self._membership_type is None:
            self.get_token()
        return self._membership_type

    @property
    def membership_id(self):
        if self._membership_id is None:
            self.get_token()
        return self._membership_id

    @property
    def manifest_data(self):
        if self._manifest_data is None:
            self._manifest_data = get_manifest_data(self.api_key)
        return self._manifest_data

    def get_token(self):
        response = requests.post('https://www.bungie.net/Platform/App/OAuth/Token', data={
            'grant_type': 'authorization_code',
            'code': self.oauth_code,
            'client_id': 32959,
            'client_secret': self.client_secret,
        }, headers={'X-API-Key': self.api_key})
        response.raise_for_status()
        output = response.json()
        self._access_token = output['access_token']
        self._refresh_token = output['refresh_token']
        self.expiration_date = time.time() + output['expires_in']

        # Get platform membership id
        output = self.make_get_call(
            '/User/GetBungieAccount/{}/{}'.format(output['membership_id'], self.bungie_membership_type))
        self._membership_id = output['Response']['destinyMemberships'][0]['membershipId']
        self._membership_type = output['Response']['destinyMemberships'][0]['membershipType']

    def get_refresh_token(self):
        response = requests.post('https://www.bungie.net/Platform/App/OAuth/Token', data={
            'grant_type': 'authorization_code',
            'refresh_token': self.refresh_token,
        }, headers={'X-API-Key': self.api_key})
        response.raise_for_status()
        output = response.json()
        self._access_token = output['access_token']
        self._refresh_token = output['refresh_token']
        self.expiration_date = time.time() + output['expires_in']
        self._membership_id = output['membership_id']

    def make_get_call(self, endpoint, params=None):
        response = requests.get(BASE_URL + endpoint,
                                params=params,
                                headers={'X-API-Key': self.api_key,
                                         'Authorization': 'Bearer {}'.format(self.access_token)})
        response.raise_for_status()
        output = response.json()
        assert output['ErrorStatus'] == 'Success'
        return output

    def get_inventory(self):
        return self.make_get_call(
            '/Destiny2/{}/Profile/{}'.format(self.membership_type, self.membership_id), {'components': '102'})['Response']['profileInventory']['data']['items']

    def get_characters(self):
        return self.make_get_call(
            '/Destiny2/{}/Profile/{}'.format(self.membership_type, self.membership_id), {'components': '200'})['Response']['characters']['data']

    def get_inventory_weapons(self):
        weapons = [
            x for x in self.get_inventory()
            if self.manifest_data['DestinyInventoryItemDefinition'][x['itemHash']]['itemType'] == 3]
        for x in weapons:
            print(self.manifest_data['DestinyInventoryItemDefinition']
                  [x['itemHash']]['displayProperties']['name'])
        return weapons

    def get_inventory_armor(self):
        return [
            x for x in self.get_inventory()
            if self.manifest_data['DestinyInventoryItemDefinition'][x['itemHash']]['itemType'] == 2]

    def get_active_character(self):
        characters = self.get_characters()

        # Figure out which has the most recent playtime
        current_datetime = datetime.utcnow()
        # for character_id, data in characters.items():
