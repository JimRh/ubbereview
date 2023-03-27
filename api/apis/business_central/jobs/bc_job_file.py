"""
    Title: Business Central Jobs File
    Description: This file will contain all functions to create a Business Central Job file.
    Created: April 12, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import datetime

from django.db import connection
from django.utils import timezone

from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.jobs.bc_job_base import BCJobBase


class BCJobFile(BCJobBase):
    """
        Build First stage of Business Central

        Fields:

            - Mandatory:
                - CustomerNo : Customer Number, ex: J00001
                - type: Either: Billable (1), Tracking (2), Quoting(3), default (1)

                - filedByExpediting: Hard Coded: False
                - closedByAccounting: Hard Coded: False

                - directiveCategory : FF (1), Supply Chain (2), Ishop(3), Cargo (4), Project Staffing (5),
                                      Distribution (6)).
                - shipmentDirection: North (1), South (2), Other (3)
                - shipmentType: Domestic (1), International (2), United States(3), default (1)
                - shipmentReadyDate - Shipment Ready date for pickup

                - createdBy - Who created the File.
                - fileOwner - Current Owner of the File.
                - portalVisible: Show in the FLMS portal
            - Optional:

                - pODSignedByName: Individual who signed for shipment
                - shipmentDueDate: Estimated delivery date.
                - actualDeliverdDateTime: When the shipment was delivered

                - quoteRequested: Hard Coded: True
                - quoteStatus: Hard Coded: 5 - Client - Quote Accepted
                - consolidatedToFileNo: None
                - numberOfConsolidatedFiles: None
                - useSummeryForBilling: False ?

                - invoicePostedDate: Won't have
                - invoiceCreatedDate: Wont't have
                - invoiceNumber: Won't have

                - salesOrderStatus: ?
                - salesOrderStatusDate: ?
    """

    _shipment_type = {
        "domestic": 1,
        "international": 2,
        "us": 3
    }

    _north = 1
    _south = 2
    _other = 3

    _file_type = {
        "billable": 1,
        "tracking": 2,
        "quoting": 3
    }

    # Actual Fields
    #
    # Hard Coded Values
    _type_quoting = 3
    _closed_by_accounting = False
    _filed_by_expediting = False

    def __init__(self, ubbe_data: dict, shipment):
        super().__init__(ubbe_data=ubbe_data, shipment=shipment)
        self.create_bc_connection()
        self._request = {}

    def _determine_shipment_type_routing(self) -> None:
        """
            Determine Shipment Type for shipment routing.
        """
        o_province = self._shipment.origin.province
        o_country_code = o_province.country.code
        d_province = self._shipment.destination.province
        d_country_code = d_province.country.code

        # Determine Shipment Type
        if o_country_code == "US" and d_country_code == "CA":
            shipment_type = "us"
        elif o_country_code == "CA" and d_country_code == "US":
            shipment_type = "us"
        elif o_country_code == "US" and d_country_code == "US":
            shipment_type = "us"
        elif o_country_code != d_country_code:
            shipment_type = "international"
        else:
            shipment_type = "domestic"

        # Determine Shipment Routing
        if o_province in ["NT", "YT", "NU"] and d_province not in ["NT", "YT", "NU"]:
            shipment_direction = self._south
        elif d_province in ["NT", "YT", "NU"] and o_province not in ["NT", "YT", "NU"]:
            shipment_direction = self._north
        else:
            shipment_direction = self._other

        self._request["ShipmentType"] = self._shipment_type[shipment_type]
        self._request["ShipmentDirection"] = shipment_direction

    def _determine_file_type(self) -> None:
        """
            Determine File Type for shipment Billable (1), Tracking (2), Quoting(3), default (1).
        """

        file_type = self._ubbe_data.get("file_type", "billable")

        self._request["Type"] = self._file_type[file_type]

    def _get_origin(self) -> dict:
        """
            Format origin dictionary.
        """
        province = self._shipment.origin.province

        return {
            'ShipmentOriginCompanyName': self._shipment.sender.company_name,
            'ShipmentOriginAddress': self._shipment.origin.address,
            'ShipmentOriginAddress2': self._shipment.origin.address_two,
            'ShipmentOriginCity': self._shipment.origin.city,
            'ShipmentOriginZipCode': self._shipment.origin.postal_code,
            'ShipmentOriginState': province.code,
            'ShipmentOriginCountryRegionCode': province.country.code,
            'ShipmentOriginContactName': self._shipment.sender.name,
            'ShipmentOriginContactPhoneNo': self._shipment.sender.phone,
            'ShipmentOriginContactEMail': self._shipment.sender.email,
            'ShipmentOriginContactFaxNo': "",
        }

    def _get_destination(self) -> dict:
        """
            Format destination dictionary.
        """
        province = self._shipment.destination.province

        return {
            'EndDestinationConsigneeCompanyName': self._shipment.receiver.company_name,
            'EndDestinationConsigneeAddress': self._shipment.destination.address,
            'EndDestinationConsigneeAddress2': self._shipment.destination.address_two,
            'EndDestinationConsigneeCity': self._shipment.destination.city,
            'EndDestinationConsigneeZipCode': self._shipment.destination.postal_code,
            'EndDestinationConsigneeState': province.code,
            'EndDestinationConsigneeCountryRegionCode': province.country.code,
            'EndDestinationConsigneeContactName': self._shipment.receiver.name,
            'EndDestinationConsigneeContactPhoneNo': self._shipment.receiver.phone,
            'EndDestinationConsigneeContactEMail': self._shipment.receiver.email,
            'EndDestinationConsigneeContactFaxNo': "",
        }

    def _determine_customer(self) -> str:
        """
            Get correct BC Customer Number for shipment. Check user specifically otherwise default to subaccount
            setting or the passed in BC Customer number.
            :return: BC Customer Number str
        """

        if self._shipment.username == "kbxekati@dcl360.com":
            return "ACDC"
        elif self._shipment.username == "kbxsabina@dcl360.com":
            return "KBXSABGOL"
        elif self._shipment.username == "kbxhopebay@dcl360.com":
            return "TMAC"

        return self._ubbe_data["bc_customer"]

    def _build(self, is_account: False) -> None:
        """
            Build request data for freight forwarding file.
        """
        default_date = datetime.datetime(year=1, month=1, day=1).isoformat()

        self._determine_shipment_type_routing()
        self._determine_file_type()

        if self._shipment.requested_pickup_time.isoformat() == default_date:
            ready_date = datetime.datetime.now(tz=timezone.utc)
        else:
            ready_date = self._shipment.requested_pickup_time

        if self._shipment.estimated_delivery_date.isoformat() == default_date:
            est_date = datetime.datetime.now(tz=timezone.utc) + datetime.timedelta(days=7)
        else:
            est_date = self._shipment.estimated_delivery_date

        # Mandatory Fields
        self._request.update({
            "FunctionName": "CreateJob",
            "CustomerNo": self._determine_customer(),
            "FiledByExpediting": self._filed_by_expediting,
            "ClosedByAccounting": self._closed_by_accounting,
            "SeasonType": "NORMAL CONDITIONS",
            "ShipmentReadyDate": ready_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "ShipmentDueDate": est_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "CreatedBy": self._ubbe_data["bc_username"],
            "FileOwner": self._ubbe_data["bc_username"],
            'BillToCustReference1': self._ubbe_data["bc_customer_reference_one"],
            'BillToCustReference2': self._ubbe_data["bc_customer_reference_two"],
            'BillToCustReference3': self._ubbe_data["bc_customer_reference_three"],
            'BillToCustReference4': self._shipment.origin.city + " To " + self._shipment.destination.city,
            'BillToCustReference5': self._shipment.shipment_id,
        })

        self._request.update(self._get_origin())
        self._request.update(self._get_destination())

        # Optional Fields?
        self._request.update({
            'UseSummeryForBilling': False,
            'QuoteRequested': False,
            # 'QuoteStatus': 5,
            'SalesOrderStatus': 2,
        })

        if is_account:
            date = datetime.datetime.now()
            self._request["JobDescription"] = f"ubbe {date.strftime('%b')} - {self._shipment.subaccount.account_name}"
            self._request["RequestedByCompanyName"] = self._shipment.subaccount.contact.company_name
            self._request["RequestedByContactName"] = self._shipment.username
            self._request["RequestedByEMail"] = self._shipment.email
            self._request["RequestedByPhoneNo"] = self._shipment.subaccount.contact.phone
            self._request["RequestedByAddress"] = self._shipment.subaccount.address.address
            self._request["RequestedByCity"] = self._shipment.subaccount.address.city
            self._request["RequestedByProvinceState"] = self._shipment.subaccount.address.province.code
            self._request["RequestedByCountryRegionCode"] = self._shipment.subaccount.address.province.country.code
            self._request["RequestedByZIPCode"] = self._shipment.subaccount.address.postal_code

        if self._shipment.billing and self._shipment.payer:
            self._request.update({
                'RequestedByCompanyName': self._shipment.payer.company_name,
                'RequestedByContactName': self._shipment.payer.name,
                'RequestedByEMail': self._shipment.payer.email,
                'RequestedByPhoneNo': self._shipment.payer.phone,
                'RequestedByAddress': self._shipment.billing.address,
                'RequestedByCity': self._shipment.billing.city,
                'RequestedByZIPCode': self._shipment.billing.postal_code,
                'RequestedByProvinceState': self._shipment.billing.province.code,
                'RequestedByCountryRegionCode': self._shipment.billing.province.country.code,
                'BillToAddress': self._shipment.billing.address,
                'BillToCity': self._shipment.billing.city,
                'BillToZIPCode': self._shipment.billing.postal_code,
                'BillToState': self._shipment.billing.province.code,
                'BillToCountryRegionCode': self._shipment.billing.province.country.code,
                'BillToCompanyName': self._shipment.payer.company_name,
                'BillToContactName': self._shipment.payer.name,
                'BillToEMail': self._shipment.payer.email,
                'BillToPhoneNo': self._shipment.payer.phone,
            })

    def create_file(self, is_account: bool = False) -> dict:
        """
            Create new Job File.
            :return: Dictionary with FF File number
        """

        # Build request data to Business Central
        try:
            self._build(is_account=is_account)
        except BusinessCentralError as e:
            connection.close()
            raise BusinessCentralError(message="Build Create Failed", data=e.message)

        # Post Data to Business Central
        try:
            response = self._post(request=self._request)
        except BusinessCentralError as e:
            connection.close()
            raise BusinessCentralError(message="File Creation Failed", data=e.message)

        return response
