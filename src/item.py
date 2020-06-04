from src.enums import WeaponType, TierType


class Item:
    """
    Class representing an instanced item, like a specific weapon or a stack of consumables. Right 
    now it is only used for weapons, but could be expanded in the future
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
        """
        The manifest data for this item. Includes things like the name and item type
        """
        return self.manifest.item_data[self.data['itemHash']]

    @property
    def name(self):
        """
        Item name according to the manifest data
        """
        return self.manifest_data['displayProperties']['name']

    @property
    def item_hash(self):
        """
        Item hash, used to cross-reference with the manifest data
        """
        return self.data['itemHash']

    @property
    def item_id(self):
        """
        Unique id for this instance of this item
        """
        return self.data['itemInstanceId']


class Weapon(Item):
    """
    Class representing an instanced weapon
    """
    @property
    def type(self):
        """
        Returns weapon type as a WeaponType enum value
        """
        return WeaponType.get_type_from_bucket_hash(
            self.manifest_data['inventory']['bucketTypeHash'])

    @property
    def is_exotic(self):
        """
        Returns true if this is an exotic weapon
        """
        return self.manifest_data['inventory']['tierType'] == TierType.EXOTIC

    @property
    def sub_type(self):
        """
        Returns weapon subtype as a WeaponSubType enum value
        """
        return self.manifest_data['itemSubType']
