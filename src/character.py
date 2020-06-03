from src.enums import ItemLocation


class Character:

    def __init__(self, api, data):
        self.api = api
        self.data = data

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
    def equipped_items(self):
        pass

    @property
    def unequipped_items(self):
        pass

    def _transfer_item(self, item, transfer_to_vault):
        return self.make_post_call(
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

    def get_character_data(self):
        output = self.api.make_get_call(
            '/Destiny2/{}/Profile/{}/Character/{}'.format(
                self.membership_type, self.membership_id, self.character_id),
            {
                'components': '201,205'  # Request equipped and unequipped items
            }
        )
        return output

    def transfer_to_character(self, item):
        return self._transfer_item(item, transfer_to_vault=False)

    def transfer_to_vault(self, item):
        return self._transfer_item(item, transfer_to_vault=True)

    def equip_item(self, item):
        """
        TODO: Check what happens when trying to equip item from another character. May need to 
        handle that specially
        """
        # If in the vault, first transfer to character
        if item.location == ItemLocation.VAULT:
            self.transfer_item(item.item_hash,
                               item.item_id,
                               transfer_to_vault=False)
        return self.make_post_call(
            '/Destiny2/Actions/Items/EquipItem',
            {
                'itemId': item.item_id,
                'characterId': self.character_id,
                'membershipType': self.membership_type
            }
        )['Response']
