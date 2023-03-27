"""
    Title: DG api serializers
    Description: The file contain serializers for all DG api endpoints.
    Created: October 25, 2018
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers


class GetDGUNNumberInfoSerializerRequest(serializers.Serializer):
    un_number = serializers.IntegerField(help_text='Specify a DG UN number to look up.')


class DGShippingNameData(serializers.Serializer):
    code = serializers.CharField(help_text='The code for the specific DG.')
    details = serializers.CharField(help_text='Description of the code.')


class DGData(serializers.Serializer):
    proper_shipping_names = serializers.ListField(help_text='A list of proper shipping names for the dangerous good with the given UN number.')
    is_nos = serializers.BooleanField(help_text='Not otherwise specified, Proper chemical name in brackets')
    is_neq = serializers.BooleanField(help_text='Any net explosive quantity')
    shipping_name_data = serializers.DictField(help_text='A dictionary of lists containing DG codes and details.', child=DGShippingNameData())


class GetDGUNNumberInfoSerializerResponse(serializers.Serializer):
    error = serializers.BooleanField(help_text='True if an error occurred')
    message = serializers.DictField(help_text='A dictionary of errors')
    content = DGData(help_text="A dictionary containing the proper shipping name of the DG.")

