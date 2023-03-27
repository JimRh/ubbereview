"""
    Title: Private northern pd address Serializers
    Description: This file will contain all functions for private northern pickup delivery address serializers.
    Created: December 02, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.models import CNInterline


class PrivateInterlineSerializer(serializers.ModelSerializer):

    class Meta:
        model = CNInterline
        fields = [
            'id',
            'origin',
            'destination',
            'interline_id',
            'interline_carrier'
        ]
