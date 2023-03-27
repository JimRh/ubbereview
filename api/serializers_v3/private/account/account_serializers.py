"""
    Title: Markup Serializers
    Description: This file will contain all functions for markup serializers.
    Created: November 18, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from api.exceptions.project import ViewException
from api.models import Account


class PrivateAccountSerializer(serializers.ModelSerializer):

    username = serializers.CharField(
        source='user.username',
        help_text='Username'
    )

    first_name = serializers.CharField(
        source='user.first_name',
        help_text='User Last Name',
    )

    last_name = serializers.CharField(
        source='user.last_name',
        help_text='User First Name',
    )

    email = serializers.CharField(
        source='user.email',
        help_text='User Email',
    )

    class Meta:
        model = Account
        fields = [
            'id',
            'user',
            'username',
            'first_name',
            'last_name',
            'email',
            'carrier',
            'subaccounts_allowed'
        ]

    @transaction.atomic
    def create(self, validated_data):
        """
            :param validated_data:
            :return:
        """
        errors = []

        try:
            user = User(**validated_data["user"])
            user.set_password(validated_data["user"]["password"])
            user.save()
        except ValidationError as e:
            errors.append({"user": f"{str(e)}"})
            raise ViewException(code="3404", message="Account: User creation issue.", errors=errors)

        try:
            account = Account.create()
            account.user = user
            account.subaccounts_allowed = validated_data["subaccounts_allowed"] == 'on'
            account.save()
            account.carrier.set(validated_data["carrier"])
            account.save()
        except ValidationError as e:
            errors.append({"account": f"{str(e)}"})
            raise ViewException(code="3404", message="Account: Account creation issue.", errors=errors)

        return account
