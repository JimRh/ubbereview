"""
    Title: Base Metric Api V3
    Description: The class is the based class that holds common functions to metrics.
    Created: Sept 24, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

import datetime
from decimal import Decimal

import pytz
from django.db import connection

from api.exceptions.project import ViewException


class MetricBase:
    """
        Base Metric Api V3 class
    """

    _hundred = 100
    _zero = 0
    _decimal_zero = Decimal("0.00")
    _one = 1
    _sig_fig = Decimal("0.01")

    _daily = "daily"
    _weekly = "weekly"
    _monthly = "monthly"
    _quarterly = "quarterly"
    _ytd = "ytd"

    _q_one = (1, 2, 3), "Q1"
    _q_two = (4, 5, 6), "Q2"
    _q_three = (7, 8, 9), "Q3"
    _q_four = (10, 11, 12), "Q4"
    _quarters = ["Q1", "Q2", "Q3", "Q4"]
    _months = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)
    _month_name = {
        1: "Jan",
        2: "Feb",
        3: "Mar",
        4: "April",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Aug",
        9: "Sept",
        10: "Oct",
        11: "Nov",
        12: "Dec"
    }

    _month_name_str = [
        "Jan",
        "Feb",
        "Mar",
        "April",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sept",
        "Oct",
        "Nov",
        "Dec"
    ]
    _year = datetime.date.today().year

    _bbe_users = [
        "lharder@bbex.com", "sjadhav", "spanesar@bbex.com", "accounting", "yabdulla@bbex.com", "asmith",
        "hschmidt@bbex.com", "psmithson", "atomulescu", "vbiradi", "lsmithson@bbex.com", "acollins",
        "jdominguez@bbex.com", "senns@bbex.com", "mjangaria@bbex.com", "zstiles@bbex.com", "kenneth",
        "gpeters@bbex.com", "vnatarajan", "rmacneill", "lhillier", "kdouglas", "hstewart@bbex.com", "sgray",
        "kortiz", "abhardwaj@bbex.com", "areghunathan@bbex.com", "awaddington@bbex.com", "astevens@bbex.com",
        "rbecker", "mdoerksen@bbex.com", "bbe_expediting", "wvanbeek", "kbosnjak", "rwelham@bbex.com",
        "jphillip@bbex.com", "smatthew@bbex.com", "abruinsma@bbex.com", "mtausa", "mgill", "slee@bbex.com",
        "kmercier@bbex.com", "mgrant@bbex.com", "ralcaraz", "bmonchuk", "wkulatunga", "kiwekpeazu", "graham",
        "bbeottawa", "moe", "tvlasic", "hgillani", "nmartinez", "wkezer", "mmccormick", "jpruden", "jjohnstone",
        "lsulyma", "krutter", "jnascimento", "jbrown", "mturnell", "ralipio", "ktacastacas", "maquin", "sdavis",
        "cchang", "cchan", "scaddick", "gmcneil", "fsommer", "demott", "bwells", "acdc_asmith@bbex.com",
        "acdc_zstiles@bbex.com", "acdc_mdoerksen@bbex.com", "acdc_kdouglas@bbex.com", "acdc_acollins@bbex.com",
        "acdc_anubhav@bbex.com", "acdc_awaddington@bbex.com", "acdc_spanesar@bbex.com"
    ]

    @staticmethod
    def _get_date():
        """
            Get datetime now.
            :return:
        """

        return datetime.datetime.now().isoformat()

    @staticmethod
    def _parse_date(date: str, field: str):
        """

            :return:
        """

        try:
            parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d').astimezone(tz=pytz.UTC)
        except ValueError:
            connection.close()
            raise ViewException(f"{field} must be in '%Y-%m-%d' format")

        return parsed_date

    def _get_sum(self, field):

        if not field:
            return self._zero

        return field

    def _get_default_years(self) -> list:
        """
            Get default years to get data for.
            :return: list of int years
        """

        starting_year = self._year - 3
        year_list = [starting_year]

        while starting_year != self._year:
            starting_year += 1
            year_list.append(starting_year)

        return year_list

    def _get_dates(self, start_date: str, end_date: str):
        """

            :param start_date:
            :param end_date:
            :return:
        """

        start_date = self._parse_date(date=start_date, field="start_date")
        end_date = self._parse_date(date=end_date, field="end_date")
        end_date = end_date + datetime.timedelta(days=self._one)

        return start_date, end_date

    def _get_decimal_value(self, metric_dict, metric_key) -> Decimal:
        """

            :param metric_dict:
            :param metric_key:
            :return:
        """

        value = metric_dict[metric_key]

        if not value:
            return self._decimal_zero.quantize(self._sig_fig)

        return Decimal(value).quantize(self._sig_fig)

    def _get_value(self, metric_dict, metric_key) -> int:
        """

            :param metric_dict:
            :param metric_key:
            :return:
        """

        value = metric_dict[metric_key]

        if not value:
            return self._zero

        return value
