from django.test import TestCase

from api.models import Country


class CountryTests(TestCase):
    fixtures = [
        "countries"
    ]
    country_json = {
        "name": "TEST",
        "code": "TT",
        "_iata_name": "TEST"
    }

    def fake_fetch_iata_name(self):
        self._iata_name = "TEST2"

    def test_create_empty(self):
        record = Country.create()
        self.assertIsInstance(record, Country)

    def test_create_full(self):
        record = Country.create(self.country_json)
        self.assertIsInstance(record, Country)

    def test_set_values(self):
        record = Country.create()
        record.set_values(self.country_json)
        self.assertEqual(record.name, "TEST")

    def test_all_fields_verbose(self):
        record = Country.create(self.country_json)
        self.assertEqual(record.name, "TEST")
        self.assertEqual(record.code, "TT")
        self.assertEqual(record._iata_name, "TEST")

    def test_repr(self):
        expected = "< Country (TEST: TT) >"
        record = Country.create(self.country_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "TEST"
        record = Country.create(self.country_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        country_json = {
            "name": "` m-=nb ",
            "code": "!@mn[ ",
            "currency_name": "ABC",
            "currency_code": "XYZ",
            "_iata_name": "TEST"
        }
        country = Country(**country_json)

        country.save()
        self.assertIsInstance(country, Country)
        self.assertEqual(Country.objects.get(name=country_json['name'].title()).code, "MN")
