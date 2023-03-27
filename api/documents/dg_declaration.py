import base64
from decimal import Decimal
from io import BytesIO

from django.core.exceptions import ObjectDoesNotExist
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image, SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.platypus.flowables import Spacer

from api.background_tasks.logger import CeleryLogger
from api.exceptions.project import ShipException
from api.globals.documents import TABLE_LINE_THICKNESS, BBE_LOGO_PATH, BBE_LOGO_WIDTH, \
    BBE_LOGO_HEIGHT
from api.models import Carrier, Airport


class DangerousGoodDeclaration:
    filename = "Dangerous Goods Declaration"
    extension = ".pdf"
    logo = Image(BBE_LOGO_PATH, BBE_LOGO_WIDTH, BBE_LOGO_HEIGHT)
    fontname = "Helvetica"
    title_font_size = 12
    default_font_size = 8
    small_font_size = 8
    medium_font_size = 8
    default_border_thickness = TABLE_LINE_THICKNESS
    bold_border_thickness = 0.5
    legal_font_size = 8
    two_places = Decimal("0.01")
    banner = Image("assets/dangerous_goods/declaration/banner.png")

    def __init__(self, world_request: dict, dg_details: list) -> None:
        self._dg_details = dg_details
        self._is_air = Carrier.objects.filter(code__in=(int(world_request["carrier_id"]),), mode="AI").exists()
        world_request["is_passenger_aircraft"] = False

        if self._is_air:
            try:
                self._origin_airbase = Airport.objects.get(code=world_request["origin"]["base"])
            except ObjectDoesNotExist:
                msg = "origin airport code " + world_request["origin"]["base"] + " does not exist"
                CeleryLogger().l_critical.delay(location="dg_declaration.py line: 44", message=msg)
                raise ShipException({"api.documentation.error": msg})

            try:
                self._destination_airbase = Airport.objects.get(code=world_request["destination"]["base"])
            except ObjectDoesNotExist:
                msg = "destination airport code " + world_request["destination"]["base"] + " does not exist"
                CeleryLogger().l_critical.delay(location="dg_declaration.py line: 51", message=msg)
                raise ShipException({"api.documentation.error": msg})

            for package in self._dg_details:
                if package["is_passenger_aircraft"]:
                    world_request["is_passenger_aircraft"] = True
                    break

        self.buffer = BytesIO()
        self.declaration = self._generate(world_request)
        self.buffer.seek(0)
        self.base64 = base64.b64encode(self.buffer.read()).decode("ascii")
        self.buffer.close()

    class _CartesianCoordinate:

        def __init__(self, x: int, y: int) -> None:
            self._x = x
            self._y = y

        @property
        def x(self) -> int:
            return self._x

        @property
        def y(self) -> int:
            return self._y

        @property
        def get_coordinate(self) -> tuple:
            return self._x, self._y

    def _generate(self, world_request: dict):
        doc = SimpleDocTemplate(self.buffer, rightMargin=0.25 * cm, leftMargin=0.25 * cm, topMargin=0.5 * cm,
                                bottomMargin=0.5 * cm)

        story = []
        styles = self.generate_styles()
        num_of_dgs = len(self._dg_details)
        pages = 2 + int(num_of_dgs / 9)
        dg_list = []

        for i in range(pages - 1):
            start = 8 * i
            end = (8 * (i + 1))

            dg_list.append(self._dg_details[start:end])

        for page_num in range(1, pages):
            if self._is_air:
                row1_data = [
                    [
                        Paragraph("Shipper:", styles["Left"]),
                        Paragraph("Air Waybill No.", styles["Left"])
                    ],
                    [
                        Spacer(width=0, height=0.25 * cm),
                        Paragraph(
                            "{} {}".format(Carrier.objects.get(code=world_request["carrier_id"]).name,
                                           world_request["awb"]),
                            styles["Left"])
                    ],
                    [
                        Paragraph(world_request["origin"]["company_name"], styles["Left"]),
                        Paragraph('', styles["Center"])
                    ],
                    [
                        Paragraph(world_request["origin"]["address"], styles["Left"]),
                        Paragraph("PAGE {} OF {} PAGE(S)".format(page_num, pages - 1), styles["Left"])
                    ],
                    [
                        Paragraph("{}, {}".format(world_request["origin"]["city"], world_request["origin"]["province"]),
                                  styles["Left"]),
                        Paragraph("SHIPPERS REFERENCE NUMBER:", styles["Left"])
                    ],
                    [
                        Paragraph(
                            "{} {}".format(world_request["origin"]["postal_code"], world_request["origin"]["phone"]),
                            styles["Left"]),
                        Paragraph("(optional)", styles["Center_Small"])
                    ],
                    [
                        Spacer(width=0, height=0.25 * cm),
                        Paragraph('', styles["Center"])
                    ]
                ]
            else:
                row1_data = [
                    [
                        Paragraph("Shipper:", styles["Left"]),
                        Paragraph("Carrier:", styles["Left"])
                    ],
                    [
                        Spacer(width=0, height=0.25 * cm),
                        Paragraph(
                            "{} {}".format(Carrier.objects.get(code=world_request["carrier_id"]).name,
                                           world_request["tracking_number"]),
                            styles["Left"])
                    ],
                    [
                        Paragraph(world_request["origin"]["company_name"], styles["Left"]),
                        Paragraph('', styles["Center"])
                    ],
                    [
                        Paragraph(world_request["origin"]["address"], styles["Left"]),
                        Paragraph("PAGE {} OF {} PAGE(S)".format(page_num, pages - 1), styles["Left"])
                    ],
                    [
                        Paragraph("{}, {}".format(world_request["origin"]["city"], world_request["origin"]["province"]),
                                  styles["Left"]),
                        Paragraph("SHIPPERS REFERENCE NUMBER:", styles["Left"])
                    ],
                    [
                        Paragraph(
                            "{} {}".format(world_request["origin"]["postal_code"], world_request["origin"]["phone"]),
                            styles["Left"]),
                        Paragraph("(optional)", styles["Center_Small"])
                    ],
                    [
                        Spacer(width=0, height=0.25 * cm),
                        Paragraph('', styles["Center"])
                    ]
                ]

            row1_table = Table(data=row1_data, colWidths=(8.8 * cm))

            row1_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(0, 6).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0)
                ]
            ))

            consignee_data = [
                [
                    Paragraph("Consignee:", styles["Left"])
                ],
                [
                    Spacer(width=0, height=0.25 * cm)
                ],
                [
                    Paragraph(world_request["destination"]["company_name"], styles["Left"])
                ],
                [
                    Paragraph(world_request["destination"]["address"], styles["Left"])
                ],
                [
                    Paragraph(
                        "{}, {}".format(world_request["destination"]["city"], world_request["destination"]["province"]),
                        styles["Left"])
                ],
                [
                    Paragraph("{} {}".format(world_request["destination"]["postal_code"],
                                             world_request["destination"]["phone"]),
                              styles["Left"])
                ],
                [
                    Spacer(width=0, height=0.25 * cm)
                ]
            ]

            consignee_table = Table(data=consignee_data, colWidths=(8.8 * cm))

            consignee_table.setStyle(TableStyle(
                [
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0)
                ]
            ))

            logo_data = [
                [Image("assets/BBE_LOGO.png", width=100, height=75, hAlign="RIGHT")]
            ]

            logo_table = Table(data=logo_data)

            row2_data = [
                [
                    consignee_table,
                    logo_table
                ]
            ]

            row2_table = Table(data=row2_data, colWidths=(8.8 * cm))

            row2_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(0, 4).get_coordinate,
                     self.default_border_thickness, colors.black),
                ]
            ))

            if not self._is_air:
                aircraft_data = [
                    [
                        Paragraph("XXXXXXXX XXXXXXXX XXXXXXXX", styles["Left"]),
                        Paragraph("XXXXXXXX XXXXXXXX XXXXXXXX", styles["Left"])
                    ]
                ]
            elif world_request["is_passenger_aircraft"]:
                aircraft_data = [
                    [
                        Paragraph("Passenger And Cargo Aircraft", styles["Left"]),
                        Paragraph("XXXXXXXX XXXXXXXX XXXXXXXX", styles["Left"])
                    ]
                ]
            else:
                aircraft_data = [
                    [
                        Paragraph("XXXXXXXX XXXXXXXX XXXXXXXX", styles["Left"]),
                        Paragraph("Cargo Aircraft Only", styles["Left"])
                    ]
                ]

            aircraft_table = Table(data=aircraft_data, colWidths=(2 * cm))

            aircraft_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("INNERGRID", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     "MIDDLE")
                ]
            ))

            shipment_limitation_data = [
                [
                    Paragraph("This shipment is within the limitations prescribed for: (delete non-applicable)",
                              styles["Left"])
                ],
                [
                    aircraft_table
                ]
            ]

            shipment_limitation_table = Table(data=shipment_limitation_data, rowHeights=(1.05 * cm, 1.45 * cm))

            shipment_limitation_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                ]
            ))

            if not self._is_air:
                airport_departure_data = [
                    [
                        Paragraph("", styles["Center"])
                    ],
                    [
                        Paragraph("", styles["Center"])
                    ]
                ]
            else:
                airport_departure_data = [
                    [
                        Paragraph("Airport of Departure", styles["Left"])
                    ],
                    [
                        Paragraph("{} ({})".format(self._origin_airbase.name, self._origin_airbase.code),
                                  styles["Left"])
                    ]
                ]

            airport_departure_table = Table(data=airport_departure_data, rowHeights=(0.5 * cm, 2 * cm))

            airport_departure_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate, "TOP")
                ]
            ))

            if not self._is_air:
                airport_destination_data = [
                    [
                        Paragraph("", styles["Center"])
                    ]
                ]
            else:
                airport_destination_data = [
                    [
                        Paragraph(
                            "Airport of destination: {} ({})".format(self._destination_airbase.name,
                                                                     self._destination_airbase.code), styles["Left"])
                    ]
                ]

            airport_destination_table = Table(data=airport_destination_data, rowHeights=(1 * cm))

            airport_destination_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     "MIDDLE")
                ]
            ))

            transport_details_title_data = [
                [
                    Paragraph("<b>TRANSPORT DETAILS</b>", styles["Left"])
                ]
            ]

            transport_details_title_table = Table(data=transport_details_title_data, rowHeights=(0.5 * cm))

            transport_details_title_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     "TOP"),
                ]
            ))

            air_shipment_details_data = [
                [
                    shipment_limitation_table,
                    airport_departure_table
                ]
            ]

            air_shipment_details_table = Table(data=air_shipment_details_data, colWidths=(4.4 * cm),
                                               rowHeights=(2.5 * cm))

            air_shipment_details_table.setStyle(TableStyle(
                [
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate, "TOP")
                ]
            ))

            deep_transport_details_data = [
                [
                    transport_details_title_table
                ],
                [
                    air_shipment_details_table
                ],
                [
                    airport_destination_table
                ]
            ]

            deep_transport_details_table = Table(data=deep_transport_details_data,
                                                 rowHeights=(0.5 * cm, 2.5 * cm, 1 * cm))

            deep_transport_details_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     2, colors.black),
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0)
                ]
            ))

            transport_details_data = [
                [
                    Paragraph(
                        "<i>Two completed and signed copies of this Declaration must be handed to the operator.</i>",
                        styles["Left_Indent"])
                ],
                [
                    deep_transport_details_table
                ]
            ]

            transport_details_table = Table(data=transport_details_data)

            transport_details_table.setStyle(TableStyle(
                [
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0)
                ]
            ))

            radioactive_data = [
                [
                    Paragraph("NON-RADIOACTIVE", styles["Center"]),
                    Paragraph("XXXXXXXXXX", styles["Center"])
                ]
            ]

            radioactive_table = Table(data=radioactive_data, colWidths=(3 * cm, 2.25 * cm))

            radioactive_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("INNERGRID", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     "MIDDLE"),
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0)
                ]
            ))

            shipment_type_data = [
                [
                    Paragraph("Shipment type: (delete non-applicable)", styles["Left"])
                ],
                [
                    radioactive_table
                ]
            ]

            shipment_type_table = Table(data=shipment_type_data, rowHeights=(0.5 * cm))

            shipment_type_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("LEFTPADDING", self._CartesianCoordinate(0, 1).get_coordinate,
                     self._CartesianCoordinate(0, 1).get_coordinate,
                     0.5 * cm),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0)
                ]
            ))

            warning_data = [
                [
                    Paragraph("WARNING", styles["Left_Indent"])
                ],
                [
                    Paragraph(
                        "Failure to comply in all respects with the applicable Dangerous Goods Regulations may be in "
                        "breach of the applicable law, subject to legal penalties.", styles["Left_Indent"])
                ],
                [
                    shipment_type_table
                ]
            ]

            warning_table = Table(data=warning_data, rowHeights=(0.5 * cm, 3.2 * cm, 1.075 * cm))

            warning_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("VALIGN", self._CartesianCoordinate(0, 1).get_coordinate,
                     self._CartesianCoordinate(0, 1).get_coordinate, "TOP"),
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0)
                ]
            ))

            row3_data = [
                [
                    transport_details_table,
                    warning_table
                ]
            ]

            row3_table = Table(data=row3_data, colWidths=(8.8 * cm))

            row3_table.setStyle(TableStyle(
                [
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate, "TOP")
                ]
            ))

            row4_data = [
                [
                    Paragraph("NATURE AND QUANTITY OF DANGEROUS GOODS", styles["Left"])
                ]
            ]

            row4_table = Table(data=row4_data, colWidths=(17.7 * cm))

            dg_ident_data = [
                [
                    Paragraph("Dangerous Goods Identification", styles["Center"])
                ]
            ]

            dg_ident_table = Table(data=dg_ident_data, colWidths=(9.8 * cm))

            dg_ident_table.setStyle(TableStyle(
                [
                    ("LINEBELOW", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(0, 0).get_coordinate,
                     self.default_border_thickness, colors.black, None, (2, 3, 0))
                ]
            ))

            dangerous_goods_data = [
                [
                    dg_ident_table
                ],
                [
                    Paragraph("UN No.", styles["Center"]),
                    Paragraph("Proper Shipping Name", styles["Center"]),
                    Paragraph("Class or Division (Subsidiary Risk)", styles["Center"]),
                    Paragraph("Packing Group", styles["Center"])
                ]
            ]
            dangerous_goods_data_row_heights = [0.6 * cm, 1.7 * cm]

            for dg in dg_list[page_num - 1]:
                if dg["packing_group_str"] == "N/A":
                    packing_group = ""
                else:
                    packing_group = dg["packing_group_str"]

                if not dg.get("excepted_quantity", False):
                    un = dg["un_number"]

                    if un == 8000:
                        str_un = "ID" + str(un)
                    else:
                        str_un = "UN" + str(un)

                    nos_neq = ""
                    if dg.get("nos"):
                        nos_neq = " (" + dg.get("nos", "") + ")"
                    elif dg.get("neq"):
                        nos_neq = " (" + dg.get("neq", "") + ")"

                    proper_name = dg["proper_shipping_name"] + nos_neq

                    data = [
                        Paragraph(str_un, styles["Center"]),
                        Paragraph(proper_name, styles["Center"]),
                        Paragraph(dg["class_div"] + " " + dg["subrisks_str"], styles["Center"]),
                        Paragraph(packing_group, styles["Center"])
                    ]

                    dangerous_goods_data.append(data)
                    dangerous_goods_data_row_heights.append(1 * cm)

            dangerous_goods_table = Table(data=dangerous_goods_data, colWidths=(1.1 * cm, 6 * cm, 1.5 * cm, 1.2 * cm),
                                          rowHeights=dangerous_goods_data_row_heights)

            dangerous_goods_table.setStyle(TableStyle(
                [
                    ("INNERGRID", self._CartesianCoordinate(0, 1).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black, None, (2, 3, 0)),
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("VALIGN", self._CartesianCoordinate(0, 1).get_coordinate,
                     self._CartesianCoordinate(3, 1).get_coordinate,
                     "MIDDLE"),
                    ("VALIGN", self._CartesianCoordinate(0, 2).get_coordinate,
                     self._CartesianCoordinate(3, -1).get_coordinate,
                     "TOP")
                ]
            ))

            amount_data = [
                [
                    Paragraph("Quantity and type of packing", styles["Center"]),
                    Paragraph("Packing Inst.", styles["Center"]),
                    Paragraph("Authorization", styles["Center"])
                ]
            ]
            amount_data_heights = [2.3 * cm]

            for dg in dg_list[page_num - 1]:
                measure_unit = dg["measure_unit"]

                if not dg.get("excepted_quantity", False):
                    if dg["is_limited"] and dg["is_gross"]:
                        measure_type = "G"
                        measure_unit = "KG"
                    else:
                        measure_type = ""

                    if dg["is_neq"]:
                        neq = ""

                    if self._is_air:
                        if dg["packing_type_str"]:
                            if dg["is_limited"] and dg["is_gross"]:
                                measure_type = "G"
                                measure_unit = "KG"
                                weight = dg["weight"]
                            else:
                                measure_type = ""
                                weight = dg["dg_quantity"]

                            des_str = "{} {} X {} {} {}".format(
                                dg["quantity"], dg["packing_type_str"], weight, measure_unit, measure_type
                            )

                            if dg["is_neq"]:
                                if dg["neq"]:
                                    des_str += "<br/>({})".format(dg["neq"])

                            data = [
                                Paragraph(des_str, styles["Center"]),
                                Paragraph(dg["packing_instruction"], styles["Center"]),
                                Paragraph('', styles["Center"])
                            ]
                        else:
                            if dg["is_limited"] and dg["is_gross"]:
                                measure_type = "G"
                                measure_unit = "KG"
                                weight = dg["weight"]
                            else:
                                measure_type = ""
                                weight = dg["dg_quantity"]

                            des_str = "{} X {} {} {}".format(
                                dg["quantity"], weight, measure_unit, measure_type
                            )

                            if dg["is_neq"]:
                                if dg["neq"]:
                                    des_str += "<br/>({})".format(dg["neq"])

                            data = [
                                Paragraph(des_str, styles["Center"]),
                                Paragraph(dg["packing_instruction"], styles["Center"]),
                                Paragraph('', styles["Center"])
                            ]
                    else:

                        des_str = "{} X {} {} {}".format(
                            dg["quantity"], dg["dg_quantity"], measure_unit, measure_type
                        )

                        if dg["is_neq"]:
                            if dg["neq"]:
                                des_str += "<br/>({})".format(dg["neq"])

                        data = [
                            Paragraph(des_str, styles["Center"]),
                            Paragraph(dg.get("packing_instruction", ""), styles["Center"]),
                            Paragraph('', styles["Center"])
                        ]

                    amount_data.append(data)
                    amount_data_heights.append(1 * cm)

            amount_table = Table(data=amount_data, colWidths=(4.2 * cm, 1.5 * cm, 2.1 * cm),
                                 rowHeights=amount_data_heights)

            amount_table.setStyle(TableStyle(
                [
                    ("INNERGRID", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black, None, (2, 3, 0)),
                    ("VALIGN", self._CartesianCoordinate(0, 1).get_coordinate,
                     self._CartesianCoordinate(2, -1).get_coordinate,
                     "TOP"),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(2, 0).get_coordinate,
                     "MIDDLE")
                ]
            ))

            row5_data = [
                [
                    dangerous_goods_table,
                    amount_table
                ]
            ]

            row5_table = Table(data=row5_data, colWidths=(9.8 * cm, 7.8 * cm))

            row5_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black, None, (2, 3, 0)),
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("INNERGRID", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black, None, (2, 3, 0)),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     "TOP")
                ]
            ))

            if not self._is_air:
                row6_data = [
                    [
                        Paragraph("Additional Handling Information", styles["Left"])
                    ],
                    [
                        Paragraph("CANUTEC 24 hr. Emergency Contact Tel. No.: 1-613-996-6666", styles["Left"])
                    ],
                    [
                        Spacer(width=0, height=0.05 * cm)
                    ]
                ]

                row6_table = Table(data=row6_data, colWidths=(17.6 * cm))

                row6_table.setStyle(TableStyle(
                    [
                        ("BOX", self._CartesianCoordinate(0, 2).get_coordinate,
                         self._CartesianCoordinate(-1, 2).get_coordinate,
                         self.default_border_thickness, colors.black)
                    ]
                ))
            else:
                row6_data = [
                    [
                        Paragraph("Additional Handling Information", styles["Left"]),
                        Paragraph("Packaged in accordance with ICAO/IATA regulations", styles["Left"])
                    ],
                    [
                        Paragraph("CANUTEC 24 hr. Emergency Contact Tel. No.: 1-613-996-6666", styles["Left"]),
                        Paragraph("Shipment is made under the provisions on ICAO", styles["Right"])
                    ],
                    [
                        Spacer(width=0, height=0.05 * cm),
                        Paragraph('', styles["Left"])
                    ]
                ]

                row6_table = Table(data=row6_data, colWidths=(8.8 * cm))

                row6_table.setStyle(TableStyle(
                    [
                        ("BOX", self._CartesianCoordinate(0, 2).get_coordinate,
                         self._CartesianCoordinate(-1, 2).get_coordinate,
                         self.default_border_thickness, colors.black)
                    ]
                ))

            declare_data = [
                [
                    Paragraph(
                        "<b>I hereby declare that the contents of this consignment are fully and accurately described "
                        "above by the proper shipping name, and are classified, packaged, marked and "
                        "labelled/placarded, and are in all respects in proper condition for transport according to "
                        "applicable international and national government regulations. I declare that all of the "
                        "applicable air transport requirements have been met.</b>",
                        styles["Left"])
                ]
            ]

            declare_table = Table(data=declare_data, colWidths=(12.6 * cm))

            signature_data = [
                [
                    Paragraph("Name/Title of Signatory:", styles["Left"])
                ],
                [
                    Paragraph("Place and Date:", styles["Left"])
                ],
                [
                    Paragraph("Signature", styles["Left_No_Leading"])
                ],
                [
                    Paragraph("(see warning above)", styles["Left_No_Leading_Small"])
                ],
                [
                    Paragraph('', styles["Center"])
                ]
            ]

            signature_table = Table(data=signature_data, colWidths=(5 * cm),
                                    rowHeights=(0.35 * cm, 1 * cm, 1 * cm, 0.35 * cm, 0.15 * cm))

            row7_data = [
                [
                    declare_table,
                    signature_table
                ]
            ]

            row7_table = Table(data=row7_data, colWidths=(12.6 * cm, 5 * cm))

            row7_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("INNERGRID", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(1, 0).get_coordinate, "TOP")
                ]
            ))

            data_data = [
                [
                    Paragraph("<b>SHIPPER'S DECLARATION FOR DANGEROUS GOODS</b>", styles["DG_Title"])
                ],
                [
                    row1_table
                ],
                [
                    row2_table
                ],
                [
                    row3_table
                ],
                [
                    row4_table
                ],
                [
                    row5_table
                ],
                [
                    row6_table
                ],
                [
                    row7_table
                ]
            ]

            data_table = Table(data=data_data, colWidths=(17.6 * cm))

            data_table.setStyle(TableStyle(
                [
                    ("BOX", self._CartesianCoordinate(0, 1).get_coordinate,
                     self._CartesianCoordinate(-1, 6).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("TOPPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0),
                    ("BOTTOMPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                     self._CartesianCoordinate(-1, -1).get_coordinate,
                     0)
                ]
            ))

            # Header
            if not self._is_air:
                header_data = [
                    [
                        Paragraph('', styles["Center"]),
                        data_table,
                        Paragraph('', styles["Center"])
                    ]
                ]
            else:
                header_data = [
                    [
                        self.banner,
                        data_table,
                        self.banner
                    ]
                ]

            header_table = Table(data=header_data, colWidths=(0.7 * cm, 17.7 * cm, 0.65 * cm))

            header_table.setStyle(TableStyle([
                ('VALIGN', self._CartesianCoordinate(0, 0).get_coordinate,
                 self._CartesianCoordinate(2, 0).get_coordinate,
                 'TOP'),
                ("LEFTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                 self._CartesianCoordinate(-1, -1).get_coordinate, 0),
                ("RIGHTPADDING", self._CartesianCoordinate(0, 0).get_coordinate,
                 self._CartesianCoordinate(-1, -1).get_coordinate, 0),
            ]))

            story.append(header_table)

        doc.build(story)
        return self.buffer.getvalue()

    def generate_styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Center",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  alignment=TA_CENTER,
                                  leading=9))
        styles.add(ParagraphStyle(name="Center_Small",
                                  fontname=self.fontname,
                                  fontSize=self.small_font_size,
                                  alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="Left",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  leading=9))
        styles.add(ParagraphStyle(name="Left_No_Leading",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  leading=0))
        styles.add(ParagraphStyle(name="Left_No_Leading_Small",
                                  fontname=self.fontname,
                                  fontSize=self.small_font_size,
                                  leading=0))
        styles.add(ParagraphStyle(name="Left_Indent",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  leftIndent=0.2 * cm,
                                  leading=9))
        styles.add(ParagraphStyle(name="Right",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  alignment=TA_RIGHT))
        styles.add(ParagraphStyle(name="Legal",
                                  fontname=self.fontname,
                                  fontSize=self.legal_font_size,
                                  leading=9))
        styles.add(ParagraphStyle(name="DG_Title",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  leading=20))
        return styles

    def get_base_64(self) -> str:
        return self.base64

    def get_filename(self) -> str:
        return self.filename + self.extension

    def get_pdf(self):
        return self.declaration
