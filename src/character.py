from datetime import datetime
import random
import time

import requests.exceptions

from src.enums import WEAPON_BUCKET_HASHES
from src.exceptions import NoAvailableWeapons
from src.item import Weapon


class Character:

    def __eq__(self, obj):
        """
        Two characters are equal if their character IDs are equal
        """
        if not isinstance(obj, Character):
            return False
        return self.character_id == obj.character_id

    def __init__(self, api, data, profile):
        self.api = api
        self.data = data

        # Needed because some equip operations require moving items from other characters
        self.profile = profile

    @property
    def membership_id(self):
        return self.data['membershipId']

    @property
    def character_id(self):
        return self.data['characterId']

    @property
    def membership_type(self):
        return self.data['membershipType']

    @property
    def last_played(self):
        return datetime.strptime(self.data['dateLastPlayed'], '%Y-%m-%dT%H:%M:%SZ')

    @property
    def equipped_weapons(self):
        return self.get_character_weapons()['equipped']

    @property
    def unequipped_weapons(self):
        return self.get_character_weapons()['unequipped']

    def _transfer_item(self, item, transfer_to_vault):
        return self.api.make_post_call(
            '/Destiny2/Actions/Items/TransferItem',
            {
                'itemReferenceHash': item.item_hash,
                'stackSize': 1,
                'transferToVault': transfer_to_vault,
                'itemId': item.item_id,
                'characterId': self.character_id,
                'membershipType': self.membership_type
            }
        )['Response']

    def get_character_weapons(self):
        items = self.api.make_get_call(
            '/Destiny2/{}/Profile/{}/Character/{}'.format(
                self.membership_type, self.membership_id, self.character_id),
            {'components': '201,205'}
        )['Response']
        all_unequipped_weapons = [
            Weapon(x, self.api.manifest) for x in items['inventory']['data']['items']
            if self.api.manifest.item_data[x['itemHash']]['itemType'] == 3]
        equipped_weapons = [
            Weapon(x, self.api.manifest) for x in items['equipment']['data']['items']
            if self.api.manifest.item_data[x['itemHash']]['itemType'] == 3]

        # This is to exclude postmaster weapons, which are in a separate bucket
        owned_unequipped_weapons = [x for x in all_unequipped_weapons
                                    if x.data['bucketHash'] in WEAPON_BUCKET_HASHES]
        postmaster_weapons = [x for x in all_unequipped_weapons
                              if x.data['bucketHash'] not in WEAPON_BUCKET_HASHES]

        return {'equipped': equipped_weapons,
                'unequipped': owned_unequipped_weapons,
                'postmaster': postmaster_weapons}

    def transfer_to_character(self, item):
        return self._transfer_item(item, transfer_to_vault=False)

    def transfer_to_vault(self, item):
        return self._transfer_item(item, transfer_to_vault=True)

    def equip_owned_weapon(self, weapon):
        """
        Equip a weapon that is currently owned by the character
        """
        return self.api.make_post_call(
            '/Destiny2/Actions/Items/EquipItem',
            {
                'itemId': weapon.item_id,
                'characterId': self.character_id,
                'membershipType': self.membership_type
            }
        )['Response']

    def equip_weapon(self, weapon, rate_limit=10):
        """
        Attempt to equip the specified weapon on this character, transferring as necessary
        """
        if time.time() - self.last_equip_time < rate_limit:
            time.sleep(rate_limit - (time.time() - self.last_equip_time))
        # Determine which character has the item, or if it is in the vault
        owner = self.profile.get_weapon_owner(weapon)

        # If item is not owned by current character
        if owner != self:
            # If owned by other character, transfer to vault
            if owner is not None:
                owner.transfer_to_vault(weapon)

            # Get the number of weapons in the same slot as the requested weapon
            same_slot_weapons = [x for x in self.unequipped_weapons if x.type == weapon.type]

            # If necessary, move last weapon in that slot to the vault to make room
            if len(same_slot_weapons) == 9:
                self.transfer_to_vault(same_slot_weapons[-1])

            # Transfer from vault to current character
            self.transfer_to_character(weapon)

        # Finally, equip the weapon
        self.equip_owned_weapon(weapon)

        self.last_equip_time = time.time()

    def equip_random_weapon(self, weapon_type=None, weapon_sub_type=None):

        weapons = self.profile.get_all_weapons()

        if weapon_sub_type is not None:
            weapons = [x for x in weapons if x.sub_type == weapon_sub_type]

        if weapon_type is None:
            # If weapon type not specified, then exclude exotics (to keep thing simple)
            weapons = [x for x in weapons if not x.is_exotic]
        else:
            # Else, restrict to the appropriate type
            weapons = [x for x in weapons if x.type == weapon_type]

            for weapon in self.equipped_weapons:
                # If a weapon in one of the other two slots is exotic
                if weapon.type != weapon_type and weapon.is_exotic:
                    # Then exclude exotics from the pool of weapons to choose from
                    weapons = [x for x in weapons if not x.is_exotic]

        if len(weapons) == 0:
            msg = 'No weapons available to equip'
            if weapon_type is not None:
                msg += ' with weapon type {}'.format(weapon_type)
            if weapon_sub_type is not None:
                msg += ' with weapon subtype {}'.format(weapon_type)
            raise NoAvailableWeapons(msg)

        self.equip_weapon(random.choice(weapons))
