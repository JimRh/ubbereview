"""
    Title: Api api views
    Description: This file will contain all functions for api api functions.
    Created: November 19, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import throttling


class NoThrottle(throttling.UserRateThrottle):
    scope = 'ubbe'
    rate = '9999999999/minute'


class BasicThrottle(throttling.UserRateThrottle):
    scope = 'basic'
    rate = '60/minute'


class ProfessionalThrottle(throttling.UserRateThrottle):
    scope = 'professional'
    rate = '120/minute'


class PremiereThrottle(throttling.UserRateThrottle):
    scope = 'premiere'
    rate = '240/minute'


class EnterpriseThrottle(throttling.UserRateThrottle):
    scope = 'enterprise'
    rate = '480/minute'

