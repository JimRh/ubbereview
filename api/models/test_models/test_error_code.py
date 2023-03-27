from uuid import UUID

from django.test import TestCase

from api.models import ErrorCode


class ErrorCodeTests(TestCase):

    def setUp(self):

        self.error_code_json = {
            "system": "UBAPI",
            "source": "Admin",
            "type": "ErrorCode",
            "code": "1000",
            "name": "Error on Table",
            "actual_message": "Table Error",
            "solution": "My solution goes here.",
            "location": "error_code.py line 123"
        }

    def test_create_empty(self):
        record = ErrorCode.create()
        self.assertIsInstance(record, ErrorCode)

    def test_create_full(self):
        record = ErrorCode.create(self.error_code_json)
        self.assertIsInstance(record, ErrorCode)

    def test_set_values(self):
        record = ErrorCode.create()
        record.set_values(self.error_code_json)
        self.assertEqual(record.name, "Error on Table")

    def test_all_fields_verbose(self):
        record = ErrorCode(**self.error_code_json)
        self.assertEqual(record.system, "UBAPI")
        self.assertEqual(record.source, "Admin")
        self.assertEqual(record.type, "ErrorCode")
        self.assertEqual(record.code, "1000")
        self.assertEqual(record.name, "Error on Table")
        self.assertEqual(record.actual_message, "Table Error")
        self.assertEqual(record.solution, "My solution goes here.")
        self.assertEqual(record.location, "error_code.py line 123")

    def test_repr(self):
        expected = '< ErrorCode (UBAPI, 1000, Error on Table)) >'
        record = ErrorCode.create(self.error_code_json)
        self.assertEqual(expected, repr(record))

    def test_str(self):
        expected = 'UBAPI-ErrorCode-1000-Error on Table'
        record = ErrorCode.create(self.error_code_json)
        self.assertEqual(expected, str(record))

    def test_save(self):
        record = ErrorCode.create(self.error_code_json)
        record.save()
        self.assertIsInstance(record, ErrorCode)
