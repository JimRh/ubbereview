"""
    Title: Metric Carriers v3
    Description: The class filter requested filters and return thee following:
        - Start date
        - End date
        - Account
    Created: Sept 28, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from django.db import connection
from django.db.models import F, Count, QuerySet

from api.apis.metric_v3.metric_base_v3 import MetricBase
from api.exceptions.project import ViewException
from api.models import API, SubAccount, Leg


class GetMetricCarriers(MetricBase):
    """
        Metric Carriers Processing
    """

    @staticmethod
    def _get_data(legs: QuerySet):
        """

            :return:
        """

        carriers = legs.values(
            carrier_name=F('carrier__name'), carrier_code=F('carrier__code')
        ).annotate(count=Count(F('carrier_code'))).order_by("-count")[:10]

        carrier_services = legs.values(
            "service_name", "service_code", carrier_name=F('carrier__name'), carrier_code=F('carrier__code')
        ).annotate(count=Count(F('service_code'))).order_by("-count")[:10]

        ret = {
            "top_carriers": list(carriers),
            "top_services": list(carrier_services)
        }

        return ret

    def _get_account_data(self, sub_account: SubAccount, start_date: str, end_date: str, query_type: str):
        """

            :param sub_account:
            :param start_date:
            :param end_date:
            :return:
        """

        if start_date and end_date:
            start_date, end_date = self._get_dates(start_date=start_date, end_date=end_date)

            if query_type == "COM":

                if sub_account.is_bbe:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account,
                        shipment__creation_date__range=[start_date, end_date],
                        is_shipped=True
                    )
                else:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account,
                        shipment__creation_date__range=[start_date, end_date],
                        is_shipped=True
                    ).exclude(shipment__username__in=self._bbe_users)

                man_legs = Leg.objects.filter(
                    shipment__bc_customer_code=sub_account.bc_customer_code,
                    shipment__username__in=self._bbe_users,
                    shipment__creation_date__range=[start_date, end_date],
                    is_shipped=True
                )

                # Combine Query Sets
                legs = legs | man_legs

            elif query_type == "MAN":
                legs = Leg.objects.filter(
                    shipment__bc_customer_code=sub_account.bc_customer_code,
                    shipment__username__in=self._bbe_users,
                    shipment__creation_date__range=[start_date, end_date],
                    is_shipped=True
                )
            else:
                if sub_account.is_bbe:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account,
                        shipment__creation_date__range=[start_date, end_date],
                        is_shipped=True
                    )
                else:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account,
                        shipment__creation_date__range=[start_date, end_date],
                        is_shipped=True
                    ).exclude(shipment__username__in=self._bbe_users)
        else:

            if query_type == "COM":

                if sub_account.is_bbe:
                    legs = Leg.objects.filter(shipment__subaccount=sub_account, is_shipped=True)
                else:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account, is_shipped=True
                    ).exclude(shipment__username__in=self._bbe_users)

                man_legs = Leg.objects.filter(
                    shipment__bc_customer_code=sub_account.bc_customer_code,
                    shipment__username__in=self._bbe_users,
                    is_shipped=True
                )

                # Combine Query Sets
                legs = legs | man_legs

            elif query_type == "MAN":
                legs = Leg.objects.filter(
                    shipment__bc_customer_code=sub_account.bc_customer_code,
                    shipment__username__in=self._bbe_users,
                    is_shipped=True
                )
            else:

                if sub_account.is_bbe:
                    legs = Leg.objects.filter(shipment__subaccount=sub_account, is_shipped=True)
                else:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account, is_shipped=True
                    ).exclude(shipment__username__in=self._bbe_users)

        return self._get_data(legs=legs)

    def _get_bbe_data(self, sub_account: SubAccount, start_date: str, end_date: str, params: dict):
        """

            :param sub_account:
            :param start_date:
            :param end_date:
            :return:
        """
        accounts = params.get("accounts", [])

        if accounts and start_date and end_date:
            start_date, end_date = self._get_dates(start_date=start_date, end_date=end_date)
            legs = Leg.objects.filter(
                shipment__creation_date__range=[start_date, end_date],
                shipment__subaccount__subaccount_number__in=accounts,
                is_shipped=True
            )

            return self._get_data(legs=legs)
        elif accounts:
            legs = Leg.objects.filter(shipment__subaccount__subaccount_number__in=accounts, is_shipped=True)

            return self._get_data(legs=legs)

        return self._get_account_data(
            sub_account=sub_account, start_date=start_date, end_date=end_date, query_type=params["query_type"]
        )

    def get_metrics(self, sub_account: SubAccount, params: dict) -> dict:
        """
            Get Metric Routes. IE: City Count and Province Count.
            :return: dictionary of metrics
        """
        errors = []

        if not API.objects.get(name="MetricCarriersV3").active:
            connection.close()
            errors.append({"metric_carriers": "Metric endpoint not active."})
            raise ViewException(code="6803", message="Metric Carriers: Endpoint not active.", errors=errors)

        start_date = params['start_date']
        end_date = params['end_date']
        query_type = params['query_type']

        if (start_date and not end_date) or (not start_date and end_date):
            connection.close()
            errors.append({"dates": "'start_date' and 'end_date' are both required if one occurs."})
            errors.append({"start_date": "Must be in '%Y-%m-%d'"})
            errors.append({"end_date": "Must be in '%Y-%m-%d'"})
            raise ViewException(code="6804", message="Metric Carriers: Invalid dates.", errors=errors)

        if sub_account.is_bbe:
            ret = self._get_bbe_data(sub_account=sub_account, start_date=start_date, end_date=end_date, params=params)
        else:
            ret = self._get_account_data(
                sub_account=sub_account, start_date=start_date, end_date=end_date, query_type=query_type
            )

        ret.update({
            "last_updated": self._get_date(),
        })

        connection.close()
        return ret
