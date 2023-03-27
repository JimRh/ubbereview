import base64
from io import BytesIO

from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Image


class DangerousGoodBattery:
    filename = "lithium-battery"
    extension = ".pdf"
    _lithium_ion = (3480, 3481)
    _lithium_metal = (3090, 3091)

    def __init__(self, un_number: int) -> None:
        self._un_number = un_number
        self._buffer = BytesIO()
        self.placard = self._generate()
        self._buffer.seek(0)
        self.base64 = base64.b64encode(self._buffer.read()).decode("ascii")
        self._buffer.close()

    def _generate(self):
        doc = SimpleDocTemplate(self._buffer)

        if self._un_number in self._lithium_ion:
            story = [
                Image("assets/dangerous_goods/labels/generic/lithium-ion-battery.png", width=120 * mm, height=110 * mm)
            ]
        else:
            story = [
                Image("assets/dangerous_goods/labels/generic/lithium-metal-battery.png", width=120 * mm, height=110 * mm)
            ]

        doc.build(story)
        return self._buffer.getvalue()

    def get_base_64(self) -> str:
        return self.base64

    def get_filename(self) -> str:
        return self.filename + self.extension

    def get_pdf(self):
        return self.placard
