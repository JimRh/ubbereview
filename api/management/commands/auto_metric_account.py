import datetime
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.core.management import BaseCommand
from django.db.models import QuerySet, Sum, F, Count

from api.models import Shipment, Leg, SubAccount, MetricAccount, Package, RateLog, MetricGoals


class Command(BaseCommand):

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
    def _get_query_shipment(account: SubAccount, metric_date: datetime, users: list) -> QuerySet:
        """
            Get shipments for account.
            :param account: account who to get shipments for
            :param metric_date: Date to get shipments for.
            :return: Shipment Queryset
        """

        if account.is_bbe:
            return Shipment.objects.filter(
                is_shipped=True,
                subaccount=account,
                creation_date__year=metric_date.year,
                creation_date__month=metric_date.month,
                creation_date__day=metric_date.day,
            )

        return Shipment.objects.filter(
            is_shipped=True,
            subaccount=account,
            creation_date__year=metric_date.year,
            creation_date__month=metric_date.month,
            creation_date__day=metric_date.day,
        ).exclude(username__in=users)

    @staticmethod
    def _get_bbe_query_shipment(account: SubAccount, metric_date: datetime, users: list) -> QuerySet:
        """
            Get shipments for account.
            :param account: account who to get shipments for
            :param metric_date: Date to get shipments for.
            :return: Shipment Queryset
        """

        return Shipment.objects.filter(
            is_shipped=True,
            bc_customer_code=account.bc_customer_code,
            creation_date__year=metric_date.year,
            creation_date__month=metric_date.month,
            creation_date__day=metric_date.day,
            username__in=users
        )

    @staticmethod
    def _get_package_data(shipments: QuerySet, data: dict):
        """

            :param shipments:a
            :param data:
            :return:
        """
        packages = Package.objects.filter(shipment__in=shipments)

        package_data = packages.aggregate(
            total_packages=Sum('quantity'),
            total_weight=Sum(F('quantity')*F('weight'))
        )

        data.update({
            "quantity": package_data["total_packages"] if package_data.get("total_packages") else Decimal("0"),
            "weight": package_data["total_weight"] if package_data.get("total_weight") else Decimal("0"),
        })

    @staticmethod
    def _get_carrier_data(legs: QuerySet, mode: str) -> tuple:
        """
            Get carrier mode specific data.
            :param legs: Leg query set for mode
            :param mode: carrier mode
            :return:
        """

        leg_data = legs.filter(carrier__mode=mode).aggregate(
            legs=Count('leg_id'),
            expense=Sum(F('base_cost') - F('base_tax')),
            revenue=Sum((F('base_cost') - F('base_tax'))*(F('markup') / 100 + 1)),
        )

        expense = leg_data["expense"] if leg_data.get("expense") else Decimal("0")
        revenue = leg_data["revenue"] if leg_data.get("revenue") else Decimal("0")
        leg_amount = leg_data["legs"] if leg_data.get("legs") else 0

        return leg_amount, revenue, expense

    def _get_leg_data(self, shipments: QuerySet, data: dict):
        """
            Get leg data.
            :param shipments: shipment query set
            :param data: data to add data to
        """
        legs = Leg.objects.filter(shipment__in=shipments)

        leg_data = legs.aggregate(
            total_expense=Sum(F('base_cost')-F('base_tax')),
            total_revenue=Sum((F('base_cost')-F('base_tax'))*(F('markup')/100 + 1))
        )

        total_expense = leg_data["total_expense"] if leg_data.get("total_expense") else Decimal("0")
        total_revenue = leg_data["total_revenue"] if leg_data.get("total_revenue") else Decimal("0")

        air_amount, air_revenue, air_expense = self._get_carrier_data(legs=legs, mode="AI")
        ltl_amount, ltl_revenue, ltl_expense = self._get_carrier_data(legs=legs, mode="LT")
        ftl_amount, ftl_revenue, ftl_expense = self._get_carrier_data(legs=legs, mode="FT")
        courier_amount, courier_revenue, courier_expense = self._get_carrier_data(legs=legs, mode="CO")
        sea_amount, sea_revenue, sea_expense = self._get_carrier_data(legs=legs, mode="SE")

        data.update({
            "air_legs": air_amount,
            "ltl_legs": ltl_amount,
            "ftl_legs": ftl_amount,
            "courier_legs": courier_amount,
            "sea_legs": sea_amount,
            "revenue": total_revenue,
            "expense": total_expense,
            "net_profit": total_revenue - total_expense,
            "air_revenue": air_revenue,
            "air_expense": air_expense,
            "air_net_profit": air_revenue - air_expense,
            "ltl_revenue": ltl_revenue,
            "ltl_expense": ltl_expense,
            "ltl_net_profit": ltl_revenue - ltl_expense,
            "ftl_revenue": ftl_revenue,
            "ftl_expense": ftl_expense,
            "ftl_net_profit": ftl_revenue - ftl_expense,
            "courier_revenue": courier_revenue,
            "courier_expense": courier_expense,
            "courier_net_profit": courier_revenue - courier_expense,
            "sea_revenue": sea_revenue,
            "sea_expense": sea_expense,
            "sea_net_profit": sea_revenue - sea_expense
        })

    def _create_daily(self, account: SubAccount, metric_date: datetime):
        """
            Create Metric Account daily.
            :param account: Sub Account
            :param metric_date: Datetime
            :return:
        """

        shipments = self._get_query_shipment(account=account, metric_date=metric_date, users=self._bbe_users)
        bbe_shipments = self._get_bbe_query_shipment(account=account, metric_date=metric_date, users=self._bbe_users)

        quotes = RateLog.objects.filter(
            sub_account=account,
            rate_date__year=metric_date.year,
            rate_date__month=metric_date.month,
            rate_date__day=metric_date.day
        ).count()

        shipped = RateLog.objects.filter(
            sub_account=account,
            rate_date__year=metric_date.year,
            rate_date__month=metric_date.month,
            rate_date__day=metric_date.day
        ).exclude(shipment_id="").count()

        data = {
            "creation_date": metric_date,
            "sub_account": account,
            "shipments": shipments.count(),
            "quotes": quotes,
            "shipped_quotes": shipped
        }

        managed_data = {
            "shipments": bbe_shipments.count()
        }

        # Self-Managed
        self._get_package_data(shipments=shipments, data=data)
        self._get_leg_data(shipments=shipments, data=data)

        # Managed
        self._get_package_data(shipments=bbe_shipments, data=managed_data)
        self._get_leg_data(shipments=bbe_shipments, data=managed_data)

        if account.is_bbe:
            managed_data = {}

        for key, value in managed_data.items():
            data[f"managed_{key}"] = value

        new_daily = MetricAccount.create(param_dict=data)
        new_daily.save()

        return new_daily

    def handle(self, *args, **options) -> None:
        metric_day = datetime.datetime.now() - datetime.timedelta(days=1)

        systems = ["UB", "FE", "DE", "TP"]
        exclude_from_goals = [
            "5edcc144-4546-423a-9fcd-2be2418e4720",  # BBE Account
            "d2ffe46d-dfeb-458c-b6c4-03e76c8f4eb8",  # McKesson- Trenton DC
            "24ca615d-268d-46b5-be9e-20f79cf2485e",  # GN Warehousing
            "2c0148a6-69d7-4b22-88ed-231a084d2db9"  # Government of Nunavut
        ]

        for system in systems:
            sub_accounts = SubAccount.objects.filter(system=system)

            try:
                rev_goal = MetricGoals.objects.get(system=system, name="Revenue", start_date__year=metric_day.year)
            except ObjectDoesNotExist:
                rev_goal = None

            try:
                ship_goal = MetricGoals.objects.get(system=system, name="Shipments", start_date__year=metric_day.year)
            except ObjectDoesNotExist:
                ship_goal = None

            for account in sub_accounts:
                new_daily = self._create_daily(account=account, metric_date=metric_day)

                if rev_goal and str(account.subaccount_number) not in exclude_from_goals:
                    rev_goal.current = Decimal(rev_goal.current + new_daily.revenue).quantize(Decimal("0.01"))
                    rev_goal.save()

                if ship_goal and str(account.subaccount_number) not in exclude_from_goals:
                    ship_goal.current += new_daily.shipments
                    ship_goal.save()
