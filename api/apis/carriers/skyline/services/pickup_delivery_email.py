from api.background_tasks.emails import CeleryEmail


class PickupDeliveryEmail:
    """
    Handles the creation of Pickup and Delivery emails to Cargo Planning
    """

    _gobox_request = {}
    _skyline_request = {}
    _skyline_response = {}
    _order_number = ""

    def __init__(
        self,
        gobox_request: dict,
        skyline_request: dict,
        skyline_response: dict,
        order_number: str,
    ):
        self._gobox_request = gobox_request
        self._skyline_request = skyline_request
        self._skyline_response = skyline_response
        self._order_number = order_number

    def _format_email_data(self, address: str):
        """
        Formant Email Context
        :param address: Either Sender or Recipient Address Dict
        """
        address = self._skyline_request.get(address, {})
        packages = self._skyline_request.get("Packages", [])

        return {
            "order_number": self._order_number,
            "airwaybill": self._skyline_response.get("AirWaybillNumber", ""),
            "date": self._gobox_request.get("date", ""),
            "start_time": self._gobox_request.get("start_time", ""),
            "end_time": self._gobox_request.get("end_time", ""),
            "handling_notes": self._skyline_request.get("handling_notes"),
            "city": address.get("City", "").capitalize(),
            "province": address.get("Province", ""),
            "contact": address.get("Name", ""),
            "phone": address.get("Telephone", ""),
            "address": address.get("Address", ""),
            "postal_code": address.get("PostalCode", ""),
            "pieces": [
                {
                    "width": box.get("Width", 0),
                    "length": box.get("Length", 0),
                    "height": box.get("Height", 0),
                    "weight": box.get("Weight", 0),
                    "quantity": box.get("Quantity", 0),
                    "description": box.get("Description", ""),
                }
                for box in packages
            ],
        }

    def send_pickup_notification(self):
        """
        Send pickup Email
        """
        context = self._format_email_data(address="Sender")
        context["is_pickup"] = True
        CeleryEmail().skyline_p_d_email.delay(data=context)

    def send_delivery_notification(self):
        """
        Send Delivery Email
        """
        context = self._format_email_data(address="Recipient")
        context["is_pickup"] = False
        CeleryEmail().skyline_p_d_email.delay(data=context)
