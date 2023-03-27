from time import sleep

from django.core.management import BaseCommand
from django.db import connection, transaction

from api.apis.carriers.skyline.skyline_interline_v3 import SkylineInterline
from api.exceptions.project import ViewException
from api.globals.carriers import CAN_NORTH
from api.models import SubAccount, Airbase, CNInterline


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('account_number', type=str, help='Account Number.')
        parser.add_argument('skyline', type=str, help='Skyline Api.')
        parser.add_argument('function', type=str, help='Skyline Api.')

    def handle(self, *args, **options) -> None:

        try:
            sub_account = SubAccount.objects.get(subaccount_number=options["account_number"])
        except ViewException as e:
            connection.close()
            print(f"{e.code}\n{e.message}\n{str(e.errors)}")
            return

        if options["function"] == "interline":
            self.interline_setup(
                skyline_key=options["skyline"],
                sub_account=sub_account
            )

    @transaction.atomic()
    def interline_setup(self, skyline_key, sub_account):
        """
            The function will configure the database for canadian north interline routes.
            :param skyline_key: Skyline Api key.
            :param sub_account: ubbe account
            :return:
        """

        interline_locations = [
            "LAK",
            "YGH",
            "YCK",
            "ZFN",
            "YWJ",
            "ZFM",
            "YPC",
            "YSY",
            "YHI",
            "YSM",
            "XGR",
            "YPJ",
            "YTQ",
            "YKG",
            "YQC",
            "YWB",
            "YZG",
            "YIK",
            "AKV",
            "YPX",
            "YPH",
            "YUD",
            "YGW",
            "YKU",
            "YKL",
            "YZV",
            "YSK",
            "YWK"
        ]

        airbases = Airbase.objects.filter(carrier__code=CAN_NORTH).values_list("code", flat=True)

        all_lanes = []

        for airbase in airbases:
            self.stderr.write(self.style.SUCCESS(f'Start: {airbase}'))
            if not airbase:
                continue
            sleep(1)
            for interline in interline_locations:

                if airbase == "YEV" and interline in ["LAK", "ZFM", "YPC", "YSY", "YHI", "YCK"]:
                    continue
                elif airbase == "YVQ" and interline in ["YGH", "YCK", "ZFN", "YWJ"]:
                    continue
                elif airbase == "YZF" and interline in ["YSM"]:
                    continue
                elif airbase == "YVP" and interline in [
                    "XGR", "YPJ", "YTQ", "YKG", "YQC", "YWB", "YZG", "YIK", "AKV", "YPX", "YPH", "YUD", "YGW", "YKU",
                    "YKL", "YZV", "YSK", "YWK"
                ]:
                    continue

                try:
                    lanes = SkylineInterline(
                        api_key=skyline_key, sub_account=sub_account
                    ).get_interline(origin=airbase, destination=interline)
                except ViewException as e:
                    self.stderr.write(
                        self.style.ERROR(f'INTERLINE: {airbase} to {interline}: {e.message}')
                    )
                    continue

                all_lanes.extend(lanes)

            self.stderr.write(self.style.SUCCESS(f'End: {airbase}'))

        for lane in all_lanes:

            interline = CNInterline.create(param_dict=lane)
            interline.save()

