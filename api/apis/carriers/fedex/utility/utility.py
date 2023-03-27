from decimal import Decimal

from api.apis.carriers.fedex.globals.globals import NOTIFICATIONS, TRANSACTION_FAIL
from api.apis.carriers.fedex.soap_objects.rate.requested_package_line_item import (
    RequestedPackageLineItem,
)
from api.apis.carriers.fedex.soap_objects.common.weight import Weight


class FedexUtility:
    @staticmethod
    def successful_response(response) -> tuple:
        """
        Check if a response is successful or not
        :param response: FedEx API response
        :return: Tuple of (is successful, API messages)
        """
        return NOTIFICATIONS.get(
            response.get("HighestSeverity", -1)
        ) != TRANSACTION_FAIL, [
            {
                "Message": notification.get("Message", ""),
                "Code": notification.get("Code", ""),
                "Source": notification.get("Source", ""),
                "MessageParameters": ",".join(
                    "{}:{}".format(p.get("Id", ""), p.get("Value", ""))
                    for p in notification.get("MessageParameters", [])
                ),
            }
            for notification in response.get("Notifications", [])
        ]

    @staticmethod
    def process_packages(gobox_request: dict, sequence=None) -> tuple:
        """
        Convert packages from internal format to FedEx format
        :param sequence:
        :param gobox_request: internal request
        :return: Tuple of (total weight, package count, package structure)
        """
        packages = []
        total_weight = Decimal("0.0")
        total_quantity = 0

        if "awb" in gobox_request:
            ref_one = f'{gobox_request.get("awb", "")}/{gobox_request.get("reference_one", "")}'
        else:
            ref_one = gobox_request.get("reference_one", "")

        for group, package in enumerate(gobox_request["packages"]):
            item = RequestedPackageLineItem(
                package=package,
                group_number=group + 1,
                sequence=sequence,
                ref_one=ref_one,
                ref_two=gobox_request.get("reference_two", ""),
                order_number=gobox_request.get("order_number", ""),
            )

            total_weight += item.weight
            total_quantity += item.quantity
            packages.append(item.data)

        return Weight(weight_value=total_weight).data, total_quantity, packages
