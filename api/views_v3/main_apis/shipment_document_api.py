"""
    Title: Shipment Document Api views
    Description: This file will contain all functions for Document Api views
    Created: Nov 08, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files.storage import default_storage
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import RetrieveUpdateDestroyAPIView

from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import ShipmentDocument
from api.serializers_v3.common.shipment_document_serializer import ShipmentDocumentSerializer, \
    CreateShipmentDocumentSerializer, UpdateShipmentDocumentSerializer
from api.utilities.utilities import Utility


class ShipmentDocumentApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'post']

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """

        if self._sub_account.is_bbe:
            document = ShipmentDocument.objects.filter(
                shipment__shipment_id=self.request.query_params.get("shipment_id", "")
            )
        else:
            document = ShipmentDocument.objects.filter(
                shipment__shipment_id=self.request.query_params.get("shipment_id", ""),
                shipment__subaccount=self._sub_account,
                type__in=["0", "1", "2", "3", "5", "6", "7", "8"]
            )
        return document

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'shipment_id', openapi.IN_QUERY, description="Shipment Id", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'document_type',
                openapi.IN_QUERY,
                description="Type of document",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_id='Get Document',
        operation_description='Get a document for a shipment.',
        responses={
            '200': openapi.Response('Get Document', ShipmentDocumentSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipment documents for the system based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'shipment_id' not in self.request.query_params:
            errors.append({"Shipment Documents": "Missing 'shipment_id' parameter."})
            return Utility.json_error_response(
                code="2200", message="Shipment Documents: Missing 'shipment_id' parameter.", errors=errors
            )
        shipment_document = self.get_queryset()
        shipment_document = self.filter_queryset(queryset=shipment_document)
        serializer = ShipmentDocumentSerializer(shipment_document, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=ShipmentDocumentSerializer,
        operation_id='Create a new Shipment Document',
        operation_description='Create a Document for a shipment.',
        responses={
            '200': openapi.Response('Create Promo Code', ShipmentDocumentSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new Document.
            :param request: request
            :return: Json of Document.
        """
        errors = []
        json_data = request.data
        serializer = CreateShipmentDocumentSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1301", message="Document: Invalid values.", errors=serializer.errors
            )

        serializer.validated_data["sub_account"] = self._sub_account

        try:
           serializer.instance = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1302", message="Document: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        response_serializer = ShipmentDocumentSerializer(serializer.instance, many=False)

        return Utility.json_response(data=response_serializer.data)


class ShipmentDocumentDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self) -> ShipmentDocument:
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """

        if self._sub_account.is_bbe:
            document = ShipmentDocument.objects.get(pk=self.kwargs["pk"])
        else:
            document = ShipmentDocument.objects.get(
                pk=self.kwargs["pk"],
                shipment__subaccount=self._sub_account,
                type__in=["0", "1", "2", "3", "5", "6", "7", "8"]
            )
        return document

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'shipment_id', openapi.IN_QUERY, description="Shipment Id", type=openapi.TYPE_STRING, required=True
            ),
            openapi.Parameter(
                'document_type',
                openapi.IN_QUERY,
                description="Type of document",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        operation_id='Get Document',
        operation_description='Get a document for a shipment.',
        responses={
            '200': openapi.Response('Get Document', ShipmentDocumentSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get shipment packages for a shipment or individual package based on the allowed parameters and determine.
            :return:
        """
        errors = []

        try:
            document = self.get_queryset()
        except ObjectDoesNotExist:
            errors.append({"document": f'\'pk\' {self.kwargs["pk"]} not found or you do not have permission.'})
            return Utility.json_error_response(code="1300", message="Document: No document found.", errors=errors)

        serializer = ShipmentDocumentSerializer(document, many=False)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Add Document',
        operation_description='Add a document to a shipment.',
        request_body=CreateShipmentDocumentSerializer,
        responses={
            '200': openapi.Response('Add Document', ShipmentDocumentSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update
            :param request: request
            :return: Json list of accounts.
        """
        errors = []
        json_data = request.data
        serializer = UpdateShipmentDocumentSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1303", message="Document: Invalid values.", errors=serializer.errors
            )

        try:
            document = self.get_queryset()
        except ObjectDoesNotExist:
            errors.append({"document": f'\'pk\' {self.kwargs["pk"]} not found or you do not have permission.'})
            return Utility.json_error_response(code="1304", message="Document: Not Found.", errors=errors)

        try:
            serializer.instance = serializer.update(instance=document, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1305", message="Document: failed to update.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        response_serializer = ShipmentDocumentSerializer(serializer.instance, many=False)

        return Utility.json_response(data=response_serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Document',
        operation_description='Delete an document for a shipment.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Get shipment document and the local stored file.
            :param request: request
            :return: Success Message.
        """
        errors = []

        try:
            document = self.get_queryset()
        except ObjectDoesNotExist:
            errors.append({"document": f' \'pk\' {self.kwargs["pk"]} not found or you do not have permission.'})
            return Utility.json_error_response(code="1307", message="Document: Not Found.", errors=errors)

        path = copy.deepcopy(document.document.path)
        document.delete()
        default_storage.delete(path)

        return Utility.json_response(data={"shipment_id": self.kwargs["pk"], "message": "Successfully Deleted"})
