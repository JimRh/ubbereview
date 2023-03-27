"""
    Title: YRC Rate Unit Tests
    Description: Unit Tests for the YRC Rate. Test Everything.
    Created: January 18, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from lxml import etree

from api.apis.carriers.yrc.endpoints.yrc_pickup import YRCPickup
from api.apis.carriers.yrc.endpoints.yrc_rate import YRCRate
from api.apis.carriers.yrc.endpoints.yrc_track import YRCTrack
from api.exceptions.project import TrackException
from api.globals.carriers import YRC
from api.models import SubAccount, Carrier, CarrierAccount


class YRCRateTests(TestCase):
    fixtures = [
        "api",
        "carriers",
        "countries",
        "provinces",
        "addresses",
        "contact",
        "user",
        "group",
        "markup",
        "carrier_markups",
        "account",
        "subaccount",
        "encryted_messages",
        "carrier_account",
        "northern_pd",
        "skyline_account",
        "nature_of_goods",
    ]

    def setUp(self):
        self.request = {
            "address": "1540 Airport Road",
            "city": "Edmonton International Airport",
            "company_name": "BBE Ottawa",
            "email": "developer@bbex.com",
            "phone": "7809326245",
            "name": "BBE",
            "country": "CA",
            "postal_code": "T9E0V6",
            "province": "AB",
        }

        self.response_one = '<?xml version="1.0" encoding="UTF-8"?><SHIPMENTS><SHIPMENT><returnCode>00</returnCode><returnMessage>SUCCESS</returnMessage><freightBillNumber>6340448636</freightBillNumber><referenceNumber></referenceNumber><originCity>WINFIELD</originCity><originState>AL</originState><originZip>35594</originZip><destinationCity>EDMONTON</destinationCity><destinationState>AB</destinationState><destinationZip>T9E1A1</destinationZip><pickupDate>12/13/2021</pickupDate><deliveredDate>01/04/2022</deliveredDate><deliveredTime>09:49</deliveredTime><tenderCode>ENTRY INFORMATION ACCEPTED, WAITING ARRIVAL OF GOODS.</tenderCode><currentStatusCode>DELIVERED</currentStatusCode><currentStatusDate>01/04/2022</currentStatusDate><currentStatusMessage>DELIVERY DATE: 01/04/2022</currentStatusMessage><estimatedDeliveryDate>01/04/2022</estimatedDeliveryDate></SHIPMENT></SHIPMENTS>'
        self.response_two = '<?xml version="1.0" encoding="UTF-8"?><SHIPMENTS><SHIPMENT><returnCode>00</returnCode><returnMessage>SUCCESS</returnMessage><freightBillNumber>6481297670</freightBillNumber><referenceNumber></referenceNumber><originCity>EDMONTON</originCity><originState>AB</originState><originZip>T9E0V6</originZip><destinationCity>MIAMI</destinationCity><destinationState>FL</destinationState><destinationZip>33196</destinationZip><pickupDate>01/18/2022</pickupDate><deliveredDate></deliveredDate><deliveredTime></deliveredTime><tenderCode>ENTRY</tenderCode><currentStatusCode>ONH</currentStatusCode><currentStatusDate>01/21/2022</currentStatusDate><currentStatusMessage>Now at WINNIPEG MB CAN</currentStatusMessage><estimatedDeliveryDate>01/25/2022</estimatedDeliveryDate></SHIPMENT></SHIPMENTS>'
        self.response_three = '<?xml version="1.0" encoding="UTF-8"?><SHIPMENTS><SHIPMENT><returnCode>00</returnCode><returnMessage>SUCCESS</returnMessage><freightBillNumber>6481297670</freightBillNumber><referenceNumber></referenceNumber><originCity>EDMONTON</originCity><originState>AB</originState><originZip>T9E0V6</originZip><destinationCity>MIAMI</destinationCity><destinationState>FL</destinationState><destinationZip>33196</destinationZip><pickupDate>01/18/2022</pickupDate><deliveredDate></deliveredDate><deliveredTime></deliveredTime><tenderCode>INFORMATION</tenderCode><currentStatusCode>fbo</currentStatusCode><currentStatusDate>01/21/2022</currentStatusDate><currentStatusMessage>Now at WINNIPEG MB CAN</currentStatusMessage><estimatedDeliveryDate>01/25/2022</estimatedDeliveryDate></SHIPMENT></SHIPMENTS>'
        self.response_four = '<?xml version="1.0" encoding="UTF-8"?><SHIPMENTS><SHIPMENT><returnCode>00</returnCode><returnMessage>SUCCESS</returnMessage><freightBillNumber>6481297670</freightBillNumber><referenceNumber></referenceNumber><originCity>EDMONTON</originCity><originState>AB</originState><originZip>T9E0V6</originZip><destinationCity>MIAMI</destinationCity><destinationState>FL</destinationState><destinationZip>33196</destinationZip><pickupDate>01/18/2022</pickupDate><deliveredDate></deliveredDate><deliveredTime></deliveredTime><tenderCode>ACCEPTED</tenderCode><currentStatusCode>lld</currentStatusCode><currentStatusDate>01/21/2022</currentStatusDate><currentStatusMessage>Now at WINNIPEG MB CAN</currentStatusMessage><estimatedDeliveryDate>01/25/2022</estimatedDeliveryDate></SHIPMENT></SHIPMENTS>'
        self.response_five = '<?xml version="1.0" encoding="UTF-8"?><SHIPMENTS><SHIPMENT><returnCode>00</returnCode><returnMessage>SUCCESS</returnMessage><freightBillNumber>6481297670</freightBillNumber><referenceNumber></referenceNumber><originCity>EDMONTON</originCity><originState>AB</originState><originZip>T9E0V6</originZip><destinationCity>MIAMI</destinationCity><destinationState>FL</destinationState><destinationZip>33196</destinationZip><pickupDate>01/18/2022</pickupDate><deliveredDate></deliveredDate><deliveredTime></deliveredTime><tenderCode>WAITING</tenderCode><currentStatusCode>ffffffff</currentStatusCode><currentStatusDate>01/21/2022</currentStatusDate><currentStatusMessage>Now at WINNIPEG MB CAN</currentStatusMessage><estimatedDeliveryDate>01/25/2022</estimatedDeliveryDate></SHIPMENT></SHIPMENTS>'
        self.response_no_response = (
            '<?xml version="1.0" encoding="UTF-8"?><SHIPMENTS></SHIPMENTS>'
        )
        self.response_unsuccessful = '<?xml version="1.0" encoding="UTF-8"?><SHIPMENTS><SHIPMENT><returnCode>00</returnCode><returnMessage>UNSUCCESS</returnMessage><freightBillNumber>6481297670</freightBillNumber><referenceNumber></referenceNumber><originCity>EDMONTON</originCity><originState>AB</originState><originZip>T9E0V6</originZip><destinationCity>MIAMI</destinationCity><destinationState>FL</destinationState><destinationZip>33196</destinationZip><pickupDate>01/18/2022</pickupDate><deliveredDate></deliveredDate><deliveredTime></deliveredTime><tenderCode>ARRIVAL</tenderCode><currentStatusCode>ffffffff</currentStatusCode><currentStatusDate>01/21/2022</currentStatusDate><currentStatusMessage>Now at WINNIPEG MB CAN</currentStatusMessage><estimatedDeliveryDate>01/25/2022</estimatedDeliveryDate></SHIPMENT></SHIPMENTS>'

        self.response_object_one = bytes(bytearray(self.response_one, encoding="utf-8"))
        self.response_object_one = etree.XML(self.response_object_one)

        self.response_object_two = bytes(bytearray(self.response_two, encoding="utf-8"))
        self.response_object_two = etree.XML(self.response_object_two)

        self.response_object_three = bytes(
            bytearray(self.response_three, encoding="utf-8")
        )
        self.response_object_three = etree.XML(self.response_object_three)

        self.response_object_four = bytes(
            bytearray(self.response_four, encoding="utf-8")
        )
        self.response_object_four = etree.XML(self.response_object_four)

        self.response_object_five = bytes(
            bytearray(self.response_five, encoding="utf-8")
        )
        self.response_object_five = etree.XML(self.response_object_five)

        self.response_object_no_response = bytes(
            bytearray(self.response_no_response, encoding="utf-8")
        )
        self.response_object_no_response = etree.XML(self.response_object_no_response)

        self.response_object_unsuccessful = bytes(
            bytearray(self.response_unsuccessful, encoding="utf-8")
        )
        self.response_object_unsuccessful = etree.XML(self.response_object_unsuccessful)

        self._yrc_track = YRCTrack()

    def test_process_response_in_transit(self):
        """
        Test Track formatting - in transit
        """
        ret = self._yrc_track._process_response(response=self.response_object_one)
        expected = {
            "status": "Delivered",
            "details": "Entry information accepted, waiting arrival of goods. DELIVERY DATE: 01/04/2022",
            "pickup_date": "12/13/2021",
            "estimated_delivery_datetime": datetime.datetime(2022, 1, 4, 0, 0),
            "delivered_datetime": datetime.datetime(2022, 1, 4, 9, 49),
        }
        self.assertDictEqual(expected, ret)

    def test_process_response_delivered(self):
        """
        Test Track formatting - delivered
        """
        ret = self._yrc_track._process_response(response=self.response_object_two)
        expected = {
            "status": "InTransit",
            "details": "Entry Now at WINNIPEG MB CAN",
            "pickup_date": "01/18/2022",
            "estimated_delivery_datetime": datetime.datetime(2022, 1, 25, 0, 0),
        }
        self.assertDictEqual(expected, ret)

    def test_process_response_pickup(self):
        """
        Test Track formatting - pickup
        """
        ret = self._yrc_track._process_response(response=self.response_object_three)
        expected = {
            "status": "Pickup",
            "details": "Information Now at WINNIPEG MB CAN",
            "pickup_date": "01/18/2022",
            "estimated_delivery_datetime": datetime.datetime(2022, 1, 25, 0, 0),
        }
        self.assertDictEqual(expected, ret)

    def test_process_response_out_for_delivery(self):
        """
        Test Track formatting - out for delivery
        """
        ret = self._yrc_track._process_response(response=self.response_object_four)
        expected = {
            "status": "OutForDelivery",
            "details": "Accepted Now at WINNIPEG MB CAN",
            "pickup_date": "01/18/2022",
            "estimated_delivery_datetime": datetime.datetime(2022, 1, 25, 0, 0),
        }
        self.assertDictEqual(expected, ret)

    def test_process_response_created(self):
        """
        Test Track formatting - created
        """
        ret = self._yrc_track._process_response(response=self.response_object_five)
        expected = {
            "status": "Created",
            "details": "Waiting Now at WINNIPEG MB CAN",
            "pickup_date": "01/18/2022",
            "estimated_delivery_datetime": datetime.datetime(2022, 1, 25, 0, 0),
        }
        self.assertDictEqual(expected, ret)

    def test_process_response_no_response(self):
        """
        Test Track formatting - no response
        """

        with self.assertRaises(TrackException) as context:
            ret = self._yrc_track._process_response(
                response=self.response_object_no_response
            )
            self.assertEqual(
                "YRC Track (L34): No Tracking status yet.", context.exception.message
            )

    def test_process_response_unsuccessful(self):
        """
        Test Track formatting - unsuccessful
        """

        with self.assertRaises(TrackException) as context:
            ret = self._yrc_track._process_response(
                response=self.response_object_unsuccessful
            )
            self.assertEqual(
                "YRC Track (L34): Not Successful Request.", context.exception.message
            )
