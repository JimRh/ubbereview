"""
    Title: DayRoss Rate
    Description: This file will contain functions related to Day Ross and Sameday Rating.
    Created: July 13, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
import re
from decimal import Decimal

from django.db import connection
from lxml import etree
from zeep.exceptions import Fault

from api.apis.carriers.day_ross_v2.endpoints.day_ross_api_v2 import DayRossAPI
from api.apis.carriers.rate_sheets.rate_sheet_api import RateSheetApi
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ViewException
from api.globals.carriers import SAMEDAY, DAY_N_ROSS
from api.utilities.date_utility import DateUtility


class DayRossRate(DayRossAPI):
    def __init__(self, ubbe_request: dict) -> None:
        super(DayRossRate, self).__init__(ubbe_request=ubbe_request)

    def _build_request(self):
        """
        Format main body for rate request.
        :return:
        """
        data = {
            "ShipperAddress": self._create_address(self._origin),
            "ConsigneeAddress": self._create_address(self._destination),
            "BillToAccount": self._account_number,
            "Items": self._create_items(self._ubbe_request["packages"]),
            "ShipmentType": self._shipment_type,
            "PaymentType": self._payment_type,
            "MeasurementSystem": self._measurement_system,
            "Division": self._division,
            "ExpiryDate": self._expiry_date,
            "ServiceType": self._service_type,
        }

        if self._carrier_id == SAMEDAY:
            data["ServiceLevel"] = "EG"

        try:
            if self._carrier_id == DAY_N_ROSS:
                self._create_options_day_ross(data=data)
            else:
                self._create_options_same_day(data=data)
        except ViewException as e:
            raise ViewException(
                {
                    "api.error.dr.ship": f"Ship Request Fail: Please contact support. {e.message}"
                }
            )

        return self._dr_ns0.Shipment(**data)

    def _format_response(self, response: list) -> list:
        """
        Format day ross rate response into ubbe rate response.
        :param response:
        :return:
        """
        if response is None:
            return []

        rates = []

        for service_level in response:
            total_amount = service_level["TotalAmount"]

            if total_amount == 0:
                continue

            charges = {"surcharge": Decimal("0.00"), "freight": Decimal("0.00")}
            tax_percent = Decimal("0.00")

            for shipment_charge in service_level["ShipmentCharges"]["ShipmentCharge"]:
                charge_code = shipment_charge["ChargeCode"]
                local_charge_code = self._charge_codes.get(charge_code, "Unknown")
                amount = Decimal(str(shipment_charge["Amount"]))

                if not amount or local_charge_code == "Identifier":
                    continue

                if local_charge_code == "Freight":
                    charges["freight"] += amount
                elif local_charge_code == "Surcharge":
                    charges["surcharge"] += amount

                if local_charge_code == "Tax":
                    match = re.match(r"\D*(\d*)%", shipment_charge["Description"])

                    if match is not None:
                        tax_percent += Decimal(match.group(1))

                if local_charge_code != "Surcharge":
                    charges[local_charge_code] = (
                        charges.get(local_charge_code, Decimal("0.00")) + amount
                    )

            if service_level["TransitTime"]:
                transit = int(service_level["TransitTime"])
            else:
                transit = -1

            estimated_delivery_date, transit = DateUtility().get_estimated_delivery(
                transit=transit,
                country=self._origin["country"],
                province=self._origin["province"],
            )

            purchase_surcharge = self.get_purchase_surcharge()
            freight = charges.get("freight", Decimal("0.00"))
            surcharges = charges["surcharge"] + purchase_surcharge

            tax = (freight + surcharges) * (tax_percent.quantize(self._sig_fig) / 100)
            new_total = freight + surcharges + tax

            rate = {
                "carrier_id": self._carrier_id,
                "carrier_name": self._name,
                "service_code": service_level["ServiceLevelCode"],
                "service_name": str(service_level["Description"]).title(),
                "freight": freight,
                "surcharge": surcharges,
                "tax": tax,
                "tax_percent": tax_percent.quantize(self._sig_fig),
                "total": new_total,
                "transit_days": transit,
                "delivery_date": estimated_delivery_date,
            }

            rates.append(rate)

        return rates

    def _domestic_rate(self) -> list:
        """
        Get Domestic Canadian Rates
        :return:
        """

        try:
            request = self._build_request()
        except ViewException as e:
            connection.close()
            CeleryLogger().l_critical.delay(
                location="day_ross_rate.py line: 273",
                message=str(
                    {
                        "api.error.dr.rate": "Rate Request Fail: {}".format(
                            str(e.message)
                        )
                    }
                ),
            )
            return []

        try:
            rate_response = self._dr_client.service.GetRate2(
                division=self._division,
                emailAddress=self._username,
                password=self._password,
                shipment=request,
            )
        except Fault as e:
            CeleryLogger().l_warning.delay(
                location="day_ross_rate.py line: 74",
                message=str(
                    {"api.error.dr.rate": "Zeep Failure: {}".format(e.message)}
                ),
            )
            CeleryLogger().l_warning.delay(
                location="day_ross_rate.py line: 74",
                message=str(
                    {
                        "api.error.dr.rate": "{}".format(
                            etree.tounicode(
                                self._dr_history.last_received["envelope"],
                                pretty_print=True,
                            )
                        )
                    }
                ),
            )

            return []
        except ValueError:
            CeleryLogger().l_warning.delay(
                location="day_ross_rate.py line: 85",
                message="{} domestic Rate request data: {}".format(
                    self._name, etree.tounicode(self._dr_history.last_sent["envelope"])
                ),
            )

            return []

        return self._format_response(rate_response)

    def _us_rate(self) -> list:
        return []

    def rate(self) -> list:
        """
        Rate Day Ross shipment.
        :return: ubbe carrier rate response
        """

        is_domestic = (
            self._origin["country"] == "CA" and self._destination["country"] == "CA"
        )

        if is_domestic:
            rates = self._domestic_rate()
        else:
            rates = self._us_rate()

        if str(self._sub_account.subaccount_number) in self._bbe_account:
            copied = copy.deepcopy(self._ubbe_request)
            copied["carrier_id"] = [self._ubbe_request["carrier_id"]]
            rs_rates = RateSheetApi(ubbe_request=copied, is_sealift=False).rate()
            rates.extend(rs_rates)

        connection.close()
        return rates
