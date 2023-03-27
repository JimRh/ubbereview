"""
    Title: Main Rate Class
    Description: This file will get rates for all available and validated carriers.
    Created: July 14, 2022
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.utils import IntegrityError

from api.apis.business_central.business_central import BusinessCentral
from api.background_tasks.business_central import CeleryBusinessCentral
from api.exceptions.project import ViewException
from api.globals.project import UPDATE_FILE, NEW_FILE
from api.models import Shipment, SubAccount, Address, Contact, Leg, Carrier, TrackingStatus, Package, API


class ManualShipment:
    """
        Manual Shipment

        Response: dict
            - rate_id - Log ID
            - rates  - List of rates
            - pickup_rates - List of Lists of Pickup Rates
            - delivery_rates - List of Lists of Delivery Rates
            - carrier_service - Carrier Service Information

        Steps:
            - Step 1 - Create Shipment
            - Step 2 - Create Leg
            - Step 3 - Create Packages
            - Step 4 - Create Business Central
    """

    def __init__(self, request: dict, sub_account: SubAccount, user: User):
        self._shipment_data = request
        self._leg_data = request.pop('legs')
        self._package_data = request.pop('packages')
        self._bc_data = request.pop('bc_fields')
        self._sub_account = sub_account
        self._user = user

    def _create_business_central(self, shipment: Shipment):
        """

            :return:
        """

        try:
            if API.objects.get(name="BusinessCentral").active and self._user.username in ["gobox", "GoBox", "test"]:
                bc_fields = self._bc_data
                bc_type = bc_fields.get("bc_type", 3)

                if bc_type == 2 or not shipment.subaccount.is_bc_push:
                    # SKIP Business Central Logic
                    return

                bc_fields["is_dangerous_shipment"] = shipment.is_dangerous_good
                bc_fields["shipment_id"] = shipment.shipment_id

                if bc_type == 0:
                    # Create New File
                    job_file = BusinessCentral().create_job_file(data=bc_fields, shipment=shipment)
                elif bc_type == 1:
                    # Update Existing Job File
                    shipment.ff_number = bc_fields["bc_job_number"]
                    shipment.save()
                    CeleryBusinessCentral().update_job_file.delay(data=bc_fields)
                elif shipment.subaccount.bc_type == UPDATE_FILE:
                    # Only should be Non BBE Accounts: IE: Raytheon
                    shipment.ff_number = shipment.subaccount.bc_job_number
                    shipment.save()
                    bc_fields["bc_job_number"] = shipment.subaccount.bc_job_number
                    CeleryBusinessCentral().update_account_ff_file.delay(data=bc_fields)
                elif shipment.subaccount.bc_type == NEW_FILE:
                    job_file = BusinessCentral().create_account_file(data=bc_fields, shipment=shipment)
                    shipment.ff_number = job_file
                    shipment.save()
        except ViewException as e:
            raise ViewException(code=e.code, message=e.message, errors=e.errors)

    @staticmethod
    def _create_leg(data: dict, shipment: Shipment) -> Leg:
        """

            :param data:
            :return:
        """
        errors = []

        try:
            carrier = Carrier.objects.get(code=data["carrier"]["code"])
        except ObjectDoesNotExist:
            errors.append({"carrier": f"'carrier_code' does not exist."})
            raise ViewException(code="2808", message=f'Leg: Carrier not found.', errors=errors)

        try:
            country = data["origin"]["province"]["country"]["code"]
            province = data["origin"]["province"]["code"]
            data["origin"]["province"] = province
            data["origin"]["country"] = country

            origin = Address.create_or_find(param_dict=data["origin"])
        except ValidationError as e:
            errors.append({"origin": f"'origin' failed to create: {str(e)}"})
            raise ViewException(code="2810", message='Leg: Origin address failed to create.', errors=errors)

        try:
            country = data["destination"]["province"]["country"]["code"]
            province = data["destination"]["province"]["code"]
            data["destination"]["province"] = province
            data["destination"]["country"] = country

            destination = Address.create_or_find(param_dict=data["destination"])
        except ValidationError as e:
            errors.append({"destination": f"'destination' failed to create: {str(e)}"})
            raise ViewException(code="2811", message='Leg: Destination address failed to create.', errors=errors)

        carrier_markup = shipment.subaccount.markup.get_carrier_percentage(carrier=carrier)

        try:
            leg = Leg.create(param_dict=data)
            leg.shipment = shipment
            leg.leg_id = f"{shipment.shipment_id}{data['postfix']}"
            leg.carrier = carrier
            leg.origin = origin
            leg.destination = destination
            leg.markup = carrier_markup
            leg.on_hold = False
            leg.save()
        except ValidationError as e:
            errors.append({"leg": f"Failed to create: {str(e)}"})
            raise ViewException(code="2812", message='Leg: failed to create.', errors=errors)
        except IntegrityError:
            leg_id = f"{shipment.shipment_id}{data['postfix']}"
            errors.append({"leg": f"'leg_id' already exists: '{leg_id}'"})
            raise ViewException(code="2813", message="Leg: 'leg_id' already exists.", errors=errors)

        status = TrackingStatus.create(param_dict={
            "leg": leg,
            "status": "Created",
            "details": f"Shipment has been created."
        })
        status.save()

        return leg

    def _create_legs(self, shipment: Shipment):
        freight = Decimal("0.00")
        surcharge = Decimal("0.00")
        tax = Decimal("0.00")
        cost = Decimal("0.00")

        for leg in self._leg_data:
            leg = self._create_leg(data=leg, shipment=shipment)

            freight += leg.freight
            surcharge += leg.surcharge
            tax += leg.tax
            cost += leg.cost

        return {
            "freight": freight,
            "surcharge": surcharge,
            "tax": tax,
            "cost": cost
        }

    def _create_packages(self, shipment: Shipment):
        """

            :param shipment:
            :return:
        """

        Package.one_step_save(packages=self._package_data, shipment=shipment)

    def _create_shipment(self):
        """

            :return:
        """
        account_number = self._shipment_data.pop("account_number")
        origin_data = self._shipment_data.pop("origin")
        destination_data = self._shipment_data.pop("destination")

        try:
            origin = Address.create_or_find(param_dict=origin_data)
            destination = Address.create_or_find(param_dict=destination_data)
            sender = Contact.create_or_find(origin_data)
            receiver = Contact.create_or_find(destination_data)
        except Exception as e:
            raise ViewException(code="XXX", message="Issue with Shipment Origin or Destination", errors=[])

        try:
            sub_account = SubAccount.objects.select_related(
                "markup"
            ).get(subaccount_number=account_number)
        except ObjectDoesNotExist:
            raise ViewException(code="XXX", message="Issue with Shipment Data", errors=[])

        try:
            shipment = Shipment.create(param_dict=self._shipment_data)
            shipment.user = self._user
            shipment.subaccount = sub_account
            shipment.markup = sub_account.markup.default_percentage
            shipment.origin = origin
            shipment.destination = destination
            shipment.sender = sender
            shipment.receiver = receiver
            shipment.set_values(pairs=self._shipment_data)
            shipment.save()
        except Exception as e:
            raise ViewException(code="XXX", message="Issue with Shipment Data", errors=[])

        return shipment

    @transaction.atomic
    def create(self):
        """

            :return:
        """

        shipment = self._create_shipment()
        leg_cost = self._create_legs(shipment=shipment)
        self._create_packages(shipment=shipment)

        shipment.freight = leg_cost["freight"]
        shipment.surcharge = leg_cost["surcharge"]
        shipment.tax = leg_cost["tax"]
        shipment.cost = leg_cost["cost"]
        shipment.save()

        self._create_business_central(shipment=shipment)

        return shipment
