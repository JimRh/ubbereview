"""
    Title: Ship api serializers
    Description: The file contain serializers for all ship api endpoints.
    Created: October 25, 2018
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers


class DocumentData(serializers.Serializer):
    document = serializers.CharField(help_text='Basee64 encode document.')
    type = serializers.CharField(help_text='Indicates Type of Document. '
                                           'Shipping Label: 1\nBOL: 2\n'
                                           'Commercial Invoice: 3\nB13A: 4\nDG: 5\nNEAS: 6\nNSSI: 1\n')


class NextLegApiData(serializers.Serializer):
    leg_id = serializers.CharField(help_text='Leg ID for a shipment, ends in P, M, or D.')
    tracking_number = serializers.CharField(help_text='Carrier Tracking Number')
    documents = DocumentData(help_text="A list containing documents")


class NextLegApiSerializerResponse(serializers.Serializer):
    error = serializers.BooleanField(help_text='True if an error occurred')
    message = serializers.DictField(help_text='A dictionary of errors')
    content = NextLegApiData(help_text="A dictionary containing the information about the shipment.")


class NextLegApiSerializerRequest(serializers.Serializer):
    shipment_id = serializers.CharField(help_text='Shipment ID - Used for Tracking')
    booking_number = serializers.CharField(help_text='Booking Reference (Sealift Only)')
