import base64
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Image, Table, TableStyle, Paragraph


class RotatedTable(Table):

    def __init__(self, data, colWidths=None, rowHeights=None, style=None,
                 repeatRows=0, repeatCols=0, splitByRow=1, emptyTableAction=None, ident=None,
                 hAlign=None, vAlign=None, normalizedData=0, cellStyles=None, rowSplitRange=None,
                 spaceBefore=None, spaceAfter=None, longTableOptimize=None):
        super().__init__(data, colWidths, rowHeights, style, repeatRows, repeatCols, splitByRow, emptyTableAction,
                         ident, hAlign, vAlign, normalizedData, cellStyles, rowSplitRange, spaceBefore, spaceAfter,
                         longTableOptimize)
        self._curweight = self._curcolor = self._curcellstyle = None

    def draw(self):
        trans_mult = self._cellvalues[0][0][0].height / 9
        x_cord = 122 + (6.25 * (trans_mult - 1))
        y_cord = -109.5 + (-2.5 * (trans_mult - 1))
        canvas = self.canv

        canvas.rotate(45)
        canvas.translate(x_cord, y_cord)
        self._drawBkgrnd()
        if not self._spanCmds:
            # old fashioned case, no spanning, steam on and do each cell
            for row, rowstyle, rowpos, rowheight in zip(self._cellvalues, self._cellStyles, self._rowpositions[1:],
                                                        self._rowHeights):
                for cellval, cellstyle, colpos, colwidth in zip(row, rowstyle, self._colpositions[:-1],
                                                                self._colWidths):
                    self._drawCell(cellval, cellstyle, (colpos, rowpos), (colwidth, rowheight))
        self._drawLines()


class DangerousGoodPlacard:
    extension = ".pdf"
    fontname = "Helvetica"
    default_font_size = 9

    def __init__(self, world_request: dict, width: int = 142, height: int = 142) -> None:
        self._width = width
        self._height = height
        self.filename = "DG-" + world_request["class_div"] + world_request["subrisks_str"]
        self._dg_label = world_request["placard_img"]
        self._color = get_color(self._dg_label.background_rgb)
        self._font_color = get_color(self._dg_label.font_rgb)
        self._buffer = BytesIO()
        self.placard = self._generate(world_request)
        self._buffer.seek(0)
        self.base64 = base64.b64encode(self._buffer.read()).decode("ascii")
        self._buffer.close()

    class _CartesianCoordinate:

        def __init__(self, x: int, y: int) -> None:
            self.x = x
            self.y = y

        @property
        def get_coordinate(self) -> tuple:
            return self.x, self.y

    def _generate(self, world_request: dict):
        doc = SimpleDocTemplate(self._buffer)
        story = []
        styles = self.generate_styles()
        story.append(Image(self._dg_label.label, width=self._width * mm, height=self._height * mm))

        data = [
            [
                Paragraph(world_request["proper_shipping_name"], styles["Center"])
            ],
            [
                Paragraph("UN" + str(world_request["un_number"]), styles["Center"])
            ]
        ]

        data_table = RotatedTable(data=data, colWidths=(100.25 * mm))

        data_table.setStyle(TableStyle(
            [
                (
                    "BOX", self._CartesianCoordinate(0, 0).get_coordinate,
                    self._CartesianCoordinate(-1, -1).get_coordinate,
                    0.65, colors.black),
                ("VALIGN", self._CartesianCoordinate(0, 0).get_coordinate,
                 self._CartesianCoordinate(-1, -1).get_coordinate,
                 "MIDDLE"),
                ("BACKGROUND", self._CartesianCoordinate(0, 0).get_coordinate,
                 self._CartesianCoordinate(-1, -1).get_coordinate,
                 self._color)
            ]
        ))

        story.append(data_table)

        doc.build(story)
        return self._buffer.getvalue()

    def generate_styles(self):
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Center",
                                  fontname=self.fontname,
                                  fontSize=self.default_font_size,
                                  alignment=TA_CENTER,
                                  leading=9,
                                  textColor=self._font_color))
        return styles

    def get_base_64(self) -> str:
        return self.base64

    def get_filename(self) -> str:
        return self.filename + self.extension

    def get_pdf(self):
        return self.placard


def get_color(value: str) -> Color:
    values = value.split(',')
    return Color(int(values[0]) / 255, int(values[1]) / 255, int(values[2]) / 255)
