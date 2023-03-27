import datetime
from decimal import Decimal

from django.test import TestCase

from api.apis.services.carrier_options.mandatory import Mandatory
from api.exceptions.services import OptionNotApplicableException
from api.globals.carriers import MANITOULIN
from api.models import Carrier


class MandatoryTests(TestCase):
    fixtures = [
        "api",
        "carriers",
        "option_name",
        "carrier_option",
        "mandatory_option"
    ]

    def setUp(self):
        self.params = {
            "carrier_id": 535,
            "origin": {
                "country": "CA",
                "province": "AB",
                "city": "Aaaaaa"
            },
            "destination": {
                "country": "CA",
                "province": "AB",
                "city": "Aaaaaa"
            },
            "packages": [
                {
                    "length": Decimal("1.1"),
                    "width": Decimal("1.1"),
                    "height": Decimal("1000"),
                    "weight": Decimal("1.1"),
                    "un_number": "fdjskfl"
                }
            ]
        }

    def test_mandatory_charges_ab_carbon_tax_landtran_origin(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "AB"

        try:
            Mandatory._ca_province_carbon_tax(province="AB", request=self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_ab_carbon_tax_landtran_destination(self):
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "AB"

        try:
            Mandatory._ca_province_carbon_tax(province="AB", request=self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_ab_carbon_tax_landtran_both(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "AB"
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "AB"

        try:
            Mandatory._ca_province_carbon_tax(province="AB", request=self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_ab_carbon_tax_landtran_neither(self):
        try:
            Mandatory._ca_province_carbon_tax(province="AB", request=self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_ab_carbon_tax_other_origin(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "AB"

        try:
            Mandatory._ca_province_carbon_tax(province="AB", request=self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_ab_carbon_tax_other_destination(self):
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "AB"

        try:
            Mandatory._ca_province_carbon_tax(province="AB", request=self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_ab_carbon_tax_other_both(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "AB"
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "AB"

        try:
            Mandatory._ca_province_carbon_tax(province="AB", request=self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_ab_carbon_tax_other_neither(self):
        try:
            Mandatory._ca_province_carbon_tax(province="AB", request=self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_deh_cho_landtran_yellowknife_middle(self):
        self.params["destination"]["city"] = "Yellowknife"

        try:
            Mandatory()._deh_cho(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_deh_cho_landtran_yellowknife_min(self):
        self.params["destination"]["city"] = "Yellowknife"

        try:
            Mandatory()._deh_cho(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_deh_cho_landtran_yellowknife_max(self):
        self.params["destination"]["city"] = "Yellowknife"

        try:
            Mandatory()._deh_cho(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_deh_cho_other_yellowknife_middle(self):
        self.params["destination"]["city"] = "Yellowknife"

        try:
            Mandatory()._deh_cho(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_deh_cho_other_yellowknife_min(self):
        self.params["destination"]["city"] = "Yellowknife"

        try:
            Mandatory()._deh_cho(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_deh_cho_other_yellowknife_max(self):
        self.params["destination"]["city"] = "Yellowknife"

        try:
            Mandatory()._deh_cho(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_long_freight_manitoulin_under(self):
        try:
            Mandatory._long_freight(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_changes_long_freight_manitoulin_over(self):
        self.params["packages"][0]["length"] = Decimal("10000000000000000.00")

        try:
            Mandatory._long_freight(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_long_freight_other_under(self):
        try:
            Mandatory._long_freight(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_changes_long_freight_other_over(self):
        self.params["packages"][0]["length"] = Decimal("10000000000000000.00")

        try:
            Mandatory._long_freight(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_road_ban_manitoulin_origin(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NT"
        Mandatory._road_ban(self.params)

    def test_mandatory_charges_road_ban_manitoulin_destination(self):
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NT"

        try:
            Mandatory._road_ban(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_road_ban_manitoulin_both(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NT"
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NT"

        try:
            Mandatory._road_ban(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_road_ban_manitoulin_neither(self):
        with self.assertRaises(OptionNotApplicableException):
            Mandatory._road_ban(self.params)

    def test_mandatory_charges_road_ban_other_origin(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NT"

        try:
            Mandatory._road_ban(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_road_ban_other_destination(self):
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NT"

        try:
            Mandatory._road_ban(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_road_ban_other_both(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "AB"
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NT"

        try:
            Mandatory._road_ban(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_road_ban_other_neither(self):
        with self.assertRaises(OptionNotApplicableException):
            Mandatory._road_ban(self.params)

    def test_mandatory_charges_nl_ship_day_n_ross_origin_under(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NL"

        try:
            Mandatory._nl_ship(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_nl_ship_day_n_ross_destination_under(self):
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NL"

        try:
            Mandatory._nl_ship(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_nl_ship_day_n_ross_both_under(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NL"
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NL"

        with self.assertRaises(OptionNotApplicableException):
            Mandatory._nl_ship(self.params)

    def test_mandatory_charges_nl_ship_day_n_ross_neither_under(self):
        with self.assertRaises(OptionNotApplicableException):
            Mandatory._nl_ship(self.params)

    def test_mandatory_charges_nl_ship_day_n_ross_origin_over(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NL"

        try:
            Mandatory._nl_ship(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_nl_ship_day_n_ross_destination_over(self):
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NL"

        try:
            Mandatory._nl_ship(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_nl_ship_day_n_ross_both_over(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NL"
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NL"

        with self.assertRaises(OptionNotApplicableException):
            Mandatory._nl_ship(self.params)

    def test_mandatory_charges_nl_ship_day_n_ross_neither_over(self):
        with self.assertRaises(OptionNotApplicableException):
            Mandatory._nl_ship(self.params)

    def test_mandatory_charges_nl_ship_other_origin_under(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NL"

        try:
            Mandatory._nl_ship(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_nl_ship_other_destination_under(self):
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NL"

        try:
            Mandatory._nl_ship(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_nl_ship_other_both_under(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NL"
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NL"

        with self.assertRaises(OptionNotApplicableException):
            Mandatory._nl_ship(self.params)

    def test_mandatory_charges_nl_ship_other_neither_under(self):
        with self.assertRaises(OptionNotApplicableException):
            Mandatory._nl_ship(self.params)

    def test_mandatory_charges_nl_ship_other_origin_over(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NL"

        try:
            Mandatory._nl_ship(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_nl_ship_other_destination_over(self):
        self.params["carrier_id"] = 1
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NL"

        try:
            Mandatory._nl_ship(self.params)
        except OptionNotApplicableException as e:
            self.fail(e)

    def test_mandatory_charges_nl_ship_other_both_over(self):
        self.params["origin"]["country"] = "CA"
        self.params["origin"]["province"] = "NL"
        self.params["destination"]["country"] = "CA"
        self.params["destination"]["province"] = "NL"

        with self.assertRaises(OptionNotApplicableException):
            Mandatory._nl_ship(self.params)

    def test_mandatory_charges_nl_ship_other_neither_over(self):
        with self.assertRaises(OptionNotApplicableException):
            Mandatory._nl_ship(self.params)

    def test_mandatory_charges_check(self):
        expected = [{
            'name': 'AB Carbon Tax',
            'cost': Decimal("1.25"),
            'percentage': Decimal('1.25'),
        }]
        carrier = Carrier.objects.get(code=127)
        ret = Mandatory().get_calculated_option_costs(carrier, self.params, Decimal("100.00"), Decimal("100.00"),
                                                      Decimal("100.00"),
                                                      datetime.datetime.today())
        self.assertListEqual(expected, ret)
