class UTCMSException(Exception):
    """Base exception for UTCMS automation"""

    pass


class MapInteractionError(UTCMSException):
    """Raised when interaction with the map fails"""

    pass


class LocationSelectionError(UTCMSException):
    """Raised when location selection fails (all methods)"""

    pass


class WaybillError(UTCMSException):
    """Raised when waybill creation fails"""

    pass
