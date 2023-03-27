"""
    Title: Tracking Report Data
    Description: The class filter requested filters and return thee following:
        - Start Date
        - End Date
    Created: July 23, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from dateutil.tz import tz
from django.db.models import QuerySet

from api.apis.reports.report_types.excel_report import ExcelReport
from api.models import TrackingStatus


class TrackingReportData:
    """
        Shipment Metric Api
    """

    headings = [
        "Account",
        "ID",
        "Account ID",
        "Date",
        "Starting Origin City",
        "Starting Origin Postal",
        "Starting Origin Province",
        "Final Destination City",
        "Final Destination Postal",
        "Final Destination Province",
        "Reference One",
        "Reference Two",
        "Total Transit Hours",
        "P: ID",
        "P: Carrier",
        "P: Service",
        "P: Origin City",
        "P: Origin Postal",
        "P: Origin Province",
        "P: Destination City",
        "P: Destination Postal",
        "P: Destination Province",
        "P: Carrier Tracking",
        "P: Carrier Pickup",
        "P: Last Updated",
        "P: Status",
        "P: Details",
        "P: Delivered",
        "P: Transit Hours",
        "M: ID",
        "M: Carrier",
        "M: Service",
        "M: Origin City",
        "M: Origin Postal",
        "M: Origin Province",
        "M: Destination City",
        "M: Destination Postal",
        "M: Destination Province",
        "M: Carrier Tracking",
        "M: Carrier Pickup",
        "M: Last Updated",
        "M: Status",
        "M: Details",
        "M: Delivered",
        "M: Transit Hours",
        "D: ID",
        "D: Carrier",
        "D: Service",
        "D: Origin City",
        "D: Origin Postal",
        "D: Origin Province",
        "D: Destination City",
        "D: Destination Postal",
        "D: Destination Province",
        "D: Carrier Tracking",
        "D: Carrier Pickup",
        "D: Last Updated",
        "D: Status",
        "D: Details",
        "D: Delivered",
        "D: Transit Hours",
    ]

    def _get_leg_data(self, shipment) -> tuple:
        leg_list = []
        legs = shipment.leg_shipment.all()
        total_hours = 0
        tracking_status_first = TrackingStatus.objects.filter(leg__shipment=shipment).first()

        if len(legs) == 1:
            leg_list.append(["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
        elif len(legs) > 1:
            first_leg = legs.first()

            if first_leg.type == "M":
                leg_list.append(["", "", "", "", "", "", "", "", "", "", "", "", "", ""])

        for leg in legs:
            hours = 0
            tracking_status = TrackingStatus.objects.filter(leg=leg).last()

            if tracking_status:
                dl_date = tracking_status.delivered_datetime.strftime('%Y-%m-%d')

                if dl_date in ["0001-01-01 00:00 AM", "0001-01-01", "1-01-01"]:
                    dl_date = ""
                else:
                    from_zone = tz.gettz('UTC')
                    to_zone = tz.gettz('America/Edmonton')
                    mountain = tracking_status.delivered_datetime.replace(tzinfo=from_zone).astimezone(to_zone)
                    dl_date = mountain.strftime('%Y-%m-%d %H:%M %p')

                status = tracking_status.status
                details = tracking_status.details
                updated_datetime = tracking_status.updated_datetime.strftime('%Y-%m-%d %H:%M %p')
                delivered_datetime = dl_date
            else:
                status = ""
                details = ""
                updated_datetime = ""
                delivered_datetime = ""

            if delivered_datetime:
                duration = tracking_status.delivered_datetime - tracking_status_first.updated_datetime
                hours = divmod(duration.total_seconds(), 3600)[0]
                total_hours = hours

            if leg.service_name == "PICK_DEL":
                leg_list.append(["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
            else:
                leg_list.append([
                    leg.leg_id,
                    leg.carrier.name,
                    leg.service_name if leg.service_name else leg.service_code,
                    leg.origin.city,
                    leg.origin.postal_code,
                    leg.origin.province.code,
                    # leg.origin.province.country.code,
                    leg.destination.city,
                    leg.destination.postal_code,
                    leg.destination.province.code,
                    # leg.destination.province.country.code,
                    leg.tracking_identifier,
                    leg.carrier_pickup_identifier,
                    updated_datetime,
                    status,
                    details,
                    delivered_datetime,
                    hours
                ])

        return leg_list, total_hours

    def _get_shipment_data(self, shipments) -> list:
        ret = []

        for shipment in shipments:
            legs, total_hours = self._get_leg_data(shipment=shipment)

            utc = shipment.creation_date.replace(tzinfo=tz.gettz('UTC'))
            mountain = utc.astimezone(tz.gettz('America/Edmonton'))

            shipment_data = [
                shipment.subaccount.contact.company_name,
                shipment.shipment_id,
                shipment.account_id,
                mountain.strftime('%Y-%m-%d %H:%M %p'),
                shipment.origin.city,
                shipment.origin.postal_code,
                shipment.origin.province.code,
                # shipment.origin.province.country.code,
                shipment.destination.city,
                shipment.destination.postal_code,
                shipment.destination.province.code,
                # shipment.destination.province.country.code,
                shipment.reference_one,
                shipment.reference_two,
                total_hours
            ]

            for l_list in legs:
                shipment_data += l_list

            ret.append(shipment_data)

        return ret

    def get_tracking(self, shipments: QuerySet, file_name: str) -> dict:
        """
                  Get Tracking Report .
                  :return: list of tracking data
              """

        tracking_data = self._get_shipment_data(shipments=shipments)

        sheet = ExcelReport(headings=self.headings, data=tracking_data).create_report()

        return {
            "type": "excel",
            "file": sheet,
            "filename": file_name
        }
