"""
    Title: Document Api views
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
from api.models import ShipDocument
from api.serializers_v3.common.document_serializer import DocumentSerializer, CreateDocumentSerializer, \
    DeleteDocumentSerializer, UpdateDocumentSerializer
from api.utilities.utilities import Utility


class LegDocumentApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'post']

    def get_queryset(self):
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """

        if self._sub_account.is_bbe:
            document = ShipDocument.objects.filter(
                leg__leg_id=self.request.query_params.get("leg_id", ""),

            )
        else:
            document = ShipDocument.objects.filter(
                leg__leg_id=self.request.query_params.get("leg_id", ""),
                leg__shipment__subaccount=self._sub_account,
                new_type__in=["0", "1", "2", "3", "4", "7"]
            )
        return document

    @swagger_auto_schema(
        operation_id='Get Document',
        operation_description='Get a document for a Leg.',
        responses={
            '200': openapi.Response('Get Document', DocumentSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get leg documents for the system based on the allowed parameters and search params.
            :return:
        """
        errors = []

        if 'leg_id' not in self.request.query_params:
            errors.append({"Leg Documents": "Missing 'leg_id' parameter."})
            return Utility.json_error_response(
                code="2200", message="Leg Documents: Missing 'leg_id' parameter.", errors=errors
            )

        leg_document = self.get_queryset()
        leg_document = self.filter_queryset(queryset=leg_document)
        serializer = DocumentSerializer(leg_document, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Add Document',
        operation_description='Add a document for to a leg.',
        request_body=CreateDocumentSerializer,
        responses={
            '200': openapi.Response('Add Document', DocumentSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a new document.
            :param request: request
            :return: Json of Webhook.
        """
        errors = []
        json_data = request.data
        serializer = CreateDocumentSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="1301", message="Document: Invalid values.", errors=serializer.errors
            )

        serializer.validated_data["sub_account"] = self._sub_account

        try:
            instance = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="1302", message="Document: failed to save.", errors=errors)
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        response_serializer = DocumentSerializer(instance, many=False)

        return Utility.json_response(data=response_serializer.data)


class LegDocumentDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    def get_queryset(self) -> ShipDocument:
        """
            Get initial shipment queryset and apply query params to the queryset.
            :return:
        """

        if self._sub_account.is_bbe:
            document = ShipDocument.objects.get(pk=self.kwargs["pk"])
        else:
            document = ShipDocument.objects.get(pk=self.kwargs["pk"], leg__shipment__subaccount=self._sub_account)
        return document

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'leg_id', openapi.IN_QUERY, description="Leg Id", type=openapi.TYPE_STRING, required=True
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
        operation_description='Get a document for a leg.',
        responses={
            '200': openapi.Response('Get Document', DocumentSerializer(many=True)),
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

        serializer = DocumentSerializer(document, many=False)
        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Update Document',
        operation_description='Update a document for a leg.',
        request_body=CreateDocumentSerializer,
        responses={
            '200': openapi.Response('Update Document', DocumentSerializer),
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
        serializer = UpdateDocumentSerializer(data=json_data, many=False)

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

        response_serializer = DocumentSerializer(serializer.instance, many=False)

        return Utility.json_response(data=response_serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Document',
        operation_description='Delete an document for a leg.',
        request_body=DeleteDocumentSerializer,
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

        return Utility.json_response(data={"leg_id": self.kwargs["pk"], "message": "Successfully Deleted"})
