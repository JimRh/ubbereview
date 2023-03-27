from django.test import TestCase

from api.apis.business_central.jobs.bc_job_file import BCJobFile
from api.models import Shipment


class BCJobFileTests(TestCase):

    fixtures = [
        "carriers",
        "countries",
        "provinces",
        "user",
        "group",
        "contact",
        "addresses",
        "markup",
        "account",
        "subaccount",
        "shipments",
        "legs"
    ]

    test_json = {
        "job_number": "J00123",
        "bc_customer": "ub123456780M",
        "bc_username": "Delivered",
        "bc_customer_reference_one": "2021-07-09",
        "bc_customer_reference_two": "Something",
        "bc_customer_reference_three": "Something two",
    }

    def setUp(self):
        self.job_file = BCJobFile(ubbe_data=self.test_json, shipment=Shipment.objects.last())

    def test_determine_shipment_type_routing(self):
        self.job_file._determine_shipment_type_routing()
        self.assertEqual(self.job_file._request["ShipmentType"], 1)
        self.assertEqual(self.job_file._request["ShipmentDirection"], 3)

    def test_determine_file_type(self):
        self.job_file._determine_file_type()
        self.assertEqual(self.job_file._request["Type"], 1)

    def test_get_origin(self):
        address = self.job_file._get_origin()
        expected = {'ShipmentOriginCompanyName': 'KenCar', 'ShipmentOriginAddress': '1759 35 Avenue E', 'ShipmentOriginAddress2': '', 'ShipmentOriginCity': 'Edmonton', 'ShipmentOriginZipCode': 'T9E0V6', 'ShipmentOriginState': 'AB', 'ShipmentOriginCountryRegionCode': 'CA', 'ShipmentOriginContactName': 'KenCar', 'ShipmentOriginContactPhoneNo': '7809326245', 'ShipmentOriginContactEMail': 'developer@bbex.com', 'ShipmentOriginContactFaxNo': ''}
        self.assertIsInstance(address, dict)
        self.assertEqual(address, expected)

    def test_get_destination(self):
        address = self.job_file._get_destination()
        expected = {'EndDestinationConsigneeCompanyName': 'KenCar', 'EndDestinationConsigneeAddress': '1759 35 Avenue E', 'EndDestinationConsigneeAddress2': '', 'EndDestinationConsigneeCity': 'Edmonton', 'EndDestinationConsigneeZipCode': 'T9E0V6', 'EndDestinationConsigneeState': 'AB', 'EndDestinationConsigneeCountryRegionCode': 'CA', 'EndDestinationConsigneeContactName': 'KenCar', 'EndDestinationConsigneeContactPhoneNo': '7809326245', 'EndDestinationConsigneeContactEMail': 'developer@bbex.com', 'EndDestinationConsigneeContactFaxNo': ''}
        self.assertIsInstance(address, dict)
        self.assertEqual(address, expected)

    def test_build(self):
        self.job_file._build(is_account=False)
        expected = {'ShipmentType': 1, 'ShipmentDirection': 3, 'Type': 1, 'FunctionName': 'CreateJob', 'CustomerNo': 'ub123456780M', 'FiledByExpediting': False, 'ClosedByAccounting': False, 'SeasonType': 'NORMAL CONDITIONS', 'CreatedBy': 'Delivered', 'FileOwner': 'Delivered', 'BillToCustReference1': '2021-07-09', 'BillToCustReference2': 'Something', 'BillToCustReference3': 'Something two', 'BillToCustReference4': 'Edmonton To Edmonton', 'BillToCustReference5': 'GO83058846222', 'ShipmentOriginCompanyName': 'KenCar', 'ShipmentOriginAddress': '1759 35 Avenue E', 'ShipmentOriginAddress2': '', 'ShipmentOriginCity': 'Edmonton', 'ShipmentOriginZipCode': 'T9E0V6', 'ShipmentOriginState': 'AB', 'ShipmentOriginCountryRegionCode': 'CA', 'ShipmentOriginContactName': 'KenCar', 'ShipmentOriginContactPhoneNo': '7809326245', 'ShipmentOriginContactEMail': 'developer@bbex.com', 'ShipmentOriginContactFaxNo': '', 'EndDestinationConsigneeCompanyName': 'KenCar', 'EndDestinationConsigneeAddress': '1759 35 Avenue E', 'EndDestinationConsigneeAddress2': '', 'EndDestinationConsigneeCity': 'Edmonton', 'EndDestinationConsigneeZipCode': 'T9E0V6', 'EndDestinationConsigneeState': 'AB', 'EndDestinationConsigneeCountryRegionCode': 'CA', 'EndDestinationConsigneeContactName': 'KenCar', 'EndDestinationConsigneeContactPhoneNo': '7809326245', 'EndDestinationConsigneeContactEMail': 'developer@bbex.com', 'EndDestinationConsigneeContactFaxNo': '', 'UseSummeryForBilling': False, 'QuoteRequested': False, 'SalesOrderStatus': 2}
        self.assertIsInstance(self.job_file._request, dict)

        del self.job_file._request["ShipmentReadyDate"]
        del self.job_file._request["ShipmentDueDate"]

        self.assertEqual(self.job_file._request, expected)
