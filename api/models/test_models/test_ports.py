from django.test.testcases import TestCase

from api.models import Port, Address


class PortTests(TestCase):

    fixtures = [
        "countries",
        "provinces",
        "addresses",
        "ports"
    ]

    def setUp(self):

        self.port_json = {
            "name": "Edmonton",
            "address": Address.objects.first(),
            "code": "VIC"
        }

    def test_create_empty(self):
        record = Port.create()
        self.assertIsInstance(record, Port)

    def test_create_full(self):
        record = Port.create(self.port_json)
        self.assertIsInstance(record, Port)

    def test_set_values(self):
        record = Port.create()
        record.set_values(self.port_json)
        self.assertEqual(record.name, "Edmonton")

    def test_all_fields_verbose(self):
        record = Port(**self.port_json)
        address = Address.objects.first()
        self.assertEqual(record.name, "Edmonton")
        self.assertEqual(record.code, "VIC")
        self.assertIsInstance(record.address, Address)
        self.assertEqual(record.address, address)

    def test_separate_ports(self):
        expected = [{'name': 'VAN', 'code': 'VAN', 'selected': 'selected'}, {'name': 'Victoria', 'code': 'VIC', 'selected': ''}]
        port = Port.objects.first()
        port_list = Port.separate_ports(owned_ports=[port])

        self.assertEqual(expected, port_list)

    def test_repr(self):
        expected = "< Port (VAN - VAN: Inuvik, CA) >"
        port = Port.objects.first()
        self.assertEqual(expected, repr(port))

    def test_str(self):
        expected = "VAN - VAN: Inuvik, CA"
        port = Port.objects.first()
        self.assertEqual(expected, str(port))

    def test_repr_none(self):

        port = Port.create()
        port.name = "Test"
        port.code = "Test"

        expected = "< Port (Test - Test: None, None) >"

        self.assertEqual(expected, repr(port))

    def test_str_none(self):

        port = Port.create()
        port.name = "Test"
        port.code = "Test"

        expected = "Test - Test: None, None"
        self.assertEqual(expected, str(port))
