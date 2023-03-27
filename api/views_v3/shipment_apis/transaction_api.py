"""
    Title: Shipment Transaction Api
    Description: This file will contain all functions for Transaction apis.
    Created: June 11, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import copy

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView

from api.background_tasks.business_central import CeleryBusinessCentral
from api.background_tasks.emails import CeleryEmail
from api.documents.receipt_document import PaymentDocuments
from api.exceptions.project import ViewException
from api.mixins.view_mixins import UbbeMixin
from api.models import Transaction, ShipmentDocument
from api.serializers_v3.private.shipments.transaction_serializers import PrivateTransactionSerializer
from api.utilities.utilities import Utility
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class TransactionApi(UbbeMixin, ListCreateAPIView):
    http_method_names = ['get', 'post']
    filter_backends = [filters.SearchFilter]
    search_fields = ['shipment__shipment_id', 'transaction_id', 'complete', 'card_type', "code", "message"]

    # Customs
    _cache_lookup_key = "transaction"

    def get_queryset(self):
        """
            Get initial transaction queryset and apply query params to the queryset.
            :return:
        """

        transactions = cache.get(self._cache_lookup_key)

        if not transactions:
            transactions = Transaction.objects.all().order_by("shipment_id", "-transaction_date")

            # Store metrics for 5 hours
            cache.set(self._cache_lookup_key, transactions, TWENTY_FOUR_HOURS_CACHE_TTL)

        if "shipment_id" in self.request.query_params:
            transactions = transactions.filter(shipment__shipment_id=self.request.query_params["shipment_id"])

        return transactions

    @swagger_auto_schema(
        operation_id='Get Transactions',
        operation_description='Get a list of transactions for shipments.',
        manual_parameters=[
            openapi.Parameter(
                'shipment_id', openapi.IN_QUERY, description="Shipment ID", type=openapi.TYPE_STRING
            ),
        ],
        responses={
            '200': openapi.Response('Get Transactions', PrivateTransactionSerializer(many=True)),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get transaction a carrier based on the allowed parameters and search params.
            :return:
        """

        transaction = self.get_queryset()
        transaction = self.filter_queryset(queryset=transaction)
        serializer = PrivateTransactionSerializer(transaction, many=True)

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        request_body=PrivateTransactionSerializer,
        operation_id='Create Transaction',
        operation_description='Create a transaction for a shipment.',
        responses={
            '200': openapi.Response('Create Transaction', PrivateTransactionSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def post(self, request, *args, **kwargs):
        """
            Create a transaction.
            :param request: request
            :return: transaction json.
        """
        errors = []
        json_data = request.data
        serializer = PrivateTransactionSerializer(data=json_data, many=False)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="5900", message="Transaction: Invalid values.", errors=serializer.errors
            )

        try:
            transaction = serializer.create(validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="5901", message="Transaction: Failed to save.", errors=errors)
        except ViewException as e:
            errors.append({"transaction": e.message})
            return Utility.json_error_response(code="5902", message="Transaction: Failed to save.", errors=errors)

        serializer.instance = transaction
        data = serializer.data
        data["transaction_date_doc"] = transaction.transaction_date.strftime("%b %d %Y %H:%M %p")

        cache.delete(self._cache_lookup_key)

        doc = PaymentDocuments().generate_receipt(data=data)

        if transaction.shipment.ff_number != "":
            copied = copy.deepcopy(data)
            copied["is_transaction"] = True
            CeleryBusinessCentral().add_job_note.delay(data=copied)
            copied["doc"] = doc
            copied["file_name"] = f"{transaction.shipment.shipment_id}_receipt.pdf"
            CeleryBusinessCentral().add_job_attachment.delay(data=copied)
            ShipmentDocument.add_document(shipment=transaction.shipment, document=doc, doc_type="0")

        email_data = copy.deepcopy(data)

        if transaction.shipment.payer:
            email_data["email"] = transaction.shipment.payer.email
        else:
            email_data["email"] = transaction.shipment.email

        CeleryEmail.receipt_email.delay(data=email_data, file=doc)

        return Utility.json_response(data=data)


class TransactionDetailApi(UbbeMixin, RetrieveUpdateDestroyAPIView):
    http_method_names = ['get', 'put', 'delete']

    # Customs
    _cache_lookup_key = "transaction"
    _cache_lookup_key_individual = "transaction_"

    def get_object(self):
        """
            Returns the object the view is displaying.
        """
        errors = []

        try:
            obj = Transaction.objects.get(pk=self.kwargs["pk"])
        except ObjectDoesNotExist:
            errors.append({"transaction": f'{self.kwargs["pk"]} not found or you do not have permission.'})
            raise ViewException(code="5903", message="Transaction: Not Found.", errors=errors)

        return obj

    @swagger_auto_schema(
        operation_id='Get Transaction',
        operation_description='Get a transaction for a shipment.',
        responses={
            '200': openapi.Response('Get Transaction', PrivateTransactionSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def get(self, request, *args, **kwargs):
        """
            Get transaction information.
            :return: Json of transaction.
        """

        lookup_key = f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}'
        cached_transaction = cache.get(lookup_key)

        if not cached_transaction:

            try:
                transaction = self.get_object()
            except ViewException as e:
                return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

            serializer = PrivateTransactionSerializer(instance=transaction, many=False)
            cached_transaction = serializer.data

            # Store metrics for 5 hours
            cache.set(lookup_key, cached_transaction, TWENTY_FOUR_HOURS_CACHE_TTL)

        return Utility.json_response(data=cached_transaction)

    @swagger_auto_schema(
        request_body=PrivateTransactionSerializer,
        operation_id='Update Transaction',
        operation_description='Update a transaction for a shipment.',
        responses={
            '200': openapi.Response('Update Transaction', PrivateTransactionSerializer),
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def put(self, request, *args, **kwargs):
        """
            Update transaction information
            :param request: request
            :return: Json of transaction.
        """
        errors = []
        json_data = request.data
        serializer = PrivateTransactionSerializer(data=json_data, many=False, partial=True)

        if not serializer.is_valid():
            return Utility.json_error_response(
                code="5904", message="Transaction: Invalid values.", errors=serializer.errors
            )

        try:
            transaction = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        try:
            transaction = serializer.update(instance=transaction, validated_data=serializer.validated_data)
        except ValidationError as e:
            errors.extend([{x: y} for x, y in e.message_dict.items()])
            return Utility.json_error_response(code="5906", message="Transaction: Failed to update.", errors=errors)
        except ViewException as e:
            errors.append({"transaction": e.message})
            return Utility.json_error_response(code="5907", message="Transaction: Failed to update.", errors=errors)

        serializer.instance = transaction
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data=serializer.data)

    @swagger_auto_schema(
        operation_id='Delete Transaction',
        operation_description='Delete an transaction for a shipment.',
        responses={
            '200': "Successfully Deleted",
            '400': "Bad Request",
            '500': "Internal Server Error"
        },
    )
    def delete(self, request, *args, **kwargs):
        """
            Delete shipment transaction from the system.
            :param request: request
            :return: Success Message.
        """

        try:
            transaction = self.get_object()
        except ViewException as e:
            return Utility.json_error_response(code=e.code, message=e.message, errors=e.errors)

        transaction.delete()
        cache.delete(self._cache_lookup_key)
        cache.delete(f'{self._cache_lookup_key_individual}{self.kwargs["pk"]}')

        return Utility.json_response(data={"transaction": self.kwargs["pk"], "message": "Successfully Deleted"})
