"""
    Title: Contact Serializers
    Description: This file will contain all functions for contact serializers.
    Created: December 29, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.globals.project import MAX_CHAR_LEN, DEFAULT_CHAR_LEN
from api.models import Contact


class ContactSerializer(serializers.ModelSerializer):

    company_name = serializers.CharField(max_length=DEFAULT_CHAR_LEN, help_text='Company Name.')
    name = serializers.CharField(max_length=MAX_CHAR_LEN, help_text="Full name, ex: John Doe or Jane Doe.")
    phone = serializers.CharField(max_length=DEFAULT_CHAR_LEN, help_text="Contacts Phone Number.")
    email = serializers.EmailField(max_length=MAX_CHAR_LEN, help_text='Contacts email address.')

    class Meta:
        model = Contact
        fields = [
            'id',
            'company_name',
            'name',
            'phone',
            'email'
        ]
