"""

"""
from decimal import Decimal

from django.core.cache import cache
from django.db import connection

from api.apis.exchange_rate.exchange_rate import ExchangeRateUtility
from api.cache_lookups.carrier_service_cache import CarrierServiceCache
from api.globals.carriers import AIR_CARRIERS, SEALIFT_CARRIERS
from api.models import SubAccount
from brain.settings import TWENTY_FOUR_HOURS_CACHE_TTL


class JoinRateV2:
    _sig_fig = Decimal("0.01")
    _hundred = Decimal("100.00")
    _one = Decimal("1.00")

    def __init__(self, rates: list, sub_account: SubAccount, carrier_accounts: dict):

        self._rates = rates
        self._sub_account = sub_account
        self._carrier_accounts = carrier_accounts
        self._markup = sub_account.markup
        self._carriers = set()
        self._pickup_index = 0
        self._delivery_index = 0
        self._response_rates = {
            "rates": [],
            "pickup_rates": [],
            "delivery_rates": [],
            "carrier_service_info": {},
            "exchange_rate": {}
        }

    def _get_carrier_markup(self, carrier_id: int) -> Decimal:
        """

            :param account:
            :param carrier_id:
            :return:
        """
        look_up = f'{str(self._sub_account.subaccount_number)}_c_markup_{carrier_id}'

        carrier_markup_multiplier = cache.get(look_up)

        if not carrier_markup_multiplier:
            carrier_markup_multiplier = self._markup.markup_multiplier(carrier_id=carrier_id)
            cache.set(look_up, carrier_markup_multiplier, TWENTY_FOUR_HOURS_CACHE_TTL)

        return carrier_markup_multiplier

    def _apply_markup(self, rate: dict, multiplier: Decimal, exchange_rate: Decimal) -> None:
        rate['freight'] = (rate['freight'] * multiplier).quantize(self._sig_fig)
        rate['surcharge'] = (rate['surcharge'] * multiplier).quantize(self._sig_fig)
        rate['tax'] = (rate['tax'] * multiplier).quantize(self._sig_fig)
        rate['total'] = (rate['total'] * multiplier).quantize(self._sig_fig)

        rate['freight'] = (rate['freight'] * exchange_rate).quantize(self._sig_fig)
        rate['surcharge'] = (rate['surcharge'] * exchange_rate).quantize(self._sig_fig)
        rate['tax'] = (rate['tax'] * exchange_rate).quantize(self._sig_fig)
        rate['total'] = (rate['total'] * exchange_rate).quantize(self._sig_fig)

    def _white_label_carriers(self, rate: dict, carrier):
        """

            :return:
        """

        if self._sub_account.is_bbe:
            is_white_label = False
        elif self._sub_account.is_public:
            is_white_label = not carrier.is_allowed_public
        else:
            is_white_label = not carrier.is_allowed_account

        if is_white_label or carrier.is_bbe_only:

            if rate["carrier_name"] in rate["service_name"]:
                rate["service_name"] = rate["service_name"].replace(rate["carrier_name"], "ubbe")

            if "Fedex" in rate["service_name"]:
                rate["service_name"] = rate["service_name"].replace("Fedex", "ubbe")

            if "TST-CF" in rate["service_name"]:
                rate["service_name"] = rate["service_name"].replace("TST-CF", "ubbe")

            rate["carrier_name"] = f"ubbe {carrier.get_mode_display()}"

    def _apply_markup_list(self, rates: list, exchange_rate: Decimal):
        """

            :param rates:
            :return:
        """

        for rate in rates:
            carrier = self._carrier_accounts[rate["carrier_id"]]["carrier"]

            self._white_label_carriers(rate=rate, carrier=carrier)
            # multiplier = self._markup.markup_multiplier(carrier_id=rate["carrier_id"])
            multiplier = self._get_carrier_markup(carrier_id=rate["carrier_id"])
            self._carriers.add((rate["carrier_id"], rate['service_code']))
            self._apply_markup(rate=rate, multiplier=multiplier, exchange_rate=exchange_rate)
            rate["type_name"] = "Direct"
            rate["type_code"] = "DRI"

            if 'origin' in rate:
                rate["origin"] = rate["origin"].replace("'", "")

            if 'destination' in rate:
                rate["destination"] = rate["destination"].replace("'", "")

            if 'pickup_city' in rate:
                rate["pickup_city"] = rate["pickup_city"].replace("'", "")

            if 'delivery_city' in rate:
                rate["delivery_city"] = rate["delivery_city"].replace("'", "")

            if "exchange_rate" in rate:
                del rate["exchange_rate"]

    def _process_rates(self, rates, exchange_rate: Decimal):
        """

            :param rates:
            :return:
        """

        for p_rate, m_rate, d_rate in rates:
            new_responses = []
            pickup_index = -1
            delivery_index = -1

            if p_rate:
                self._apply_markup_list(rates=p_rate, exchange_rate=exchange_rate)
                self._response_rates["pickup_rates"].append(p_rate)
                pickup_index = self._pickup_index
                self._pickup_index += 1

            if d_rate:
                self._apply_markup_list(rates=d_rate, exchange_rate=exchange_rate)

                self._response_rates["delivery_rates"].append(d_rate)
                delivery_index = self._delivery_index
                self._delivery_index += 1

            for rate in m_rate:
                self._carriers.add((rate["carrier_id"], rate['service_code']))
                carrier = self._carrier_accounts[rate["carrier_id"]]["carrier"]

                self._white_label_carriers(rate=rate, carrier=carrier)

                if 'mid_o' in rate:
                    mid_origin = rate.pop('mid_o')
                    rate["pickup_city"] = mid_origin['city']
                    rate["pickup_code"] = mid_origin['base']

                if 'mid_d' in rate:
                    mid_destination = rate.pop('mid_d')
                    rate["delivery_city"] = mid_destination['city']
                    rate["delivery_code"] = mid_destination['base']

                if pickup_index > -1:
                    rate["pickup"] = pickup_index

                if delivery_index > -1:
                    rate["delivery"] = delivery_index

                if rate["carrier_id"] in AIR_CARRIERS:
                    rate["type_name"] = "Airport to Airport"
                    rate["type_code"] = "ATA"
                elif rate["carrier_id"] in SEALIFT_CARRIERS:
                    rate["type_name"] = "Port to Port"
                    rate["type_code"] = "PTP"
                else:
                    rate["type_name"] = "Direct"
                    rate["type_code"] = "DRI"

                if 'origin' in rate:
                    rate["origin"] = rate["origin"].replace("'", "")

                if 'destination' in rate:
                    rate["destination"] = rate["destination"].replace("'", "")

                if 'pickup_city' in rate:
                    rate["pickup_city"] = rate["pickup_city"].replace("'", "")

                if 'delivery_city' in rate:
                    rate["delivery_city"] = rate["delivery_city"].replace("'", "")

                # multiplier = self._markup.markup_multiplier(carrier_id=rate["carrier_id"])
                multiplier = self._get_carrier_markup(carrier_id=rate["carrier_id"])
                self._apply_markup(rate=rate, multiplier=multiplier, exchange_rate=exchange_rate)

                if "exchange_rate" in rate:
                    del rate["exchange_rate"]

                new_responses.append(rate)

            self._response_rates["rates"].extend(new_responses)

    def join_rates(self) -> dict:
        """

            :return:
        """

        exchange_rate = ExchangeRateUtility(
            source_currency="CAD", target_currency=self._sub_account.currency_code
        ).get_exchange_rate()

        self._response_rates["exchange_rate"].update({
            "value": exchange_rate,
            "from_currency": "CAD",
            "to_currency": self._sub_account.currency_code
        })

        for rates in self._rates:

            if not rates:
                continue

            self._process_rates(rates=rates, exchange_rate=exchange_rate)

        for carrier_id, service_code in self._carriers:

            service_info = CarrierServiceCache().get_service_information(
                carrier_id=carrier_id, service_code=service_code
            )

            if service_info["description"] == "No Service":
                continue

            if str(carrier_id) not in self._response_rates["carrier_service_info"]:
                self._response_rates["carrier_service_info"][f"{carrier_id}"] = {}

            self._response_rates["carrier_service_info"][f"{carrier_id}"][f"{service_code}"] = service_info

        connection.close()
        return self._response_rates
