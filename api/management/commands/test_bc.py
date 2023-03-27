from decimal import Decimal
from uuid import UUID
from django.contrib.auth.models import User
from django.core.management import BaseCommand

from api.apis.business_central.business_central import BusinessCentral
from api.apis.business_central.exceptions import BusinessCentralError
from api.apis.business_central.jobs.bc_job_attachments import BCJobAttachment
from api.apis.business_central.jobs.bc_job_file import BCJobFile
from api.apis.business_central.jobs.bc_job_planning import BCJobPlanningLines
from api.apis.business_central.jobs.bc_job_shipment_items import BCJobShipmentItems
from api.apis.business_central.jobs.bc_job_task import BCJobTask
from api.models import SubAccount, Carrier, CarrierAccount, Shipment


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:

        carrier = Carrier.objects.get(code=708)

        bc_items = BusinessCentral().get_job_list(username="bbex\\VNATARAJAN", is_all=False)
        print(bc_items)

        # request = {
        #     'account_number': '8cd0cae7-6a22-4477-97e1-a7ccfbed3e01',
        #     'service':
        #         {'carrier_id': 708, 'service_code': '1', 'origin_base': 'YEG', 'destination_base': 'YEV'},
        #     'pickup':
        #         {'start_time': '08:00', 'date': '2019-12-05', 'end_time': '16:30'},
        #     'origin': {
        #         'company_name': 'TESTING INC', 'name': 'TESTING INC TWO', 'email': 'developer@bbex.com',
        #         'phone': '7809326245', 'address': '140 Thad Johnson Private 7',
        #         'city': 'Edmonton International Airport', 'country': 'CA', 'province': 'AB',
        #         'postal_code': 'T9E0V6'
        #     },
        #     'destination': {
        #         'address': '140 Thad Johnson Road', 'city': 'Inuvik',
        #         'company_name': 'KENNETH CARMICHAEL', 'country': 'CA', 'postal_code': 'X0E0T0',
        #         'province': 'NT', 'name': 'TESTING INC TWO', 'email': 'developer@bbex.com',
        #         'phone': '7809326245'
        #     }, 'packages': [{
        #         'width': Decimal('10.6'), 'package_type': 'BOX', 'quantity': 1, 'length': Decimal('10.6'),
        #         'package': 1, 'description': 'TEST', 'height': Decimal('10.6'), 'weight': Decimal('10.6'),
        #         'imperial_length': Decimal('4.17'), 'imperial_width': Decimal('4.17'),
        #         'imperial_height': Decimal('4.17'), 'imperial_weight': Decimal('23.37'), 'is_dangerous_good': False,
        #         'volume': Decimal('0.00119102'), 'is_last': True
        #     }],
        #     'reference_one': 'SOMEREF',
        #     'reference_two': 'SOMEREF',
        #     'is_food': False,
        #     'is_metric': True,
        #     'total_pieces': Decimal('1'),
        #     'total_weight': Decimal('10.60'),
        #     'total_volume': Decimal('1191.02'),
        #     'total_weight_imperial': Decimal('23.37'),
        #     'total_volume_imperial': Decimal('0.04'),
        #     'is_international': False,
        #     'is_dangerous_shipment': False,
        #     'objects': {
        #         'sub_account': SubAccount.objects.get(subaccount_number=UUID("8cd0cae7-6a22-4477-97e1-a7ccfbed3e01")),
        #         'user':  User.objects.get(username="gobox"),
        #         'carrier_accounts': {
        #             708: {
        #                 'account': CarrierAccount.objects.get(carrier=carrier, subaccount__is_default=True),
        #                 'carrier': carrier
        #             }
        #         },
        #         'sealift_list': [40, 41],
        #         'm_carrier':  carrier
        #     },
        #     'is_bbe': False,
        #     'order_number': "order_number",
        # }
        #
        # # data = BCFreightForwardingFile(gobox_request=request).create_file()
        # #
        # # print(data)
        #
        # shipment = Shipment.objects.get(shipment_id="ub3210399539")
        #
        # data = shipment.create_context()
        #
        # data.update({
        #     'bc_customer': "1BDEC",
        #     'bc_username': "bbex\\kcarmichael",
        #     'bc_location': "YEGFF",
        #     'bc_customer_reference_one': "",
        #     'bc_customer_reference_two': "",
        #     'bc_customer_reference_three': "",
        #     'bc_planning_lines': [
        #         {
        #             "leg": "M",
        #             "carrier_id": 708,
        #             "line_type": 0,
        #             "item": "TRANSPORTATION",
        #             "markup": "",
        #             # "branch_code": "131",
        #             # "cost_centre": "210",
        #             # "location_code": "YEGFFAPP",
        #         }
        #     ]
        # })

        # print(json.dumps(shipment.create_context()))

        # try:
        #     job_number = BCJobFile(ubbe_data=data, shipment=shipment).create_file()
        # except BusinessCentralError as e:
        #     print(e.message)
        #     raise Exception
        # print(job_number)
        # data["bc_job_number"] = job_number
        # try:
        #     j_task = BCJobTask(ubbe_data=data, shipment=shipment)
        #     j_task.create_bc_connection()
        #     print(j_task.create_job_task())
        # except BusinessCentralError as e:
        #     print(e.message)
        #
        # try:
        #     j_task = BCJobShipmentItems(ubbe_data=data, shipment=shipment)
        #     j_task.create_bc_connection()
        #     print(j_task.create_shipment_items())
        # except BusinessCentralError as e:
        #     print(e.message)
        #
        # try:
        #     j_task = BCJobPlanningLines(ubbe_data=data, shipment=shipment)
        #     j_task.create_bc_connection()
        #     print(j_task.create_planning_lines())
        # except BusinessCentralError as e:
        #     print(e.message)
        #
        # try:
        #     j_task = BCJobAttachment(ubbe_data=data, shipment=shipment)
        #     j_task.create_bc_connection()
        #     print(j_task.create_attachment())
        # except BusinessCentralError as e:
        #     print(e.message)

        # try:
        #     j_task = BCJobTask(
        #         ubbe_data={
        #             "bc_job_number": job_number,
        #             "leg_id": "ub7703954825M",
        #             "delivered": "2021-04-15T14:00:00+00:00",
        #             "tracking": "518-YEG-11176491",
        #             "detail": "Delivered"
        #         },
        #         shipment=shipment
        #     )
        #     j_task.create_bc_connection()
        #     print(j_task.deliver_job_task())
        # except BusinessCentralError as e:
        #     print(e.message)
