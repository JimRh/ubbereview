import re
from datetime import datetime
from decimal import Decimal

from django.db import connection
from zeep.exceptions import Fault

from api.apis.carriers.canada_post.abstraction.canadapost_api import CanadaPostAPI
from api.apis.carriers.canada_post.exceptions.exceptions import CanadaPostAPIException
from api.apis.carriers.canada_post.globals.util import Endpoints
from api.apis.carriers.canada_post.soap_objects.pickup_request_details import (
    PickupRequestDetails,
)
from api.background_tasks.emails import CeleryEmail
from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import PickupException
from api.globals.carriers import CAN_POST
from api.globals.project import POSTAL_CODE_REGEX, LOGGER


# TODO: review whole file implementation, so many loggers
from api.utilities.date_utility import DateUtility


class CanadaPostPickup(CanadaPostAPI):
    _null_pickup = {
        "subtotal": Decimal("0.00"),
        "total": Decimal("0.00"),
        "tax": Decimal("0.00"),
        "pickup_id": "",
        "pickup_message": "(Canada Post) Pickup Failed.",
        "pickup_status": "Failed",
    }

    def __init__(self, world_request: dict) -> None:
        super(CanadaPostPickup, self).__init__(world_request)
        self._order_number = world_request["order_number"]
        self._canadapost_response = {}
        self._availability_response = {}
        self.world_response = {}

        self.carrier_account = world_request["objects"]["carrier_accounts"][CAN_POST][
            "account"
        ]

        self.endpoints = Endpoints(self.carrier_account)
        self._world_request["_carrier_account"] = self.carrier_account

    @property
    def get_null_pickup(self) -> dict:
        return self._null_pickup

    def _clean(self):
        regex = POSTAL_CODE_REGEX["CA"]

        if (
            re.fullmatch(
                regex, self._world_request["origin"]["postal_code"], re.IGNORECASE
            )
            is None
        ):
            connection.close()
            raise PickupException(
                {
                    "api.error.canada_post.pickup": "Origin postal code does not match format '"
                    + regex
                    + "'"
                }
            )

    def _get_pickup_availability(self):
        self._availability_response = (
            self.endpoints.PICKUP_SERVICE.GetPickupAvailability(
                **{"postal-code": self._world_request["origin"]["postal_code"]}
            )
        )

    def _process_availability_response(self):
        if self._availability_response["messages"] is None:
            pu_data = self._availability_response["pickup-availability"]

            if not pu_data["on-demand-tour"]:
                raise PickupException(
                    {
                        "api.error.canada_post.pickup": "Pickup not available for specified location"
                    }
                )

            requested_endtime = datetime.strptime(
                self._world_request["pickup"]["end_time"], "%H:%M"
            )
            pu_endtime = datetime.strptime(pu_data["on-demand-cutoff"], "%H:%M")

            if requested_endtime > pu_endtime:
                self._world_request["pickup"]["end_time"] = pu_data["on-demand-cutoff"]
        else:
            messages = [
                "Canada Post Errcode: {} - {}".format(
                    message["code"], str(message["description"])
                )
                for message in self._canadapost_response["messages"]["message"]
            ]
            connection.close()
            raise PickupException({"api.error.canada_post.pickup": messages})

    # TODO: Add try/except on SOAP post
    # @staticmethod
    # def cancel(request_id: str) -> dict:
    #     if len(request_id) > 35:
    #         return {"Success": False}
    #
    #     response = REQUEST_PICKUP_SERVICE.CancelPickupRequest(**{
    #         "customer-number": CANADA_POST_CUSTOMER_NUMBER,
    #         "request-id": request_id
    #     })
    #
    #     if response["cancel-pickup-success"] is None:
    #         return {"Success": False}
    #     return {"Success": response["cancel-pickup-success"]}

    def create(self) -> dict:
        if "_carrier_account" in self._error_world_request:
            del self._error_world_request["_carrier_account"]

        try:
            self._clean()
        except PickupException as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_pickup.py line: 112",
                message=str({"api.error.canada_post.Pickup": e.message}),
            )
            CeleryEmail().pickup_issue_email.delay(
                data=self._error_world_request,
                carrier="Canada Post",
                order_number=self._order_number,
                pickup_data={},
                is_fail=True,
            )

            return self._null_pickup

        try:
            self._get_pickup_availability()
        except Fault as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_pickup.py line: 123",
                message=str(
                    {
                        "api.error.canada_post.pickup": "Zeep Failure: {}".format(
                            e.message
                        )
                    }
                ),
            )
            CeleryEmail().pickup_issue_email.delay(
                data=self._error_world_request,
                carrier="Canada Post",
                order_number=self._order_number,
                pickup_data={},
                is_fail=True,
            )

            return self._null_pickup

        try:
            self._process_availability_response()
        except PickupException as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_pickup.py line: 134",
                message=str({"api.error.canada_post.pickup": e.message}),
            )

            LOGGER.debug(self._error_world_request)

            CeleryEmail().pickup_issue_email.delay(
                data=self._error_world_request,
                carrier="Canada Post",
                order_number=self._order_number,
                pickup_data={},
                is_fail=True,
            )

            return self._null_pickup

        try:
            self._post()
        except Fault as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_pickup.py line: 150",
                message=str(
                    {
                        "api.error.canada_post.pickup": "Zeep Failure: {}".format(
                            e.message
                        )
                    }
                ),
            )

            CeleryEmail().pickup_issue_email.delay(
                data=self._error_world_request,
                carrier="Canada Post",
                order_number=self._order_number,
                pickup_data={},
                is_fail=True,
            )

            return self._null_pickup
        except CanadaPostAPIException as e:
            CeleryLogger().l_critical.delay(
                location="canadapost_pickup.py line: 160",
                message=str({"api.error.canada_post.pickup": e.message}),
            )

            CeleryEmail().pickup_issue_email.delay(
                data=self._error_world_request,
                carrier="Canada Post",
                order_number=self._order_number,
                pickup_data={},
                is_fail=True,
            )

            return self._null_pickup

        if self._canadapost_response["messages"] is not None:
            nbd = DateUtility().next_business_day(
                self._world_request["origin"]["country"],
                self._world_request["origin"]["province"],
                self._world_request["pickup"]["date"],
            )
            pickup_request_data = {
                "pickup_date": nbd,
                "ready_time": "12:00",
                "company_close_time": self._availability_response[
                    "pickup-availability"
                ]["on-demand-cutoff"],
            }
            self._world_request["pickup"]["date"] = nbd
            self._world_request["pickup"]["start_time"] = "12:00"

            CeleryLogger().l_info.delay(
                location="canadapost_pickup.py line: 181",
                message="CCanada Post Modified Pickup posting data: {}".format(
                    self._error_world_request
                ),
            )

            try:
                self._post()
            except Fault as e:
                CeleryLogger().l_critical.delay(
                    location="canadapost_pickup.py line: 190",
                    message=str(
                        {
                            "api.error.canada_post.Pickup": "Zeep Failure: {}".format(
                                e.message
                            )
                        }
                    ),
                )

                CeleryEmail().pickup_issue_email.delay(
                    data=self._error_world_request,
                    carrier="Canada Post",
                    order_number=self._order_number,
                    pickup_data={},
                    is_fail=True,
                )

                return self._null_pickup
            except CanadaPostAPIException as e:
                CeleryLogger().l_critical.delay(
                    location="canadapost_pickup.py line: 198",
                    message=str({"api.error.canada_post.Pickup": e.message}),
                )

                CeleryEmail().pickup_issue_email.delay(
                    data=self._error_world_request,
                    carrier="Canada Post",
                    order_number=self._order_number,
                    pickup_data={},
                    is_fail=True,
                )

                return self._null_pickup

            if self._canadapost_response["messages"] is not None:
                messages = [
                    "Canada Post Errcode: {} - {}".format(
                        message["code"], str(message["description"])
                    )
                    for message in self._canadapost_response["messages"]["message"]
                ]

                CeleryLogger().l_critical.delay(
                    location="canadapost_pickup.py line: 212",
                    message=str(
                        {"api.error.canada_post.Pickup": PickupException(messages)}
                    ),
                )

                CeleryEmail().pickup_issue_email.delay(
                    data=self._error_world_request,
                    carrier="Canada Post",
                    order_number=self._order_number,
                    pickup_data={},
                    is_fail=True,
                )

                return self._null_pickup

            CeleryEmail().pickup_issue_email.delay(
                data=self._error_world_request,
                carrier="Canada Post",
                order_number=self._order_number,
                pickup_data=pickup_request_data,
                is_fail=False,
            )

        self._format_response()

        return self.world_response

    def is_pickup_available(self):
        try:
            self._clean()
        except PickupException as e:
            CeleryLogger().l_warning.delay(
                location="canadapost_pickup.py line: 238",
                message="CP Failure: {}".format(e.message),
            )
            return False

        try:
            self._get_pickup_availability()
        except Fault as e:
            CeleryLogger().l_warning.delay(
                location="canadapost_pickup.py line: 247",
                message="Zeep Failure: {}".format(e.message),
            )
            return False

        if self._availability_response["messages"] is None:
            if not self._availability_response["pickup-availability"]["on-demand-tour"]:
                return False
        else:
            CeleryLogger().l_warning.delay(
                location="canadapost_pickup.py line: 257",
                message="Error message obtained from checking pickup availability: {}".format(
                    self._availability_response
                ),
            )

            return False
        return True

    # Override
    def _format_response(self) -> None:
        response = self._canadapost_response["pickup-request-info"]
        pickup_price = response["pickup-request-price"]
        pickup_message = "(Canada Post) Pickup Failed."
        pickup_status = "Failed"

        if response["pickup-request-header"]["request-id"]:
            pickup_message = "Booked"
            pickup_status = "Success"

        self.world_response = {
            "pickup_id": response["pickup-request-header"]["request-id"],
            "pickup_message": pickup_message,
            "pickup_status": pickup_status,
            "subtotal": pickup_price["pre-tax-amount"],
            "total": pickup_price["due-amount"],
            "tax": Decimal("0.00"),
        }

        for tax_field in {"gst-amount", "pst-amount", "hst-amount"}:
            self.world_response["tax"] += (
                pickup_price[tax_field] if pickup_price[tax_field] else Decimal("0.00")
            )

    # Override
    def _post(self) -> None:
        self._canadapost_response = (
            self.endpoints.REQUEST_PICKUP_SERVICE.CreatePickupRequest(
                **{
                    "customer-number": self.carrier_account.account_number.decrypt(),
                    "pickup-request-details": PickupRequestDetails(
                        self._world_request
                    ).data(),
                }
            )
        )
