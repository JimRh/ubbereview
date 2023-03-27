"""
    Title: Business Central Exceptions
    Description: Contains exceptions for any business central errors.
    Created: November 28, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""


class BusinessCentralError(Exception):

    def __init__(self, message: str, data: any):
        super().__init__()
        self._message = message
        self._data = data

    @property
    def message(self):
        return "BC Error: {}. Data: {}".format(self._message, str(self._data))
