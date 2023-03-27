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
from api.exceptions.project import DangerousGoodsException
from api.globals.carriers import CAN_POST
from api.models import DangerousGood, DangerousGoodGenericLabel, Carrier


class DangerousGoodsGround(DangerousGoodsAPI):

    @staticmethod
    def _is_absolute_forbidden(dangerous_good: DangerousGood) -> bool:
        return not dangerous_good.ground_limited_quantity_cutoff and not dangerous_good.ground_maximum_quantity_cutoff

    def _parse_dg_package(self, package: dict) -> dict:
        un_number = package["un_number"]
        packing_group = package["packing_group"]
        proper_shipping_name = package["proper_shipping_name"]

        if un_number and packing_group:
            try:
                dg = DangerousGood.objects.prefetch_related(
                    "subrisks"
                ).select_related(
                    "packing_group",
                    "classification__label"
                ).get(un_number=un_number, packing_group__packing_group=packing_group,
                      short_proper_shipping_name=proper_shipping_name)
            except ObjectDoesNotExist:
                raise DangerousGoodsException({
                    "api.error.dangerous_goods.ground": "UN{} in packing group {} with proper shipping name {} does not exist".format(
                        un_number,
                        packing_group,
                        proper_shipping_name
                    )
                })

            if dg.is_ground_exempt:
                return {}

            dg_quantity = package["dg_quantity"]

            base_package = copy.deepcopy(package)
            base_package["is_limited"] = False

            if dg.unit_measure == "K":
                base_package["measure_unit"] = "KG"
            else:
                base_package["measure_unit"] = "L"

            if False and dg_quantity <= dg.excepted_quantity.outer_cutoff_value:
                base_package["excepted_quantity"] = True
            elif dg.ground_limited_quantity_cutoff and dg_quantity <= dg.ground_limited_quantity_cutoff:
                if package.get("is_exempted", False):
                    if un_number in (3480, 3481) and not self._is_battery_lithium_ion:
                        self._is_battery_lithium_ion = True
                    elif un_number in (3090, 3091) and not self._is_battery_lithium_metal:
                        self._is_battery_lithium_metal = True
                    return {}
                base_package["is_limited"] = True
            elif dg.ground_maximum_quantity_cutoff and dg_quantity <= dg.ground_maximum_quantity_cutoff:
                if package.get("is_exempted", False):
                    if un_number in (3480, 3481) and not self._is_battery_lithium_ion:
                        self._is_battery_lithium_ion = True
                    elif un_number in (3090, 3091) and not self._is_battery_lithium_metal:
                        self._is_battery_lithium_metal = True
                    return {}
            else:
                raise DangerousGoodsException(
                    {
                        "api.error.dangerous_goods.ground": "The provided Mass/Volume is to high for shipping UN" + str(
                            un_number)
                    }
                )
            base_package["proper_shipping_name"] = dg.short_proper_shipping_name
            base_package["class_div"] = dg.classification.verbose_classification()
            base_package["class"] = dg.classification.classification
            base_package["division"] = dg.classification.division
            base_package["subrisks"] = list(dg.subrisks.all())
            base_package["subrisks_str"] = dg.subrisks_str()
            base_package["packing_group_str"] = dg.packing_group.get_packing_group_display()
            base_package["placard_img"] = dg.classification.label
            base_package["specialty_label"] = dg.specialty_label
            base_package["is_gross"] = dg.is_gross_measure

            return base_package

    def parse(self):
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

    # Override
    def _pre_process(self) -> None:
        for package in self._packages:
            un_number = package.get("un_number", 0)
            packing_group = package.get("packing_group", '')
            proper_shipping_name = package.get("proper_shipping_name", '')

            if un_number:
                if un_number in self._radioactive_un_numbers:
                    raise DangerousGoodsException(
                        {"api.error.dangerous_goods": "Radioactive dangerous goods are forbidden"}
                    )

                if not packing_group:
                    raise DangerousGoodsException(
                        {"api.error.dangerous_goods": "DG package must have a packing group."})

                if not proper_shipping_name:
                    raise DangerousGoodsException(
                        {"api.error.dangerous_goods": "DG package must have a proper shipping name."})

                if not package.get("dg_quantity", Decimal("0.00")):
                    raise DangerousGoodsException(
                        {"api.error.dangerous_goods": "Key 'dg_quantity' must be provided a value."}
                    )

                try:
                    dg = DangerousGood.objects.get(un_number=un_number,
                                                   packing_group__packing_group=packing_group,
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

                if not dg.is_ground_exempt:
                    self._dangerous_goods.append(dg)

                    if not self.is_shipment_dg:
                        if "handling_notes" not in self._world_request:
                            self._world_request["handling_notes"] = ""

                        self.is_shipment_dg = True
                        self._world_request["is_dg_shipment"] = True

    # Override
    def _process_carrier_specific_rules(self, carrier_id: int) -> None:
        if carrier_id == CAN_POST:
            for dg in self._dangerous_goods:
                if dg.un_number not in self._battery_un_numbers:
                    if self._is_ship_request:
                        raise DangerousGoodsException(
                            {
                                "api.error.dangerous_goods.ground.CanadaPost":
                                    "Canada Post may only ship UN Numbers: " + str(self._battery_un_numbers)
                            }
                        )
                    self._world_request["carrier_id"].remove(20)
                    break

    # Override
    def clean(self, strict: bool = True) -> None:
        self._pre_process()

        if not self.is_shipment_dg:
            return

        self._process(is_air=False)

        for dangerous_good in self._dangerous_goods:
            if self._is_absolute_forbidden(dangerous_good):
                if strict:
                    raise DangerousGoodsException(
                        {
                            "api.error.dangerous_goods.ground":
                                "UN{} in packing group {} with proper shipping name {} is forbidden from all ground transport".format(
                                    dangerous_good.un_number,
                                    dangerous_good.packing_group.get_packing_group_display(),
                                    dangerous_good.short_proper_shipping_name
                                )
                        }
                    )
                else:
                    for ground_carrier_id in Carrier.objects.filter(is_air=False, is_dangerous_good=True).values(
                            "code"):
                        try:
                            self._world_request["carrier_id"].remove(ground_carrier_id["code"])
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
                img_path = self._create_excepted_quantity_label(dg["class_div"])
                dg_documents.append(SimpleImageOverlay(img_path).get_pdf())

                try:
                    os.remove(img_path)
                except FileNotFoundError:
                    CeleryLogger().l_error.delay(
                        location="dangerous_goods_ground.py line: 242",
                        message="Delete file error: {} does not exist".format(img_path)
                    )
                    continue
        else:
            threads = []

            if not self._is_exempted:
                dg_dec_thread = gevent.spawn(DangerousGoodDeclaration(self._world_request, dangerous_goods).get_pdf)
                threads.append(dg_dec_thread)
                gevent.joinall(threads)
                dg_documents = [dg_dec_thread.value]
            else:
                dg_documents = []

            if self._is_battery_lithium_ion:
                dg_documents.append(DangerousGoodBattery(3480).get_pdf())

            if self._is_battery_lithium_metal:
                dg_documents.append(DangerousGoodBattery(3090).get_pdf())

            for dg in dangerous_goods:
                if dg.get("is_limited", False) and "Limited Quantity" not in self._generic_label_names:
                    self._generic_label_names.append("Limited Quantity Ground")

                if dg["specialty_label"] is not None:
                    self._generic_label_names.append(dg["specialty_label"].name)

                if False and dg.get("excepted_quantity", False):
                    img_path = self._create_excepted_quantity_label(dg["class_div"])
                    dg_documents.append(SimpleImageOverlay(img_path).get_pdf())

                    try:
                        os.remove(img_path)
                    except FileNotFoundError:
                        CeleryLogger().l_error.delay(
                            location="dangerous_goods_air.py line: 278",
                            message="Delete file error: {} does not exist".format(img_path)
                        )
                        continue

                if not dg.get("excepted_quantity", False):
                    dg_documents.append(DangerousGoodPlacard(dg).get_pdf())

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
