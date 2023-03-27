"""
    Title: Dangerous Good Packing Instruction Serializers
    Description: This file will contain all functions for Dangerous Good packing instruction serializers.
    Created: November 25, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from rest_framework import serializers

from api.models import DangerousGoodPackingInstruction


class DGPackingInstructionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DangerousGoodPackingInstruction
        fields = [
            'id',
            'code',
            'packaging_types',
            'exempted_statement'

        ]
