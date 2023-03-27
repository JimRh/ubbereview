from rest_framework import serializers

from api.globals.project import DEFAULT_CHAR_LEN, SHIPMENT_IDENTIFIER_LEN
from api.models import Leg
from api.serializers_v3.common.address_serializer import AddressSerializer
from api.serializers_v3.common.track_serializers import TrackSerializer


class LegOverdueSerializer(serializers.ModelSerializer):

    sub_account = serializers.CharField(
        source="shipment.subaccount.contact.company_name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name."
    )

    account_number = serializers.CharField(
        source="shipment.subaccount.subaccount_number",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name."
    )

    shipment_id = serializers.CharField(
        source="shipment.shipment_id",
        max_length=SHIPMENT_IDENTIFIER_LEN,
        help_text='Shipment ID - ubbe identification and used for tracking.'
    )

    carrier = serializers.CharField(
        source="carrier.name",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Name."
    )

    carrier_id = serializers.CharField(
        source="carrier.code",
        max_length=DEFAULT_CHAR_LEN,
        help_text="Carrier Code."
    )

    origin = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the origin."
    )

    destination = AddressSerializer(
        many=False,
        help_text="A dictionary containing information about the destination."
    )

    tracking_list = serializers.SerializerMethodField(
        'get_tracking_status',
        help_text='A list of tracking.',
    )

    class Meta:
        model = Leg
        fields = [
            'id',
            'ship_date',
            'sub_account',
            'account_number',
            'shipment_id',
            'leg_id',
            'carrier',
            'carrier_id',
            'service_name',
            'origin',
            'destination',
            'tracking_identifier',
            'carrier_pickup_identifier',
            'transit_days',
            'tracking_list',
            'estimated_delivery_date',
            'updated_est_delivery_date',
            'delivered_date',
            'is_pickup_overdue',
            'is_overdue'
        ]

    def get_tracking_status(self, obj):
        ordered_queryset = obj.tracking_status_leg.all().order_by("updated_datetime")
        return TrackSerializer(ordered_queryset, many=True, context=self.context).data
