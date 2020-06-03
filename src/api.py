import time

import requests

from src.manifest import Manifest


BASE_URL = 'https://www.bungie.net/Platform'  # Base API url


class API:
    """
    Handles all the authentication details and provides methods for making api calls to arbitrary
    Bungie endpoints
    """

    def __init__(self, api_key, client_id, client_secret, oauth_code, bungie_membership_type):
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_code = oauth_code
        self.bungie_membership_type = bungie_membership_type
        self._membership_type = None
        self._access_token = None
        self._membership_id = None
        self.expiration_date = None

        self.manifest = Manifest(self.api_key)

        self.last_api_call_time = 0

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

    def make_get_call(self, endpoint, params=None, rate_limit=0):
        if time.time() - self.last_api_call_time < rate_limit:
            time.sleep(rate_limit - (time.time() - self.last_api_call_time))
        response = requests.get(BASE_URL + endpoint,
                                params=params,
                                headers={'X-API-Key': self.api_key,
                                         'Authorization': 'Bearer {}'.format(self.access_token)})
        response.raise_for_status()
        output = response.json()
        assert output['ErrorStatus'] == 'Success'
        self.last_api_call_time = time.time()
        return output

    def make_post_call(self, endpoint, data=None, rate_limit=0):
        if time.time() - self.last_api_call_time < rate_limit:
            time.sleep(rate_limit - (time.time() - self.last_api_call_time))
        response = requests.post(BASE_URL + endpoint,
                                 json=data,
                                 headers={'X-API-Key': self.api_key,
                                          'Authorization': 'Bearer {}'.format(self.access_token)})
        response.raise_for_status()
        output = response.json()
        assert output['ErrorStatus'] == 'Success'
        return output
