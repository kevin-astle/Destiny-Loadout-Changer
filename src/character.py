from datetime import datetime
import random
import time

import requests.exceptions

from src.enums import WeaponSubType, WeaponType
from src.exceptions import NoAvailableWeaponsError, InvalidSelectionError, TransferOrEquipError
from src.item import Weapon


class Character:
    """
    Class for performing character-specific API operations
    """

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

        # Needed because some equip operations require moving items from other characters, which is
        # an account-level operation
        self.profile = profile

    @property
    def membership_id(self):
        """
        Character membership ID
        """
        return self.data['membershipId']

    @property
    def character_id(self):
        """
        Character ID
        """
        return self.data['characterId']

    @property
    def membership_type(self):
        """
        Character membership type
        """
        return self.data['membershipType']

    @property
    def last_played(self):
        """
        Last time this character was played
        """
        return datetime.strptime(self.data['dateLastPlayed'], '%Y-%m-%dT%H:%M:%SZ')

    @property
    def equipped_weapons(self):
        """
        Returns the 3 weapons equipped on the character (as Weapon objects)
        """
        return self.get_character_weapons()['equipped']

    @property
    def unequipped_weapons(self):
        """
        Returns all unequipped weapons currently in the character's possession (as Weapon objects)
        """
        return self.get_character_weapons()['unequipped']

    def _transfer_item(self, item, transfer_to_vault):
        """
        Transfer an item to or from the vault
        """
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
        """
        Get all weapons associated with the current character. Includes equipped weapons, unequipped
        weapons, and weapons in the postmaster's inventory
        """
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
                                    if x.data['bucketHash'] in WeaponType.BUCKET_HASHES]
        postmaster_weapons = [x for x in all_unequipped_weapons
                              if x.data['bucketHash'] not in WeaponType.BUCKET_HASHES]

        return {'equipped': equipped_weapons,
                'unequipped': owned_unequipped_weapons,
                'postmaster': postmaster_weapons}

    def transfer_to_character(self, item):
        """
        Transfer an item from the vault to the character
        """
        return self._transfer_item(item, transfer_to_vault=False)

    def transfer_to_vault(self, item):
        """
        Transfer an item from the character to the vault
        """
        return self._transfer_item(item, transfer_to_vault=True)

    def equip_owned_weapon(self, weapon):
        """
        Equip a weapon that is currently in the character's possession
        """
        response = self.api.make_post_call(
            '/Destiny2/Actions/Items/EquipItem',
            {
                'itemId': weapon.item_id,
                'characterId': self.character_id,
                'membershipType': self.membership_type
            }
        )
        if response['ErrorStatus'] != 'Success':
            raise TransferOrEquipError('Unable to equip item. Error message: {}'.format(
                response['Message']))

    def equip_weapon(self, weapon, retries=3):
        """
        Attempt to equip the specified weapon on this character, transferring from other characters
        and from the vault as necessary
        """
        while True:
            try:
                # Determine which character has the item, or if it is in the vault
                owner = self.profile.get_weapon_owner(weapon)

                # If item is not owned by current character
                if owner != self:
                    # If owned by other character, transfer to vault
                    if owner is not None:
                        owner.transfer_to_vault(weapon)

                    # Get the number of weapons in the same slot as the requested weapon
                    same_slot_weapons = [
                        x for x in self.unequipped_weapons if x.type == weapon.type]

                    # If necessary, move last weapon in that slot to the vault to make room
                    if len(same_slot_weapons) == 9:
                        self.transfer_to_vault(same_slot_weapons[-1])

                    # Transfer from vault to current character
                    self.transfer_to_character(weapon)

                # Finally, equip the weapon
                self.equip_owned_weapon(weapon)

                self.profile.last_equip_time = time.time()
            except requests.exceptions.HTTPError as e:
                if retries <= 0:
                    response_json = e.response.json()
                    if response_json['ErrorCode'] == 1623:  # Item requested was not found
                        raise TransferOrEquipError(
                            'Unable to transfer or equip item. Please try again')
                    else:
                        raise TransferOrEquipError(response_json['Message'])
                retries -= 1
                time.sleep(3)
            else:
                break

    def select_random_weapon(self, weapon_type=None, weapon_sub_type=None):
        """
        Select a random weapon, given certain optional constraints. For valid weapon type
        constraints, see WeaponType.get_enum_from_string. For valid weapon subtype constraints, see
        WeaponSubType.get_enum_from_string
        """
        if weapon_sub_type == WeaponSubType.TRACE_RIFLE:
            raise InvalidSelectionError('Random selections of Trace Rifles are not supported at '
                                        'this time')

        weapons = self.profile.get_all_weapons()

        if weapon_sub_type is not None:
            for weapon in self.equipped_weapons:
                # If any exotic weapons are equipped
                if weapon.is_exotic:
                    # Then exclude exotics from the pool of weapons to choose from
                    weapons = [x for x in weapons if x.sub_type == weapon_sub_type]

        # If weapon type not specified, and an exotic weapon is equipped, then exclude exotics
        # from the pool of weapons to choose from
        if weapon_type is None:
            for weapon in self.equipped_weapons:
                if weapon.is_exotic:
                    weapons = [x for x in weapons if x.sub_type == weapon_sub_type]
                    break
        else:
            # Else if weapon type is specified, restrict to the appropriate type
            weapons = [x for x in weapons if x.type == weapon_type]

            for weapon in self.equipped_weapons:
                # If a weapon in one of the other two slots is exotic
                if weapon.type != weapon_type and weapon.is_exotic:
                    # Then exclude exotics from the pool of weapons to choose from
                    weapons = [x for x in weapons if not x.is_exotic]
                    break

        if len(weapons) == 0:
            msg = 'No weapons available to equip'
            if weapon_type is not None:
                msg += ' with weapon type {}'.format(weapon_type)
            if weapon_sub_type is not None:
                msg += ' with weapon subtype {}'.format(
                    WeaponSubType.get_string_representation(weapon_sub_type))
            raise NoAvailableWeaponsError(msg)

        return random.choice(weapons), len(weapons)

    def select_specific_weapon(self, weapon_name):
        """
        Search for and select a weapon by name. If one or more exact matches is found, choose one of
        those. If not, then look for partial matches and choose one of those. The matching is not
        case-sensitive
        """
        weapon_name_lowercase = weapon_name.lower()

        weapons = self.profile.get_all_weapons()

        # Look for exact matches
        matching = [x for x in weapons if x.name.lower() == weapon_name_lowercase]

        # If none found, look for partial matches
        if len(matching) == 0:
            matching = [x for x in weapons if weapon_name_lowercase in x.name.lower()]

        if len(matching) == 0:
            raise NoAvailableWeaponsError(
                'Could not find any unequipped weapons matching "{}"'.format(weapon_name))

        # In case there's multiple options, choose a random one
        return random.choice(matching), len(matching)
