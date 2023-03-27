from requests import Response


class ViewException(Exception):

    def __init__(self, message, code: str = "", errors: list = None):
        super().__init__()

        if not errors:
            errors = []

        self.message = message
        self.code = code
        self.errors = errors

    def __repr__(self) -> str:
        return f"Code: {self.code}, Message: {self.message}, Errors: {str(self.errors)}"

    def __str__(self) -> str:
        return f"Code: {self.code}, Message: {self.message}, Errors: {str(self.errors)}"


class RequestError(Exception):

    def __init__(self, response: Response = None, data: dict = None):
        super().__init__()

        if response is None:
            self._message = 'Request Error'
        else:
            url = response.url
            headers = response.headers
            history = str(response.history)
            status = response.status_code
            content = response.text[:200]

            self._message = 'Request Error\n\nURL:\n{}\nHeaders:\n{}\nHistory:\n{}\nStatus:\n{}\nContent:\n{}\nData:\n{}'.format(
                url, headers, history, status, content, data)

    def __repr__(self) -> str:
        return self._message

    def __str__(self) -> str:
        return self._message


class RateException(ViewException):
    pass


class RateExceptionNoEmail(ViewException):
    pass


class ShipException(ViewException):
    pass


class ShipNextException(ViewException):
    pass


class TrackException(ViewException):
    pass


class DocumentException(ViewException):
    pass


class PickupException(ViewException):
    pass


class CancelException(ViewException):
    pass


class DatabaseException(ViewException):
    pass


class NoTrackingStatus(Exception):
    pass


class DangerousGoodsException(ViewException):
    pass
