
from django.core.management import BaseCommand
from django.db import connection

from api.apis.carriers.skyline.skyline_accounts_v3 import SkylineAccounts
from api.exceptions.project import ViewException
from api.models import SubAccount
from api.utilities import utilities


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('account_number', type=str, help='Account Number.')
        parser.add_argument('skyline', type=str, help='Skyline Api.')

    def handle(self, *args, **options) -> None:

        try:
            sub_account = SubAccount.objects.get(subaccount_number=options["account_number"])
        except ViewException as e:
            connection.close()
            print(f"{e.code}\n{e.message}\n{str(e.errors)}")
            return

        sky = SkylineAccounts(api_key=options["skyline"], sub_account=sub_account)
        sky.accounts()
