import base64
from io import BytesIO

from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Image


class SimpleImageOverlay:
    filename = "Generic Placard"
    extension = ".pdf"

    def __init__(self, placard, width: int = 100, height: int = 100):
        self._placard = placard
        self._width = width
        self._height = height
        self._buffer = BytesIO()
        self.declaration = self._generate()
        self._buffer.seek(0)
        self.base64 = base64.b64encode(self._buffer.read()).decode("ascii")
        self._buffer.close()

    def _generate(self):
        doc = SimpleDocTemplate(self._buffer)
        story = [Image(self._placard, width=self._width * mm, height=self._height * mm)]

        doc.build(story)
        return self._buffer.getvalue()

    def get_base_64(self) -> str:
        return self.base64

    def get_filename(self) -> str:
        return self.filename + self.extension

    def get_pdf(self):
        return self.declaration
