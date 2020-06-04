"""
This module mostly based on the code found here:
http://destinydevs.github.io/BungieNetPlatform/docs/Manifest#/Python-v3X
"""

from builtins import property
import json
import os
import pickle
import sqlite3
import zipfile

import requests


class Manifest:
    """
    Retrieve and store the Manifest data for Destiny 2, which holds static information like weapon
    names, lore, etc.
    """

    def __init__(self, api_key):
        self.api_key = api_key
        self._data = None
        self._manifest_info = None

        # For now, only one table is needed by the bot. If more data is needed later, then
        # more tables can be added to this dictionary
        self.required_db_info = {
            'DestinyInventoryItemDefinition': 'hash'
        }

    @property
    def data(self):
        """
        Lazily initialized. Gets the manifest data, either by loading saved manifest data or by
        downloading the latest manifest db file and extracting the desired data. If manifest data
        is loaded from a saved file, the version is compared against the current version to see if
        it is out of date. If so, the latest manifest data will be downloaded
        """
        if self._data is None:
            # Load saved manifest data, and check if it is out of date. If so, discard it
            if os.path.isfile('manifest.data'):
                self._data = pickle.load(open('manifest.data', 'rb'))
                if self._data.get('version') != self.manifest_version:
                    self._data = None

            # If, after checking for saved manifest data, we still need to acquire the manifest data
            if self._data is None:
                # Download and parse manifest data, and save to a file
                self._data = self.get_manifest()
                self._data['version'] = self.manifest_version  # Include version info before saving
                with open('manifest.data', 'wb') as f:
                    pickle.dump(self._data, f)
        return self._data

    @property
    def item_data(self):
        """
        Returns the item section of the manifest data
        """
        return self.data['DestinyInventoryItemDefinition']

    @property
    def manifest_info(self):
        """
        Gets the manifest metadata. This includes a link to the latest manifest db file, as well as
        the current version. This is lazily initialized, so it is downloaded once per session
        """
        if self._manifest_info is None:
            response = requests.get(
                'http://www.bungie.net/Platform/Destiny2/Manifest',
                headers={'X-API-Key': self.api_key})
            response.raise_for_status()
            self._manifest_info = response.json()['Response']
        return self._manifest_info

    @property
    def manifest_version(self):
        """
        Version of the latest manifest data
        """
        return self.manifest_info['version']

    @property
    def manifest_db_url(self):
        """
        URL of the db file with the latest manifest data
        """
        return 'http://www.bungie.net' + self.manifest_info['mobileWorldContentPaths']['en']

    def get_manifest(self):
        """
        Download the manifest data and extract the desired information from it
        """
        # Download the sqlite db zip file, write it to 'manifest.zip'
        r = requests.get(self.manifest_db_url)
        with open("manifest.zip", "wb") as zip_file:
            zip_file.write(r.content)

        # Extract the zip file
        with zipfile.ZipFile('manifest.zip') as zip_file:
            name = zip_file.namelist()
            if os.path.exists(name[0]):
                os.remove(name[0])
            zip_file.extractall()

        connection = sqlite3.connect(name[0])
        cursor = connection.cursor()

        all_data = {}
        # for every table that data is to be extracted from
        for table_name, hash_value in self.required_db_info.items():
            # Get all json strings from the table
            cursor.execute('SELECT json from ' + table_name)
            rows = cursor.fetchall()

            # Deserialize json for each row, and convert to a dictionary, where the keys are the
            # hashes specified in hash_dict and the values are the dictionaries just loaded
            table_data = {}
            for row in rows:
                row_data = json.loads(row[0])  # db rows are returned as tuples, hence row[0]
                table_data[row_data[hash_value]] = row_data

            all_data[table_name] = table_data

        # Clean up
        connection.close()
        os.remove('manifest.zip')
        os.remove(name[0])

        return all_data
