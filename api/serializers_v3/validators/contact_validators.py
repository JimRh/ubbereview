"""
    Title: Contact Validators
    Description: This file will contain functions for contact validating.
    Created: November 29, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers


class PhoneValidator:

    def __init__(self, phone: str):
        self.phone = phone

    def valid(self) -> str:
        phone = self.phone.strip()

        if not phone.isdigit():
            raise serializers.ValidationError({'phone': [f'This field mush be numbers only.']})

        return phone
