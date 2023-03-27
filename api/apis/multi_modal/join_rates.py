import datetime
from decimal import Decimal

from django.db import connection

from api.globals.carriers import PUROLATOR
from api.models import SubAccount


class JoinRate:
    _sig_fig = Decimal("0.01")
    _chl = "b72c8b2c-2e24-4763-b130-da1d233550d2"
    _hundred = Decimal("100.00")
    _one = Decimal("1.00")

    def __init__(self, air_rates: list, sealift_rates: list, ground_rates: list, interline_rates: list, sub_account: SubAccount):

        if air_rates:
            self._air_rates = air_rates
        else:
            self._air_rates = None

        if sealift_rates:
            self._sealift_rates = sealift_rates
        else:
            self._sealift_rates = None

        if ground_rates:
            self._ground_rates = ground_rates
        else:
            self._ground_rates = None

        if interline_rates:
            self._interline_rates = interline_rates
        else:
            self._interline_rates = None

        self._sub_account = sub_account
        self._markup = sub_account.markup

        self._pickup_index = 0
        self._delivery_index = 0
        self._carriers = set()
        self._rates = {
            "rates": [],
            "pickup_rates": [],
            "delivery_rates": [],
            "carriers": []
        }

    @staticmethod
    def _apply_markup(data: dict, multiplier: Decimal) -> None:
        sig_fig = Decimal("0.01")

        data['freight'] = (data['freight'] * multiplier).quantize(sig_fig)
        data['surcharge'] = (data['surcharge'] * multiplier).quantize(sig_fig)
        data['tax'] = (data['tax'] * multiplier).quantize(sig_fig)
        data['total'] = (data['total'] * multiplier).quantize(sig_fig)

    def _get_multiplier(self, markup: Decimal, c_markup: Decimal):
        return (markup / self._hundred) + (c_markup / self._hundred) + self._one

    def _apply_markup_list(self, rates: list):
        for rate in rates:
            self._carriers.add((rate["carrier_id"], rate['service_code']))

            # TEMP For CHL #

            if str(self._sub_account.subaccount_number) == self._chl and rate["carrier_id"] == PUROLATOR:

                if rate.get("origin", "").lower() == "les cedres" and rate.get("destination", "").lower() == "ottawa":
                    multiplier = self._get_multiplier(markup=self._markup.default_percentage, c_markup=Decimal("0.00"))
                else:
                    multiplier = self._markup.markup_multiplier(carrier_id=rate["carrier_id"])
            else:
                multiplier = self._markup.markup_multiplier(carrier_id=rate["carrier_id"])

            # TEMP For CHL #

            self._apply_markup(data=rate, multiplier=multiplier)

    def _process_rates(self, rates):

        for p_rate, m_rate, d_rate in rates:
            new_rate = {}

            if p_rate:
                self._apply_markup_list(rates=p_rate)

                self._rates["pickup_rates"].append(p_rate)
                new_rate["pickup"] = self._pickup_index
                self._pickup_index += 1

            if d_rate:
                self._apply_markup_list(rates=d_rate)

                self._rates["delivery_rates"].append(d_rate)
                new_rate["delivery"] = self._delivery_index
                self._delivery_index += 1

            new_responses = []

            for rate in m_rate:
                carrier_id = rate.pop('carrier_id')
                self._carriers.add((carrier_id, rate['service_code']))

                if 'mid_o' in rate:
                    mid_origin = rate.pop('mid_o')
                    new_rate["pickup_city"] = mid_origin['city']
                    new_rate["pickup_code"] = mid_origin['base']

                if 'mid_d' in rate:
                    mid_destination = rate.pop('mid_d')
                    new_rate["delivery_city"] = mid_destination['city']
                    new_rate["delivery_code"] = mid_destination['base']

                new_rate["carrier_id"] = carrier_id
                new_rate["carrier_name"] = rate.pop('carrier_name')

                # TEMP For CHL #

                if str(self._sub_account.subaccount_number) == self._chl and carrier_id == PUROLATOR:

                    if rate.get("origin", "").lower() == "les cedres" and rate.get("destination",  "").lower() == "ottawa":
                        multiplier = self._get_multiplier(markup=self._markup.default_percentage, c_markup=Decimal("0.00"))
                    else:
                        multiplier = self._markup.markup_multiplier(carrier_id=carrier_id)
                else:
                    multiplier = self._markup.markup_multiplier(carrier_id=carrier_id)

                # TEMP For CHL #

                self._apply_markup(data=rate, multiplier=multiplier)

                new_responses.append(rate)

            new_rate['middle'] = new_responses

            self._rates["rates"].append(new_rate)

    def _process_interline(self):

        for f_rate_list, location, l_rate_list in self._interline_rates:

            self._apply_markup_list(rates=f_rate_list)
            self._apply_markup_list(rates=l_rate_list)

            f_rate = f_rate_list[0]
            l_rate = l_rate_list[0]

            if 'BBEQUO' in str(f_rate["service_code"]) or 'BBEQUO' in str(l_rate["service_code"]):
                continue

            if (not f_rate["transit_days"] and f_rate["transit_days"] != -1) and (not l_rate["transit_days"] and l_rate["transit_days"] != -1):
                transit = f_rate["transit_days"] + l_rate["transit_days"]
            else:
                transit = -1

            if transit != -1:
                estimated_delivery_date = datetime.datetime.utcnow() + datetime.timedelta(days=transit)
            else:
                estimated_delivery_date = datetime.datetime(year=1, month=1, day=1)

            new_rate = {
                "carrier_id": 903,
                "carrier_name": "ubbe",
                "middle_city": location["city"],
                "middle_base": location["base"],
                "middle": [
                    {
                        "service_code": f'{f_rate["carrier_id"]}|{f_rate["service_code"]}|{l_rate["carrier_id"]}|{l_rate["service_code"]}',
                        "service_name": f'{location["base"]} - Interline Ground',
                        "freight": Decimal(f_rate["freight"] + l_rate["freight"]).quantize(self._sig_fig),
                        "surcharge": Decimal(f_rate["surcharge"] + l_rate["surcharge"]).quantize(self._sig_fig),
                        "tax": Decimal(f_rate["tax"] + l_rate["tax"]).quantize(self._sig_fig),
                        "tax_percent": Decimal(f_rate["tax_percent"] + l_rate["tax_percent"]).quantize(self._sig_fig),
                        "total": Decimal(f_rate["total"] + l_rate["total"]).quantize(self._sig_fig),
                        "transit_days": transit,
                        "delivery_date": estimated_delivery_date.replace(microsecond=0).isoformat()
                    }
                ]
            }

            self._rates["rates"].append(new_rate)

    def join_rates(self) -> dict:

        if self._air_rates:
            self._process_rates(rates=self._air_rates)

        if self._sealift_rates:
            self._process_rates(rates=self._sealift_rates)

        if self._ground_rates:
            self._process_rates(rates=self._ground_rates)

        if self._interline_rates:
            self._process_interline()

        if not self._rates:
            connection.close()
            return {
                "rates": [],
                "pickup_rates": [],
                "delivery_rates": [],
                "carriers": []
            }
        else:
            connection.close()
            self._rates["carriers"] = list(self._carriers)
            return self._rates
