import base64

from django.db import connection

from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.jobs.bc_job_base import BCJobBase
from api.globals.project import DOCUMENT_TYPE_SHIPPING_LABEL, DOCUMENT_TYPE_BILL_OF_LADING, \
    DOCUMENT_TYPE_COMMERCIAL_INVOICE, DOCUMENT_TYPE_B13A, DOCUMENT_TYPE_DG, DOCUMENT_TYPE_NEAS, DOCUMENT_TYPE_NSSI


class BCJobAttachment(BCJobBase):
    """
            Build Business Central Job Attachment
    """

    def __init__(self, ubbe_data: dict, shipment):
        super().__init__(ubbe_data=ubbe_data, shipment=shipment)
        self._request_list = []

    @staticmethod
    def _file_type_name(file_type: int) -> str:
        """
            Determine File Type Name.
            :param file_type: int from type from document.
            :return:
        """

        if int(DOCUMENT_TYPE_SHIPPING_LABEL) == file_type:
            return "Shipping Label"
        elif int(DOCUMENT_TYPE_BILL_OF_LADING) == file_type:
            return "Bill of Lading"
        elif int(DOCUMENT_TYPE_COMMERCIAL_INVOICE) == file_type:
            return "Commercial Invoice"
        elif int(DOCUMENT_TYPE_B13A) == file_type:
            return "B13A"
        elif int(DOCUMENT_TYPE_DG) == file_type:
            return "DG Declaration"
        elif int(DOCUMENT_TYPE_NEAS) == file_type:
            return "NEAS Form"
        elif int(DOCUMENT_TYPE_NSSI) == file_type:
            return "NSSI Form"
        else:
            return "Other"

    def _create_attachment(self):
        from api.models import ShipDocument
        """
            Create attachment request per item.
            :return:
        """

        documents = ShipDocument.objects.filter(leg__shipment=self._shipment)

        for doc in documents:
            self._request_list.append(self._build_attachment(doc=doc))

    def _build_attachment(self, doc) -> dict:
        """
            Create attachment request

            Optional:
                - LegID ?

        """
        encoded_string = base64.b64encode(doc.document.open(mode='rb').read())
        doc.document.close()

        return {
            "FunctionName": "AddAttachment",
            "JobNo": self._job_number,
            "LegID": doc.leg.leg_id,
            "Filename": doc.document.name,
            "Comment": doc.leg.leg_id + ": " + self._file_type_name(file_type=int(doc.type)),
            "FileContent": encoded_string
        }

    def _build_attachment_base_64(self) -> dict:
        """
            Create attachment request
        """

        return {
            "FunctionName": "AddAttachment",
            "JobNo": self._job_number,
            "LegID":  f"{self._shipment.shipment_id}M",
            "Filename": self._ubbe_data["file_name"],
            "Comment": f"Payment receipt for {self._shipment.shipment_id}.",
            "FileContent": self._ubbe_data["doc"]
        }

    def _send_requests(self) -> list:
        """
            Send attachment requests to Business Central.
            :return:
        """
        response_list = []

        for request in self._request_list:

            try:
                response = self._post(request=request)
            except BusinessCentralError as e:
                connection.close()
                continue
            except TypeError:
                continue

            response_list.append(response)

        return response_list

    def create_attachment(self) -> list:
        """
            Add new attachments to an existing Freight Forwarding File.
            :return: Dictionary with FF File number
        """

        if not self._job_number:
            raise BusinessCentralError(message="FF Number empty", data=self._job_number)

        # Build request data to Business Central
        try:
            self._create_attachment()
        except BusinessCentralError as e:
            connection.close()
            raise BusinessCentralError(
                message="{}: Failed to build attachment requests.".format(self._job_number), data=str(e)
            )

        # Post Data to Business Central
        try:
            response = self._send_requests()
        except BusinessCentralError as e:
            connection.close()
            raise BusinessCentralError(
                message="{}: Failed to send attachment requests.".format(self._job_number), data=str(e)
            )

        return response

    def create_attachment_single(self) -> list:
        """
            Add new attachments to an existing Freight Forwarding File.
            :return: Dictionary with FF File number
        """

        if not self._job_number:
            raise BusinessCentralError(message="FF Number empty", data=self._job_number)

        # Build request data to Business Central
        try:
            requeest = self._build_attachment_base_64()
        except BusinessCentralError as e:
            connection.close()
            raise BusinessCentralError(
                message="{}: Failed to build attachment requests.".format(self._job_number), data=str(e)
            )

        self._request_list.append(requeest)

        # Post Data to Business Central
        try:
            response = self._send_requests()
        except BusinessCentralError as e:
            connection.close()
            raise BusinessCentralError(
                message="{}: Failed to send attachment requests.".format(self._job_number), data=str(e)
            )

        return response
