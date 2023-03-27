from unittest import mock
from unittest.mock import Mock

from django.test import TestCase

from api.models import Province, Country


class ProvinceTests(TestCase):
    fixtures = [
        "countries",
        "provinces"
    ]
    country = mock.Mock(spec=Country)
    country._state = Mock()
    province_json = {
        "name": "TEST",
        "code": "TT",
        "country": country
    }

    def test_create_empty(self):
        record = Province.create()
        self.assertIsInstance(record, Province)

    def test_create_full(self):
        record = Province.create(self.province_json)
        self.assertIsInstance(record, Province)

    def test_set_values(self):
        record = Province.create()
        record.set_values(self.province_json)
        self.assertEqual(record.name, "TEST")

    def test_all_fields_verbose(self):
        record = Province(**self.province_json)
        self.assertEqual(record.name, "TEST")
        self.assertEqual(record.code, "TT")
        self.assertIsInstance(record.country, Country)

    def test_repr(self):
        expected = "< Province (Alberta: AB, Canada: CA) >"
        record = Province.objects.get(code="AB", country__code="CA")
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = "Alberta, Canada"
        record = Province.objects.get(code="AB", country__code="CA")
        self.assertEqual(expected, str(record))

    def test_save(self):
        province_json = {
            "country": Country.objects.get(pk=1),
            "name": "thfdskj",
            "code": "%# $] tj"
        }
        province = Province(**province_json)

        province.save()

        self.assertIsInstance(province, Province)
        self.assertEqual(Province.objects.get(name="Thfdskj").code, "TJ")
