import base64
from decimal import Decimal
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import Image, SimpleDocTemplate, Table, Paragraph, TableStyle, Spacer

from api.globals.documents import TABLE_LINE_THICKNESS, BBE_LOGO_PATH, BBE_BLUE, TABLE_HEADER_COLOUR, BBE_LOGO_WIDTH, \
    BBE_LOGO_HEIGHT


class CartesianCoordinate:

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    @property
    def get_coordinate(self) -> tuple:
        return self.x, self.y


class CommercialInvoice:
    filename = "Commercial_Invoice"
    extension = ".pdf"
    logo = Image(BBE_LOGO_PATH, BBE_LOGO_WIDTH, BBE_LOGO_HEIGHT)
    fontname = "Helvetica"
    title_font_size = 12
    default_font_size = 10
    small_font_size = 8
    medium_font_size = 8
    default_border_thickness = TABLE_LINE_THICKNESS
    bold_border_thickness = 0.5
    legal_font_size = 8
    sig_fig = Decimal("0.01")

    def __init__(self, shipdata: dict, order_number: str) -> None:
        self._order_number = order_number
        self.buffer = BytesIO()
        self.invoice = self._generate(shipdata)
        self.buffer.seek(0)
        self.base64 = base64.b64encode(self.buffer.read())
        self.base64 = self.base64.decode("ascii")
        self.buffer.close()

    def _generate(self, shipdata: dict):
        doc = SimpleDocTemplate(self.buffer, rightMargin=0.5 * cm, leftMargin=0.5 * cm, topMargin=1.5 * cm,
                                bottomMargin=1.5 * cm)

        story = []
        styles = self.generate_styles()

        # Header
        header_data = [
            [
                self.logo,
                Paragraph("COMMERCIAL INVOICE", styles["Default"]),
                Paragraph("", styles["Right"])
            ]
        ]

        header_table = Table(data=header_data, colWidths=(3 * cm, 11.5 * cm, 3.5 * cm))

        header_table.setStyle(TableStyle([]))

        story.append(header_table)

        # Row one
        data = [
            [
                Paragraph("DATE OF EXPORT", styles["Center_Descriptor"]),
                Paragraph("REFERENCE ONE", styles["Center_Descriptor"]),
                Paragraph("REFERENCE TWO", styles["Center_Descriptor"])
            ]
        ]

        table = Table(data=data, colWidths=(6 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BACKGROUND", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 BBE_BLUE)
            ]
        ))

        story.append(table)

        if shipdata.get("reference_two", ""):
            ref_two = "{}, {}".format(self._order_number, shipdata["reference_two"])
        else:
            ref_two = self._order_number

        # Row two
        data = [
            [
                Paragraph("", styles["Default"]),
                Paragraph(shipdata.get("reference_one", ""), styles["Default"]),
                Paragraph(ref_two, styles["Default"])
            ]
        ]

        table = Table(data=data, colWidths=(6 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 1).get_coordinate,
                 self.default_border_thickness, colors.black)
            ]
        ))

        story.append(table)

        # Row three
        data = [
            [
                Paragraph("SHIPPER/EXPORTER", styles["Center_Descriptor"]),
                Paragraph("DESTINATION", styles["Center_Descriptor"])
            ]
        ]

        table = Table(data=data, colWidths=(9 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BACKGROUND", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 BBE_BLUE)
            ]
        ))

        story.append(table)

        # Row four
        data = [
            [
                Paragraph(shipdata["origin"]["company_name"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["company_name"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"])
            ],
            [
                Paragraph(shipdata["origin"]["name"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["name"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"])
            ],
            [
                Paragraph(shipdata["origin"]["address"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["address"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"])
            ],
            [
                Paragraph(shipdata["origin"]["city"], styles["Left_Medium"]),
                Paragraph(shipdata["origin"]["province"], styles["Left_Medium"]),
                Paragraph(shipdata["origin"]["postal_code"], styles["Left_Medium"]),
                Paragraph(shipdata["origin"]["country"], styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["city"], styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["province"], styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["postal_code"], styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["country"], styles["Left_Medium"])
            ],
            [
                Paragraph("TEL: " + shipdata["origin"]["phone"], styles["Left_Medium"]),
                Paragraph("TAX ID:", styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph("TEL: " + shipdata["destination"]["phone"], styles["Left_Medium"]),
                Paragraph("TAX ID:", styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"])
            ],
        ]

        table = Table(data=data,
                      colWidths=(3.5 * cm, 2.7 * cm, 1.95 * cm, 0.85 * cm, 3.5 * cm, 2.7 * cm, 1.95 * cm, 0.85 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(3, 5).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BOX", CartesianCoordinate(4, 0).get_coordinate, CartesianCoordinate(7, 5).get_coordinate,
                 self.default_border_thickness, colors.black)
            ]
        ))

        story.append(table)

        # Row five
        data = [
            [
                Paragraph("BROKER", styles["Center_Descriptor"]),
                Paragraph("SOLD TO", styles["Center_Descriptor"])
            ]
        ]

        table = Table(data=data, colWidths=(9 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BACKGROUND", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 BBE_BLUE)
            ]
        ))

        story.append(table)

        # Row six
        data = [
            [
                Paragraph(shipdata.get("broker", {}).get("company_name", ""), styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["company_name"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"])
            ],
            [
                Paragraph(shipdata.get("broker", {}).get("address", ""), styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["name"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"])
            ],
            [
                Paragraph(shipdata.get("broker", {}).get("city", ""), styles["Left_Medium"]),
                Paragraph(shipdata.get("broker", {}).get("postal_code", ""), styles["Left_Medium"]),
                Paragraph(shipdata.get("broker", {}).get("province", ""), styles["Left_Medium"]),
                Paragraph(shipdata.get("broker", {}).get("country", ""), styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["address"], styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"])
            ],
            [
                Paragraph("TEL: " + shipdata.get("broker", {}).get("phone", ""), styles["Left_Medium"]),
                Paragraph("ACCOUNT#:", styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["city"], styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["province"], styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["postal_code"], styles["Left_Medium"]),
                Paragraph(shipdata["destination"]["country"], styles["Left_Medium"])
            ],
            [
                Paragraph("FAX:", styles["Left_Medium"]),
                Paragraph("TAX ID:", styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph("TEL: " + shipdata["destination"]["phone"], styles["Left_Medium"]),
                Paragraph("TAX ID:", styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"]),
                Paragraph('', styles["Left_Medium"])
            ],
        ]

        table = Table(data=data,
                      colWidths=(3.5 * cm, 2.7 * cm, 1.95 * cm, 0.85 * cm, 3.5 * cm, 2.7 * cm, 1.95 * cm, 0.85 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(3, 5).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BOX", CartesianCoordinate(4, 0).get_coordinate, CartesianCoordinate(7, 5).get_coordinate,
                 self.default_border_thickness, colors.black)
            ]
        ))

        story.append(table)

        # Row seven
        data = [
            [
                Paragraph("COUNTRY OF ULTIMATE DESTINATION", styles["Center_Descriptor"]),
                Paragraph("REASON FOR SENDING", styles["Center_Descriptor"]),
                Paragraph("INTERNATIONAL AIR WAYBILL NUMBER", styles["Center_Descriptor"])
            ]
        ]

        table = Table(data=data, colWidths=(6.75 * cm, 4.5 * cm, 6.75 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BACKGROUND", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 BBE_BLUE)
            ]
        ))

        story.append(table)

        # Row eight
        data = [
            [
                Paragraph(shipdata["destination"]["country"], styles["Default"]),
                Paragraph("SOLD", styles["Default"]),
                Paragraph(shipdata.get("AWB", ""), styles["Default"])
            ]
        ]

        table = Table(data=data, colWidths=(6.75 * cm, 4.5 * cm, 6.75 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 1).get_coordinate,
                 self.default_border_thickness, colors.black)
            ]
        ))

        story.append(table)

        # Row nine
        data = [
            [
                Paragraph("DESCRIPTION OF GOODS", styles["Center_Descriptor"]),
                Paragraph("COM", styles["Center_Descriptor"]),
                Paragraph("QTY", styles["Center_Descriptor"]),
                Paragraph("TOTAL WEIGHT", styles["Center_Descriptor"]),
                Paragraph("UNIT VALUE", styles["Center_Descriptor"]),
                Paragraph("TOTAL VALUE", styles["Center_Descriptor"])
            ]
        ]

        table = Table(data=data, colWidths=(8 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(2, 0).get_coordinate, CartesianCoordinate(3, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(3, 0).get_coordinate, CartesianCoordinate(4, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(4, 0).get_coordinate, CartesianCoordinate(5, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BACKGROUND", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 BBE_BLUE)
            ]
        ))

        story.append(table)

        total_items = 0
        total_weight = Decimal("0.00")
        total_value = Decimal("0.00")
        total_unit_value = Decimal("0.00")

        for commodity in shipdata["commodities"]:
            total_value += (commodity["quantity"] * Decimal(commodity["unit_value"]))
            total_unit_value += Decimal(commodity["unit_value"])
            total_items += commodity["quantity"]
            total_weight += Decimal(commodity["total_weight"])
            data = [
                [
                    Paragraph(commodity["description"], styles["Default"]),
                    Paragraph(commodity["made_in_country_code"], styles["Default"]),
                    Paragraph(str(commodity["quantity"]), styles["Default"]),
                    Paragraph(str(Decimal(commodity["total_weight"]).quantize(self.sig_fig)), styles["Default"]),
                    Paragraph(str(Decimal(commodity["unit_value"]).quantize(self.sig_fig)), styles["Default"]),
                    Paragraph(str((Decimal(commodity["unit_value"]) * commodity["quantity"]).quantize(self.sig_fig)),
                              styles["Default"])
                ]
            ]

            table = Table(data=data, colWidths=(8 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm))

            table.setStyle(TableStyle(
                [
                    ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("INNERGRID", CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("INNERGRID", CartesianCoordinate(2, 0).get_coordinate, CartesianCoordinate(3, 1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("INNERGRID", CartesianCoordinate(3, 0).get_coordinate, CartesianCoordinate(4, 1).get_coordinate,
                     self.default_border_thickness, colors.black),
                    ("INNERGRID", CartesianCoordinate(4, 0).get_coordinate, CartesianCoordinate(5, 1).get_coordinate,
                     self.default_border_thickness, colors.black)
                ]
            ))

            story.append(table)

        # Row eleven
        data = [
            [
                Paragraph("SUB-TOTAL", styles["Center_Descriptor"]),
                Paragraph("", styles["Default"]),
                Paragraph(str(total_items), styles["Center_Descriptor"]),
                Paragraph(str(total_weight.quantize(self.sig_fig)), styles["Center_Descriptor"]),
                Paragraph(str(total_unit_value.quantize(self.sig_fig)), styles["Center_Descriptor"]),
                Paragraph(str(total_value.quantize(self.sig_fig)), styles["Center_Descriptor"])
            ]
        ]

        table = Table(data=data, colWidths=(8 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(2, 0).get_coordinate, CartesianCoordinate(3, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(3, 0).get_coordinate, CartesianCoordinate(4, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(4, 0).get_coordinate, CartesianCoordinate(5, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BACKGROUND", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 colors.blueviolet)
            ]
        ))

        story.append(table)

        # Row twelve
        data = [
            [
                Paragraph("TOTAL NO. OF PACKAGES", styles["Center_Descriptor"]),
                Paragraph("BILL OF LADING", styles["Center_Descriptor"])
            ]
        ]

        table = Table(data=data, colWidths=(9 * cm, 9 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("BACKGROUND", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 BBE_BLUE)
            ]
        ))

        story.append(table)

        # Row thirteen
        data = [
            [
                Paragraph(str(total_items), styles["Default"]),
                Paragraph(shipdata.get("tracking_number", ""), styles["Default"])
            ]
        ]

        table = Table(data=data, colWidths=(9 * cm, 9 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness, colors.black)
            ]
        ))

        story.append(table)

        # Row fourteen
        data = [
            [
                [
                    Paragraph("Comments:", styles["Left"]),
                    Paragraph(shipdata.get("special_instructions", ""), styles["Left_Medium"]),
                ],
                [
                    [Paragraph("CURRENCY", styles["Center_Small"])],
                    [Paragraph("CAD", styles["Default"])],
                ],
                Paragraph("TOTAL VALUE OF GOODS: ", styles["Left"]),
                Paragraph(str(total_value.quantize(self.sig_fig)), styles["Right"])
            ]
        ]

        table = Table(data=data, colWidths=(7.9 * cm, 2.1 * cm, 4.95 * cm, 3.05 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness,
                 colors.black),
                ("INNERGRID", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(1, 1).get_coordinate,
                 self.default_border_thickness,
                 colors.black),
                ("INNERGRID", CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 1).get_coordinate,
                 self.default_border_thickness,
                 colors.black),
                (
                    'VALIGN', CartesianCoordinate(1, 0).get_coordinate, CartesianCoordinate(2, 0).get_coordinate,
                    'MIDDLE'),
                ('VALIGN', CartesianCoordinate(2, 0).get_coordinate, CartesianCoordinate(3, 0).get_coordinate, 'MIDDLE')
            ]
        ))

        story.append(table)

        # Row fifteen
        data = [
            [
                Paragraph(
                    "I hearby certify that this invoice shows the actual price of the goods described, that no other "
                    "invoice has been issued, and that all particulars are true and correct.",
                    styles["Legal"])
            ]
        ]

        table = Table(data=data, colWidths=(18 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black)
            ]
        ))

        story.append(table)

        # Row sixteen
        data = [
            [Spacer(0, 0.5 * cm)],
            [
                Paragraph('', styles["Default"]),
                Paragraph('', styles["Default"]),
                Paragraph('', styles["Default"]),
                Paragraph('', styles["Default"])
            ],
            [
                Paragraph("____________________________", styles["Center_Low"]),
                Paragraph("____________________________", styles["Center_Low"]),
                Paragraph("___________", styles["Center_Low"]),
                Paragraph("_____________", styles["Center_Low"])
            ],
            [
                Paragraph("Shipper Name", styles["Legal"]),
                Paragraph("Signature", styles["Legal"]),
                Paragraph("Time HH:MM", styles["Legal"]),
                Paragraph("Date DD-MM-YYYY", styles["Legal"])
            ]
        ]

        table = Table(data=data, colWidths=(6 * cm, 6 * cm, 3 * cm, 3 * cm))

        table.setStyle(TableStyle(
            [
                ("BOX", CartesianCoordinate(0, 0).get_coordinate, CartesianCoordinate(-1, -1).get_coordinate,
                 self.default_border_thickness, colors.black)
            ]
        ))

        story.append(table)

        doc.build(story)
        return self.buffer.getvalue()

    def generate_styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Default",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="Left",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size))
        styles.add(ParagraphStyle(name="Right",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  alignment=TA_RIGHT))
        styles.add(ParagraphStyle(name="Center_Descriptor",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  alignment=TA_CENTER,
                                  textColor=TABLE_HEADER_COLOUR))
        styles.add(ParagraphStyle(name="Center_Small",
                                  fontname=self.fontname,
                                  fontSize=self.small_font_size,
                                  alignment=TA_CENTER))
        styles.add(ParagraphStyle(name="Left_Medium",
                                  fontname=self.fontname,
                                  fontSize=self.medium_font_size))
        styles.add(ParagraphStyle(name="Center_Low",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  alignment=TA_CENTER, leading=6))
        styles.add(ParagraphStyle(name="Legal",
                                  fontname=self.fontname,
                                  fontSize=self.legal_font_size,
                                  leading=10,
                                  alignment=TA_CENTER))
        return styles

    def get_base_64(self) -> str:
        return self.base64

    def get_filename(self) -> str:
        return self.filename + self.extension

    def get_pdf(self):
        return self.invoice
