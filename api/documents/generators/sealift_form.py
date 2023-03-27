"""

"""
import base64
import io
from datetime import datetime

import pdfrw

from api.globals.carriers import NEAS, NSSI


class SealiftForm:
    """
       Auto fill sealift forms (NSSI and NEAS)
    """
    _first = "FI"
    _second = "SE"
    _third = "TH"

    _annot_key = '/Annots'
    _annot_field_key = '/T'
    _annot_val_key = '/V'
    _annot_rect_key = '/Rect'
    _subtype_key = '/Subtype'
    _widget_subtype_key = '/Widget'

    _nssi_template = 'api/documents/pdf/nssi.pdf'
    _neas_template = 'api/documents/pdf/neas.pdf'

    _packing_name = {
        "OC": "Open Crate",
        "CC": "Closed Crate",
        "FC": "Fragile Closed Crate",
        "ST": "Strapping",
        "SB": "Strapping on a base"
    }

    def __init__(self, gobox_request: dict):
        self._code = gobox_request["carrier_id"]
        self._gobox_request = gobox_request

    def write_fillable_pdf(self, input_pdf_path, data_dict):
        """
            Writes data to a fillable form pdf file
            :param input_pdf_path: Path of Form location
            :param data_dict: Dictionary of data to be written to form
            :return: Encoded base64 string of the PDF
        """
        template_pdf = pdfrw.PdfReader(input_pdf_path)

        # Loop through pages of the pdf
        for page in template_pdf.pages:

            annotations = page[self._annot_key]
            # Loop through annotation (PDF Form fields)
            for annotation in annotations:
                if annotation[self._subtype_key] == self._widget_subtype_key:

                    if annotation[self._annot_field_key]:
                        key = annotation[self._annot_field_key][1:-1]

                        if key in data_dict.keys():
                            # Add value to the PDF Form
                            annotation.update(pdfrw.PdfDict(V='{}'.format(data_dict[key])))

        template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))

        # Capture PDF output stream and create base 64 doc string
        output_stream = io.BytesIO()
        pdfrw.PdfWriter().write(output_stream, template_pdf)
        output_stream.seek(0)
        encoded = base64.b64encode(output_stream.read()).decode('ascii')
        output_stream.close()

        return encoded

    def _map_data(self):
        """
            Map GoBox Request to Form data format
        """
        origin = self._gobox_request["origin"]
        destination = self._gobox_request["destination"]
        sailing = self._gobox_request["objects"]["sailing"]

        first_date = ""
        second_date = ""
        third_date = ""

        if sailing.name == "FI":
            first_date = sailing.get_name_display()
        elif sailing.name == "SE":
            second_date = sailing.get_name_display()
        elif sailing.name == "TH":
            third_date = sailing.get_name_display()

        self._data = {
            'port': sailing.port.name,
            'first': first_date,
            'second': second_date,
            'third': third_date,
            'order_number': self._gobox_request["order_number"],
            'project': self._gobox_request.get("project", ""),
            'po_number': self._gobox_request.get("reference_one", ""),
            'reference_two': self._gobox_request.get("reference_two", ""),
            'notes': self._gobox_request.get("special_instructions", ""),
            'bill_name': "BBE Expediting Ltd.",
            'origin_address': origin["address"],
            'origin_city': origin["city"],
            'origin_province': origin["province"],
            'origin_country': origin["country"],
            'origin_postal_code': origin["postal_code"],
            'origin_name': origin["name"],
            'origin_phone': origin["phone"],
            'origin_email': origin["email"],
            'destination_address': destination["address"],
            'destination_city': destination["city"],
            'destination_city_1': destination["city"],
            'destination_province': destination["province"],
            'destination_country': destination["country"],
            'destination_postal_code': destination["postal_code"],
            'destination_company': destination["company_name"],
            'destination_name': destination["name"],
            'destination_phone': destination["phone"],
            'destination_email': destination["email"],
            'date': datetime.now().strftime("%Y/%m/%d"),
            'signature': origin["name"],
        }

    def _nssi_sailing(self):
        sailing_date = self._gobox_request["objects"]["sailing"]
        sailing = sailing_date.name

        city = self._gobox_request["destination"].get("city", "")
        city = city.lower()

        if city in ["arctic bay", "clyde river", "grise fjord", "kugaaruk", "nanisivik", "pond inlet", "qikiqtarjuaq",
                    "resolute bay"]:
            self._data["se_pond"] = "X"
        elif city in ["igloolik", "hall beach"]:
            self._data["se_hall"] = "X"
        elif city in ["repulse bay", "naujat"]:
            self._data["se_repluse"] = "X"

            if sailing == self._second:
                self._data["se_repluse"] = "X"
            elif sailing == self._third:
                self._data["th_repluse"] = "X"

        elif city in ["iqaluit"]:

            if sailing == self._first:
                self._data["fr_iqaluit"] = "X"
            elif sailing == self._second:
                self._data["se_iqaluit"] = "X"
            elif sailing == self._third:
                self._data["th_iqaluit"] = "X"

        elif city in ["cape dorset"]:

            if sailing == self._first:
                self._data["fr_cape_dorset"] = "X"
            elif sailing == self._third:
                self._data["th_cape_dorset"] = "X"

        elif city in ["kimmirut", "pangnirtung"]:

            if sailing == self._first:
                self._data["fr_kimmirut"] = "X"
            elif sailing == self._third:
                self._data["se_kimmirut"] = "X"

        elif city in ["cambridge bay", "kugluktuk", "bathurst inlet", "umingmaktok", "gjoa haven", "taloyoak"]:
            self._data["se_cam"] = "X"
        elif city in ["sanikiluaq"]:

            if sailing == self._first:
                self._data["fr_sani"] = "X"
            elif sailing == self._third:
                self._data["th_sani"] = "X"

        elif city in ["rankin inlet"]:

            if sailing == self._first:
                self._data["fr_rankin"] = "X"
            elif sailing == self._second:
                self._data["se_rankin"] = "X"
            elif sailing == self._third:
                self._data["th_rankin"] = "X"

        elif city in ["arviat", "chesterfield inlet", "whale cove", "coral harbour"]:

            if sailing == self._first:
                self._data["fr_aviat"] = "X"
            elif sailing == self._third:
                self._data["th_aviat"] = "X"

        elif city in ["baker lake"]:

            if sailing == self._first:
                self._data["fr_baker"] = "X"
            elif sailing == self._second:
                self._data["se_baker"] = "X"

    def _generate_packages(self):
        """
            Format packages to pdf form format.
        """
        data = {}
        package_count = 1
        crating_count = 1
        dg_count = 1
        vehicle_count = 1
        container_count = 0

        for pack in self._gobox_request["packages"]:

            if pack["package_type"] == "DG":
                description = "{}: {}, PG: {}".format(
                    pack["description"],
                    pack["proper_shipping_name"],
                    pack["packing_group"]
                )

                data["dg_des_row_{}".format(dg_count)] = description
                data["dg_qty_row_{}".format(dg_count)] = pack["quantity"]
                data["dg_l_row_{}".format(dg_count)] = pack["length"]
                data["dg_w_row_{}".format(dg_count)] = pack["width"]
                data["dg_h_row_{}".format(dg_count)] = pack["height"]
                data["dg_vol_row_{}".format(dg_count)] = pack["volume"]
                data["dg_weight_row_{}".format(dg_count)] = pack["weight"]
                data["dg_un_row_{}".format(dg_count)] = pack["un_number"]
                data["dg_class_row_{}".format(dg_count)] = pack["class"]
                dg_count += 1
            elif pack["package_type"] == "VEHICLE":
                description = "{} - {} - {}, VIN: {}, Running: {}, Theft: {}".format(
                    pack["description"],
                    pack["year"],
                    pack["model"],
                    pack["vin"],
                    pack["condition"],
                    pack["anti_theft"],
                )

                data["vehicle_des_row_{}".format(vehicle_count)] = description
                data["vehicle_model_row_{}".format(vehicle_count)] = pack["model"]
                data["vehicle_year_row_{}".format(vehicle_count)] = pack["year"]
                data["vehicle_qty_row_{}".format(vehicle_count)] = pack["quantity"]
                data["vehicle_vol_row_{}".format(vehicle_count)] = pack["volume"]
                data["vehicle_weight_row_{}".format(vehicle_count)] = pack["weight"]
                vehicle_count += 1
            elif pack["package_type"] == "CONTAINER":
                container_count += 1
            else:
                description = "{} - {}x{}x{} cm".format(
                    pack["description"],
                    pack["length"],
                    pack["width"],
                    pack["height"],
                )
                dims = "{}x{}x{} cm".format(
                    pack["length"],
                    pack["width"],
                    pack["height"],
                )

                data["package_des_row_{}".format(package_count)] = description
                data["package_dims_row_{}".format(package_count)] = dims
                data["package_qty_row_{}".format(package_count)] = pack["quantity"]
                data["package_vol_row_{}".format(package_count)] = pack["volume"]
                data["package_weight_row_{}".format(package_count)] = pack["weight"]
                package_count += 1

            packing = pack.get('packaging', "NA")

            if packing != "NA":
                description = "{} - {}x{}x{} cm".format(
                    pack["description"],
                    pack["length"],
                    pack["width"],
                    pack["height"],
                )

                data["crate_d_row_{}".format(crating_count)] = description
                data["crate_type_row_{}".format(crating_count)] = self._packing_name.get(packing, "OC")
                data["crate_v_row_{}".format(crating_count)] = pack["volume"]
                crating_count += 1
        if container_count >= 1:
            data["merchant"] = "Yes"
            data["container_qty_merchant"] = container_count

        self._data.update(data)

    def make_form(self):
        """
            Create filled sealift form based on the carrier code.
            :return: Encoded base64 string of the PDF or empty string
        """
        self._map_data()
        self._generate_packages()

        if self._code == NEAS:
            encoded = self.write_fillable_pdf(input_pdf_path=self._neas_template, data_dict=self._data)
            return encoded
        elif self._code == NSSI:
            self._nssi_sailing()
            encoded = self.write_fillable_pdf(input_pdf_path=self._nssi_template, data_dict=self._data)
            return encoded
        return ""
