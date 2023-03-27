"""
    Title: Config Update
    Description: This file is intended to configurate the system or create DB entries that are mandatory and adding
                stuff to accounts.
    Created: Nov 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.core.management import BaseCommand
from django.db import connection, transaction

from api.models import SubAccount, Shipment, Leg


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('account_number', type=str, help='Account Number. (BBE Account)')
        parser.add_argument('option', type=str, help='Option: 1 Account BC Populate, 2: BBE user set. 3: Set Markup')
        parser.add_argument('bc_code', type=str, help='Mandatory for 3: BC Code')
        parser.add_argument('markup', type=str, help='Mandatory for 3: Markup Percentage')

    @transaction.atomic()
    def handle(self, *args, **options) -> None:

        if options["option"] == "1":
            self.populate_accounts_bc_details_to_shipments()
        elif options["option"] == "2":
            self.populate_bbe_users()
        elif options["option"] == "3":
            self.populate_leg_markups(bc_code=options["bc_code"], markup=options["markup"])

        print("Finished")

    @transaction.atomic()
    def populate_accounts_bc_details_to_shipments(self):
        """

            :return:
        """

        print(Shipment.objects.count())
        print(SubAccount.objects.count())

        # Will populate all account shipments with their BC Code and Name.
        for account in SubAccount.objects.all():
            print("---------------------")
            print(account)
            if account.bc_customer_code in ["BBE"]:
                continue

            shipments = Shipment.objects.prefetch_related("leg_shipment").filter(
                subaccount=account, creation_date__year=2022
            )
            print(shipments.count())

            for shipment in shipments:
                shipment.bc_customer_code = account.bc_customer_code
                shipment.bc_customer_name = account.bc_customer_name
                shipment.save()

    @transaction.atomic()
    def populate_bbe_users(self):
        """

            :return:
        """
        bbe_account = SubAccount.objects.get(is_default=True)
        bbe_users = [
            ("psmithson", "CHLLL", "Canadian Helicopters"),
            ("sgray", "BBE", "BBE Ltd."),
            ("kdouglas", "TRUALL", "Truck-All Depot Ltd."),
            ("atomulescu", "MCKCANN", "McKesson Canada")
        ]

        print(Shipment.objects.count())
        print(SubAccount.objects.count())

        for user, bc_code, bc_name in bbe_users:
            print(f"{user} - {bc_code} - {bc_name}")

            shipments = Shipment.objects.select_related("sender").filter(
                username=user, creation_date__year=2022, bc_customer_code=""
            )

            print(shipments.count())

            for shipment in shipments:
                is_set = True

                if user == 'kdouglas':

                    if "Truckall" not in shipment.sender.company_name:
                        print("Not Setting")
                        is_set = False
                elif user == 'atomulescu':

                    if "M1" not in shipment.reference_one:
                        print("Not Setting")
                        is_set = False

                if is_set:
                    shipment.bc_customer_name = bc_name
                    shipment.bc_customer_code = bc_code
                    shipment.save()

    @transaction.atomic()
    def populate_leg_markups(self, bc_code: str, markup: str):
        """

            :return:
        """
        bbe_account = SubAccount.objects.get(is_default=True)

        legs = Leg.objects.select_related("shipment").filter(
            shipment__subaccount=bbe_account, shipment__bc_customer_code=bc_code, shipment__creation_date__year=2022
        )

        print(legs.count())

        for leg in legs:
            print(f"{leg.leg_id} - {leg.shipment.bc_customer_code}")
            leg.markup = Decimal(markup)
            leg.save()


