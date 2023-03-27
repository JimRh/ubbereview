"""
    Title: Package Type Serializers
    Description: This file will contain all functions for Package Type serializers.
    Created: Jan 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import PackageType, Account


class PackageTypeSerializer(serializers.ModelSerializer):
    not_changeable = [
        'account'
    ]

    account_name = serializers.CharField(
        source='account.user.username',
        help_text='Account Name'
    )

    class Meta:
        model = PackageType
        fields = [
            'id',
            'account_name',
            'code',
            'name',
            'min_overall_dims',
            'max_overall_dims',
            'min_weight',
            'max_weight',
            'is_common',
            'is_dangerous_good',
            'is_pharma',
            'is_active',
            'carrier'
        ]

    @transaction.atomic
    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """
        errors = []

        try:
            account = Account.objects.get(user__username=validated_data["account"]["user"]["username"])
        except ObjectDoesNotExist:
            errors.append({"account": "Account not found."})
            raise ViewException(code="1109", message="Package Types: Account not found.", errors=errors)

        package_type = PackageType.create(param_dict=validated_data)
        package_type.account = account
        package_type.save()
        package_type.carrier.add(*validated_data["carrier"])
        package_type.save()

        return package_type

    @transaction.atomic
    def update(self, instance, validated_data):
        """
            Update City Alias for a carrier.
            :param instance:
            :param validated_data:
            :return:
        """
        for field in self.not_changeable:
            if field in validated_data:
                del validated_data[field]

        carriers = validated_data.pop("carrier")

        instance.set_values(validated_data)
        instance.save()
        instance.carrier.set(carriers)

        return instance
