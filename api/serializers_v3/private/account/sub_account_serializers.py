"""
    Title: Sub Account Serializers
    Description: This file will contain all functions for markup serializers.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import SubAccount, Contact, Address, Province, AccountTier
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.contact_serializer import ContactSerializer
from api.serializers_v3.private.account.markup_serializers import PrivateMarkupSerializer


class PrivateSubAccountSerializer(serializers.ModelSerializer):

    not_changeable = [
        'system',
        'client_account',
        'is_default',
        'is_bbe',
        'subaccount_number',
        'webhook_key',
        'markup'
    ]

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the address information."
    )

    contact = ContactSerializer(
        many=False,
        help_text="A dictionary containing information about the contact information."
    )

    markup = PrivateMarkupSerializer(
        many=False,
        help_text="A dictionary containing information about the markup information."
    )

    system_name = serializers.CharField(
        source='get_system_display',
        help_text='System Name',
        required=False
    )

    tier_id = serializers.IntegerField(
        source='tier.id',
        default=-1,
        help_text='Tier Id',
    )

    tier_name = serializers.CharField(
        source='tier.name',
        help_text='Tier name',
        default="",
        required=False
    )

    class Meta:
        model = SubAccount
        fields = [
            'id',
            'creation_date',
            'system',
            'system_name',
            'client_account',
            'address',
            'contact',
            'markup',
            'tier_id',
            'tier_name',
            'is_default',
            'subaccount_number',
            'webhook_key',
            'bc_type',
            'bc_customer_code',
            'bc_job_number',
            'bc_location_code',
            'bc_line_type',
            'bc_item',
            'bc_file_owner',
            'is_bc_push',
            'is_account_id',
            'id_prefix',
            'id_counter',
            'is_dangerous_good',
            'is_pharma',
            'is_metric_included',
            'is_bbe'
        ]

    def update(self, instance, validated_data):
        """
            Update a carrier markup.
            :param instance:
            :param validated_data:
            :return:
        """
        errors = []
        address = validated_data.pop("address")
        code = address["province"]["code"]
        country = address["province"]["country"]["code"]

        try:
            province = Province.objects.get(code=code, country__code=country)
            address["province"] = province
        except ObjectDoesNotExist:
            errors.append({"province": f"Not found 'code': {code} and 'country': {country}."})
            raise ViewException(code="3508", message=f'Sub Account: Province not found.', errors=errors)

        if "tier" in validated_data:
            try:
                tier = AccountTier.objects.get(id=validated_data["tier"]["id"])
                validated_data["tier"] = tier
            except ObjectDoesNotExist:
                errors.append({"tier": f'Tier not found for id {validated_data["tier"]["id"]}.'})
                raise ViewException(code="3507", message=f'Sub Account: tier not found.', errors=errors)

        instance.address.set_values(pairs=address)
        instance.address.save()

        contact = validated_data.pop("contact")
        instance.contact.set_values(pairs=contact)
        instance.contact.save()

        instance.set_values(pairs=validated_data)
        instance.save()

        return instance


class PrivateCreateSubAccountSerializer(serializers.ModelSerializer):

    address = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the address information."
    )

    contact = ContactSerializer(
        many=False,
        help_text="A dictionary containing information about the contact information."
    )

    class Meta:
        model = SubAccount
        fields = [
            'system',
            'client_account',
            'address',
            'contact',
            'markup',
            'tier',
            'bc_type',
            'bc_customer_code',
            'bc_job_number',
            'bc_location_code',
            'bc_line_type',
            'bc_item',
            'bc_file_owner',
            'is_bc_push',
            'is_account_id',
            'id_prefix',
            'is_dangerous_good',
            'is_pharma',
            'is_metric_included'
        ]

    @transaction.atomic
    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """
        errors = []
        address = validated_data.pop("address")
        code = address["province"]["code"]
        country = address["province"]["country"]["code"]

        validated_data["contact"]["company_name"] = validated_data["contact"]["company_name"].title().strip()

        if SubAccount.objects.filter(contact__company_name=validated_data["contact"]["company_name"]).exists():
            errors.append({"sub_account": f'{validated_data["contact"]["company_name"]} already exists.'})
            raise ViewException(code="3509", message="Sub Account: Already Exists.", errors=errors)

        try:
            province = Province.objects.get(code=code, country__code=country)
            address["province"] = province
        except ObjectDoesNotExist:
            errors.append({"province": f"Not found 'code': {code} and 'country': {country}."})
            raise ViewException(code="3510", message="Sub Account: Province not found.", errors=errors)

        try:
            tier = AccountTier.objects.get(code="enterprise")
        except ObjectDoesNotExist:
            errors.append({"province": f"Tier Not found."})
            raise ViewException(code="3510", message="Sub Account: Province not found.", errors=errors)

        address = Address.create(param_dict=address)
        address.save()
        validated_data["address"] = address

        contact = Contact.create(param_dict=validated_data["contact"])
        contact.save()
        validated_data["contact"] = contact

        sub_account = SubAccount.create(param_dict=validated_data)
        sub_account.tier = tier
        sub_account.save()

        return sub_account
