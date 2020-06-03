from src.enums import WeaponType, TierType


class Item:
    """
    Class representing an instanced item, like a specific weapon or a stack of consumables.
    """

    def __eq__(self, obj):
        """
        Two instanced items are equal if their item IDs are the same
        """
        if not isinstance(obj, Item):
            return False
        return self.item_id == obj.item_id

    def __init__(self, data, manifest):
        self.data = data
        self.manifest = manifest

    @property
    def manifest_data(self):
        return self.manifest.item_data[self.data['itemHash']]

    @property
    def name(self):
        return self.manifest_data['displayProperties']['name']

    @property
    def item_hash(self):
        return self.data['itemHash']

    @property
    def item_id(self):
        return self.data['itemInstanceId']


class Weapon(Item):
    @property
    def type(self):
        return WeaponType.get_type_from_bucket_hash(
            self.manifest_data['inventory']['bucketTypeHash'])

    @property
    def is_exotic(self):
        return self.manifest_data['inventory']['tierType'] == TierType.EXOTIC

    @property
    def sub_type(self):
        return self.manifest_data['itemSubType']
