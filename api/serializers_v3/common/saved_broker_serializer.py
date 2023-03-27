"""
    Title: Saved Broker Serializers
    Description: This file will contain all functions for Saved Broker serializers.
    Created: May 10, 2022
    Author: Yusuf Abdulla
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import SavedBroker, SubAccount, Province, Address, Contact
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.contact_serializer import ContactSerializer


class SavedBrokerSerializer(serializers.ModelSerializer):

    account_number = serializers.CharField(
        source='sub_account.subaccount_number',
        help_text='Sub Account, account number.',
        required=True
    )

    account = serializers.CharField(
        source='sub_account.contact.company_name',
        help_text='Sub Account, account name',
        read_only=True
    )

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    contact = ContactSerializer(
        many=False,
        help_text="A dictionary containing information about the shipper."
    )

    class Meta:
        model = SavedBroker
        fields = [
            'id',
            'account_number',
            'account',
            'address',
            'contact',
        ]

    def create(self, validated_data):
        """
            Create New Saved Broker.
            :param validated_data:
            :return:
        """

        errors = []
        account = validated_data["sub_account"]["subaccount_number"]
        address = validated_data.pop("address")

        try:
            sub_account = SubAccount.objects.get(subaccount_number=account)
            validated_data["sub_account"] = sub_account
        except ObjectDoesNotExist as e:
            connection.close()
            errors.append({"sub_account": "Sub Account not found."})
            raise ViewException(code="1209", message="Saved Broker: Sub Account not found.", errors=errors)

        # if SavedBroker.objects.filter(event=validated_data["event"], sub_account__subaccount_number=account).exists():
        #     errors.append({"sub_account": "Sub Account already has event configured."})
        #     raise ViewException(code="1210", message="Saved Broker: Sub Account Already configured.", errors=errors)

        try:
            province = Province.objects.get(code=address["province"]["code"], country__code=address["province"]["country"]["code"])
            address["province"] = province
        except ObjectDoesNotExist:
            errors.append({"province": f"Not found 'code': {address['province']['code']} and 'country': {address['province']['country']['code']}."})
            raise ViewException(code="3510", message="Sub Account: Province not found.", errors=errors)

        address = Address.create(param_dict=address)
        address.save()
        validated_data["address"] = address

        contact = Contact.create(param_dict=validated_data["contact"])
        contact.save()
        validated_data["contact"] = contact

        instance = SavedBroker.create(param_dict=validated_data)
        instance.save()

        return instance

    def update(self, instance, validated_data):
        """
            Update a Saved Broker.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []
        del validated_data["sub_account"]
        address = validated_data.pop("address")

        try:
            province = Province.objects.get(
                code=address["province"]["code"], country__code=address["province"]["country"]["code"]
            )
            address["province"] = province
        except ObjectDoesNotExist:
            errors.append({"province": f"Not found 'code': {address['province']['code']} and "
                                       f"'country': {address['province']['country']['code']}."})
            raise ViewException(code="3510", message="Sub Account: Province not found.", errors=errors)

        instance.address.set_values(pairs=address)
        instance.address.save()

        instance.contact.set_values(pairs=validated_data['contact'])
        instance.contact.save()

        instance.save()

        return instance



