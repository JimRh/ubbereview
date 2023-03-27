"""
    Title: Google Api Base Class
    Description: This file will contain common functions between the different google apis.
    Created: March 2, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

import googlemaps

from brain.settings import GOOGLE_API_KEY


class GoogleApi:
    """
        Class will handle common details between the sub classes.
    """
    _STATUS_OK = "OK"
    _THOUSAND = 1000
    _sig_fig = Decimal(".01")

    _google = googlemaps.Client(key=GOOGLE_API_KEY)
    _url = "https://maps.googleapis.com/maps/api/"
