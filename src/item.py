from src.manifest import Manifest


class Item:

    def __init__(self, data, manifest):
        self.data = data
        self.manifest = manifest

    @property
    def name(self):
        return self.manifest.item_data[self.data['itemHash']]['displayProperties']['name']

    @property
    def item_hash(self):
        return self.data['itemHash']

    @property
    def item_id(self):
        return self.data['itemInstanceId']

    @property
    def location(self):
        return self.data['location']

    def is_equipped_on_character(self, character):
        """
        Check if item is equipped on the given character
        """
        pass


class Weapon(Item):
    pass
