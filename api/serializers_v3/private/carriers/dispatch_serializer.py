"""
    Title: Dispatch Serializers
    Description: This file will contain all functions for dispatch serializers.
    Created: November 16, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import Dispatch, Contact, Carrier
from api.serializers_v3.common.contact_serializer import ContactSerializer


class PrivateDispatchSerializer(serializers.ModelSerializer):
    not_changeable = [
        'carrier'
    ]

    carrier_name = serializers.CharField(
        source='carrier.name',
        help_text='Carrier Name',
        required=False
    )

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Code',
        required=False
    )

    contact = ContactSerializer(
        many=False,
        help_text="A dictionary containing information about the contact."
    )

    class Meta:
        model = Dispatch
        fields = [
            'id',
            'carrier_name',
            'carrier_code',
            'contact',
            'location',
            'is_default',
        ]

    def update(self, instance, validated_data):
        """
            Update Dispatch for carrier.
            :param instance:
            :param validated_data:
            :return:
        """
        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        contact_info = validated_data.pop("contact")

        instance.contact.set_values(pairs=contact_info)
        instance.contact.save()
        instance.location = validated_data["location"]
        instance.is_default = validated_data["is_default"]
        instance.save()

        return instance


class PrivateCreateDispatchSerializer(serializers.ModelSerializer):

    carrier_code = serializers.IntegerField(
        source='carrier.code',
        help_text='Carrier Code',
        required=False
    )

    contact = ContactSerializer(
        many=False,
        help_text="A dictionary containing information about the contact."
    )

    class Meta:
        model = Dispatch
        fields = [
            'carrier_code',
            'contact',
            'location',
            'is_default'
        ]

    def create(self, validated_data):
        """
            Create Dispatch for carrier.
            :param validated_data:
            :return:
        """
        errors = []

        try:
            carrier = Carrier.objects.get(code=validated_data["carrier"]["code"])
            validated_data["carrier"] = carrier
        except ObjectDoesNotExist:
            errors.append({"carrier": "'carrier_code' does not exist."})
            raise ViewException(code="1909", message=f'Dispatch: Carrier not found.', errors=errors)

        is_default = validated_data["is_default"]
        validated_data["location"] = validated_data["location"].title()

        if is_default and Dispatch.objects.filter(carrier=carrier, is_default=is_default).exists():
            errors.append({"dispatch": "Dispatch already has a default."})
            raise ViewException(code="1910", message='Dispatch: Already has a default.', errors=errors)
        elif Dispatch.objects.filter(carrier=carrier, location=validated_data["location"]).exists():
            errors.append({"dispatch": f"dispatch already has location: {validated_data['location']}"})
            raise ViewException(code="1911", message=f'Dispatch: Already has a location.', errors=errors)

        contact = Contact.create(param_dict=validated_data["contact"])
        contact.save()
        validated_data["contact"] = contact
        validated_data["location"] = validated_data["location"].title()

        dispatch = Dispatch.create(param_dict=validated_data)
        dispatch.save()

        return dispatch
