"""
    Title: Metric Averages v3
    Description: The class filter requested filters and return thee following:
        - Start date
        - End date
        - Account
    Created: Sept 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import numpy

from django.db import connection
from django.db.models import QuerySet
from scipy import stats

from api.apis.metric_v3.metric_base_v3 import MetricBase
from api.exceptions.project import ViewException
from api.models import API, SubAccount, Leg, Shipment


class GetMetricAverages(MetricBase):
    """
        Metric Averages
    """

    @staticmethod
    def _get_mode_value(mode_count) -> str:
        """
            Get Mode value and ensure its in correct format for json.
            :param mode_count:
            :return: str
        """

        if mode_count:
            str_mode_count = str(mode_count[0])
        else:
            str_mode_count = "-"

        return str_mode_count

    def _get_average_data(self, data: list, is_shipment: bool) -> dict:
        """
            Get Average date for cost list.
            :param data: list of costs
            :return: dict of averages
        """

        mode = stats.mode(data)
        mode_count = mode.count

        mode_count = self._get_mode_value(mode_count=mode_count)

        mean = str(round(numpy.mean(data), 2))
        median_cost = str(round(numpy.median(data), 2))

        if is_shipment:
            note = "The averages are based on the sum of all shipment legs."
        else:
            note = "The averages are based on individual shipment legs."

        return {
            "mode_count": mode_count,
            "mean_cost": mean if mean != "nan" else "-",
            "median_cost": median_cost if median_cost != "nan" else "-",
            "note": note
        }

    def _get_average_transit_time(self, legs: QuerySet) -> dict:
        """
            Get Legs for an account.
            :param args: query params for leg model
            :return: Shipment QuerySet
        """

        data = legs.exclude(transit_days__in=[-1]).values_list("transit_days", flat=True)

        mode = stats.mode(data)
        mode_count = mode.count

        mode_count = self._get_mode_value(mode_count=mode_count)

        mean = str(round(numpy.mean(data), 2))
        median_cost = str(round(numpy.median(data), 2))

        return {
            "transit_averages": {
                "mode_count": mode_count,
                "mean_transit": mean if mean != "nan" else "-",
                "median_transit": median_cost if median_cost != "nan" else "-",
                "note": "Average Transit Time for leg to arrived at destination. (All 0's excluded)"
            }
        }

    def _get_averages(self, data: QuerySet, is_shipment: bool) -> dict:
        """
            Get metrics about shipment or leg cost. IE: Mode, Mean, Median, and Note.
            :param data: QuerySet of Shipments or Legs
            :return: dictionary of Average Metrics
        """

        cost_list = []
        dg_list = []
        delivered_list = []

        for item in data:
            cost_list.append(float((item.cost - item.tax) * ((item.markup / self._hundred) + self._one)))

            if item.is_dangerous_good:
                dg_list.append(float((item.cost - item.tax) * ((item.markup / self._hundred) + self._one)))

            if item.is_delivered:
                delivered_list.append(
                    float((item.cost - item.tax) * ((item.markup / self._hundred) + self._one))
                )

        shipment_averages = self._get_average_data(data=cost_list, is_shipment=is_shipment)
        dg_averages = self._get_average_data(data=dg_list, is_shipment=is_shipment)
        delivered_averages = self._get_average_data(data=delivered_list, is_shipment=is_shipment)

        return {
            "shipment_averages": shipment_averages,
            "dg_averages": dg_averages,
            "delivered_averages": delivered_averages
        }

    def _get_account_data(self, sub_account: SubAccount, start_date: str, end_date: str, query_type: str):
        """

            :param sub_account:
            :param start_date:
            :param end_date:
            :return:
        """
        ret = {
            "shipments": {},
            "legs": {},
            "transit": {}
        }

        if start_date and end_date:
            start_date, end_date = self._get_dates(start_date=start_date, end_date=end_date)

            if query_type == "COM":

                if sub_account.is_bbe:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account,
                        shipment__creation_date__range=[start_date, end_date],
                        is_shipped=True
                    )
                    shipments = Shipment.objects.filter(
                        subaccount=sub_account,
                        creation_date__range=[start_date, end_date],
                        is_shipped=True
                    )
                else:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account,
                        shipment__creation_date__range=[start_date, end_date],
                        is_shipped=True
                    ).exclude(shipment__username__in=self._bbe_users)
                    shipments = Shipment.objects.filter(
                        subaccount=sub_account,
                        creation_date__range=[start_date, end_date],
                        is_shipped=True
                    ).exclude(username__in=self._bbe_users)

                man_legs = Leg.objects.filter(
                    shipment__bc_customer_code=sub_account.bc_customer_code,
                    shipment__username__in=self._bbe_users,
                    shipment__creation_date__range=[start_date, end_date],
                    is_shipped=True
                )
                man_shipments = Shipment.objects.filter(
                    bc_customer_code=sub_account.bc_customer_code,
                    username__in=self._bbe_users,
                    subaccount=sub_account,
                    creation_date__range=[start_date, end_date],
                    is_shipped=True
                )

                # Combine Query Sets
                legs = legs | man_legs
                shipments = shipments | man_shipments

            elif query_type == "MAN":
                legs = Leg.objects.filter(
                    shipment__bc_customer_code=sub_account.bc_customer_code,
                    shipment__username__in=self._bbe_users,
                    shipment__creation_date__range=[start_date, end_date],
                    is_shipped=True
                )
                shipments = Shipment.objects.filter(
                    bc_customer_code=sub_account.bc_customer_code,
                    username__in=self._bbe_users,
                    subaccount=sub_account,
                    creation_date__range=[start_date, end_date],
                    is_shipped=True
                )
            else:

                if sub_account.is_bbe:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account,
                        shipment__creation_date__range=[start_date, end_date],
                        is_shipped=True
                    )
                    shipments = Shipment.objects.filter(
                        subaccount=sub_account,
                        creation_date__range=[start_date, end_date],
                        is_shipped=True
                    )
                else:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account,
                        shipment__creation_date__range=[start_date, end_date],
                        is_shipped=True
                    ).exclude(shipment__username__in=self._bbe_users)
                    shipments = Shipment.objects.filter(
                        subaccount=sub_account,
                        creation_date__range=[start_date, end_date],
                        is_shipped=True
                    ).exclude(username__in=self._bbe_users)

        else:
            if query_type == "COM":

                if sub_account.is_bbe:
                    legs = Leg.objects.filter(shipment__subaccount=sub_account, is_shipped=True)
                    shipments = Shipment.objects.filter(subaccount=sub_account, is_shipped=True)
                else:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account, is_shipped=True
                    ).exclude(username__in=self._bbe_users)
                    shipments = Shipment.objects.filter(
                        subaccount=sub_account, is_shipped=True
                    ).exclude(username__in=self._bbe_users)

                    man_legs = Leg.objects.filter(
                        shipment__bc_customer_code=sub_account.bc_customer_code,
                        shipment__username__in=self._bbe_users,
                        shipment__subaccount=sub_account,
                        is_shipped=True
                    )
                    man_shipments = Shipment.objects.filter(
                        bc_customer_code=sub_account.bc_customer_code,
                        username__in=self._bbe_users,
                        subaccount=sub_account,
                        is_shipped=True
                    )

                    # Combine Query Sets
                    legs = legs | man_legs
                    shipments = shipments | man_shipments

            elif query_type == "MAN":
                legs = Leg.objects.filter(
                    shipment__bc_customer_code=sub_account.bc_customer_code,
                    shipment__username__in=self._bbe_users,
                    shipment__subaccount=sub_account,
                    is_shipped=True
                )
                shipments = Shipment.objects.filter(
                    bc_customer_code=sub_account.bc_customer_code,
                    username__in=self._bbe_users,
                    subaccount=sub_account,
                    is_shipped=True
                )
            else:

                if sub_account.is_bbe:
                    legs = Leg.objects.filter(shipment__subaccount=sub_account, is_shipped=True)
                    shipments = Shipment.objects.filter(subaccount=sub_account, is_shipped=True)
                else:
                    legs = Leg.objects.filter(
                        shipment__subaccount=sub_account, is_shipped=True
                    ).exclude(shipment__username__in=self._bbe_users)
                    shipments = Shipment.objects.filter(
                        subaccount=sub_account, is_shipped=True
                    ).exclude(username__in=self._bbe_users)

        leg_averages = self._get_averages(data=legs, is_shipment=False)
        shipment_averages = self._get_averages(data=shipments, is_shipment=True)
        transit_averages = self._get_average_transit_time(legs=legs)

        ret["shipments"].update(shipment_averages)
        ret["legs"].update(leg_averages)
        ret["transit"].update(transit_averages)

        return ret

    def _get_bbe_data(self, sub_account: SubAccount, start_date: str, end_date: str, params: dict):
        """

            :param sub_account:
            :param start_date:
            :param end_date:
            :return:
        """
        accounts = params.get("accounts", [])
        ret = {
            "shipments": {},
            "legs": {},
            "transit": {}
        }

        if accounts and start_date and end_date:
            start_date, end_date = self._get_dates(start_date=start_date, end_date=end_date)
            legs = Leg.objects.filter(
                shipment__creation_date__range=[start_date, end_date],
                shipment__subaccount__subaccount_number__in=accounts,
                is_shipped=True
            )

            shipments = Shipment.objects.filter(
                creation_date__range=[start_date, end_date],
                subaccount__subaccount_number__in=accounts,
                is_shipped=True
            )

            leg_averages = self._get_averages(data=legs, is_shipment=False)
            shipment_averages = self._get_averages(data=shipments, is_shipment=True)
            transit_averages = self._get_average_transit_time(legs=legs)

            ret["shipments"].update(shipment_averages)
            ret["legs"].update(leg_averages)
            ret["transit"].update(transit_averages)

            return ret
        elif accounts:
            legs = Leg.objects.filter(shipment__subaccount__subaccount_number__in=accounts, is_shipped=True)
            shipments = Shipment.objects.filter(subaccount__subaccount_number__in=accounts, is_shipped=True)

            leg_averages = self._get_averages(data=legs, is_shipment=False)
            shipment_averages = self._get_averages(data=shipments, is_shipment=True)
            transit_averages = self._get_average_transit_time(legs=legs)

            ret["shipments"].update(shipment_averages)
            ret["legs"].update(leg_averages)
            ret["transit"].update(transit_averages)

            return ret

        return self._get_account_data(
            sub_account=sub_account, start_date=start_date, end_date=end_date, query_type=params["query_type"]
        )

    def get_metrics(self, sub_account: SubAccount, params: dict) -> dict:
        """
            Get Metric Averages.
            :return: dictionary of metrics
        """
        errors = []

        if not API.objects.get(name="MetricAveragesV3").active:
            connection.close()
            errors.append({"metric_average": "Metric endpoint not active."})
            raise ViewException(code="6703", message="MetricAverages: Endpoint not active.", errors=errors)

        start_date = params['start_date']
        end_date = params['end_date']
        query_type = params['query_type']

        if (start_date and not end_date) or (not start_date and end_date):
            connection.close()
            errors.append({"dates": "'start_date' and 'end_date' are both required if one occurs."})
            errors.append({"start_date": "Must be in '%Y-%m-%d'"})
            errors.append({"end_date": "Must be in '%Y-%m-%d'"})
            raise ViewException(code="6704", message="MetricAverages: Invalid dates.", errors=errors)

        if sub_account.is_bbe:
            ret = self._get_bbe_data(sub_account=sub_account, start_date=start_date, end_date=end_date, params=params)
        else:
            ret = self._get_account_data(
                sub_account=sub_account, start_date=start_date, end_date=end_date, query_type=query_type
            )

        ret.update({
            "weight_units": "KG",
            "currency": "CAD",
            "last_updated": self._get_date(),
        })

        connection.close()
        return ret
