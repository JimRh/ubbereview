import copy
from collections import OrderedDict

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from api.exceptions.project import ViewException
from api.models import SubAccount, PackageType
from api.serializers_v3.common.package_type_serializer import PackageTypeSerializer


class PackageTypeSerializerTests(TestCase):

    fixtures = [
        "carriers",
        "countries",
        "provinces",
        "user",
        "group",
        "contact",
        "addresses",
        "markup",
        "account",
        "subaccount",
        "package_type"
    ]

    def setUp(self):
        self.sub_account = SubAccount.objects.first()

        self.package_json = {
            "account_name": "gobox",
            "username": "gobox",
            "account_number": "8cd0cae7-6a22-4477-97e1-a7ccfbed3e01",
            "code": "DGSKID",
            "name": "Dangerous Goods Skid",
            "min_overall_dims": "0.00",
            "max_overall_dims": "10000.00",
            "min_weight": "0.00",
            "max_weight": "10000.00",
            "is_common": True,
            "is_dangerous_good": True,
            "is_pharma": True,
            "is_active": True,
            "carrier": [
                17,
                24,
                9,
                19,
                4,
                33
            ]
        }

    def test_get_all(self):
        expected = [OrderedDict([('id', 6), ('account_name', 'gobox'), ('code', 'BUNDLES'), ('name', 'Bundles'), ('min_overall_dims', '0.00'), ('max_overall_dims', '1000.00'), ('min_weight', '0.00'), ('max_weight', '1000.00'), ('is_common', False), ('is_dangerous_good', True), ('is_pharma', True), ('is_active', True), ('carrier', [17])]), OrderedDict([('id', 3), ('account_name', 'gobox'), ('code', 'CONTAINER'), ('name', 'Container'), ('min_overall_dims', '0.00'), ('max_overall_dims', '10000.00'), ('min_weight', '0.00'), ('max_weight', '20000.00'), ('is_common', False), ('is_dangerous_good', True), ('is_pharma', True), ('is_active', True), ('carrier', [17])])]
        package_types = PackageType.objects.all()
        serializer = PackageTypeSerializer(package_types[:2], many=True)
        ret = serializer.data
        self.assertIsInstance(ret, list)
        self.assertListEqual(expected, ret)

    def test_get_one_first(self):
        expected = {'id': 6, 'account_name': 'gobox', 'code': 'BUNDLES', 'name': 'Bundles', 'min_overall_dims': '0.00', 'max_overall_dims': '1000.00', 'min_weight': '0.00', 'max_weight': '1000.00', 'is_common': False, 'is_dangerous_good': True, 'is_pharma': True, 'is_active': True, 'carrier': [17]}
        package_type = PackageType.objects.first()
        serializer = PackageTypeSerializer(package_type, many=False)
        ret = serializer.data
        self.assertIsInstance(ret, dict)
        self.assertDictEqual(ret, expected)

    def test_get_one_last(self):
        expected = {'id': 14, 'account_name': 'gobox', 'code': 'VEHICLE', 'name': 'Vehicle', 'min_overall_dims': '0.00', 'max_overall_dims': '20000.00', 'min_weight': '0.00', 'max_weight': '20000.00', 'is_common': False, 'is_dangerous_good': True, 'is_pharma': True, 'is_active': True, 'carrier': [17]}
        package_type = PackageType.objects.last()
        serializer = PackageTypeSerializer(package_type, many=False)
        ret = serializer.data

        self.assertIsInstance(ret, dict)
        self.assertDictEqual(ret, expected)

    def test_create(self):
        expected = {'account_name': 'gobox', 'code': 'DGSKID', 'name': 'Dangerous Goods Skid', 'min_overall_dims': '0.00', 'max_overall_dims': '10000.00', 'min_weight': '0.00', 'max_weight': '10000.00', 'is_common': True, 'is_dangerous_good': True, 'is_pharma': True, 'is_active': True, 'carrier': [17, 24, 9, 19, 4, 33]}

        serializer = PackageTypeSerializer(data=self.package_json, many=False)

        if serializer.is_valid():
            serializer.validated_data["username"] = self.package_json["username"]
            serializer.create(validated_data=serializer.validated_data)
            ret = serializer.data
            self.assertIsInstance(ret, dict)
            self.assertDictEqual(expected, ret)

    def test_create_fail(self):
        copied = copy.deepcopy(self.package_json)
        copied["account_number"] = '8cd0cae7-6a22-4477-97e1-a7ccfbed3e09'

        serializer = PackageTypeSerializer(data=copied, many=False)

        with self.assertRaises(ViewException) as e:

            if serializer.is_valid():
                serializer.validated_data["account"]["user"]["username"] = "daskdmmdk"
                serializer.create(validated_data=serializer.validated_data)

        self.assertEqual(e.exception.message, "Package Types: Account not found.")
