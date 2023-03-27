from api.exceptions.project import ViewException


class LocationNotFoundException(Exception):
    pass


class IATAApiException(Exception):
    pass


class CarrierOptionException(ViewException):
    pass


class OptionNotApplicableException(CarrierOptionException):
    pass
