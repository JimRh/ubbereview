import copy
from decimal import Decimal

from django.db import connection
from gevent import Greenlet

from api.apis.exchange_rate.exchange_rate import ExchangeRateUtility
from api.exceptions.project import ShipException
from api.models import Shipment
from api.utilities.carriers import CarrierUtility


class ShipCommon:
    """
        ubbe Multi Model Shipping - Determines what mode to ship. IE: Ground, Air, or Sealift
    """

    _air = "AI"
    _sealift = "SE"

    _hundred = Decimal("100.00")
    _one = Decimal("1.00")

    def __init__(self, gobox_request: dict) -> None:
        self._gobox_request = copy.deepcopy(gobox_request)
        self._base = copy.deepcopy(gobox_request)
        self._appointment_delivery = 1
        self._service = self._base.pop("service")

        self._user = self._gobox_request["objects"]["user"]
        self._sub_account = self._gobox_request["objects"]["sub_account"]

        self._main_carrier = None
        self._pickup_carrier = None
        self._delivery_carrier = None
        self._mid_origin = None
        self._mid_destination = None
        self._pickup_request = {}
        self._main_request = {}
        self._delivery_request = {}
        self._dg_main = None
        self._response = {}

    @staticmethod
    def _apply_markup_to_rate(rate: dict, multiplier: Decimal) -> None:
        """
            Apply markup to rate
            :param rate: Rate dict
            :param multiplier: Decimal markup multiplier
        """
        sig_fig = Decimal("0.01")
        rate['un_total'] = rate['total']
        rate['un_freight'] = rate['freight']
        rate['un_taxes'] = rate['taxes']

        rate['total'] = (Decimal(rate['total']) * multiplier).quantize(sig_fig)
        rate['freight'] = (Decimal(rate['freight']) * multiplier).quantize(sig_fig)
        rate['taxes'] = (Decimal(rate['taxes']) * multiplier).quantize(sig_fig)

    @staticmethod
    def _create_greenlets(order_number: str, request: dict):
        request["order_number"] = order_number
        instance = CarrierUtility.get_ship_api(request)
        greenlet = Greenlet.spawn(instance.ship, order_number=order_number)

        return greenlet

    @staticmethod
    def _update_address(address: dict, info: dict):
        address['email'] = info['email']
        address['company_name'] = info['company_name']
        address['name'] = info['name']
        address['phone'] = info['phone']

    @staticmethod
    def update_packages(shipment: Shipment, request_data: dict):
        try:
            for i, package in enumerate(shipment.package_shipment.all()):
                request_data["packages"][i]["package_account_id"] = package.package_account_id
        except Exception:
            pass

    def _get_exchange_rate(self):
        
        exchange_rate = ExchangeRateUtility(
            source_currency="CAD", target_currency=self._sub_account.currency_code
        ).get_exchange_rate()

        return exchange_rate

    def _get_data_from_greenlet(self, leg, greenlet, markup):

        try:
            data = greenlet.get()
        except ShipException as e:
            connection.close()
            raise ShipException(e.message)

        multiplier = self._get_multiplier(markup=markup.default_percentage, c_markup=leg.markup)
        self._apply_markup_to_rate(data, multiplier)

        return data

    def _get_multiplier(self, markup: Decimal, c_markup: Decimal):
        return (markup / self._hundred) + (c_markup / self._hundred) + self._one

    def _setup_address(self, address: dict, key: str):
        """

            :param address:
            :param key:
            :return:
        """
        address['email'] = self._base[key]['email']
        address['company_name'] = self._base[key]['company_name']
        address['name'] = self._base[key]['name']
        address['phone'] = self._base[key]['phone']
