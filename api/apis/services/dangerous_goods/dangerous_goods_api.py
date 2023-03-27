import abc
from typing import List

from PIL import Image, ImageDraw, ImageFont

from api.exceptions.project import DangerousGoodsException, ShipException
from api.models import Carrier, DangerousGood

"""
Excepted Quantity DGs skipped. Even though there is data and rules in the IATA book, excepted quantities are 
typically a human case by case shipping item. For clarity, excepted quantity code is kept but skipped by False short 
circuiting. It is safer to assume limited quantity for a DG rather than Excepted.
"""


# TODO: Dont have duplicate UN numbers in same request
class DangerousGoodsAPI(abc.ABC):
    _radioactive_un_numbers = {
        2908, 2909, 2910, 2911, 2912, 2913, 2915, 2916, 2917, 2919, 2977, 2978, 3321, 3322, 3323, 3324, 3325, 3326,
        3327, 3328, 3329, 3330, 3331, 3332, 3333, 3507
    }
    _battery_un_numbers = {3090, 3091, 3480, 3481}
    _document_type_dg_docs = "7"

    def __init__(self, world_request: dict) -> None:
        self._world_request = world_request
        self._carrier_ids = []
        self._packages = world_request["packages"]
        self.is_shipment_dg = False
        self._is_ship_request = False
        self._dangerous_goods = []
        self._generic_label_names = ["Arrows"]
        self._air_waybill_statements = ""
        self._is_battery_lithium_ion = False
        self._is_battery_lithium_metal = False
        self._is_exempted = False

        if 'special_instructions' not in self._world_request:
            self._world_request["special_instructions"] = ""

        if 'handling_notes' not in self._world_request:
            self._world_request["handling_notes"] = ""

    @staticmethod
    def _create_excepted_quantity_label(classdiv: str) -> str:
        # Not used currently
        excepted_quantity_path = "Assets/DangerousGoods/Labels/Template/excepted-quantity.png"

        try:
            working_img = Image.open(excepted_quantity_path)
        except FileNotFoundError:
            raise ShipException({"api.error.dangerous_goods": "File " + excepted_quantity_path + " not found"})
        m_width, m_height = working_img.size
        draw = ImageDraw.Draw(working_img)
        font = ImageFont.truetype("Assets/Fonts/Vera-Bold.ttf", 30)
        width, height = draw.textsize(classdiv)

        draw.text((((m_width - (width * 2)) / 2), ((m_height - (height * 2)) / 2)), classdiv, fill="black", font=font)
        excepted_quantity_filled_path = "Assets/DangerousGoods/Tmp/excepted-quantity-filled.png"

        try:
            working_img.save(excepted_quantity_filled_path)
        except IOError:
            raise ShipException(
                {
                    "api.error.dangerous_goods":
                        "Write error: " + excepted_quantity_filled_path + " could not be written to"
                }
            )
        return excepted_quantity_filled_path

    def _conditional_add_dg_carriers(self, is_air: bool, requested_carriers: list) -> None:
        if is_air:
            dg_carrier_codes = [
                carrier_code["code"]
                for carrier_code in Carrier.objects.filter(mode="AI", is_dangerous_good=True).values("code")
            ]
        else:
            dg_carrier_codes = [
                carrier_code["code"]
                for carrier_code in Carrier.objects.filter(is_dangerous_good=True).exclude(mode="AI").values("code")
            ]

        if not any(elem in dg_carrier_codes for elem in requested_carriers):
            self._world_request["carrier_id"].extend(dg_carrier_codes)

    def _is_all_excepted_quantity(self, processed_dgs: list) -> bool:
        unique_packages_amount = len(self._world_request["packages"])
        excepted_dg_amount = 0

        for dg in processed_dgs:
            if dg.get("excepted_quantity", False):
                excepted_dg_amount += 1
        return unique_packages_amount == excepted_dg_amount

    def _process(self, is_air: bool) -> None:
        if self.is_shipment_dg:
            requested_carriers = self._world_request.get("carrier_id", [])

            if "service" in self._world_request:
                self._is_ship_request = True
                carrier_code = self._world_request["service"]["carrier_id"]
                self._carrier_ids = carrier_code

                if is_air and not Carrier.objects.filter(code=carrier_code, mode="AI", is_dangerous_good=True).exists():
                    raise DangerousGoodsException(
                        {
                            "api.error.dangerous_goods": "Carrier ID: " + str(
                                carrier_code) + " either does not exist or cannot ship dangerous goods"
                        }
                    )
                elif not is_air and not Carrier.objects.filter(code=carrier_code, is_dangerous_good=True).exclude(
                        type="AI").exists():
                    raise DangerousGoodsException(
                        {
                            "api.error.dangerous_goods": "Carrier ID: " + str(
                                carrier_code) + " either does not exist or cannot ship dangerous goods"
                        }
                    )

                if not self._is_exempted:
                    if "DANGEROUS GOODS AS PER ATTACHED" not in self._world_request["handling_notes"].upper():
                        self._air_waybill_statements = "Dangerous Goods as per associated DGD."

            elif isinstance(requested_carriers, int):
                self._is_ship_request = True
                carrier_code = self._world_request["carrier_id"]
                self._carrier_ids = carrier_code

                if not self._is_exempted:
                    if "DANGEROUS GOODS AS PER ATTACHED" not in self._world_request["handling_notes"].upper():
                        self._air_waybill_statements = "Dangerous Goods as per associated DGD."

                if is_air and not Carrier.objects.filter(code=carrier_code, mode="AI", is_dangerous_good=True).exists():
                    raise DangerousGoodsException(
                        {
                            "api.error.dangerous_goods": "Carrier ID: " + str(
                                carrier_code) + " either does not exist or cannot ship dangerous goods"
                        }
                    )
                elif not is_air and not Carrier.objects.filter(code=carrier_code, is_dangerous_good=True).exclude(
                        type="AI").exists():
                    raise DangerousGoodsException(
                        {
                            "api.error.dangerous_goods": "Carrier ID: " + str(
                                carrier_code) + " either does not exist or cannot ship dangerous goods"
                        }
                    )
            elif not requested_carriers:
                if is_air:
                    self._carrier_ids = [
                        carrier_code["code"]
                        for carrier_code in Carrier.objects.filter(mode="AI", is_dangerous_good=True).values("code")
                    ]
                else:
                    self._carrier_ids = [
                        carrier_code["code"]
                        for carrier_code in
                        Carrier.objects.filter(is_dangerous_good=True).exclude(mode="AI").values("code")
                    ]
                self._world_request["carrier_id"] = self._carrier_ids
            else:
                self._remove_non_dg_carriers(is_air, requested_carriers)
                self._conditional_add_dg_carriers(is_air, requested_carriers)
                self._carrier_ids = self._world_request["carrier_id"]

    def _remove_non_dg_carriers(self, is_air: bool, requested_carriers: list) -> None:
        if is_air:
            non_dg_carrier_codes = [
                carrier_code["code"]
                for carrier_code in Carrier.objects.filter(mode="AI", is_dangerous_good=False).values("code")
            ]
        else:
            non_dg_carrier_codes = [
                carrier_code["code"]
                for carrier_code in Carrier.objects.filter(is_dangerous_good=False).exclude(mode="AI").values("code")
            ]

        for non_dg_carrier_code in non_dg_carrier_codes:
            if non_dg_carrier_code in requested_carriers:
                self._world_request["carrier_id"].remove(non_dg_carrier_code)

    @staticmethod
    @abc.abstractmethod
    def _is_absolute_forbidden(dangerous_good: DangerousGood) -> bool:
        pass

    @abc.abstractmethod
    def _parse_dg_package(self, package: dict) -> dict:
        pass

    @abc.abstractmethod
    def _pre_process(self) -> None:
        pass

    @abc.abstractmethod
    def _process_carrier_specific_rules(self, carrier_id: int) -> None:
        pass

    @abc.abstractmethod
    def clean(self) -> None:
        pass

    @abc.abstractmethod
    def generate_documents(self) -> List[dict]:
        pass

    @abc.abstractmethod
    def parse(self) -> None:
        pass
