from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist

from api.background_tasks.logger import CeleryLogger
from api.models import NorthernPDAddress


class PickupDeliveryCost:
    """
    Handles the creation of Pickup and Delivery to be passed to Skyline
    """

    _sig_fig = Decimal("0.01")
    _is_pickup = False
    _is_delivery = False
    _chargeable_weight = Decimal("0.00")
    _local_pickup_id = 104
    _local_delivery_id = 105
    _local_pickup_name = "Local Pickup Charge"
    _local_delivery_name = "Local Delivery Charge"
    _origin_city = ""
    _delivery_city = ""

    def __init__(
        self,
        is_pickup: bool,
        is_delivery: bool,
        total_weight: Decimal,
        total_dim: Decimal,
        origin_city: str,
        delivery_city: str,
    ):
        self._is_pickup = is_pickup
        self._is_delivery = is_delivery
        self._origin_city = origin_city
        self._delivery_city = delivery_city

        if total_weight > total_dim:
            self._chargeable_weight = total_weight
        else:
            self._chargeable_weight = total_dim

    @staticmethod
    def create_surcharge(
        pickup_company_id: int, charge: Decimal, definition_id: int, fee_name: str
    ) -> dict:
        """
        Get Northern Address P & D cost values
        :param pickup_company_id: 3 Character string: YEG
        :param charge:
        :param definition_id:
        :param fee_name:
        :return: Airbase Object
        """

        return {
            "PickupCompanyId": pickup_company_id,
            "Charge": charge,
            "DefinitionId": definition_id,
            "FeeName": fee_name,
        }

    def calculate_charge(self, airbase: NorthernPDAddress) -> Decimal:
        """
        Calculates cost of P or D.
        :param airbase: CanadianAirBases Object
        :return: Amount
        """

        if self._chargeable_weight < airbase.cutoff_weight:
            amount = airbase.min_price
        else:
            extra_weight = Decimal(self._chargeable_weight) - airbase.cutoff_weight

            amount = (Decimal(extra_weight) * airbase.price_per_kg) + airbase.min_price
        return Decimal(amount).quantize(self._sig_fig)

    def calculate_pickup(self) -> dict:
        try:
            pickup_address = NorthernPDAddress.objects.get(
                city_name__iexact=self._origin_city
            )
        except ObjectDoesNotExist:
            CeleryLogger().l_debug.delay(
                location="pickup_delivery_cost.py line: 74",
                message=f"Lookup Error (Pickup Charge): Canadian North Airbase does not exist: {self._origin_city}",
            )
            return {}

        amount = self.calculate_charge(airbase=pickup_address)

        charge = self.create_surcharge(
            pickup_company_id=pickup_address.pickup_id,
            charge=amount,
            definition_id=self._local_pickup_id,
            fee_name=self._local_pickup_name,
        )
        return charge

    def calculate_delivery(self) -> dict:
        try:
            delivery_address = NorthernPDAddress.objects.get(
                city_name__iexact=self._delivery_city
            )
        except ObjectDoesNotExist:
            CeleryLogger().l_debug.delay(
                location="pickup_delivery_cost.py line: 90",
                message=f"Lookup Error (Delivery Charge): Canadian North Airbase does not exist: {self._delivery_city}",
            )

            return {}

        amount = self.calculate_charge(airbase=delivery_address)

        charge = self.create_surcharge(
            pickup_company_id=delivery_address.delivery_id,
            charge=amount,
            definition_id=self._local_delivery_id,
            fee_name=self._local_delivery_name,
        )

        return charge

    def calculate_pickup_delivery(self) -> list:
        """
        Creates all pickup and Delivery Charges. Also includes third party charges
        :return: List of Dicts
        """
        request_response = []

        if self._is_pickup:
            charge = self.calculate_pickup()
            request_response.append(charge)

        if self._is_delivery:
            charge = self.calculate_delivery()
            request_response.append(charge)

        return request_response
