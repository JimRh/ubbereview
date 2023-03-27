import re
from datetime import datetime

import gevent
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from pytz import UTC

from api.exceptions.project import ViewException
from api.models import RateSheet, SubAccount, Province, RateSheetLane, Carrier


class NewRateSheetManagement:
    _provinces = {}

    def __init__(
        self,
        sub_account: SubAccount,
        carrier: Carrier,
        service_name: str,
        service_code: str,
        rs_type: str,
    ) -> None:
        self._sub_account = sub_account
        self._carrier = carrier
        self._service_name = service_name
        self._service_code = service_code
        self._rs_type = rs_type
        self._get_initial_provinces()

    @staticmethod
    def convert_day(days: str) -> str:
        if not days or days == "None":
            return ""
        day_map = {
            "1": "Mon",
            "2": "Tues",
            "3": "Wed",
            "4": "Thurs",
            "5": "Fri",
            "6": "Sat",
            "7": "Sun",
        }
        ret = []

        for day in days.split(","):
            new = day_map.get(day)

            if not new:
                connection.close()
                raise ViewException(
                    code="6408",
                    message=f"RateSheetUpload: Day of the week does not exist",
                    errors=[{"rate_sheet_upload": f"Day of the week does not exist"}],
                )
            ret.append(new)

        return ", ".join(ret)

    @staticmethod
    def make_list_rates(workbook, num_col_info: int, num_ranges: int) -> list:
        list_rates = []

        for x in range(num_ranges):
            val = workbook["1"][num_col_info + x].value

            if not val:
                connection.close()
                raise ViewException(
                    code="6406",
                    message=f"RateSheetUpload: Spreadsheet is not in the correct format",
                    errors=[
                        {
                            "rate_sheet_upload": f"Spreadsheet is not in the correct format"
                        }
                    ],
                )

            header = val
            header = header.lower()
            header = header[: header.index("l")]
            header = header.replace(" ", "")

            if x == num_ranges - 1 and "+" in header:
                range_val = header.split("+")
                range_val[1] = "999999999"
            else:
                range_val = header.split("-")

            list_rates.append(range_val)
        return list_rates

    @classmethod
    def _get_initial_provinces(cls) -> None:
        """
        Get initial Provinces such as CA ans US to start with.
        """

        provinces = Province.objects.select_related("country").filter(
            country__code__in=["CA", "US"]
        )

        for province in provinces:
            lookup = f"{province.code}{province.country.code}"
            cls._provinces[lookup] = province

    @classmethod
    def _get_province(
        cls, province: str, country: str, p_type: str, province_dict: dict
    ) -> Province:
        """

        :return:
        """
        lookup = f"{province}{country}"

        if lookup in province_dict:
            return province_dict[lookup]

        try:
            province = Province.objects.get(
                code=province.upper(), country__code=country.upper()
            )
        except ObjectDoesNotExist:
            connection.close()
            raise ViewException(
                code="6407",
                message=f"RateSheetUpload: Incorrect Province and Country.",
                errors=[
                    {
                        "province": f"{p_type} province: '{province}' and country: '{country}' could not be found"
                    }
                ],
            )

        return province

    def create_sheet(
        self,
        row: list,
        num_col_info: int,
        num_ranges: int,
        list_rates: list,
        fields: dict,
    ) -> tuple:
        """

        :param fields:
        :param row:
        :param num_col_info:
        :param num_ranges:
        :param list_rates:
        :return:
        """
        lanes = {}
        military_time = re.compile(r"^([01]\d|2[0-3]):?([0-5]\d)$")

        origin = self._get_province(
            province=str(row[2].value).strip(),
            country=str(row[3].value).strip(),
            p_type="Origin",
            province_dict=fields["province_dict"],
        )
        destination = self._get_province(
            province=str(row[5].value).strip(),
            country=str(row[6].value).strip(),
            p_type="Destination",
            province_dict=fields["province_dict"],
        )

        sheet = RateSheet()
        sheet.sub_account = fields["sub_account"]
        sheet.upload_date = datetime.now(tz=UTC)
        sheet.expiry_date = row[0].value
        sheet.origin_city = str(row[1].value).strip().title()
        sheet.origin_province = origin
        sheet.destination_city = str(row[4].value).strip().title()
        sheet.destination_province = destination
        sheet.currency = row[10].value
        sheet.minimum_charge = Decimal("%.2f" % row[11].value)
        sheet.transit_days = str(row[7].value) if str(row[7].value) else -1
        sheet.availability = self.convert_day(str(row[9].value))

        if military_time.match(str(row[8].value)):
            sheet.cut_off_time = str(row[8].value)

        sheet.carrier = fields["carrier"]
        sheet.service_code = fields["service_code"]
        sheet.service_name = fields["service_name"]
        sheet.rs_type = fields["rs_type"]

        save_lanes = []

        for col in range(num_ranges):
            rate = RateSheetLane()
            rate.rate_sheet = sheet
            rate.min_value = list_rates[col][0]
            rate.max_value = list_rates[col][1]
            cost = row[num_col_info + col].value

            if not cost:
                continue

            rate.cost = "%.2f" % cost
            save_lanes.append(rate)

        o = f"{sheet.service_code}{sheet.origin_city.replace(' ', '')}{sheet.origin_province.code}"
        d = f"{sheet.service_code}{sheet.destination_city.replace(' ', '')}{sheet.destination_province.code}"

        lanes[f"{o}{d}"] = save_lanes

        connection.close()
        return [sheet], lanes

    def _make_rate_list(
        self, rows, num_col_info, num_ranges, list_rates, fields
    ) -> dict:
        sheets = []
        lanes = {}

        if len(rows) == 1:
            row = rows[0]

            if not row[0].value:
                connection.close()
                return {"rs": sheets, "lane": lanes}

            sheet, save_lanes = self.create_sheet(
                row, num_col_info, num_ranges, list_rates, fields
            )
            sheets.extend(sheet)
            lanes.update(save_lanes)

            connection.close()
            return {"rs": sheets, "lane": lanes}

        mid = len(rows) // 2

        left = gevent.Greenlet.spawn(
            self._make_rate_list,
            rows[:mid],
            num_col_info,
            num_ranges,
            list_rates,
            fields,
        )
        right = gevent.Greenlet.spawn(
            self._make_rate_list,
            rows[mid:],
            num_col_info,
            num_ranges,
            list_rates,
            fields,
        )

        gevent.joinall([left, right])

        left_sheet = left.get()
        right_sheet = right.get()

        if left_sheet["rs"] and left_sheet["lane"]:
            sheets.extend(left_sheet["rs"])
            lanes.update(left_sheet["lane"])

        if right_sheet["rs"] and right_sheet["lane"]:
            sheets.extend(right_sheet["rs"])
            lanes.update(right_sheet["lane"])

        connection.close()
        return {"rs": sheets, "lane": lanes}

    def _map_lane_costs(self, sheets: list, lane_cost) -> list:
        mapped = []

        if len(sheets) == 1:
            sheet = sheets[0]
            o = f"{sheet.service_code}{sheet.origin_city.replace(' ', '')}{sheet.origin_province.code}"
            d = f"{sheet.service_code}{sheet.destination_city.replace(' ', '')}{sheet.destination_province.code}"

            lane_list = lane_cost[f"{o}{d}"]

            for lane in lane_list:
                lane.rate_sheet = sheet
                mapped.append(lane)

            connection.close()
            return mapped

        mid = len(sheets) // 2

        left = gevent.Greenlet.spawn(self._map_lane_costs, sheets[:mid], lane_cost)
        right = gevent.Greenlet.spawn(self._map_lane_costs, sheets[mid:], lane_cost)

        gevent.joinall([left, right])

        left_sheet = left.get()
        right_sheet = right.get()

        if left_sheet:
            mapped.extend(left_sheet)

        if right_sheet:
            mapped.extend(right_sheet)

        connection.close()
        return mapped

    def import_rate_sheet(self, workbook) -> None:
        """

        :param workbook:
        :return:
        """

        for i in range(len(workbook["1"])):
            if workbook["1"][i].value == "MINIMUM CHARGE":
                num_col_info = i + 1
                break
        else:
            connection.close()
            raise ViewException(
                code="6405",
                message=f"RateSheetUpload: Spreadsheet is not in the correct format",
                errors=[
                    {"rate_sheet_upload": f"Spreadsheet is not in the correct format"}
                ],
            )

        num_ranges = len(workbook["1"]) - num_col_info
        list_rates = self.make_list_rates(workbook, num_col_info, num_ranges)
        rows = workbook.rows
        next(rows)

        fields = {
            "sub_account": self._sub_account,
            "carrier": self._carrier,
            "service_code": self._service_code,
            "service_name": self._service_name,
            "rs_type": self._rs_type,
            "province_dict": self._provinces,
        }

        sheets = self._make_rate_list(
            list(rows), num_col_info, num_ranges, list_rates, fields
        )

        # Create Sheets
        RateSheet.objects.bulk_create(sheets["rs"])
        connection.close()

        # Maps Create Sheets to lane costs
        saved_lanes = list(
            RateSheet.objects.filter(
                carrier=self._carrier, service_code=self._service_code
            )
        )
        lanes = self._map_lane_costs(sheets=saved_lanes, lane_cost=sheets["lane"])
        # Bulk Create Lane Costs
        RateSheetLane.objects.bulk_create(lanes)
        connection.close()
