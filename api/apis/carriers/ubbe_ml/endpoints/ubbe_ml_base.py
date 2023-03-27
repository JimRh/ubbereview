"""
    Title: ubbe ML Base Carrier Api
    Description: TThis file will contain functions related to ubbe ML Base Api.
    Created: Jan 6, 2023
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import copy
import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from api.apis.services.carrier_options.carrier_options import CarrierOptions
from api.apis.services.carrier_options.mandatory import Mandatory
from api.apis.google.route_apis.distance_api import GoogleDistanceApi
from api.apis.services.taxes.taxes import Taxes
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ViewException
from api.exceptions.services import CarrierOptionException
from api.globals.carriers import UBBE_ML
from api.models import FuelSurcharge, Carrier, UbbeMlRegressors, LocationDistance


class MLCarrierBase:
    """
    Class will handle common details between the sub classes.
    """

    _hundred = Decimal("100.00")
    _thousand = Decimal("1000.00")
    _cubic = Decimal("2.5")
    _sig_fig = Decimal("0.01")
    _zero = Decimal("0.00")
    _service = "LTL"
    _service_name = "ubbe LTL"
    _carrier_name = "ubbe LTL"
    _carrier_id = UBBE_ML
    _markup = 0

    def __init__(self, ubbe_request: dict) -> None:
        self._ubbe_request = copy.deepcopy(ubbe_request)
        self._error_world_request = copy.deepcopy(self._ubbe_request)
        self._process_ubbe_data()
        self._clean_error_copy()

    def _process_ubbe_data(self) -> None:
        """
        Pre set used vars as quick class vars
        """
        self._date = datetime.datetime.now(tz=timezone.utc)

        # self._carrier_id = self._ubbe_request["carrier_id"]
        self._origin = self._ubbe_request["origin"]
        self._destination = self._ubbe_request["destination"]
        self._packages = self._ubbe_request["packages"]
        self._total_quantity = self._ubbe_request.get("total_quantity", 1)

        # Weight Information
        self._total_mass_metric = self._ubbe_request["total_weight"]
        self._total_volume_metric = self._ubbe_request["total_volume"]

        self._total_mass_imperial = self._ubbe_request["total_weight_imperial"]
        self._total_volume_imperial = self._ubbe_request["total_volume_imperial"]

        self._is_metric = self._ubbe_request["is_metric"]

        self._carrier = self._ubbe_request["objects"]["carrier_accounts"][
            self._carrier_id
        ]["carrier"]

    def _clean_error_copy(self) -> None:
        """
        Remove any objects for celery and redis
        """

        if "dg_service" in self._error_world_request:
            del self._error_world_request["dg_service"]

        if "objects" in self._error_world_request:
            del self._error_world_request["objects"]

    def _get_fuel_surcharge_cost(
        self, carrier_id: int, final_weight: Decimal, freight_cost: Decimal
    ) -> dict:
        """
        Get Fuel Surcharge percentage for carrier and lane, based on Weight and Freight Cost.
        :param carrier_id: Carrier ID
        :param final_weight: Final total weight
        :param freight_cost: Final Freight Cost
        :return: Fuel Surcharge Cost
        """

        if self._origin["country"] == self._destination["country"]:
            fuel_type = "D"
        else:
            fuel_type = "I"

        try:
            fuel_surcharge = FuelSurcharge.objects.get(
                carrier__code=carrier_id, fuel_type=fuel_type
            )
        except ObjectDoesNotExist:
            return {
                "carrier_id": carrier_id,
                "name": "Fuel Surcharge",
                "cost": self._zero,
                "percentage": self._zero,
            }

        return fuel_surcharge.get_json(weight=final_weight, freight_cost=freight_cost)

    @staticmethod
    def _get_distance(origin: dict, destination: dict) -> LocationDistance:
        """
        Get the location distance object for an origin and destination.
        :param origin: Origin Dict
        :param destination: Destination Dict
        :return: LocationDistance object
        """

        try:
            distance = GoogleDistanceApi().get_distance(origin, destination)
        except KeyError as e:
            raise ViewException("Error getting distance.") from e

        return distance

    def _get_final_weight(self, carrier: Carrier) -> Decimal:
        """
        Get the max weight between dimensional weight and the total mass in imperial.
        :param carrier: Carrier object
        :return: Max weight
        """
        dimensional_weight = self._total_volume_imperial * carrier.linear_weight
        return max(dimensional_weight, self._total_mass_imperial)

    def _get_taxes(self, freight: Decimal, surcharges_cost: Decimal) -> Decimal:
        """
        Get the tax calculation for the total cost of freight and surchages at the destination.
        :param freight: freight cost
        :param surcharges_cost: surcharges cost
        :return: Tax amount
        """
        try:
            return Taxes(self._destination).get_tax_rate(
                Decimal(freight) + surcharges_cost
            )
        except Exception:
            # raise ShipException({"api.error.ubbe_ml.api": "Error fetching tax: {}".format(str(e))})
            return Decimal("0.00")

    def _get_mandatory_options(self, carrier, freight_cost) -> list:
        """
        Get the mandatory options for the carrier, freight cost may be required for additional costs..
        :param carrier: Carrier object
        :param freight_cost: cost of freight
        :return: List of mandatory options
        """
        mandatory_request = {
            "carrier_id": self._carrier_id,
            "is_dg_shipment": self._ubbe_request.get("is_dangerous_shipment", False),
            "origin": self._origin,
            "destination": self._destination,
            "packages": self._packages,
        }

        if self._is_metric:
            mass = self._total_mass_metric
            volume = self._total_volume_metric
        else:
            mass = self._total_mass_imperial
            volume = self._total_volume_imperial

        try:
            mandatory_options = Mandatory().get_calculated_option_costs(
                carrier=carrier,
                request=mandatory_request,
                actual=mass,
                cubic=volume,
                freight=freight_cost,
                date=self._date,
            )
        except CarrierOptionException as e:
            mandatory_options = []
            raise CarrierOptionException(
                {"api.error.ubbeml.api": f"Carrier Option Exception: {str(e)}"}
            ) from e

        return mandatory_options

    def _get_carrier_options(
        self, carrier, freight_cost: Decimal, is_metric: bool
    ) -> list:
        """
        Get chosen option cost for carrier ratesheet
        :param is_metric: Is metric units
        :param sheet: ratesheet
        :param freight_cost: Freight Cost
        :return: list of option cost
        """

        if is_metric:
            mass = self._total_mass_metric
            volume = self._total_volume_metric
        else:
            mass = self._total_mass_imperial
            volume = self._total_volume_imperial

        try:
            carrier_options = CarrierOptions().get_calculated_option_costs(
                carrier=carrier,
                options=self._ubbe_request.get("carrier_options", []),
                actual=mass,
                cubic=volume,
                freight=freight_cost,
                date=self._date,
            )
        except CarrierOptionException:
            return []

        return carrier_options

    def _get_all_surcharges(self, freight_cost) -> tuple:
        """
        Get all the surcharges for a shipment.
        :param freight_cost: cost of freight
        :return: Total cost, Surcharges and Taxes
        """
        surcharges = self._zero
        carrier = self._carrier

        final_weight = self._get_final_weight(carrier)

        # Get Mandatory Options
        surcharges_list = self._get_mandatory_options(
            carrier=carrier, freight_cost=freight_cost
        )
        surcharges_list.extend(
            self._get_carrier_options(
                carrier=carrier, freight_cost=freight_cost, is_metric=False
            )
        )

        for option in surcharges_list:
            surcharges += option["cost"]

        # Get Fuel Surcharge
        fuel_surcharge = self._get_fuel_surcharge_cost(
            carrier_id=self._carrier_id,
            final_weight=final_weight,
            freight_cost=freight_cost,
        )
        surcharges += fuel_surcharge["cost"]
        taxes = self._get_taxes(freight_cost, surcharges)
        total = freight_cost + surcharges + taxes
        return total, surcharges, taxes

    @staticmethod
    def get_ml_price_cents(weight_kg: float, distance_km: float) -> int:
        """
        Returns a price given the following data:
        Weight of the shipment in kg,
        Distance as returned by Google DistanceMatrixAPI in km,
        Markup as percentage value i.e. 10 would be 10%, 25 would be 25%.
        returns canadian cents
        """

        # Input checking
        # TODO log the error to aid in debugging
        if weight_kg <= 0:
            CeleryLogger().l_info.delay(
                location="ube_ml_api.py line: 183", message="Weight <= 0"
            )
            raise ValueError(
                {
                    "api.error.ubbeml.api": f"Invalid Weight: Weight cannot be less than 0: {str(weight_kg)}"
                }
            )
        if distance_km <= 0:
            CeleryLogger().l_info.delay(
                location="ube_ml_api.py line: 186", message="Distance <= 0"
            )
            raise ValueError(
                {
                    "api.error.ubbeml.api": f"Invalid Distance: Distance cannot be less than 0: {str(distance_km)}"
                }
            )

        # lbs = kg * 2.2 pounds per kg, take 1/0.45359237 and grab extra figs to be sure
        weight_lbs = float(weight_kg * 2.2046226218488)
        # 1 centipound = 100 pounds  ==>   1/100 centipounds = 1 pound   ==> 0.01 centipounds per pound
        weight_centipounds = float(weight_lbs * 0.01)

        # Round to the nearest integer, including zero as we already guarded against it.
        weight_lbs = round(weight_lbs)

        # Choose the correct regressor based on weight
        try:
            regressors = UbbeMlRegressors.objects.get(active=True)
        except (ObjectDoesNotExist, Exception) as e:
            raise ObjectDoesNotExist(
                {"api.error.ubbeml.api:": f"regressor not found: {str(e)}"}
            ) from e

        if 0 <= weight_lbs < 501:
            coefficient_m = float(regressors.lbs_0_500_m)
            coefficient_b = float(regressors.lbs_0_500_b)
        elif 501 <= weight_lbs < 1001:
            coefficient_m = float(regressors.lbs_500_1000_m)
            coefficient_b = float(regressors.lbs_500_1000_b)
        elif 1001 <= weight_lbs < 2001:
            coefficient_m = float(regressors.lbs_1000_2000_m)
            coefficient_b = float(regressors.lbs_1000_2000_b)
        elif 2001 <= weight_lbs < 5001:
            coefficient_m = float(regressors.lbs_2000_5000_m)
            coefficient_b = float(regressors.lbs_2000_5000_b)
        elif 5001 <= weight_lbs < 10001:
            coefficient_m = float(regressors.lbs_5000_10000_m)
            coefficient_b = float(regressors.lbs_5000_10000_b)
        # It's over 9000!!! (actually it's over 10,000 pounds)
        else:
            coefficient_m = float(regressors.lbs_10000_plus_m)
            coefficient_b = float(regressors.lbs_10000_plus_b)

        # Returning canadian cents. Weight * price per km * distance  * markup * 100 cents per dollar
        # NEW FORMULA! (m*distance +b)*weight*100
        price_cents = round(
            ((coefficient_m * distance_km) + coefficient_b) * weight_centipounds * 100
        )

        coefficient_m = float(regressors.min_price_m)
        coefficient_b = float(regressors.min_price_b)
        # The minimum price is a dollar amount, not a rate, so it doesn't get multiplied by centipounds.
        min_price_cents = round(((coefficient_m * distance_km) + coefficient_b) * 100)

        return min_price_cents if (min_price_cents > price_cents) else price_cents
