import datetime
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import BaseCommand

from api.apis.carriers.tst_cf_express.endpoints.tst_cf_track_v2 import TstCfExpressTrack
from api.globals.carriers import MANITOULIN
from api.globals.carriers import TST
from api.models import Leg
from api.models import Shipment, SubAccount, Carrier, CarrierAccount


class Command(BaseCommand):
    _street_types = {
        "abbey",
        "end",
        "montéé",
        "village",
        "acres",
        "esplanade",
        "mount",
        "villas",
        "allée",
        "estates",
        "mountain",
        "vista",
        "alley",
        "expressway",
        "parade",
        "voie",
        "autoroute",
        "extension",
        "parc",
        "walk",
        "avenue",
        "field",
        "park",
        "way",
        "avenue",
        "forest",
        "parkway",
        "wharf",
        "bay",
        "freeway",
        "passage",
        "wood",
        "beach",
        "front",
        "path",
        "wynd",
        "bend",
        "gardens",
        "pathway",
        "boulevard",
        "gate",
        "pines",
        "branch",
        "glade",
        "place",
        "by-pass",
        "by pass",
        "glen",
        "plateau",
        "campus",
        "green",
        "plaza",
        "cape",
        "grounds",
        "point",
        "carré",
        "grove",
        "pointe",
        "carrefour",
        "harbour",
        "port",
        "centre",
        "heath",
        "private",
        "cercle",
        "height",
        "promenade",
        "chase",
        "heights",
        "quai",
        "chemin",
        "highlands",
        "quay",
        "circle",
        "highway",
        "ramp",
        "circuit",
        "hill",
        "rang",
        "close",
        "hollow",
        "ridge",
        "common",
        "île",
        "rise",
        "concession",
        "impasse",
        "road",
        "corners",
        "inlet",
        "route",
        "côte",
        "island",
        "row",
        "cour",
        "key",
        "rue",
        "cours",
        "knoll",
        "ruelle",
        "court",
        "landing",
        "run",
        "cove",
        "lane",
        "sentier",
        "crest",
        "limits",
        "square",
        "crescent",
        "line",
        "street",
        "croissant",
        "link",
        "subdivision",
        "crossing",
        "lookout",
        "terrace",
        "cul-de-sac",
        "cul de sac",
        "loop",
        "terrasse",
        "dale",
        "mall",
        "townline",
        "dell",
        "manor",
        "trail",
        "diversion",
        "maze",
        "turnabout",
        "downs",
        "meadow",
        "vale",
        "drive",
        "mews",
        "view",
    }

    @staticmethod
    def mark_delivered(sub_account: str, start_date: datetime, end_date: datetime):
        shipments = Shipment.objects.filter(
            subaccount__subaccount_number=sub_account,
            is_delivered=False,
            creation_date__range=[start_date, end_date]
        )

        for shipment in shipments:

            for leg in shipment.leg_shipment.all():
                leg.is_delivered = True
                leg.is_pickup_overdue = False
                leg.is_overdue = False
                leg.save()

            shipment.is_delivered = True
            shipment.save()

    def _get_street_info(self, address: str) -> tuple:
        """
        Get street number andd street type.
        :param address:
        :return:
        """
        address = address.replace("-", " ") + " 0"
        components = []
        street_type = "road"

        for i, com in enumerate(address.split(" ")):
            if com.isdigit():
                components.append(com)

            if com.lower() in self._street_types:
                street_type = com
            elif com.lower() in self.s:
                street_type = self.s[com.lower()]

        return components[0][:6], street_type.title()

    def handle(self, *args, **options) -> None:
        print("**************************** KC TEST ****************************")
        # To mark shipments as delivered for a date range
        # self.mark_delivered(
        #     sub_account="2c0148a6-69d7-4b22-88ed-231a084d2db9",
        #     start_date=datetime.datetime.strptime("2017-07-01", "%Y-%m-%d"),
        #     end_date=datetime.datetime.strptime("2021-05-01", "%Y-%m-%d")
        # )

        sub_account = SubAccount.objects.get(subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01")
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=TST)
        carrier_account = CarrierAccount.objects.get(subaccount=sub_account, carrier=carrier)

        request = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "burnaby",
                "company_name": "BBE Ottawa",
                "name": "BBE Ottawa",
                "phone": "7808906811",
                "email": "developer@bbex.com",
                "country": "CA",
                "postal_code": "V5A4W4",
                "province": "BC",
                "is_residential": False,
                "has_shipping_bays": True
            },
            "destination": {
                "address": "1540 Airport Road",
                "city": "edmonton international airport",
                "company_name": "BBE Ottawa",
                "name": "BBE Ottawa",
                "phone": "7808906811",
                "email": "developer@bbex.com",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "has_shipping_bays": True,
                "is_residential": False,
            },
            'pickup': {
                "date": datetime.datetime.strptime("2022-06-27", "%Y-%m-%d").date(),
                "start_time": "10:00",
                "end_time": "16:00"
            },
            "packages": [
                {
                    "package_type": "SKID",
                    "freight_class": "70.00",
                    "quantity": 1,
                    "length": "48",
                    "width": "48",
                    "height": "48",
                    "weight": "100",
                    'imperial_length': Decimal('48'),
                    'imperial_width': Decimal('48'),
                    'imperial_height': Decimal('48'),
                    'imperial_weight': Decimal('100'),
                    'description': 'TEST',
                    'is_dangerous_good': False,
                    'volume': Decimal('0.00119102'),
                }
            ],
            "objects": {
                'sub_account': sub_account,
                'user': user,
                'carrier_accounts': {
                    MANITOULIN: {
                        'account': carrier_account,
                        "carrier": carrier
                    }
                },
            },
            "carrier_options": [],
            'reference_one': 'SOMEREF',
            'reference_two': 'SOMEREF',
            'order_number': "UB1234567890",
            'service_code': "GD|2CAR220252DB676B6164",
            "total_weight_imperial": 10000,
            "is_dangerous_goods": False,
            "rock_solid_service_value": "A",
            "rock_solid_service_guarantee": "True"
        }

