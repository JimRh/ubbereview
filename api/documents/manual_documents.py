import base64
import copy
import os
from io import BytesIO

from django.template.loader import get_template
from xhtml2pdf import pisa

from api.documents.generators.sealift_form import SealiftForm
from api.globals.carriers import CALM_AIR, AIR_CARRIERS, AIR_NORTH, PERIMETER_AIR, CARGO_JET, WESTJET, BUFFALO_AIRWAYS, \
    AIR_INUIT
from brain import settings
from brain.settings import BASE_DIR


class ManualDocuments:
    _b13a_template = 'api/documents/pdf/b13a_template.pdf'

    def __init__(self, gobox_request: dict) -> None:
        self._gobox_request = gobox_request
        self._sub_account = gobox_request["objects"]['sub_account']
        self._is_dg = gobox_request["is_dangerous_goods"]

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

    def _format_carrier_options(self):
        option_names = self._gobox_request.get("option_names", [])

        if option_names:
            names = option_names[0]

            for i in range(1, len(option_names)):
                names += ", " + option_names[i]

            self._gobox_request["names"] = names
        else:
            self._gobox_request["names"] = ""

    def _format_awb_packages(self):
        processed = []
        temp = []
        count = 0
        is_bottom = False
        is_move_both = False
        is_first_page = True

        for package in self._gobox_request["packages"]:

            if is_first_page:
                if 7 <= count < 17:
                    is_bottom = True
                elif 18 <= count < 19:
                    is_bottom = False
                    is_move_both = True

                if count >= 19:
                    is_bottom = False
                    is_move_both = False
                    is_first_page = False
                    processed.append((temp, True))
                    temp = []
                    count = 0
                else:
                    count += 2

                    if package.get("is_dangerous_good", False):
                        count += 1

                    if package.get("is_pharma", False):
                        count += 1
            else:
                if 33 <= count < 48:
                    is_bottom = True
                elif 49 <= count < 50:
                    is_bottom = False
                    is_move_both = True

                if count >= 51:
                    is_bottom = False
                    is_move_both = False
                    is_first_page = False
                    processed.append((temp, True))
                    temp = []
                    count = 0
                else:
                    count += 2

                    if package.get("is_dangerous_good", False):
                        count += 1

                    if package.get("is_pharma", False):
                        count += 1

            temp.append(package)

        if is_first_page:
            if 8 <= count < 19:
                is_bottom = True
            elif 20 <= count < 21:
                is_bottom = False
                is_move_both = True
        else:
            if 34 <= count < 49:
                is_bottom = True
            elif 50 <= count < 51:
                is_bottom = False
                is_move_both = True

        processed.append((temp, False))

        self._gobox_request["is_bottom"] = is_bottom
        self._gobox_request["is_move_both"] = is_move_both
        self._gobox_request["awb_packages"] = processed

    def _format_bol_packages(self):
        processed = []
        temp = []
        count = 0
        is_move_dg_info = False
        is_move_both = False
        is_first_page = True

        for package in self._gobox_request["packages"]:
            if is_first_page:
                if 5 <= count < 7:
                    is_move_dg_info = True
                elif 7 <= count < 8:
                    is_move_dg_info = False
                    is_move_both = True

                if count >= 8:
                    is_move_dg_info = False
                    is_move_both = False
                    is_first_page = False
                    processed.append((temp, True))
                    temp = []
                    count = 0
                else:
                    count += 1

                    if package.get("is_dangerous_good", False):
                        count += 1

                    if package.get("is_pharma", False):
                        count += 1

            else:
                if 10 <= count < 12:
                    is_move_dg_info = True
                elif 12 <= count < 14:
                    is_move_dg_info = False
                    is_move_both = True

                if count >= 14:
                    is_move_dg_info = False
                    is_move_both = False
                    is_first_page = False
                    processed.append((temp, True))
                    temp = []
                    count = 0
                else:
                    count += 1

                    if package.get("is_dangerous_good", False):
                        count += 1

                    if package.get("is_pharma", False):
                        count += 1

            package["total_weight_imperial"] = round(package["imperial_weight"] * package["quantity"], 2)
            package["total_weight"] = round(package["weight"] * package["quantity"], 2)
            temp.append(package)

        if is_first_page:
            if 8 <= count < 10:
                is_move_dg_info = True
            elif 10 <= count < 12:
                is_move_dg_info = False
                is_move_both = True
        else:
            if 14 <= count < 16:
                is_move_dg_info = True
            elif 16 <= count < 18:
                is_move_dg_info = False
                is_move_both = True

        processed.append((temp, False))

        self._gobox_request["is_move_dg"] = is_move_dg_info
        self._gobox_request["is_move_both"] = is_move_both
        self._gobox_request["bol_packages"] = processed

    def _format_cargo_packages(self):
        processed = []

        for package in self._gobox_request["packages"]:
            qty = package["quantity"]

            for i in range(0, int(qty)):
                copied = copy.deepcopy(package)
                copied["is_last"] = False
                processed.append(copied)

        processed[-1]["is_last"] = True
        self._gobox_request["cargo_packages"] = processed

    def generate_bol(self):
        self._format_bol_packages()
        self._format_carrier_options()

        if str(self._sub_account.subaccount_number) in ["1b65f4d9-9cd6-4162-84b2-5ad85bd12346", "1ac69699-f4fc-4cd2-a400-6ac582f005a2"]:
            self._gobox_request["is_fathom"] = True
        else:
            self._gobox_request["is_fathom"] = False

        template = get_template("pdf_files/bill_of_lading.html")
        html = template.render(self._gobox_request)
        result = BytesIO()

        pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result, link_callback=self.link_callback)

        if not pdf.err:
            pdf_str = base64.b64encode(result.getvalue()).decode('ascii')

            return pdf_str
        return None

    def generate_cargo_label(self):
        self._format_cargo_packages()

        template = get_template("pdf_files/cargo_labels.html")
        html = template.render(self._gobox_request)
        result = BytesIO()

        pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result, link_callback=self.link_callback)

        if not pdf.err:
            pdf_str = base64.b64encode(result.getvalue()).decode('ascii')

            return pdf_str
        return None

    def generate_airwaybill(self, carrier_id: int):

        if not carrier_id or carrier_id not in AIR_CARRIERS:
            raise Exception

        self._format_awb_packages()

        if carrier_id == CALM_AIR:
            template = get_template("pdf_files/airline_awb/calm_air_awb.html")
        elif carrier_id == AIR_NORTH:
            template = get_template("pdf_files/airline_awb/air_north_awb.html")
        elif carrier_id == PERIMETER_AIR:
            template = get_template("pdf_files/airline_awb/perimeter_awb.html")
        elif carrier_id == CARGO_JET:
            template = get_template("pdf_files/airline_awb/cargojet_awb.html")
        elif carrier_id == WESTJET:
            template = get_template("pdf_files/airline_awb/westjet.html")
        elif carrier_id == BUFFALO_AIRWAYS:
            template = get_template("pdf_files/airline_awb/buffalo_awb.html")
        elif carrier_id == AIR_INUIT:
            template = get_template("pdf_files/airline_awb/air_inuit_awb.html")
        else:
            template = get_template("pdf_files/airline_awb/bbe_awb.html")

        html = template.render(self._gobox_request)
        result = BytesIO()

        pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result, link_callback=self.link_callback)

        if not pdf.err:
            pdf_str = base64.b64encode(result.getvalue()).decode('ascii')

            return pdf_str
        return None

    def generate_calm_air_label(self):
        self._format_cargo_packages()

        template = get_template("pdf_files/calm_air_label.html")
        html = template.render(self._gobox_request)
        result = BytesIO()

        pdf = pisa.CreatePDF(BytesIO(html.encode("UTF-8")), dest=result, link_callback=self.link_callback)

        if not pdf.err:
            pdf_str = base64.b64encode(result.getvalue()).decode('ascii')

            return pdf_str
        return None

    # TODO: Improve DG declaration and move it here
    def generate_dg_declaration(self):
        pass

    # TODO: Improve DG placard and move it here
    def generate_dg_placard(self):
        pass

    def generate_sealift_form(self):
        """
            Create Filled sealift shipping form.
            :return: Encoded base64 string of the PDF
        """
        form = SealiftForm(gobox_request=self._gobox_request)

        return form.make_form()
