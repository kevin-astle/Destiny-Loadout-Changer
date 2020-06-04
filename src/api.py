import time

import requests

from src.manifest import Manifest


BASE_URL = 'https://www.bungie.net/Platform'  # Base API url


class API:
    """
    Class for performing Bungie API operations. Includes functions for getting/refreshing oauth 
    access tokens, and for making GET/POST calls to arbitrary Bungie endpoints.
    """

    def __init__(self, api_key, client_id, client_secret, oauth_code, bungie_membership_type):
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_code = oauth_code
        self.bungie_membership_type = bungie_membership_type
        self._membership_type = None
        self._access_token = None
        self.refresh_token = None
        self._membership_id = None
        self.expiration_time = None

        self.manifest = Manifest(self.api_key)

    @property
    def access_token(self):
        """
        Returns the access token needed for performing protected API operations. Lazily initialized,
        so it will request the access token the first time this is called.
        """
        if self._access_token is None:
            self.get_token()
        # If access token is expired, refresh it
        if time.time() - self.expiration_time > 0:
            self.refresh_access_token()
        return self._access_token

    @property
    def membership_type(self):
        """
        Get the membership type of the player
        """
        if self._membership_type is None:
            self.get_token()
        return self._membership_type

    @property
    def membership_id(self):
        """
        Get the membership ID of the player
        """
        if self._membership_id is None:
            self.get_token()
        return self._membership_id

    def get_token(self):
        """
        Request an access token for performing protected API operations on the player
        """
        response = requests.post('https://www.bungie.net/Platform/App/OAuth/Token', data={
            'grant_type': 'authorization_code',
            'code': self.oauth_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
        }, headers={'X-API-Key': self.api_key})
        response.raise_for_status()
        output = response.json()
        self._access_token = output['access_token']
        self.refresh_token = output['refresh_token']
        self.expiration_time = time.time() + output['expires_in']

        # Get platform membership id and type for the player
        output = self.make_get_call('/User/GetBungieAccount/{}/{}'.format(
            output['membership_id'], self.bungie_membership_type))
        self._membership_id = output['Response']['destinyMemberships'][0]['membershipId']
        self._membership_type = output['Response']['destinyMemberships'][0]['membershipType']

    def refresh_access_token(self):
        """
        Refresh the access token. Access tokens expire an hour after they are issued
        """
        response = requests.post('https://www.bungie.net/Platform/App/OAuth/Token', data={
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }, headers={'X-API-Key': self.api_key})
        response.raise_for_status()
        output = response.json()
        self._access_token = output['access_token']
        self.refresh_token = output['refresh_token']
        self.expiration_time = time.time() + output['expires_in']

    def make_get_call(self, endpoint, params=None):
        """
        Make an API GET call to the Bungie API. If an error occurs during the call, a
        requests.exceptions.HTTPError will be raised

        params:
            endpoint (str): The endpoint to call, e.g. "/Destiny2/123/Profile/456/Character/789"
            params (dict): URL parameters to use for the GET call

        returns: The deserialized JSON returned by the endpoint
        """
        response = requests.get(BASE_URL + endpoint,
                                params=params,
                                headers={'X-API-Key': self.api_key,
                                         'Authorization': 'Bearer {}'.format(self.access_token)})
        response.raise_for_status()
        return response.json()

    def make_post_call(self, endpoint, data=None):
        """
        Make an API POST call to the Bungie API. If an error occurs during the call, a
        requests.exceptions.HTTPError will be raised

        params:
            endpoint (str): The endpoint to call, e.g. "/Destiny2/Actions/Items/EquipItem"
            data (dict): Data to use for the body of the POST call

        returns: The deserialized JSON returned by the endpoint
        """
        response = requests.post(BASE_URL + endpoint,
                                 json=data,
                                 headers={'X-API-Key': self.api_key,
                                          'Authorization': 'Bearer {}'.format(self.access_token)})
        response.raise_for_status()
        return response.json()
