class Error(Exception):
    pass


class NoAvailableWeaponsError(Error):
    pass


class InvalidSelectionError(Error):
    pass


class TransferError(Error):
    pass
