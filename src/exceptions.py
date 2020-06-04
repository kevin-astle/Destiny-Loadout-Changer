class Error(Exception):
    """
    Base error class
    """
    pass


class NoAvailableWeaponsError(Error):
    """
    Error when there are no available weapons which match the given criteria
    """
    pass


class InvalidSelectionError(Error):
    """
    Error when the given criteria are fundamentally invalid
    """
    pass


class TransferOrEquipError(Error):
    """
    Error when an item could either not be transferred or equipped
    """
    pass
