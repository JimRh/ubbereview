import copy
import datetime
from decimal import Decimal
from typing import Tuple

import gevent
from django.db import connection
from gevent.queue import Queue  # pylint: disable=ungrouped-imports
from zeep.exceptions import Fault

from api.apis.carriers.canada_post.abstraction.canadapost_api import CanadaPostAPI
from api.apis.carriers.canada_post.abstraction.canadapost_pickup import CanadaPostPickup
from api.apis.carriers.canada_post.abstraction.canadapost_validate_service import (
    CanadaPostValidateRate,
)
from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.globals.util import Endpoints
from api.apis.carriers.canada_post.soap_objects.mailing_scenario import MailingScenario
from api.apis.services.taxes.taxes import Taxes
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import RateException
from api.globals.carriers import CAN_POST
from api.utilities.date_utility import DateUtility


class CanadaPostRate(CanadaPostAPI):
    _price_precision = Decimal("0.01")
    _flat_pickup_rate = Decimal("3.50")
    # Ref: https://www.canadapost.ca/cpo/mc/business/productsservices/developers/services/rating/getrates/default.jsf
    _priority_worldwide_services = (
        "DOM.PC",
        "USA.PW.ENV",
        "USA.PW.PAK",
        "USA.PW.PARCEL",
        "INT.PW.ENV",
        "INT.PW.PAK",
        "INT.PW.PARCEL",
    )
    _domestic_services = ("DOM.RP", "DOM.EP", "DOM.XP", "DOM.XP.CERT", "DOM.PC")
    _united_states_services = (
        "USA.EP",
        "USA.PW.ENV",
        "USA.PW.PAK",
        "USA.PW.PARCEL",
        "USA.SP.AIR",
        "USA.TP",
        "USA.TP.LVM",
        "USA.XP",
    )
    _international_services = (
        "INT.XP",
        "INT.IP.AIR",
        "INT.IP.SURF",
        "INT.PW.ENV",
        "INT.PW.PAK",
        "INT.PW.PARCEL",
        "INT.SP.AIR",
        "INT.SP.SURF",
        "INT.TP",
    )

    def __init__(self, world_request: dict) -> None:
        super(CanadaPostRate, self).__init__(world_request)
        self.world_response = []
        self._canadapost_responses = []
        self._valid_services = []
        self._packages = world_request["packages"]
        self._canadapost_requests = Queue()

        self.sub_account = world_request["objects"]["sub_account"]
        self.carrier_account = world_request["objects"]["carrier_accounts"][CAN_POST][
            "account"
        ]
        self.carrier = world_request["objects"]["carrier_accounts"][CAN_POST]["carrier"]
        self.endpoints = Endpoints(self.carrier_account)

    @staticmethod
    def _calc_total_surcharges(surcharges: list) -> Decimal:
        return sum(surcharge["adjustment-cost"] for surcharge in surcharges)

    def _calc_total_tax(self, taxes: dict) -> Tuple[Decimal, Decimal]:
        total_tax_percent = sum(
            taxes[tax]["percent"] for tax in taxes if taxes[tax]["percent"] is not None
        )

        if total_tax_percent == 0:
            total_tax_percent = Decimal("0.00")
        else:
            total_tax_percent = total_tax_percent.quantize(self._price_precision)

        return sum(taxes[tax]["_value_1"] for tax in taxes), total_tax_percent

    def rate(self) -> list:
        # Temporary
        if self._world_request["destination"]["country"] != "CA":
            connection.close()
            return []

        if self._world_request.get("carrier_options", []):
            connection.close()
            return []

        if self._world_request["destination"]["country"] == "CA":
            for service in self._domestic_services:
                request = copy.deepcopy(self._world_request)
                request["service_code"] = service
                valid_service, _ = CanadaPostValidateRate(request).is_valid()

                if valid_service:
                    self._valid_services.append(service)
        elif self._world_request["destination"]["country"] == "US":
            for service in self._united_states_services:
                request = copy.deepcopy(self._world_request)
                request["service_code"] = service
                valid_service, _ = CanadaPostValidateRate(request).is_valid()

                if valid_service:
                    self._valid_services.append(service)
        else:
            for service in self._international_services:
                request = copy.deepcopy(self._world_request)
                request["service_code"] = service
                valid_service, _ = CanadaPostValidateRate(request).is_valid()

                if valid_service:
                    self._valid_services.append(service)

        if not self._valid_services:
            CeleryLogger().l_warning.delay(
                location="canadapost_rate line: 121",
                message=str("No valid services for rate request"),
            )
            connection.close()
            return []

        try:
            self._post()
        except Fault as e:
            CeleryLogger().l_error.delay(
                location="canadapost_ship line: 131",
                message=str(
                    {"api.error.canada_post.rate": "Zeep Failure: {}".format(e.message)}
                ),
            )
            connection.close()
            return []
        except CanadaPostAPIException as e:
            CeleryLogger().l_error.delay(
                location="canadapost_ship line: 138",
                message=str({"api.error.canada_post.rate": e.message}),
            )
            connection.close()
            return []

        try:
            self._format_response()
        except RateException as e:
            CeleryLogger().l_error.delay(
                location="canadapost_ship line: 138",
                message=str({"api.error.canada_post.rate": e.message}),
            )
            connection.close()
            return []

        connection.close()
        return self.world_response

    def worker(self) -> None:
        while not self._canadapost_requests.empty():
            canadapost_request = self._canadapost_requests.get()

            canadapost_response = self.endpoints.RATE_SERVICE.GetRates(
                **{"mailing-scenario": MailingScenario(canadapost_request).data()}
            )

            if canadapost_response["messages"] is None:
                self._canadapost_responses.append(canadapost_response)
            else:
                CeleryLogger().l_warning.delay(
                    location="canadapost_ship line: 138",
                    message="Canada Post rating response data: {}".format(
                        canadapost_response
                    ),
                )

    # Override
    def _format_response(self) -> None:
        if not self._canadapost_responses:
            raise RateException(
                {"api.canadapost.error": "Canada Post Rate: No Rates found."}
            )

        self.world_response = [
            {
                "carrier_id": CAN_POST,
                "carrier_name": "Canada Post",
                "service_code": rate["service-code"],
                "service_name": rate["service-name"],
                "freight": Decimal("0.00"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("0.00"),
                "tax_percent": Decimal("0.00"),
                "total": Decimal("0.00"),
                "transit_days": 0,
            }
            for rate in self._canadapost_responses[0]["price-quotes"]["price-quote"]
            if rate["service-code"] in self._valid_services
        ]

        for rate in self.world_response:
            tax_percent = Decimal("0.00")

            for i, can_post_rate in enumerate(self._canadapost_responses):
                pkg_qty = self._packages[i]["quantity"]

                for service_rate in can_post_rate["price-quotes"]["price-quote"]:
                    if (
                        service_rate["service-code"] in self._valid_services
                        and rate["service_code"] == service_rate["service-code"]
                    ):
                        tax_amount, tax_percent = self._calc_total_tax(
                            service_rate["price-details"]["taxes"]
                        )
                        rate["total"] += service_rate["price-details"]["due"] * pkg_qty

                        # Zeep oddity, cannot perform a .get() operation or cast to dict()
                        try:
                            service_rate["adjustments"]
                        except KeyError:
                            pass
                        else:
                            rate["surcharge"] += (
                                self._calc_total_surcharges(
                                    service_rate["price-details"]["adjustments"][
                                        "adjustment"
                                    ]
                                )
                                * pkg_qty
                            )
                        rate["tax"] += tax_amount * pkg_qty

                        if not service_rate["service-standard"][
                            "expected-transit-time"
                        ]:
                            rate["delivery_date"], rate["transit_days"] = DateUtility(
                                pickup=self._world_request.get("pickup", {})
                            ).get_estimated_delivery(
                                transit=self._default_transit,
                                province=self._world_request["origin"]["province"],
                                country=self._world_request["origin"]["country"],
                            )
                        else:
                            rate["transit_days"] = service_rate["service-standard"][
                                "expected-transit-time"
                            ]
                            delivery_date = service_rate["service-standard"][
                                "expected-delivery-date"
                            ]
                            estimated_delivery_date = datetime.datetime.combine(
                                delivery_date, datetime.datetime.min.time()
                            )
                            rate["delivery_date"] = estimated_delivery_date

            rate["freight"] = rate["total"] - rate["tax"] - rate["surcharge"]
            rate["tax_percent"] = tax_percent

            # Ref: https://www.canadapost.ca/cpc/en/business/shipping/request-pickup.page#!navtabd2054e7
            if rate["service_code"] not in self._priority_worldwide_services:
                pickup_tax = Taxes(self._world_request["origin"]).get_tax_rate(
                    self._flat_pickup_rate
                )
                rate["total"] += self._flat_pickup_rate + pickup_tax
                rate["surcharge"] += self._flat_pickup_rate
                rate["tax"] += pickup_tax

    # Override
    def _post(self) -> None:
        for package in self._packages:
            self._canadapost_requests.put_nowait(
                {
                    "origin": self._world_request["origin"],
                    "destination": self._world_request["destination"],
                    "package": package,
                    "_carrier_account": self.carrier_account,
                }
            )

        workers = [gevent.spawn(self.worker) for _ in self._packages]
        gevent.joinall(workers)

        for worker in workers:
            worker.get()
