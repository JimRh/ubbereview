"""
    Title: YRC Rate Unit Tests
    Description: Unit Tests for the YRC Rate. Test Everything.
    Created: January 18, 2020
    Author: Carmichael, Kenneth
    Edited By:
    Edited Date:
"""
import copy
import datetime
from decimal import Decimal

import xmltodict
from django.contrib.auth.models import User
from django.test import TestCase

from api.apis.carriers.abf_freight.endpoints.abf_rate import ABFRate
from api.exceptions.project import RateException
from api.globals.carriers import ABF_FREIGHT
from api.models import SubAccount, Carrier, CarrierAccount


class ABFRateTests(TestCase):
    fixtures = [
        "api",
        "carriers",
        "countries",
        "provinces",
        "addresses",
        "contact",
        "user",
        "group",
        "markup",
        "carrier_markups",
        "account",
        "subaccount",
        "encryted_messages",
        "carrier_account",
        "northern_pd",
        "skyline_account",
        "nature_of_goods",
    ]

    def setUp(self):
        sub_account = SubAccount.objects.get(
            subaccount_number="8cd0cae7-6a22-4477-97e1-a7ccfbed3e01"
        )
        user = User.objects.get(username="gobox")
        carrier = Carrier.objects.get(code=ABF_FREIGHT)
        carrier_account = CarrierAccount.objects.get(
            subaccount=sub_account, carrier=carrier
        )

        self.request = {
            "origin": {
                "address": "1540 Airport Road",
                "city": "Edmonton International Airport",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "T9E0V6",
                "province": "AB",
                "is_residential": False,
                "has_shipping_bays": True,
            },
            "destination": {
                "address": "140 THAD JOHNSON PRIV Suite 7",
                "city": "Ottawa",
                "company_name": "BBE Ottawa",
                "country": "CA",
                "postal_code": "K1V0R1",
                "province": "ON",
                "has_shipping_bays": True,
                "is_residential": False,
            },
            "pickup": {
                "date": datetime.datetime.strptime("2021-08-12", "%Y-%m-%d").date(),
                "start_time": "10:00",
                "end_time": "16:00",
            },
            "packages": [
                {
                    "description": "Test",
                    "package_type": "SKID",
                    "freight_class": "70.00",
                    "quantity": 1,
                    "length": "48",
                    "width": "48",
                    "height": "48",
                    "weight": "100",
                    "imperial_length": Decimal("48"),
                    "imperial_width": Decimal("48"),
                    "imperial_height": Decimal("48"),
                    "imperial_weight": Decimal("100"),
                }
            ],
            "objects": {
                "sub_account": sub_account,
                "user": user,
                "carrier_accounts": {
                    ABF_FREIGHT: {"account": carrier_account, "carrier": carrier}
                },
            },
            "carrier_options": [],
        }

        self.response_us_ltl = xmltodict.parse(
            xml_input='<?xml version="1.0"?><ABF><QUOTEID>LF3Q761752</QUOTEID><CHARGE>1458.04</CHARGE><DISCOUNTPERCENTAGE></DISCOUNTPERCENTAGE><ADVERTISEDTRANSIT>1 Day</ADVERTISEDTRANSIT><ADVERTISEDDUEDATE>2022-06-21</ADVERTISEDDUEDATE><SHIPDATE>2022-06-20</SHIPDATE><EFFECTIVEDATE>2022-06-20</EFFECTIVEDATE><EXPIRATIONDATE>2022-06-26</EXPIRATIONDATE><CODFEE></CODFEE><TPDELIVERYCHARGE></TPDELIVERYCHARGE><TPCHARGEPERBOX></TPCHARGEPERBOX><ORIGTERMINFO><ORIGTERMADDRESS>4242 IRVING BLVD</ORIGTERMADDRESS><ORIGTERMCITY>DALLAS</ORIGTERMCITY><ORIGTERMSTATE>TX</ORIGTERMSTATE><ORIGTERMZIP>75247</ORIGTERMZIP><ORIGTERMPHONE>2146880448</ORIGTERMPHONE><TYPE>DIRECT</TYPE></ORIGTERMINFO><DESTTERMINFO><DESTTERMADDRESS>4410 S. JACKSON</DESTTERMADDRESS><DESTTERMCITY>TULSA</DESTTERMCITY><DESTTERMSTATE>OK</DESTTERMSTATE><DESTTERMZIP>74107</DESTTERMZIP><DESTTERMPHONE>9184460122</DESTTERMPHONE><TYPE>DIRECT</TYPE></DESTTERMINFO><INCLUDEDCHARGES><FUELSURCHARGE>Included</FUELSURCHARGE><LIFTGATEGROUNDPICKUP></LIFTGATEGROUNDPICKUP><INSIDEPICKUP></INSIDEPICKUP><LIMITEDACCESSPICKUP></LIMITEDACCESSPICKUP><RESIDENTIALPICKUP></RESIDENTIALPICKUP><CONSTRUCTIONDELIVERY></CONSTRUCTIONDELIVERY><LIFTGATEGROUNDDELIVERY></LIFTGATEGROUNDDELIVERY><INSIDEDELIVERY></INSIDEDELIVERY><LIMITEDACCESSDELIVERY></LIMITEDACCESSDELIVERY><RESIDENTIALDELIVERY></RESIDENTIALDELIVERY><FLATBEDDELIVERY></FLATBEDDELIVERY><ARRIVALNOTIFICATION></ARRIVALNOTIFICATION><CAPACITYLOAD></CAPACITYLOAD><CUSTOMSINBONDFREIGHT></CUSTOMSINBONDFREIGHT><EXCESSLIABILITY></EXCESSLIABILITY><OVERDIMENSION></OVERDIMENSION><SINGLESHIPMENT></SINGLESHIPMENT><SORTSEGREGATE></SORTSEGREGATE><SHIPPERLOAD></SHIPPERLOAD><CONSIGNEEUNLOAD></CONSIGNEEUNLOAD><PALLETIZEDSHIPMENT></PALLETIZEDSHIPMENT><HAZARDOUSSHIPMENT></HAZARDOUSSHIPMENT><DELIVERON></DELIVERON><DELIVERBY></DELIVERBY><TRADESHOWPICKUP></TRADESHOWPICKUP><TRADESHOWDELIVERY></TRADESHOWDELIVERY><CUSTOMSADMINFEE></CUSTOMSADMINFEE><CROSSBORDERADMINFEE></CROSSBORDERADMINFEE><NEWYORKISLANDDELIVERY></NEWYORKISLANDDELIVERY><DCDELIVERY></DCDELIVERY><NYCMETRODELIVERY></NYCMETRODELIVERY><FREEZEPROTECTION></FREEZEPROTECTION><ADVANCEWAREHOUSE></ADVANCEWAREHOUSE><DIRECTTOSHOW></DIRECTTOSHOW></INCLUDEDCHARGES><GUARANTEEDOPTIONS><NUMOPTIONS>2</NUMOPTIONS><OPTION><GUARANTEEDCHARGE>2085.00</GUARANTEEDCHARGE><GUARANTEEDDELDATE>2022-06-21</GUARANTEEDDELDATE><GUARANTEEDBYTIME>1200</GUARANTEEDBYTIME></OPTION><OPTION><GUARANTEEDCHARGE>1895.45</GUARANTEEDCHARGE><GUARANTEEDDELDATE>2022-06-21</GUARANTEEDDELDATE><GUARANTEEDBYTIME>1700</GUARANTEEDBYTIME></OPTION></GUARANTEEDOPTIONS><ITEMIZEDCHARGES></ITEMIZEDCHARGES><SHIPMENTCUBE><ACTUAL UNIT="FT">64.000</ACTUAL><RATED UNIT="FT">64.000</RATED></SHIPMENTCUBE><NOTES></NOTES><LINKS></LINKS><NUMERRORS>0</NUMERRORS></ABF>'
        )
        self.response_ltl = xmltodict.parse(
            xml_input='<?xml version="1.0"?><ABF><QUOTEID>LXGP7T2972</QUOTEID><CHARGE>2779.45</CHARGE><SAVEMONEY>You could save money by contacting ABF Customer Service and asking about discounted rates. To contact your local ABF Service Center go to https://arcb.com/tools/service-search.html</SAVEMONEY><DISCOUNTPERCENTAGE></DISCOUNTPERCENTAGE><ADVERTISEDTRANSIT>7 Days</ADVERTISEDTRANSIT><ADVERTISEDDUEDATE>2022-10-31</ADVERTISEDDUEDATE><SHIPDATE>2022-10-20</SHIPDATE><EFFECTIVEDATE></EFFECTIVEDATE><EXPIRATIONDATE></EXPIRATIONDATE><CODFEE></CODFEE><TPDELIVERYCHARGE></TPDELIVERYCHARGE><TPCHARGEPERBOX></TPCHARGEPERBOX><ORIGTERMINFO><ORIGTERMADDRESS>14941-131 AVE NW</ORIGTERMADDRESS><ORIGTERMCITY>EDMONTON</ORIGTERMCITY><ORIGTERMSTATE>AB</ORIGTERMSTATE><ORIGTERMZIP>T5V1S9</ORIGTERMZIP><ORIGTERMPHONE>7804513333</ORIGTERMPHONE><TYPE>DIRECT</TYPE></ORIGTERMINFO><DESTTERMINFO><DESTTERMADDRESS>4120 BELGREEN DRIVE</DESTTERMADDRESS><DESTTERMCITY>OTTAWA</DESTTERMCITY><DESTTERMSTATE>ON</DESTTERMSTATE><DESTTERMZIP>K1G3N2</DESTTERMZIP><DESTTERMPHONE>6132443593</DESTTERMPHONE><TYPE>DIRECT</TYPE></DESTTERMINFO><INCLUDEDCHARGES><FUELSURCHARGE>524.97</FUELSURCHARGE><LIFTGATEGROUNDPICKUP></LIFTGATEGROUNDPICKUP><INSIDEPICKUP></INSIDEPICKUP><LIMITEDACCESSPICKUP></LIMITEDACCESSPICKUP><RESIDENTIALPICKUP>227.50</RESIDENTIALPICKUP><CONSTRUCTIONDELIVERY></CONSTRUCTIONDELIVERY><LIFTGATEGROUNDDELIVERY>300.00</LIFTGATEGROUNDDELIVERY><INSIDEDELIVERY>188.50</INSIDEDELIVERY><LIMITEDACCESSDELIVERY></LIMITEDACCESSDELIVERY><RESIDENTIALDELIVERY></RESIDENTIALDELIVERY><FLATBEDDELIVERY></FLATBEDDELIVERY><ARRIVALNOTIFICATION></ARRIVALNOTIFICATION><CAPACITYLOAD></CAPACITYLOAD><CUSTOMSINBONDFREIGHT></CUSTOMSINBONDFREIGHT><EXCESSLIABILITY></EXCESSLIABILITY><OVERDIMENSION></OVERDIMENSION><SINGLESHIPMENT>75.00</SINGLESHIPMENT><SORTSEGREGATE></SORTSEGREGATE><SHIPPERLOAD></SHIPPERLOAD><CONSIGNEEUNLOAD></CONSIGNEEUNLOAD><PALLETIZEDSHIPMENT></PALLETIZEDSHIPMENT><HAZARDOUSSHIPMENT></HAZARDOUSSHIPMENT><DELIVERON></DELIVERON><DELIVERBY></DELIVERBY><TRADESHOWPICKUP></TRADESHOWPICKUP><TRADESHOWDELIVERY></TRADESHOWDELIVERY><CUSTOMSADMINFEE></CUSTOMSADMINFEE><CROSSBORDERADMINFEE></CROSSBORDERADMINFEE><NEWYORKISLANDDELIVERY></NEWYORKISLANDDELIVERY><DCDELIVERY></DCDELIVERY><NYCMETRODELIVERY></NYCMETRODELIVERY><FREEZEPROTECTION></FREEZEPROTECTION><ADVANCEWAREHOUSE></ADVANCEWAREHOUSE><DIRECTTOSHOW></DIRECTTOSHOW></INCLUDEDCHARGES><GUARANTEEDOPTIONS><NUMOPTIONS>2</NUMOPTIONS><OPTION><GUARANTEEDCHARGE>2493.62</GUARANTEEDCHARGE><GUARANTEEDDELDATE>2022-10-31</GUARANTEEDDELDATE><GUARANTEEDBYTIME>1200</GUARANTEEDBYTIME></OPTION><OPTION><GUARANTEEDCHARGE>2335.54</GUARANTEEDCHARGE><GUARANTEEDDELDATE>2022-10-31</GUARANTEEDDELDATE><GUARANTEEDBYTIME>1700</GUARANTEEDBYTIME></OPTION></GUARANTEEDOPTIONS><ITEMIZEDCHARGES><ITEM TYPE="CHARGE" FOR="FREIGHT" AMOUNT="1143.72" DESCRIPTION="105 LB CL70, 1 PKG @ 48 x 48 x 48 IN"/><ITEM TYPE="CHARGE" FOR="SS" AMOUNT="75.00" DESCRIPTION="/ SINGLE SHIPMENT"/><ITEM TYPE="CHARGE" FOR="RESO" AMOUNT="227.50" DESCRIPTION="/ RESIDENTIAL PICKUP"/><ITEM TYPE="CHARGE" FOR="IDEL" AMOUNT="188.50" DESCRIPTION="/ INSIDE DELIVERY"/><ITEM TYPE="CHARGE" FOR="GRD" AMOUNT="300.00" DESCRIPTION="/ GROUND DELIVERY SERVICE"/><ITEM TYPE="CHARGE" FOR="FSC" AMOUNT="524.97" DESCRIPTION="/ FUEL SURCHARGE" RATE="45.9%"/><ITEM TYPE="CHARGE" FOR="HST" AMOUNT="319.76" DESCRIPTION="// HARMONIZED SALES TAX" RATE="13%"/></ITEMIZEDCHARGES><SHIPMENTCUBE><ACTUAL UNIT="FT">64.000</ACTUAL><RATED UNIT="FT">64.000</RATED></SHIPMENTCUBE><NOTES><NOTE TYPE="CITY-ADJUSTED">The SHIPPER information was changed to EDMONTON, AB (from EDMONTON INTERNATIONAL AIRPORT, AB) based on zip/postal code T9E0V6.</NOTE></NOTES><LINKS></LINKS><NUMERRORS>0</NUMERRORS></ABF>'
        )
        self.response_spot = xmltodict.parse(
            xml_input='<?xml version="1.0" encoding="utf-8"?><ARCBEST><QUOTEID>V7VQ6D1752</QUOTEID><CHARGE>1612.66</CHARGE><EQUIPMENT>18 FOOT</EQUIPMENT><QUOTEDESCRIPTION>Minimum price including Fuel Surcharge (max 15300 lbs/18 linear ft)</QUOTEDESCRIPTION><ESTIMATEDTRANSIT>1 Day</ESTIMATEDTRANSIT><QUOTEEXPIRATIONDATE>2022-06-30</QUOTEEXPIRATIONDATE><ORIGTERMINFO><ORIGTERMADDRESS>4242 IRVING BLVD</ORIGTERMADDRESS><ORIGTERMCITY>DALLAS</ORIGTERMCITY><ORIGTERMSTATE>TX</ORIGTERMSTATE><ORIGTERMZIP>75247</ORIGTERMZIP><ORIGTERMPHONE>8004334909</ORIGTERMPHONE><TYPE>DIRECT</TYPE></ORIGTERMINFO><DESTTERMINFO><DESTTERMADDRESS>4410 S. JACKSON</DESTTERMADDRESS><DESTTERMCITY>TULSA</DESTTERMCITY><DESTTERMSTATE>OK</DESTTERMSTATE><DESTTERMZIP>74107</DESTTERMZIP><DESTTERMPHONE>9184460122</DESTTERMPHONE><TYPE>DIRECT</TYPE></DESTTERMINFO><INCLUDEDCHARGES><LIFTGATEGROUNDPICKUP></LIFTGATEGROUNDPICKUP><INSIDEPICKUP></INSIDEPICKUP><LIMITEDACCESSPICKUP></LIMITEDACCESSPICKUP><RESIDENTIALPICKUP></RESIDENTIALPICKUP><CONSTRUCTIONDELIVERY></CONSTRUCTIONDELIVERY><LIFTGATEGROUNDDELIVERY></LIFTGATEGROUNDDELIVERY><INSIDEDELIVERY></INSIDEDELIVERY><LIMITEDACCESSDELIVERY></LIMITEDACCESSDELIVERY><RESIDENTIALDELIVERY></RESIDENTIALDELIVERY><FLATBEDDELIVERY></FLATBEDDELIVERY><SORTSEGREGATE></SORTSEGREGATE><SHIPPERLOAD></SHIPPERLOAD><CONSIGNEEUNLOAD></CONSIGNEEUNLOAD><HAZARDOUSSHIPMENT></HAZARDOUSSHIPMENT><TRADESHOWPICKUP></TRADESHOWPICKUP><TRADESHOWDELIVERY></TRADESHOWDELIVERY><CUSTOMSADMINFEE></CUSTOMSADMINFEE><CROSSBORDERADMINFEE></CROSSBORDERADMINFEE><CARBONBLACK></CARBONBLACK></INCLUDEDCHARGES><NUMERRORS>0</NUMERRORS><APIREQUEST><ID>8W2Q9QS5</ID><ACCOUNT>02169Q</ACCOUNT></APIREQUEST></ARCBEST>'
        )
        self.response_error_ltl = xmltodict.parse(
            xml_input="<?xml version=\"1.0\"?><ABF><NUMERRORS>2</NUMERRORS><ERROR><ERRORCODE>57</ERRORCODE><ERRORMESSAGE>Invalid REQUESTER AFFILIATION.  Please indicate what party you are on the bill by passing in 'SHIPAFF=Y', 'CONSAFF=Y' or 'TPBAFF=Y'.</ERRORMESSAGE><ERRORCODE>8</ERRORCODE><ERRORMESSAGE>LWHType option must be IN when providing handling unit dimensions.</ERRORMESSAGE></ERROR></ABF>"
        )
        self.response_error_spot = xmltodict.parse(
            xml_input="<?xml version=\"1.0\"?><ARCBEST><NUMERRORS>2</NUMERRORS><ERROR><ERRORCODE>57</ERRORCODE><ERRORMESSAGE>Invalid REQUESTER AFFILIATION.  Please indicate what party you are on the bill by passing in 'SHIPAFF=Y', 'CONSAFF=Y' or 'TPBAFF=Y'.</ERRORMESSAGE><ERRORCODE>8</ERRORCODE><ERRORMESSAGE>LWHType option must be IN when providing handling unit dimensions.</ERRORMESSAGE></ERROR></ARCBEST>"
        )

        self._abf_rate = ABFRate(ubbe_request=self.request)

    def test_build_address_origin(self):
        """
        Test build address origin.
        """
        ret = self._abf_rate._build_address(key="Ship", address=self.request["origin"])
        expected = {
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
        }
        self.assertDictEqual(expected, ret)

    def test_build_address_destination(self):
        """
        Test build address destination.
        """
        ret = self._abf_rate._build_address(
            key="Cons", address=self.request["destination"]
        )
        expected = {
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages(self):
        """
        Test build packages.
        """
        ret = self._abf_rate._build_packages()
        expected = {
            "FrtLWHType": "IN",
            "Desc1": "Test",
            "UnitNo1": 1,
            "UnitType1": "SKD",
            "Class1": 70,
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "Wgt1": Decimal("100.00"),
        }
        self.assertDictEqual(expected, ret)

    def test_build_packages_multiple(self):
        """
        Test build packages.
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
                "description": "Test",
                "package_type": "SKID",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100.00"),
            }
        )
        abf_rate = ABFRate(ubbe_request=copied)
        ret = abf_rate._build_packages()
        expected = {
            "FrtLWHType": "IN",
            "Desc1": "Test",
            "UnitNo1": 1,
            "UnitType1": "SKD",
            "Class1": 70,
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "Wgt1": Decimal("100.00"),
            "Desc2": "Test",
            "UnitNo2": 1,
            "UnitType2": "SKD",
            "Class2": 70,
            "FrtLng2": Decimal("48"),
            "FrtWdth2": Decimal("48"),
            "FrtHght2": Decimal("48"),
            "Wgt2": Decimal("100.00"),
        }
        self.assertDictEqual(expected, ret)

    def test_build_pickup(self):
        """
        Test build address origin.
        """
        ret = self._abf_rate._build_pickup()
        expected = {"ShipMonth": 8, "ShipDay": 12, "ShipYear": 2021}
        self.assertDictEqual(expected, ret)

    def test_build_pickup_two(self):
        """
        Test build address origin.
        """
        copied = copy.deepcopy(self.request)
        del copied["pickup"]
        abf_rate = ABFRate(ubbe_request=copied)

        d = datetime.datetime.today().date()

        ret = abf_rate._build_pickup()
        expected = {"ShipMonth": d.month, "ShipDay": d.day, "ShipYear": d.year}
        self.assertDictEqual(expected, ret)

    def test_build_options(self):
        """
        Test build Options
        """
        ret = self._abf_rate._build_options(options=[])
        expected = {}
        self.assertDictEqual(expected, ret)

    def test_build_options_origin_is_residential(self):
        """
        Test build Options: Residental Origin
        """
        copied = copy.deepcopy(self.request)
        copied["origin"]["has_shipping_bays"] = False

        abf_rate = ABFRate(ubbe_request=copied)
        ret = abf_rate._build_options(options=[])
        expected = {"Acc_RPU": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_options_destination_is_residential(self):
        """
        Test build Options: Residental Destination
        """
        copied = copy.deepcopy(self.request)
        copied["destination"]["has_shipping_bays"] = False

        abf_rate = ABFRate(ubbe_request=copied)
        ret = abf_rate._build_options(options=[])
        expected = {"Acc_RDEL": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_options_inside_pickup(self):
        """
        Test build Options: Inside Pickup
        """
        ret = self._abf_rate._build_options(options=[9])
        expected = {"Acc_IPU": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_options_inside_delivery(self):
        """
        Test build Options: Inside Delivery
        """
        ret = self._abf_rate._build_options(options=[10])
        expected = {"Acc_IDEL": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_options_power_tailgate_pickup(self):
        """
        Test build Options: Power Tailgate Pickup
        """
        ret = self._abf_rate._build_options(options=[3])
        expected = {"Acc_GRD_PU": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_options_power_tailgate_delivery(self):
        """
        Test build Options: Power Tailgate Delivery
        """
        ret = self._abf_rate._build_options(options=[17])
        expected = {"Acc_GRD_DEL": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_options_heated_truck(self):
        """
        Test build Options: Heated Truck
        """
        ret = self._abf_rate._build_options(options=[6])
        expected = {"Acc_FRE": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_options_multi_one(self):
        """
        Test build Options: Power Tailgate Pickup + Delivery + Heated truck
        """
        ret = self._abf_rate._build_options(options=[3, 17, 6])
        expected = {"Acc_FRE": "Y", "Acc_GRD_DEL": "Y", "Acc_GRD_PU": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_options_multi_two(self):
        """
        Test build Options: Inside Pickup + Delivery + Heated truck
        """
        ret = self._abf_rate._build_options(options=[9, 10, 6])
        expected = {"Acc_FRE": "Y", "Acc_IPU": "Y", "Acc_IDEL": "Y"}
        self.assertDictEqual(expected, ret)

    def test_build_third_party(self):
        """
        Test build third party
        """
        ret = self._abf_rate._build_third_party()
        expected = {
            "TPBAff": "Y",
            "TPBPay": "Y",
            "TPBName": "BBE Expediting",
            "TPBAddr": "1759 35 Ave E",
            "TPBCity": "Edmonton Intl Airport",
            "TPBState": "AB",
            "TPBZip": "T9E0V6",
            "TPBCountry": "CA",
            "TPBAcct": "BBEYZF",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request(self):
        """
        Test build request
        """
        ret = self._abf_rate._build_request()
        expected = {
            "ID": "BBEYZF",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "TPBAff": "Y",
            "TPBPay": "Y",
            "TPBName": "BBE Expediting",
            "TPBAddr": "1759 35 Ave E",
            "TPBCity": "Edmonton Intl Airport",
            "TPBState": "AB",
            "TPBZip": "T9E0V6",
            "TPBCountry": "CA",
            "TPBAcct": "BBEYZF",
            "FrtLWHType": "IN",
            "Desc1": "Test",
            "UnitNo1": 1,
            "UnitType1": "SKD",
            "Class1": 70,
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "Wgt1": Decimal("100.00"),
            "ShipMonth": 8,
            "ShipDay": 12,
            "ShipYear": 2021,
        }
        self.assertDictEqual(expected, ret)

    def test_build_request_two(self):
        """
        Test build request: multi package
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
                "description": "Test",
                "package_type": "SKID",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100.00"),
            }
        )

        abf_rate = ABFRate(ubbe_request=copied)
        ret = abf_rate._build_request()
        expected = {
            "ID": "BBEYZF",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "TPBAff": "Y",
            "TPBPay": "Y",
            "TPBName": "BBE Expediting",
            "TPBAddr": "1759 35 Ave E",
            "TPBCity": "Edmonton Intl Airport",
            "TPBState": "AB",
            "TPBZip": "T9E0V6",
            "TPBCountry": "CA",
            "TPBAcct": "BBEYZF",
            "FrtLWHType": "IN",
            "Desc1": "Test",
            "UnitNo1": 1,
            "UnitType1": "SKD",
            "Class1": 70,
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "Wgt1": Decimal("100.00"),
            "Desc2": "Test",
            "UnitNo2": 1,
            "UnitType2": "SKD",
            "Class2": 70,
            "FrtLng2": Decimal("48"),
            "FrtWdth2": Decimal("48"),
            "FrtHght2": Decimal("48"),
            "Wgt2": Decimal("100.00"),
            "ShipMonth": 8,
            "ShipDay": 12,
            "ShipYear": 2021,
        }
        self.assertDictEqual(expected, ret)

    def test_build_request_three(self):
        """
        Test build request: carrier options
        """
        copied = copy.deepcopy(self.request)
        copied["carrier_options"].extend([3, 17, 6])

        abf_rate = ABFRate(ubbe_request=copied)
        ret = abf_rate._build_request()
        expected = {
            "ID": "BBEYZF",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "TPBAff": "Y",
            "TPBPay": "Y",
            "TPBName": "BBE Expediting",
            "TPBAddr": "1759 35 Ave E",
            "TPBCity": "Edmonton Intl Airport",
            "TPBState": "AB",
            "TPBZip": "T9E0V6",
            "TPBCountry": "CA",
            "TPBAcct": "BBEYZF",
            "FrtLWHType": "IN",
            "Desc1": "Test",
            "UnitNo1": 1,
            "UnitType1": "SKD",
            "Class1": 70,
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "Wgt1": Decimal("100.00"),
            "ShipMonth": 8,
            "ShipDay": 12,
            "ShipYear": 2021,
            "Acc_GRD_PU": "Y",
            "Acc_GRD_DEL": "Y",
            "Acc_FRE": "Y",
        }
        self.assertDictEqual(expected, ret)

    def test_build_request_four(self):
        """
        Test build request: carrier options + packages
        """
        copied = copy.deepcopy(self.request)
        copied["packages"].append(
            {
                "description": "Test",
                "package_type": "SKID",
                "freight_class": "70.00",
                "quantity": 1,
                "length": "48",
                "width": "48",
                "height": "48",
                "weight": "100",
                "imperial_length": Decimal("48"),
                "imperial_width": Decimal("48"),
                "imperial_height": Decimal("48"),
                "imperial_weight": Decimal("100.00"),
            }
        )
        copied["carrier_options"].extend([3, 17, 6])

        abf_rate = ABFRate(ubbe_request=copied)
        ret = abf_rate._build_request()
        expected = {
            "ID": "BBEYZF",
            "ShipCity": "edmonton international airport",
            "ShipState": "AB",
            "ShipCountry": "CA",
            "ShipZip": "T9E0V6",
            "ConsCity": "ottawa",
            "ConsState": "ON",
            "ConsCountry": "CA",
            "ConsZip": "K1V0R1",
            "TPBAff": "Y",
            "TPBPay": "Y",
            "TPBName": "BBE Expediting",
            "TPBAddr": "1759 35 Ave E",
            "TPBCity": "Edmonton Intl Airport",
            "TPBState": "AB",
            "TPBZip": "T9E0V6",
            "TPBCountry": "CA",
            "TPBAcct": "BBEYZF",
            "FrtLWHType": "IN",
            "Desc1": "Test",
            "UnitNo1": 1,
            "UnitType1": "SKD",
            "Class1": 70,
            "FrtLng1": Decimal("48"),
            "FrtWdth1": Decimal("48"),
            "FrtHght1": Decimal("48"),
            "Wgt1": Decimal("100.00"),
            "Desc2": "Test",
            "UnitNo2": 1,
            "UnitType2": "SKD",
            "Class2": 70,
            "FrtLng2": Decimal("48"),
            "FrtWdth2": Decimal("48"),
            "FrtHght2": Decimal("48"),
            "Wgt2": Decimal("100.00"),
            "ShipMonth": 8,
            "ShipDay": 12,
            "ShipYear": 2021,
            "Acc_GRD_PU": "Y",
            "Acc_GRD_DEL": "Y",
            "Acc_FRE": "Y",
        }
        self.assertDictEqual(expected, ret)

    def test_format_response_empty(self):
        """
        Test Format Response for ABF
        """
        abf_rate = ABFRate(ubbe_request=self.request)
        ret = abf_rate._format_response(response={}, rate_type="NORMAL")
        expected = []

        self.assertListEqual(expected, ret)

    def test_format_response_empty_abf(self):
        """
        Test Format Response for ABF
        """
        abf_rate = ABFRate(ubbe_request=self.request)
        ret = abf_rate._format_response(response={"ABF": {}}, rate_type="NORMAL")
        expected = []

        self.assertListEqual(expected, ret)

    def test_format_response_empty_spot(self):
        """
        Test Format Response for ABF
        """
        abf_rate = ABFRate(ubbe_request=self.request)
        ret = abf_rate._format_response(response={"ARCBEST": {}}, rate_type="SPOT")
        expected = []

        self.assertListEqual(expected, ret)

    def test_format_response_abf(self):
        """
        Test Format Response for ABF
        """
        abf_rate = ABFRate(ubbe_request=self.request)
        ret = abf_rate._format_response(response=self.response_ltl, rate_type="NORMAL")
        expected = [
            {
                "carrier_id": 512,
                "carrier_name": "ABF Freight",
                "service_code": "LTL|LXGP7T2972",
                "service_name": "LTL",
                "freight": Decimal("1143.72"),
                "surcharge": Decimal("1315.97"),
                "tax": Decimal("319.76"),
                "tax_percent": Decimal("13"),
                "total": Decimal("2779.45"),
                "transit_days": 7,
            },
            {
                "carrier_id": 512,
                "carrier_name": "ABF Freight",
                "service_code": "1200|LXGP7T2972",
                "service_name": "Guaranteed 1200",
                "freight": Decimal("2206.74"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("286.88"),
                "tax_percent": Decimal("13"),
                "total": Decimal("2493.62"),
                "transit_days": 7,
                "surcharge_list": [],
            },
            {
                "carrier_id": 512,
                "carrier_name": "ABF Freight",
                "service_code": "1700|LXGP7T2972",
                "service_name": "Guaranteed 1700",
                "freight": Decimal("2066.85"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("268.69"),
                "tax_percent": Decimal("13"),
                "total": Decimal("2335.54"),
                "transit_days": 7,
                "surcharge_list": [],
            },
        ]

        for r in ret:
            del r["delivery_date"]

        self.assertListEqual(expected, ret)

    def test_format_response_spot(self):
        """
        Test Format Response for ABF
        """
        copied = copy.deepcopy(self.request)
        copied["destination"]["country"] = "US"

        abf_rate = ABFRate(ubbe_request=copied)
        ret = abf_rate._format_response(response=self.response_spot, rate_type="SPOT")

        for r in ret:
            del r["delivery_date"]

        expected = [
            {
                "carrier_id": 512,
                "carrier_name": "ABF Freight",
                "service_code": "SV|V7VQ6D1752",
                "service_name": "Spot LTL",
                "freight": Decimal("1612.66"),
                "surcharge": Decimal("0.00"),
                "tax": Decimal("0.00"),
                "tax_percent": "0",
                "total": Decimal("1612.66"),
                "transit_days": 10,
            }
        ]
        self.assertListEqual(expected, ret)

    def test_format_response_abf_error(self):
        """
        Test Format Response for ABF Error
        """
        abf_rate = ABFRate(ubbe_request=self.request)
        ret = abf_rate._format_response(
            response=self.response_error_ltl, rate_type="NORMAL"
        )
        expected = []
        self.assertListEqual(expected, ret)

    def test_format_response_spot_error(self):
        """
        Test Format Response for ABF Error
        """
        abf_rate = ABFRate(ubbe_request=self.request)
        ret = abf_rate._format_response(
            response=self.response_error_spot, rate_type="SPOT"
        )
        expected = []
        self.assertListEqual(expected, ret)
