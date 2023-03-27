import base64
import copy
import io
import os
from decimal import Decimal

import gevent
from PyPDF2 import PdfFileMerger
from django.core.exceptions import ObjectDoesNotExist

from api.apis.services.dangerous_goods.dangerous_goods_api import DangerousGoodsAPI
from api.background_tasks.logger import CeleryLogger
from api.documents.dg_battery import DangerousGoodBattery
from api.documents.dg_declaration import DangerousGoodDeclaration
from api.documents.dg_placard import DangerousGoodPlacard
from api.documents.simple_image_overlay import SimpleImageOverlay
from api.exceptions.project import DangerousGoodsException, ShipException
from api.models import DangerousGood, DangerousGoodGenericLabel, Carrier, DangerousGoodPackagingType


class DangerousGoodsAir(DangerousGoodsAPI):

    @staticmethod
    def _is_absolute_forbidden(dangerous_good: DangerousGood) -> bool:
        return dangerous_good.air_quantity_cutoff.filter(cutoff_value=Decimal("0.00")).count() == 3

    @staticmethod
    def _process_misc_dg(base_package: dict, package: dict, dg_quantity: Decimal, un_number: int) -> None:
        if un_number == 3363:
            if "dg_state" not in package:
                raise DangerousGoodsException({
                    "api.error.dangerous_goods.air": "Key 'DGState' must be provided for UN" + str(un_number)
                })
            if package["dg_state"] == "S":
                if dg_quantity > Decimal("1.00"):
                    raise DangerousGoodsException({
                        "api.error.dangerous_goods.air": "The provided Mass is to high for shipping UN" + str(
                            un_number)
                    })
                base_package["measure_unit"] = "KG"
            elif package["dg_state"] == "L":
                if dg_quantity > Decimal("0.50"):
                    raise DangerousGoodsException({
                        "api.error.dangerous_goods.air": "The provided Volume is to high for shipping UN" + str(
                            un_number)
                    })
                base_package["measure_unit"] = "L"
            else:
                if dg_quantity > Decimal("0.50"):
                    raise DangerousGoodsException({
                        "api.error.dangerous_goods.air": "The provided Mass is to high for shipping UN" + str(
                            un_number)
                    })
                base_package["measure_unit"] = "KG"

    def _parse_dg_package(self, package: dict) -> dict:
        un_number = package["un_number"]
        packing_group = package["packing_group"]
        proper_shipping_name = package["proper_shipping_name"]

        try:
            dg = DangerousGood.objects.prefetch_related(
                "air_quantity_cutoff__packing_instruction__packaging_types",
                "subrisks",
                "air_special_provisions"
            ).select_related(
                "packing_group",
                "classification__label"
            ).get(un_number=un_number, packing_group__packing_group=packing_group,
                  short_proper_shipping_name=package["proper_shipping_name"])
        except ObjectDoesNotExist:
            raise DangerousGoodsException({
                "api.error.dangerous_goods.air": "UN{} in packing group {} with proper shipping name {} does not exist".format(
                    un_number,
                    packing_group,
                    proper_shipping_name
                )
            })
        pkg_weight = package["weight"]
        dg_quantity = package["dg_quantity"]

        base_package = copy.deepcopy(package)
        base_package["is_limited"] = False
        base_package["is_passenger_aircraft"] = False

        if dg.unit_measure == "K":
            base_package["measure_unit"] = "KG"
        else:
            base_package["measure_unit"] = "L"

        if False and dg_quantity <= dg.excepted_quantity.outer_cutoff_value:
            base_package["excepted_quantity"] = True
            base_package["is_passenger_aircraft"] = True
        elif dg.is_gross_measure and pkg_weight <= dg.air_quantity_cutoff.get(type="L").cutoff_value:
            if package.get("is_exempted", False):
                if un_number == 1845:
                    e_stmt = "UN1845 Dry Ice {} x {}KG".format(package["quantity"], dg_quantity)
                else:
                    e_stmt = dg.limited_quantity_cutoff.packing_instruction.exempted_statement

                if e_stmt:
                    self._air_waybill_statements += " " + e_stmt
                else:
                    for asp in dg.air_special_provisions.all():
                        if asp.is_non_restricted:
                            self._air_waybill_statements += "Not Restricted as per SP A" + str(asp.code)

                if un_number in (3480, 3481) and not self._is_battery_lithium_ion:
                    self._is_battery_lithium_ion = True
                elif un_number in (3090, 3091) and not self._is_battery_lithium_metal:
                    self._is_battery_lithium_metal = True
                return {}
            base_package["is_limited"] = True
            base_package["is_passenger_aircraft"] = True
            base_package["packing_instruction"] = "Y" + str(
                dg.air_quantity_cutoff.get(type="L").packing_instruction.code)

            if dg.air_quantity_cutoff.get(type="L").packing_instruction.packaging_types.count() != 0:
                try:
                    packing_type = dg.air_quantity_cutoff.get(type="L").packing_instruction.packaging_types.get(
                        code=base_package["packing_type"])
                except ObjectDoesNotExist:
                    msg = "UN{} in packing group {} with proper shipping name {} of {}{} G is forbidden from packing type {}".format(
                        un_number,
                        packing_group,
                        proper_shipping_name,
                        pkg_weight,
                        base_package["measure_unit"],
                        base_package["packing_type"]
                    )
                    raise DangerousGoodsException({"api.error.dangerous_goods.air": msg})
                base_package["packing_type_str"] = "{} {}".format(
                    packing_type.get_material_display(),
                    packing_type.get_packaging_type_display()
                )
            else:
                try:
                    packing_type = DangerousGoodPackagingType.objects.get(code=base_package["packing_type"])
                except ObjectDoesNotExist:
                    raise DangerousGoodsException({"api.error.dangerous_goods.air": "packing_type" + base_package[
                        "packing_type"] + " does not exist"})
                base_package[
                    "packing_type_str"] = packing_type.get_material_display() + " " + packing_type.get_packaging_type_display()
        elif dg_quantity <= dg.air_quantity_cutoff.get(type="L").cutoff_value:
            if package.get("is_exempted", False):
                if un_number == 1845:
                    e_stmt = "UN1845 Dry Ice {} x {}KG".format(package["quantity"], dg_quantity)
                else:
                    e_stmt = dg.limited_quantity_cutoff.packing_instruction.exempted_statement

                if e_stmt:
                    self._air_waybill_statements += " " + e_stmt
                else:
                    for asp in dg.air_special_provisions.all():
                        if asp.is_non_restricted:
                            self._air_waybill_statements += "Not Restricted as per SP A" + str(asp.code)

                if un_number in (3480, 3481) and not self._is_battery_lithium_ion:
                    self._is_battery_lithium_ion = True
                elif un_number in (3090, 3091) and not self._is_battery_lithium_metal:
                    self._is_battery_lithium_metal = True
                return {}
            base_package["is_limited"] = True
            base_package["is_passenger_aircraft"] = True
            base_package["packing_instruction"] = "Y" + str(
                dg.air_quantity_cutoff.get(type="L").packing_instruction.code)

            if dg.air_quantity_cutoff.get(type="L").packing_instruction.packaging_types.count() != 0:
                try:
                    packing_type = dg.air_quantity_cutoff.get(type="L").packing_instruction.packaging_types.get(
                        code=base_package["packing_type"])
                except ObjectDoesNotExist:
                    msg = "UN{} in packing group {} with proper shipping name {} of {}{} is forbidden from packing type {}".format(
                        un_number,
                        packing_group,
                        proper_shipping_name,
                        dg_quantity,
                        base_package["measure_unit"],
                        base_package["packing_type"]
                    )
                    raise DangerousGoodsException({"api.error.dangerous_goods.air": msg})
                base_package["packing_type_str"] = "{} {}".format(
                    packing_type.get_material_display(),
                    packing_type.get_packaging_type_display()
                )
            else:
                try:
                    packing_type = DangerousGoodPackagingType.objects.get(code=base_package["packing_type"])
                except ObjectDoesNotExist:
                    raise DangerousGoodsException({"api.error.dangerous_goods.air": "packing_type" + base_package[
                        "packing_type"] + " does not exist"})
                base_package[
                    "packing_type_str"] = packing_type.get_material_display() + " " + packing_type.get_packaging_type_display()
        elif dg_quantity <= dg.air_quantity_cutoff.get(type="P").cutoff_value:
            passenger_aircraft_cutoff = dg.air_quantity_cutoff.get(type="P")

            if package.get("is_exempted", False):
                if un_number == 1845:
                    e_stmt = "UN1845 Dry Ice {} x {}KG".format(package["quantity"], dg_quantity)
                else:
                    e_stmt = passenger_aircraft_cutoff.packing_instruction.exempted_statement

                if e_stmt:
                    self._air_waybill_statements += " " + e_stmt
                else:
                    for asp in dg.air_special_provisions.all():
                        if asp.is_non_restricted:
                            self._air_waybill_statements += "Not Restricted as per SP A" + str(asp.code)

                if un_number in (3480, 3481) and not self._is_battery_lithium_ion:
                    self._is_battery_lithium_ion = True
                elif un_number in (3090, 3091) and not self._is_battery_lithium_metal:
                    self._is_battery_lithium_metal = True
                return {}
            base_package["is_passenger_aircraft"] = True
            base_package["packing_instruction"] = str(dg.air_quantity_cutoff.get(type="P").packing_instruction.code)

            if dg.air_quantity_cutoff.get(type="P").packing_instruction.packaging_types.count() != 0:
                try:
                    packing_type = dg.air_quantity_cutoff.get(type="P").packing_instruction.packaging_types.get(
                        code=base_package["packing_type"])
                except ObjectDoesNotExist:
                    msg = "UN{} in packing group {} with proper shipping name {} of {}{} is forbidden from packing type {}".format(
                        un_number,
                        packing_group,
                        proper_shipping_name,
                        dg_quantity,
                        base_package["measure_unit"],
                        base_package["packing_type"]
                    )
                    raise DangerousGoodsException({"api.error.dangerous_goods.air": msg})
                base_package["packing_type_str"] = "{} {}".format(
                    packing_type.get_material_display(),
                    packing_type.get_packaging_type_display()
                )
            else:
                try:
                    packing_type = DangerousGoodPackagingType.objects.get(code=base_package["packing_type"])
                except ObjectDoesNotExist:
                    raise DangerousGoodsException({"api.error.dangerous_goods.air": "packing_type" + base_package[
                        "packing_type"] + " does not exist"})
                base_package[
                    "packing_type_str"] = packing_type.get_material_display() + " " + packing_type.get_packaging_type_display()
        elif dg_quantity <= dg.air_quantity_cutoff.get(type="C").cutoff_value:
            print("HERE 3")
            if package.get("is_exempted", False):
                if un_number == 1845:
                    e_stmt = "UN1845 Dry Ice {} x {}KG".format(package["quantity"], dg_quantity)
                else:
                    e_stmt = dg.cargo_aircraft_cutoff.packing_instruction.exempted_statement

                if e_stmt:
                    self._air_waybill_statements += " " + e_stmt
                else:
                    for asp in dg.air_special_provisions.all():
                        if asp.is_non_restricted:
                            self._air_waybill_statements += "Not Restricted as per SP A" + str(asp.code)

                if un_number in (3480, 3481) and not self._is_battery_lithium_ion:
                    self._is_battery_lithium_ion = True
                elif un_number in (3090, 3091) and not self._is_battery_lithium_metal:
                    self._is_battery_lithium_metal = True
                return {}
            if "CARGO AIRCRAFT ONLY" not in self._world_request["special_instructions"].upper() or "CAO" not in \
                    self._world_request["special_instructions"].upper():
                self._air_waybill_statements += " CAO."
            base_package["packing_instruction"] = str(dg.air_quantity_cutoff.get(type="C").packing_instruction.code)

            if dg.air_quantity_cutoff.get(type="C").packing_instruction.packaging_types.count() != 0:
                try:
                    packing_type = dg.air_quantity_cutoff.get(type="C").packing_instruction.packaging_types.get(
                        code=base_package["packing_type"])
                except ObjectDoesNotExist:
                    msg = "UN{} in packing group {} with proper shipping name {} of {}{} is forbidden from packing type {}".format(
                        un_number,
                        packing_group,
                        proper_shipping_name,
                        dg_quantity,
                        base_package["measure_unit"],
                        base_package["packing_type"]
                    )
                    raise DangerousGoodsException({"api.error.dangerous_goods.air": msg})
                base_package["packing_type_str"] = "{} {}".format(
                    packing_type.get_material_display(),
                    packing_type.get_packaging_type_display()
                )
            else:
                try:
                    packing_type = DangerousGoodPackagingType.objects.get(code=base_package["packing_type"])
                except ObjectDoesNotExist:
                    raise DangerousGoodsException({"api.error.dangerous_goods.air": "packing_type" + base_package[
                        "packing_type"] + " does not exist"})
                base_package[
                    "packing_type_str"] = packing_type.get_material_display() + " " + packing_type.get_packaging_type_display()
        else:
            raise DangerousGoodsException(
                {
                    "api.error.dangerous_goods.air": "The provided Mass/Volume is to high for shipping UN" + str(
                        un_number)
                }
            )
        if dg.classification.classification == 9:
            self._process_misc_dg(base_package, package, dg_quantity, un_number)

        base_package["proper_shipping_name"] = dg.short_proper_shipping_name
        base_package["class_div"] = dg.classification.verbose_classification()
        base_package["class"] = dg.classification.classification
        base_package["division"] = dg.classification.division
        base_package["subrisks"] = dg.subrisks.all()
        base_package["subrisks_str"] = dg.subrisks_str()
        base_package["packing_group_str"] = dg.packing_group.get_packing_group_display()
        base_package["placard_img"] = dg.classification.label
        base_package["specialty_label"] = dg.specialty_label
        base_package["is_gross"] = dg.is_gross_measure

        return base_package

    def parse(self) -> None:
        for package in self._world_request["packages"]:
            if package.get("un_number", 0):
                data = self._parse_dg_package(package)

                if not data:
                    del package["un_number"]
                    del package["packing_group"]
                    del package["packing_type"]
                    del package["dg_quantity"]
                    del package["proper_shipping_name"]
                else:
                    package.update(data)
        self._world_request["handling_notes"] = self._air_waybill_statements + " " \
                                                + self._world_request["handling_notes"]

    # Override
    def _pre_process(self) -> None:
        for package in self._packages:
            un_number = package.get("un_number", 0)
            packing_group = package.get("packing_group", '')
            proper_shipping_name = package.get("proper_shipping_name", '')

            if un_number:
                if not packing_group:
                    raise DangerousGoodsException(
                        {"api.error.dangerous_goods": "DG package must have a packing group."})

                if un_number in self._radioactive_un_numbers:
                    raise DangerousGoodsException(
                        {"api.error.dangerous_goods": "Radioactive dangerous goods are forbidden."}
                    )

                if not package.get("dg_quantity", Decimal("0.00")):
                    raise DangerousGoodsException(
                        {"api.error.dangerous_goods": "Key 'DGQuantity' must be provided a value."}
                    )

                try:
                    dg = DangerousGood.objects.get(un_number=un_number, packing_group__packing_group=packing_group,
                                                   short_proper_shipping_name=proper_shipping_name)
                except ObjectDoesNotExist:
                    raise DangerousGoodsException(
                        {
                            "api.error.dangerous_goods": "UN{} in packing group {} with proper shipping name {} does not exist".format(
                                un_number,
                                packing_group,
                                proper_shipping_name
                            )
                        }
                    )
                if package.get("is_exempted", False):
                    self._is_exempted = True
                else:
                    self._is_exempted = False

                self._dangerous_goods.append(dg)

                if not self.is_shipment_dg:
                    if "handling_notes" not in self._world_request:
                        self._world_request["handling_notes"] = ""

                    self.is_shipment_dg = True
                    self._world_request["is_dg_shipment"] = True

                # TODO: Investigate better logic to reincorporate into rate logic
                if self.is_shipment_dg:
                    if "packing_type" not in package:
                        raise DangerousGoodsException(
                            {"api.error.dangerous_goods": "Key 'packing_type' is required for shipping"}
                        )
                    elif not package["packing_type"]:
                        raise DangerousGoodsException(
                            {
                                "api.error.dangerous_goods": "Key 'packing_type' must contain a value for air "
                                                            "transport/processing"
                            }
                        )

    # Override
    def _process_carrier_specific_rules(self, carrier_id: int) -> None:
        return None

    # Override
    def clean(self, strict: bool = True) -> None:
        self._pre_process()

        if not self.is_shipment_dg:
            return

        self._process(is_air=True)

        for dangerous_good in self._dangerous_goods:
            if self._is_absolute_forbidden(dangerous_good):
                if strict:
                    raise DangerousGoodsException(
                        {
                            "api.error.dangerous_goods.air":
                                "UN{} in packing group {} with proper shipping name {} is forbidden from all air transport".format(
                                    dangerous_good.un_number,
                                    dangerous_good.packing_group.get_packing_group_display(),
                                    dangerous_good.short_proper_shipping_name
                                )
                        }
                    )
                else:
                    for air_carrier_id in Carrier.objects.filter(mode="AI", is_dangerous_good=True).values(
                            "code"):
                        try:
                            self._world_request["carrier_id"].remove(air_carrier_id["code"])
                        except ValueError:
                            continue
                    return None
        self._world_request["dangerous_goods"] = self._dangerous_goods

        if self._is_ship_request:
            self._process_carrier_specific_rules(self._carrier_ids)
        else:
            for carrier_id in self._carrier_ids:
                self._process_carrier_specific_rules(carrier_id)

    # Override
    def generate_documents(self) -> dict:
        dg_documents = []
        dangerous_goods = [
            package
            for package in self._world_request["packages"] if package.get("un_number", 0)
        ]

        if False and self._is_all_excepted_quantity(dangerous_goods):
            for dg in dangerous_goods:
                try:
                    img_path = self._create_excepted_quantity_label(dg["class_div"])
                except ShipException as e:
                    CeleryLogger().l_error.delay(
                        location="dangerous_goods_air.py line: 451",
                        message="DG AIR: {}".format(e.message)
                    )
                    continue
                dg_documents.append(SimpleImageOverlay(img_path).get_pdf())

                try:
                    os.remove(img_path)
                except FileNotFoundError:
                    CeleryLogger().l_error.delay(
                        location="dangerous_goods_air.py line: 461",
                        message="Delete file error: {} does not exist".format(img_path)
                    )
                    continue
        else:
            threads = []

            if not self._is_exempted:
                dg_dec_thread = gevent.spawn(DangerousGoodDeclaration(self._world_request, dangerous_goods).get_pdf)
                threads.append(dg_dec_thread)

            dg_placard_threads = [
                gevent.spawn(DangerousGoodPlacard(dangerous_good).get_pdf)
                for dangerous_good in dangerous_goods if not dangerous_good.get("excepted_quantity", False)
            ]

            for dangerous_good in dangerous_goods:
                if False and not dangerous_good.get("excepted_quantity", False):
                    for subrisk in dangerous_good["Subrisks"]:
                        params = {
                            "class_div": subrisk.verbose_classification(),
                            "subrisks_str": "",
                            "placard_img": subrisk.label,
                            "proper_shipping_name": dangerous_good["proper_shipping_name"],
                            "un_number": dangerous_good["un_number"],
                        }
                        dg_placard_threads.append(gevent.spawn(DangerousGoodPlacard(params).get_pdf))

            threads.extend(dg_placard_threads)
            gevent.joinall(threads)

            if not self._is_exempted:
                dg_documents = [dg_dec_thread.value]
            else:
                dg_documents = []

            if self._is_battery_lithium_ion:
                dg_documents.append(DangerousGoodBattery(3480).get_pdf())

            if self._is_battery_lithium_metal:
                dg_documents.append(DangerousGoodBattery(3090).get_pdf())

            for dg_placard_thread in dg_placard_threads:
                dg_documents.append(dg_placard_thread.value)

            for dg in dangerous_goods:
                if dg.get("is_limited", False) and "Limited Quantity" not in self._generic_label_names:
                    self._generic_label_names.append("Limited Quantity Air")

                if not dg.get("is_passenger_aircraft", False) and "Cargo Aircraft Only" not in self._generic_label_names:
                    self._generic_label_names.append("Cargo Aircraft Only")

                if dg["specialty_label"] is not None:
                    self._generic_label_names.append(dg["specialty_label"].name)

                if False and dg.get("excepted_quantity", False):
                    img_path = self._create_excepted_quantity_label(dg["class_div"])
                    dg_documents.append(SimpleImageOverlay(img_path).get_pdf())

                    try:
                        os.remove(img_path)
                    except FileNotFoundError:
                        CeleryLogger().l_error.delay(
                            location="dangerous_goods_air.py line: 524",
                            message="Delete file error: {} does not exist".format(img_path)
                        )
                        continue

            for dg_generic_label in DangerousGoodGenericLabel.objects.filter(name__in=self._generic_label_names):
                dg_documents.append(
                    SimpleImageOverlay(dg_generic_label.label, dg_generic_label.width,
                                       dg_generic_label.height).get_pdf()
                )
        files = [
            document
            for document in dg_documents
        ]
        m_buffer = io.BytesIO()
        merger = PdfFileMerger()

        for file in files:
            merger.append(io.BytesIO(file))
        merger.write(m_buffer)
        m_buffer.seek(0)
        document = {'document': base64.b64encode(m_buffer.read()).decode("ascii"), 'type': self._document_type_dg_docs}

        m_buffer.close()

        return document
