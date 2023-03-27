import base64
import datetime
import os
from io import BytesIO

from django.template.loader import get_template
from xhtml2pdf import pisa

from brain import settings
from brain.settings import BASE_DIR


class PaymentDocuments:

    @staticmethod
    def link_callback(uri, rel):
        """
            Convert HTML URIs to absolute system paths so xhtml2pdf can access those
            resources
        """

        # use short variable names
        sUrl = settings.STATIC_URL  # Typically /static/
        sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
        mUrl = '/media/'  # Typically /static/media/
        mRoot = os.path.join(BASE_DIR, 'media')  # Typically /home/userX/project_static/media/

        # convert URIs to absolute system paths
        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri  # handle absolute uri (ie: http://some.tld/foo.png)

        # make sure that file exists
        if not os.path.isfile(path):
            raise Exception(
                'media URI must start with %s or %s' % (sUrl, mUrl)
            )

        return path

    def generate_receipt(self, data: dict):

        template = get_template("pdf_files/receipt.html")
        html = template.render(data)
        result = BytesIO()

        pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result, link_callback=self.link_callback)

        if not pdf.err:
            pdf_str = base64.b64encode(result.getvalue()).decode('ascii')

            return pdf_str
        return None
