"""
    Title: Metric Account Serializers
    Description: This file will contain all functions for Metric Goals serializers.
    Created: Jan 3, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import MetricAccount


class MetricAccountSerializer(serializers.ModelSerializer):

    legs = serializers.SerializerMethodField(
        'get_leg_total',
        required=False
    )

    class Meta:
        model = MetricAccount
        fields = [
            'id',
            'sub_account',
            'creation_date',
            'shipments',
            'legs',
            'air_legs',
            'ltl_legs',
            'ftl_legs',
            'courier_legs',
            'sea_legs',
            'quantity',
            'weight',
            'revenue',
            'expense',
            'net_profit',
            'air_revenue',
            'air_expense',
            'air_net_profit',
            'ltl_revenue',
            'ltl_expense',
            'ltl_net_profit',
            'ftl_revenue',
            'ftl_expense',
            'ftl_net_profit',
            'courier_revenue',
            'courier_expense',
            'courier_net_profit',
            'sea_revenue',
            'sea_expense',
            'sea_net_profit'
        ]

    @staticmethod
    def get_leg_total(obj):
        return obj.air_legs + obj.ltl_legs + obj.ftl_legs + obj.courier_legs + obj.sea_legs
