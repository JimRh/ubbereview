"""
    Title: Ship BC Serializers
    Description: This file will contain all functions for ship BC serializers.
    Created: March 22, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from rest_framework import serializers

from api.globals.project import API_CHAR_LEN, API_CHAR_MID_LEN


class ShipBCPlanningSerializer(serializers.Serializer):

    leg = serializers.CharField(
        help_text='Business Central - Line Leg: M, P, D, Handling, or Allin.',
        max_length=API_CHAR_LEN,
    )

    carrier_id = serializers.CharField(
        help_text='Business Central - Carrier ID.',
        default="",
        allow_blank=True
    )

    line_type = serializers.CharField(
        help_text='Business Central - Line Type: Budget (1), Billable (2), or Both Budget and Billable (3)',
        max_length=API_CHAR_LEN,
    )

    item = serializers.CharField(
        help_text='Business Central - Item Code.',
        max_length=API_CHAR_LEN,
    )

    markup = serializers.CharField(
        help_text='Business Central - Markup, if blank default pricing is used.',
        default="",
        allow_blank=True
    )

    branch_code = serializers.CharField(
        help_text='Business Central - Branch Code to assign',
        max_length=API_CHAR_LEN,
    )

    cost_centre = serializers.CharField(
        help_text='Business Central - Cost Centre to assign',
        max_length=API_CHAR_LEN,
    )

    location_code = serializers.CharField(
        help_text='Business Central - Cost Centre to assign',
        max_length=API_CHAR_LEN,
    )


class ShipBCSerializer(serializers.Serializer):

    bc_type = serializers.IntegerField(
        help_text='Business Central Push type: New File (0), Update Existing (1), or Skip (2).',
        required=False
    )

    bc_customer = serializers.CharField(
        help_text='Optional: Business Central customer number.',
        max_length=API_CHAR_LEN,
        allow_blank=True,
        required=False
    )

    bc_job_number = serializers.CharField(
        help_text='Optional: Business Central Job Number - Must be created in the system.',
        max_length=API_CHAR_LEN,
        allow_blank=True,
        required=False
    )

    bc_username = serializers.CharField(
        help_text='Business Central Username',
        max_length=API_CHAR_LEN,
        required=False
    )

    bc_location = serializers.CharField(
        help_text='Business Central User Location',
        max_length=API_CHAR_LEN,
        required=False
    )

    bc_customer_reference_one = serializers.CharField(
        help_text='Business Central Customer Reference one: ubbe Reference One',
        max_length=API_CHAR_MID_LEN,
        allow_blank=True,
        required=False
    )

    bc_customer_reference_two = serializers.CharField(
        help_text='Business Central Customer Reference two: ubbe Reference Two',
        max_length=API_CHAR_MID_LEN,
        allow_blank=True,
        required=False
    )

    bc_customer_reference_three = serializers.CharField(
        help_text='Business Central Customer Reference three: Code 99 or Regular',
        max_length=API_CHAR_MID_LEN,
        allow_blank=True,
        required=False
    )

    bc_planning_lines = ShipBCPlanningSerializer(
        help_text='Business Central Planning Lines',
        many=True,
        required=False
    )


