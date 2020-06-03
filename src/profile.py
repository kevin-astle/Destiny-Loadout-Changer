from datetime import datetime

from src.character import Character
from src.item import Weapon


class Profile:

    def __init__(self, api):
        self.api = api
        self._active_character = None

    @property
    def active_character(self):
        """
        Assume that the most-recently-played character is currently online and active
        """
        if self._active_character is None:
            self._active_character = self.get_most_recent_character()
        return self._active_character

    def get_characters(self):
        """
        Get all characters in the account
        """
        characters = self.api.make_get_call(
            '/Destiny2/{}/Profile/{}'.format(self.api.membership_type, self.api.membership_id),
            {'components': '200'}
        )['Response']['characters']['data']
        return [Character(x) for x in characters]

    def get_most_recent_character(self):
        """
        Returns the character that was played most recently. If currently playing, then the active 
        character will be returned
        """
        characters = self.get_characters()

        most_recent_character = None
        most_recent_playtime = None
        current_datetime = datetime.utcnow()

        # Figure out which character has the most recent playtime
        for data in characters.values():
            # Convert most recent playtime to a datetime for comparison
            last_played = datetime.strptime(data['dateLastPlayed'], '%Y-%m-%dT%H:%M:%SZ')

            if most_recent_character is None:
                most_recent_character = data
                most_recent_playtime = last_played
            else:
                # If the character in question has more recent playtime than the other characters
                # already inspected, then set as the new most recent character
                if (current_datetime - last_played).total_seconds() < \
                        (current_datetime - most_recent_playtime).total_seconds():
                    most_recent_character = data
                    most_recent_playtime = last_played

        return most_recent_character

    def get_inventory(self):
        """
        Get profile-wide inventory, including weapons, armor, consumables, etc., both in the 
        character inventories as well as in the vault
        """
        return self.api.make_get_call(
            '/Destiny2/{}/Profile/{}'.format(self.api.membership_type, self.api.membership_id),
            {'components': '102'}
        )['Response']['profileInventory']['data']['items']

    def get_inventory_weapons(self):
        """
        Get all weapons in character inventories and in the vault
        """
        weapons = [
            x for x in self.get_inventory()
            if self.api.manifest.item_data[x['itemHash']]['itemType'] == 3]
        return [Weapon(x) for x in weapons]  # Convert to a list of Weapon class instances
