from datetime import datetime

from src.character import Character
from src.item import Weapon


class Profile:

    def __init__(self, api):
        self.api = api
        self._active_character = None
        self.last_equip_time = 0

    @property
    def active_character(self):
        """
        Assume that the most-recently-played character is currently online and active
        """
        if self._active_character is None:
            self._active_character = self.get_most_recent_character()
        return self._active_character

    @property
    def characters(self):
        """
        Get all characters in the account
        """
        characters = self.api.make_get_call(
            '/Destiny2/{}/Profile/{}'.format(self.api.membership_type, self.api.membership_id),
            {'components': '200'}
        )['Response']['characters']['data']
        return [Character(self.api, x, self) for x in characters.values()]

    def get_most_recent_character(self):
        """
        Returns the character that was played most recently. If currently playing, then the active 
        character will be returned
        """
        most_recent_character = None
        most_recent_playtime = None
        current_datetime = datetime.utcnow()

        # Figure out which character has the most recent playtime
        for character in self.characters:

            if most_recent_character is None:
                most_recent_character = character
                most_recent_playtime = character.last_played
            else:
                # If the character in question has more recent playtime than the other characters
                # already inspected, then set as the new most recent character
                if (current_datetime - character.last_played).total_seconds() < \
                        (current_datetime - most_recent_playtime).total_seconds():
                    most_recent_character = character
                    most_recent_playtime = character.last_played

        return most_recent_character

    def get_vault_weapons(self):
        """
        Get all weapons in the vault
        """
        items = self.api.make_get_call(
            '/Destiny2/{}/Profile/{}'.format(self.api.membership_type, self.api.membership_id),
            {'components': '102'}
        )['Response']['profileInventory']['data']['items']
        return [
            Weapon(x, self.api.manifest) for x in items
            if self.api.manifest.item_data[x['itemHash']]['itemType'] == 3
        ]

    def get_all_weapons(self):
        """
        Get all weapons, across all characters and the vault. Does not include postmaster weapons 
        or currently equipped weapons
        """
        all_weapons = self.get_vault_weapons()

        for character in self.characters:
            unequipped = character.unequipped_weapons
            all_weapons += unequipped

        return all_weapons

    def get_weapon_owner(self, weapon):
        """
        Return the character currently in possession of a specified weapon. If no character has it,
        then return None
        """
        if weapon in self.get_vault_weapons():
            return None

        for character in self.characters:
            for char_weapon in character.equipped_weapons:
                if char_weapon == weapon:
                    return character
            for char_weapon in character.unequipped_weapons:
                if char_weapon == weapon:
                    return character

        return None  # No character has this weapon
