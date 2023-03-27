import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from api.apis.services.carrier_options.carrier_options import CarrierOptions
from api.apis.services.carrier_options.option_utilities import min_max_update, date_check, check_carrier
from api.exceptions.services import CarrierOptionException
from api.models import Carrier, OptionName, CarrierOption


class CarrierOptionsTests(TestCase):
    fixtures = [
        "carriers",
        "option_name",
        "carrier_option"
    ]

    def setUp(self):
        self.maxDiff = None

    def test_carrier_options_min_max_function_middle(self):
        val = min_max_update(25, 20, 30)
        self.assertEqual(25, val)

    def test_carrier_options_min_max_function_over(self):
        val = min_max_update(35, 20, 30)
        self.assertEqual(30, val)

    def test_carrier_options_min_max_function_under(self):
        val = min_max_update(15, 20, 30)
        self.assertEqual(20, val)

    def test_carrier_options_date_function_ok(self):
        date = datetime.datetime.today()
        date_check(date, date - datetime.timedelta(days=3), date + datetime.timedelta(days=3))

    def test_carrier_options_date_function_early(self):
        date = datetime.datetime.today()
        with self.assertRaises(CarrierOptionException):
            date_check(date, date + datetime.timedelta(days=1), date + datetime.timedelta(days=7))

    def test_carrier_options_date_function_late(self):
        date = datetime.datetime.today()
        with self.assertRaises(CarrierOptionException):
            date_check(date, date - datetime.timedelta(days=7), date - datetime.timedelta(days=1))

    def test_carrier_options_date_function_ok_miss_start(self):
        date = datetime.datetime.today()
        date_check(date, None, date + datetime.timedelta(days=3))

    def test_carrier_options_date_function_late_miss_start(self):
        date = datetime.datetime.today()
        with self.assertRaises(CarrierOptionException):
            date_check(date, None, date - datetime.timedelta(days=1))

    def test_carrier_options_date_function_ok_miss_end(self):
        date = datetime.datetime.today()
        date_check(date, date - datetime.timedelta(days=3), None)

    def test_carrier_options_date_function_early_miss_end(self):
        date = datetime.datetime.today()
        with self.assertRaises(CarrierOptionException):
            date_check(date, date + datetime.timedelta(days=1), None)

    def test_carrier_options_carrier_check_id(self):
        carrier = check_carrier(535)
        self.assertIsInstance(carrier, Carrier)
        self.assertEqual(5, carrier.id)

    def test_carrier_options_carrier_check_instance(self):
        input_carrier = Carrier.objects.get(pk=1)
        carrier = check_carrier(input_carrier)
        self.assertEqual(input_carrier, carrier)

    def test_carrier_options_carrier_check_garbage(self):
        with self.assertRaises(CarrierOptionException):
            # noinspection PyTypeChecker
            check_carrier("hgfd")

    def test_carrier_options_evaluate_actual(self):
        val = CarrierOptions().get_calculated_option_costs(535,
                                                           [1],
                                                           Decimal("50"),
                                                           Decimal("10"),
                                                           Decimal("100"),
                                                           datetime.datetime.today())

        expected = [{'name': 'Delivery Appointment', 'cost': Decimal('45.90'), 'percentage': Decimal('0.00')}]

        self.assertListEqual(expected, val)

    def test_carrier_options_evaluate_actual_add(self):
        val = CarrierOptions().get_calculated_option_costs(535,
                                                           [3],
                                                           Decimal("50"),
                                                           Decimal("10"),
                                                           Decimal("100"),
                                                           datetime.datetime.today())

        expected = [{'name': 'Power Tailgate', 'cost': Decimal('62.80'), 'percentage': Decimal('0.00')}]

        self.assertListEqual(expected, val)

    def test_carrier_options_evaluate_actual_multiply_whole(self):
        val = CarrierOptions().get_calculated_option_costs(535,
                                                           [5],
                                                           Decimal("50"),
                                                           Decimal("10"),
                                                           Decimal("100"),
                                                           datetime.datetime.today())
        self.maxDiff = None
        expected = [{'name': 'Refrigerated Truck', 'cost': Decimal('33.65'), 'percentage': Decimal('0.15')}]

        self.assertListEqual(expected, val)

    def test_carrier_options_evaluate_actual_multiply_decimal(self):
        val = CarrierOptions().get_calculated_option_costs(535,
                                                           [3],
                                                           Decimal("50"),
                                                           Decimal("10"),
                                                           Decimal("100"),
                                                           datetime.datetime.today())

        expected = [{'name': 'Power Tailgate', 'cost': Decimal('62.80'), 'percentage': Decimal('0.00')}]

        self.assertListEqual(expected, val)

    def test_carrier_options_evaluate_multiple(self):
        val = CarrierOptions().get_calculated_option_costs(535,
                                                           [1, 3],
                                                           Decimal("50"),
                                                           Decimal("10"),
                                                           Decimal("100"),
                                                           datetime.datetime.today())

        expected = [{'name': 'Delivery Appointment', 'cost': Decimal('45.90'), 'percentage': Decimal('0.00')}, {'name': 'Power Tailgate', 'cost': Decimal('62.80'), 'percentage': Decimal('0.00')}]

        self.assertListEqual(expected, val)

    def test_carrier_options_check_carrier_has_options_true(self):
        val = CarrierOptions().check_carrier_has_options(535, [1])
        self.assertTrue(val)

    def test_carrier_options_check_carrier_has_options_false(self):
        val = CarrierOptions().check_carrier_has_options(1, [1, 2, 3, 4])
        self.assertFalse(val)

    def test_carrier_options_check_carrier_save_new(self):
        carrier = Carrier.objects.get(pk=1)
        option = OptionName.objects.get(pk=2)
        car_opt = CarrierOption()
        car_opt.carrier = carrier
        car_opt.option = option
        car_opt.evaluation_expression = "asdf"
        car_opt.carrier_option_id = "Test"
        try:
            car_opt.save()
        except ValidationError:
            raise AssertionError("Should not raise validation error")

    def test_carrier_options_check_carrier_save_dup(self):
        carrier = Carrier.objects.get(pk=5)
        option = OptionName.objects.get(pk=1)
        car_opt = CarrierOption()
        car_opt.carrier = carrier
        car_opt.option = option
        car_opt.evaluation_expression = "asdf"
        car_opt.carrier_option_id = "Test"

        with self.assertRaises(ValidationError):
            car_opt.save()
