"""
This code taken almost verbatim from http://destinydevs.github.io/BungieNetPlatform/docs/Manifest
"""

import json
import os
import pickle
import sqlite3
import zipfile

import requests


def get_manifest(api_key):
    manifest_url = 'http://www.bungie.net/Platform/Destiny2/Manifest/'

    # get the manifest location from the json
    r = requests.get(manifest_url, headers={'X-API-Key': api_key})
    manifest = r.json()
    mani_url = 'http://www.bungie.net' + manifest['Response']['mobileWorldContentPaths']['en']

    # Download the file, write it to 'MANZIP'
    r = requests.get(mani_url)
    with open("MANZIP", "wb") as zip:
        zip.write(r.content)

    # Extract the file contents, and rename the extracted file
    # to 'Manifest.content'
    with zipfile.ZipFile('MANZIP') as zip:
        name = zip.namelist()
        zip.extractall()
    if os.path.exists('manifest.content'):
        os.remove('manifest.content')
    os.rename(name[0], 'manifest.content')


hashes = {
    'DestinyInventoryItemDefinition': 'hash'
}


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
        hash = hash_dict[table_name]
        for item in item_jsons:
            if hash in item:
                item_dict[item[hash]] = item

        # add that dictionary to our all_data using the name of the table
        # as a key.
        all_data[table_name] = item_dict

    return all_data


def get_manifest_data(api_key):
    # check if pickle exists, if not create one.
    if not os.path.isfile('manifest.pickle'):
        get_manifest(api_key)
        all_data = build_dict(hashes)
        with open('manifest.pickle', 'wb') as data:
            pickle.dump(all_data, data)

    with open('manifest.pickle', 'rb') as data:
        all_data = pickle.load(data)

    return all_data
