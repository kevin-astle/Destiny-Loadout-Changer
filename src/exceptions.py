class Error(Exception):
    pass


class NoAvailableWeaponsError(Error):
    pass


class InvalidSelectionError(Error):
    pass


class TransferOrEquipError(Error):
    pass
