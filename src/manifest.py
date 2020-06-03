"""
Portions of this code taken from http://destinydevs.github.io/BungieNetPlatform/docs/Manifest 
and modified
"""

from builtins import property
import json
import os
import pickle
import sqlite3
import zipfile

import requests


class Manifest:
    def __init__(self, api_key):
        self.api_key = api_key
        self._data = None

    def get_manifest_data(self, api_key):
        # check if pickle file exists, if not create one.
        if os.path.isfile('manifest.pickle'):
            all_data = pickle.load(open('manifest.pickle', 'rb'))
        else:
            get_manifest(api_key)
            all_data = build_dict({
                'DestinyInventoryItemDefinition': 'hash'
            })
            with open('manifest.pickle', 'wb') as f:
                pickle.dump(all_data, f)
        return all_data

    @property
    def data(self):
        if self._data is None:
            self._data = self.get_manifest_data()
        return self._data

    @property
    def item_data(self):
        return self.data['DestinyInventoryItemDefinition']


def get_manifest(api_key):
    manifest_url = 'http://www.bungie.net/Platform/Destiny2/Manifest/'

    # get the manifest location from the json
    r = requests.get(manifest_url, headers={'X-API-Key': api_key})
    manifest = r.json()
    mani_url = 'http://www.bungie.net' + manifest['Response']['mobileWorldContentPaths']['en']

    # Download the file, write it to 'manifest.zip'
    r = requests.get(mani_url)
    with open("manifest.zip", "wb") as zip:
        zip.write(r.content)

    # Extract the file contents, and rename the extracted file
    # to 'manifest.content'
    with zipfile.ZipFile('manifest.zip') as zip:
        name = zip.namelist()
        zip.extractall()
    if os.path.exists('manifest.content'):
        os.remove('manifest.content')
    os.rename(name[0], 'manifest.content')


def build_dict(hash_dict):
    # connect to the manifest
    con = sqlite3.connect('manifest.content')
    # create a cursor object
    cur = con.cursor()

    all_data = {}
    # for every table name in the dictionary
    for table_name in hash_dict.keys():
        # get a list of all the jsons from the table
        cur.execute('SELECT json from ' + table_name)

        # this returns a list of tuples: the first item in each tuple is our json
        items = cur.fetchall()

        # create a list of jsons
        item_jsons = [json.loads(item[0]) for item in items]

        # create a dictionary with the hashes as keys
        # and the jsons as values
        item_dict = {}
        for item in item_jsons:
            item_dict[item[hash_dict[table_name]]] = item

        # add that dictionary to our all_data using the name of the table
        # as a key.
        all_data[table_name] = item_dict

    return all_data
