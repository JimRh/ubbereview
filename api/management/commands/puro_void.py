
from django.core.management import BaseCommand

from api.apis.carriers.purolator.courier.purolator_api import PurolatorApi
from api.models import SubAccount, Carrier, CarrierAccount


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('account_number', type=str, help='Account Number in ubbe')
        parser.add_argument('tracking', type=str, help='Puro Tracking Number in ubbe')
        parser.add_argument('--pickup', type=str, help='Puro Pickup Number in ubbe.')

    def handle(self, *args, **options) -> None:
        """

            :param args:
            :param options:
            :return:
        """

        sub_account = SubAccount.objects.get(subaccount_number=options["account_number"])

        if not sub_account:
            raise Exception

        carrier = Carrier.objects.get(code=11)
        carrier_account = CarrierAccount.objects.get(subaccount=sub_account, carrier=carrier)
        carrier_two = Carrier.objects.get(code=734)
        carrier_account_two = CarrierAccount.objects.get(subaccount=sub_account, carrier=carrier_two)

        ubbe_request = {
            'order_number': options["tracking"],
            'service_code': "Cancel",
            'tracking_number': options["tracking"],
            'pickup_id': options["pickup"],
            "objects": {
                'sub_account': sub_account,
                'user': sub_account,
                'carrier_accounts': {
                    11: {
                        'account': carrier_account,
                        "carrier": carrier
                    },
                    734: {
                        'account': carrier_account_two,
                        "carrier": carrier_two
                    }
                },
            }
        }

        try:
            puro = PurolatorApi(ubbe_request=ubbe_request).cancel()
            self.stderr.write(
                self.style.SUCCESS(f'Purolator Tracking: {options["tracking"]} - Voided: {puro["is_void"]}')
            )

            if options["pickup"]:
                pickup = PurolatorApi(ubbe_request=ubbe_request).cancel_pickup()
                self.stderr.write(
                    self.style.SUCCESS(f'Purolator Pickup: {options["pickup"]} - Voided: {pickup["is_void"]}')
                )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Purolator Void Failed: {str(e)}'))
