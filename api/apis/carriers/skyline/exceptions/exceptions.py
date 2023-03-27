from api.exceptions.project import ViewException


class SkylineAPIException(ViewException):
    pass


class SkylineRateError(SkylineAPIException):
    pass


class SkylineShipError(SkylineAPIException):
    pass


class SkylineTrackError(SkylineAPIException):
    pass


class SkylineDocumentError(SkylineAPIException):
    pass


class SkylineAccountError(SkylineAPIException):
    pass


class SkylinePickupDeliveryError(SkylineAPIException):
    pass
