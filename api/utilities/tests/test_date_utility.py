"""
    Title: Date Utility Unit Tests
    Description: Unit Tests for the Date Utility. Test Everything, think of edge cases.
    Created: August 12, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import datetime

from django.test import TestCase

from api.utilities.date_utility import DateUtility


class DateUtilityTests(TestCase):

    def test_class_initialization_empty(self):
        record = DateUtility()
        self.assertIsInstance(record, DateUtility)
        self.assertIsInstance(record._pickup_date, datetime.datetime)

    def test_class_initialization_full(self):
        record = DateUtility(pickup={"date": "2021-08-09", "start": "10:00", "end": "16:00"})
        self.assertIsInstance(record, DateUtility)
        self.assertIsInstance(record._pickup_date, datetime.datetime)

    def test_get_estimated_delivery_monday(self):
        record = DateUtility(pickup={"date": "2021-08-09", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=4, country="CA", province="AB")
        self.assertEqual(estimated, "2021-08-13T00:00:00")
        self.assertEqual(transit, 4)

    def test_get_estimated_delivery_friday(self):
        record = DateUtility(pickup={"date": "2021-08-13", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-08-16T00:00:00")
        self.assertEqual(transit, 1)

    def test_get_estimated_delivery_saturday(self):
        record = DateUtility(pickup={"date": "2021-08-14", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-08-16T00:00:00")
        self.assertEqual(transit, 1)

    def test_get_estimated_delivery_sunday(self):
        record = DateUtility(pickup={"date": "2021-08-15", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-08-16T00:00:00")
        self.assertEqual(transit, 1)

    def test_get_estimated_delivery_friday_before_monday_holiday(self):
        record = DateUtility(pickup={"date": "2021-07-30", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-08-03T00:00:00")
        self.assertEqual(transit, 2)

    def test_get_estimated_delivery_monday_holiday(self):
        record = DateUtility(pickup={"date": "2021-08-01", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-08-03T00:00:00")
        self.assertEqual(transit, 2)

    def test_get_estimated_delivery_friday_holiday(self):
        record = DateUtility(pickup={"date": "2021-01-01", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-01-04T00:00:00")
        self.assertEqual(transit, 1)

    def test_get_estimated_delivery_thursday_before_friday_holiday(self):
        record = DateUtility(pickup={"date": "2020-12-31", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-01-04T00:00:00")
        self.assertEqual(transit, 2)

    def test_get_estimated_delivery_monday_friday_holiday(self):
        record = DateUtility(pickup={"date": "2021-04-02", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-04-06T00:00:00")
        self.assertEqual(transit, 2)

    def test_get_estimated_delivery_thursday_before_monday_friday_holiday(self):
        record = DateUtility(pickup={"date": "2021-04-01", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=1, country="CA", province="AB")
        self.assertEqual(estimated, "2021-04-06T00:00:00")
        self.assertEqual(transit, 3)

    def test_get_estimated_delivery_negative_tranit(self):
        record = DateUtility(pickup={"date": "2021-04-01", "start": "10:00", "end": "16:00"})
        estimated, transit = record.get_estimated_delivery(transit=-1, country="CA", province="AB")
        self.assertEqual(estimated, "0001-01-01T00:00:00")
        self.assertEqual(transit, -1)

    def test_next_business_day(self):
        record = DateUtility()
        date = record.next_business_day(country_code="CA", prov_code="AB", in_date=datetime.datetime.strptime("2021-08-13", "%Y-%m-%d"))
        self.assertEqual(date, "2021-08-16")

    def test_next_business_day_monday_holiday(self):
        record = DateUtility()
        date = record.next_business_day(country_code="CA", prov_code="AB", in_date=datetime.datetime.strptime("2021-08-02", "%Y-%m-%d"))
        self.assertEqual(date, "2021-08-03")

    def test_next_business_day_friday_holiday(self):
        record = DateUtility()
        date = record.next_business_day(country_code="CA", prov_code="AB", in_date=datetime.datetime.strptime("2021-01-01", "%Y-%m-%d"))
        self.assertEqual(date, "2021-01-04")

    def test_next_business_saturday(self):
        record = DateUtility()
        date = record.next_business_day(country_code="CA", prov_code="AB", in_date=datetime.datetime.strptime("2021-08-14", "%Y-%m-%d"))
        self.assertEqual(date, "2021-08-16")

    def test_next_business_sunday(self):
        record = DateUtility()
        date = record.next_business_day(country_code="CA", prov_code="AB", in_date=datetime.datetime.strptime("2021-08-15", "%Y-%m-%d"))
        self.assertEqual(date, "2021-08-16")

    def test_next_business_weekday(self):
        record = DateUtility()
        date = record.next_business_day(country_code="CA", prov_code="AB", in_date=datetime.datetime.strptime("2021-08-11", "%Y-%m-%d"))
        self.assertEqual(date, "2021-08-12")
