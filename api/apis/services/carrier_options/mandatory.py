from datetime import datetime
from decimal import Decimal
from typing import Union

import numexpr

from api.apis.services.carrier_options.option_utilities import check_carrier, date_check, min_max_update
from api.exceptions.services import CarrierOptionException, OptionNotApplicableException
from api.general.convert import Convert
from api.models import API, Carrier, MandatoryOption


class Mandatory:
    _destinations = ("Fort Providence", "Rae-Edzo", "Edzo", "Yellowknife", "Dettah")

    @staticmethod
    def _ca_province_carbon_tax(province: str, request: dict) -> None:
        origin = request["origin"]
        destination = request["destination"]

        origin_province = origin["province"] == province
        origin_country = origin["country"] == "CA"
        destination_province = destination["province"] == province
        destination_country = destination["country"] == "CA"
        applies = origin_province and origin_country or destination_province and destination_country

        if not applies:
            raise OptionNotApplicableException({"option.invalid": "Option does not apply"})

    # pylint:disable=unused-argument
    @staticmethod
    def _evaluate_expression(option: MandatoryOption, actual: float, dimensional: float, weight: float, freight: float,
                             date: datetime) -> Decimal:
        date_check(date, option.start_date, option.end_date)
        value = Decimal(numexpr.evaluate(option.evaluation_expression).item()).quantize(Decimal("0.01"))

        return min_max_update(value, option.minimum_value, option.maximum_value)

    # pylint:enable=unused-argument

    @staticmethod
    def _long_freight(request: dict) -> None:
        for package in request["packages"]:
            length = package["length"]
            width = package["width"]
            height = package["height"]
            max_len = max(length, width, height)

            if (Convert().cms_to_inches(max_len) / Decimal("12.00")).quantize(Decimal("0.01")) > Decimal("12.00"):
                return None
        raise OptionNotApplicableException({"option.invalid": "Option does not apply"})

    @staticmethod
    def _nl_ship(request: dict) -> None:
        origin_province = request["origin"]["province"] == "NL"
        origin_country = request["origin"]["country"] == "CA"
        destination_province = request["destination"]["province"] == "NL"
        destination_country = request["destination"]["country"] == "CA"
        origin = origin_province and origin_country
        destination = destination_province and destination_country
        applies = (origin or destination) and origin != destination

        if not applies:
            raise OptionNotApplicableException({"option.invalid": "Option does not apply"})

    @staticmethod
    def _road_ban(request: dict) -> Union[Decimal, None]:
        northern_roadban_territories = {"YT", "NT"}
        origin_province = request["origin"]["province"] in northern_roadban_territories
        origin_country = request["origin"]["country"] == "CA"
        destination_province = request["destination"]["province"] in northern_roadban_territories
        destination_country = request["destination"]["country"] == "CA"
        applies = origin_province and origin_country or destination_province and destination_country

        if not applies:
            raise OptionNotApplicableException({"option.invalid": "Option does not apply"})

        if API.objects.get(name="NorthernRoadBan").active:
            return Decimal("0.00")
        raise OptionNotApplicableException({"option.invalid": "Option does not apply"})

    def _deh_cho(self, request: dict) -> None:
        if request["destination"]["city"] not in self._destinations:
            raise OptionNotApplicableException({"option.implementation": "Option not supported"})

    def _get_calculated_mandatory_option_cost(self, option: MandatoryOption, request: dict, actual: float,
                                              dimensional: float, weight: float, freight: float,
                                              date: datetime) -> dict:
        option_name = option.option.name

        if option_name == "AB Carbon Tax":
            self._ca_province_carbon_tax(province="AB", request=request)
        elif option_name == "BC Carbon Tax":
            self._ca_province_carbon_tax(province="BC", request=request)
        elif option_name == "MB Carbon Tax":
            self._ca_province_carbon_tax(province="MB", request=request)
        elif option_name == "NB Carbon Tax":
            self._ca_province_carbon_tax(province="NB", request=request)
        elif option_name == "NF Carbon Tax":
            self._ca_province_carbon_tax(province="NL", request=request)
        elif option_name == "NT Carbon Tax":
            self._ca_province_carbon_tax(province="NT", request=request)
        elif option_name == "NS Carbon Tax":
            self._ca_province_carbon_tax(province="NS", request=request)
        elif option_name == "NU Carbon Tax":
            self._ca_province_carbon_tax(province="NU", request=request)
        elif option_name == "ON Carbon Tax":
            self._ca_province_carbon_tax(province="ON", request=request)
        elif option_name == "PE Carbon Tax":
            self._ca_province_carbon_tax(province="PE", request=request)
        elif option_name == "QC Carbon Tax":
            self._ca_province_carbon_tax(province="QC", request=request)
        elif option_name == "SK Carbon Tax":
            self._ca_province_carbon_tax(province="SK", request=request)
        elif option_name == "YT Carbon Tax":
            self._ca_province_carbon_tax(province="YT", request=request)
        elif option_name == "Deh Cho Bridge":
            self._deh_cho(request)
        elif option_name == "Long Freight":
            self._long_freight(request)
        elif option_name == "Northern Road Ban":
            self._road_ban(request)
        elif option_name == "Newfoundland Ferry":
            self._nl_ship(request)
        elif option_name == "Residential Pickup" and not request["origin"].get("has_shipping_bays", True):
            pass
        elif option_name == "Residential Delivery" and not request["destination"].get("has_shipping_bays", True):
            pass
        elif option_name == "Weekend or Holiday Pickup":
            self._w_or_h_pu(request)
        elif option_name == "Dangerous Goods" and request.get("is_dg_shipment", False):
            pass
        elif option_name == "Fuel Surcharge":
            pass
        elif option_name == "Nav Canada":
            pass
        elif option_name == "Carbon Tax":
            pass
        elif option_name == "Domestic Handling fee":
            pass
        elif option_name == "Cargo Screening":
            pass
        elif option_name == "Administration Fee":
            pass
        elif option_name == "Pickup Charge":
            pass
        else:
            raise OptionNotApplicableException({"option.invalid": "Option does not apply"})
        return {
            "name": option_name,
            "cost": self._evaluate_expression(option, actual, dimensional, weight, freight, date),
            "percentage": option.percentage
        }

    # Keep commented code. Pending future implementation/integration.
    def _w_or_h_pu(self, request: dict) -> None:
        raise OptionNotApplicableException({"option.implementation": "Option not supported"})
        # if request.get("Service", {}).get("Pickup") is not None:
        #     pu_date = datetime.strptime(request["Pickup"]["Date"], "%Y-%m-%d")
        #
        #     if pu_date.weekday() < 5 and pu_date.date() not in self._ca_holidays:
        #         raise OptionNotApplicableException({"option.invalid": "Option does not apply"})
        #     return None
        # raise OptionNotApplicableException({"option.invalid": "Option does not apply"})

    def _get_carbon_tax(self, carbon_tax, request, actual, dimensional,weight, freight, date) -> dict:
        """
            Get carbon tax for an carrier, if multiple carbon tax get the highest percentage.
            :return:
        """
        origin_province = request["origin"]["province"]
        destination_province = request["destination"]["province"]
        highest = None

        if len(carbon_tax) == 1:
            try:
                carbon_cost = self._get_calculated_mandatory_option_cost(
                    carbon_tax[0], request, actual, dimensional, weight, freight, date
                )
            except CarrierOptionException:
                return {}

            return carbon_cost

        for option in carbon_tax:
            applies = origin_province in option.option.name or destination_province in option.option.name

            if not highest and applies:
                highest = option

            if highest and option.percentage > highest.percentage and applies:
                highest = option

        try:
            carbon_cost = self._get_calculated_mandatory_option_cost(
                highest, request, actual, dimensional, weight, freight, date
            )
        except CarrierOptionException:
            return {}

        carbon_cost["name"] = "Carbon Tax"

        return carbon_cost

    def get_calculated_option_costs(self, carrier: Union[Carrier, int], request: dict, actual: Decimal, cubic: Decimal,
                                    freight: Decimal, date: datetime) -> list:
        carrier = check_carrier(carrier)
        dimensional = float(cubic * carrier.linear_weight)
        actual = float(Convert().kgs_to_lbs(actual))
        weight = max(dimensional, actual)
        freight = float(freight)
        processed_carrier_options = []
        carbon_tax = []

        for option in MandatoryOption.objects.filter(carrier=carrier):

            if "Carbon Tax" in option.option.name:
                carbon_tax.append(option)
                continue

            try:
                evaluation = self._get_calculated_mandatory_option_cost(option, request, actual, dimensional,
                                                                        weight, freight, date)
            except CarrierOptionException:
                continue
            processed_carrier_options.append(evaluation)

        if carbon_tax:
            carbon_cost = self._get_carbon_tax(carbon_tax, request, actual, dimensional, weight, freight, date)

            if carbon_cost:
                processed_carrier_options.append(carbon_cost)

        return processed_carrier_options
