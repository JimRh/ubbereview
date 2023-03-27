import base64
import io
from decimal import Decimal
from enum import unique, IntEnum
from typing import Dict, Any, Union, Tuple, List

from PyPDF2 import PdfFileReader, PdfFileWriter
from django.core.mail import EmailMessage
from django.utils.datetime_safe import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
from reportlab.pdfgen import canvas

from api.models import Province, Country, Carrier
from brain.settings import B13A_FILING_EMAIL, EMAIL_HOST_USER

TEMPLATE_FILE = 'api/Documents/b13a_template.pdf'
FONT_NAME = 'Helvetica'
FONT_SIZE = 12


@unique
class ModeOfTransportation(IntEnum):
    road = 1
    rail = 2
    sea = 3
    air = 4
    other = 5


def b13a(shipping_request: Dict[str, Any], order_number: str, total_shipping_cost: Decimal, tracking_number: str = '',
         transport_mode: ModeOfTransportation = ModeOfTransportation.air) -> str:
    page_one_packet = io.BytesIO()
    page_one_canvas = canvas.Canvas(page_one_packet, pagesize=letter)

    # HEADER
    process_header(page_one_canvas)
    # HEADER

    # SECTION_ONE
    # process_section_one(page_one_canvas)
    # SECTION_ONE

    # SECTION_TWO
    # SECTION_TWO

    # SECTION_THREE
    process_section_three(shipping_request, page_one_canvas)
    # SECTION_THREE

    # SECTION_FOUR
    process_section_four(shipping_request, page_one_canvas)
    # SECTION_FOUR

    # SECTION_FIVE
    process_section_five(shipping_request, page_one_canvas)
    # SECTION_FIVE

    # SECTION_SIX
    process_section_six(shipping_request, page_one_canvas)
    # SECTION_SIX

    # SECTION_SEVEN
    process_section_seven(tracking_number, page_one_canvas)
    # SECTION_SEVEN

    # SECTION_EIGHT
    process_section_eight(transport_mode, page_one_canvas)
    # SECTION_EIGHT

    # SECTION_NINE
    # SECTION_NINE

    # SECTION_TEN
    # SECTION_TEN

    # SECTION_ELEVEN
    process_section_eleven(page_one_canvas)
    # SECTION_ELEVEN

    # SECTION_TWELVE
    process_section_twelve(shipping_request, page_one_canvas)
    # SECTION_TWELVE

    # SECTION_THIRTEEN
    process_section_thirteen(shipping_request, page_one_canvas)
    # SECTION_THIRTEEN

    # SECTION_FOURTEEN
    process_section_fourteen(order_number, page_one_canvas)
    # SECTION_FOURTEEN

    # SECTION_FIFTEEN
    # SECTION_FIFTEEN

    # SECTION_SIXTEEN,SEVENTEEN,EIGHTEEN,NINETEEN,TWENTY
    addl_packets = process_section_sixteen_through_twenty_three(shipping_request, order_number, page_one_canvas)
    # SECTION_SIXTEEN,SEVENTEEN,EIGHTEEN,NINETEEN,TWENTY

    # SECTION_TWENTY_ONE
    process_section_twenty_one(page_one_canvas)
    # SECTION_TWENTY_ONE

    # SECTION_TWENTY_TWO
    process_section_twenty_two(shipping_request, page_one_canvas)
    # SECTION_TWENTY_TWO

    # SECTION_TWENTY_FOUR
    process_section_twenty_four(total_shipping_cost, page_one_canvas)
    # SECTION_TWENTY_FOUR

    # SECTION_PAGE_NUMBERS
    process_section_page_numbers(len(addl_packets), page_one_canvas)
    # SECTION_PAGE_NUMBERS

    page_one_canvas.save()
    page_one_packet.seek(0)
    page_one_new = PdfFileReader(page_one_packet)
    template_file = open(TEMPLATE_FILE, 'rb')
    existing_pdf = PdfFileReader(template_file)
    output = PdfFileWriter()
    page_one = existing_pdf.getPage(0)
    page_one.mergePage(page_one_new.getPage(0))
    # page_one = page_one_new.getPage(0)
    # page_one.mergePage(existing_pdf.getPage(0))
    output.addPage(page_one)

    handles = []
    for packet in addl_packets:
        packet.seek(0)

        new_page = PdfFileReader(packet)

        t = open(TEMPLATE_FILE, 'rb')
        e = PdfFileReader(t)
        new_page_two = e.getPage(1)
        new_page_two.mergePage(new_page.getPage(0))
        handles.append(t)

        output.addPage(new_page_two)

    page_three = existing_pdf.getPage(2)
    page_four = existing_pdf.getPage(3)
    # output.addPage(existing_pdf.getPage(1))
    output.addPage(page_three)
    output.addPage(page_four)

    output_stream = io.BytesIO()
    output.write(output_stream)
    output_stream.seek(0)
    encoded = base64.b64encode(output_stream.read()).decode('ascii')
    output_stream.close()
    template_file.close()
    for handle in handles:
        handle.close()
    for packet in addl_packets:
        packet.close()
    return encoded


def notify_b13a_filing(document: str, order_number: str):
    message = 'Attached is the B13A document for shipment {}.\n' \
              '1. Complete the required sections 1 (NBNR if no business number), 18, 27 and 28.\n' \
              '2. Check the validity of other sections.\n' \
              '3. Complete/change other sections as necessary.\n'.format(order_number)

    mail = EmailMessage(
        "B13A Filing Notification {}".format(order_number),
        message,
        EMAIL_HOST_USER,
        [B13A_FILING_EMAIL],
        attachments=[('document.pdf', base64.b64decode(document), 'application/pdf')]
    )
    mail.send()


def get_font_size(text: str, max_width: Union[int, float], font_size: int, font_name: str, c: canvas.Canvas) -> float:
    text_width = c.stringWidth(text, font_name, font_size)
    while text_width + 3 > max_width and font_size > 6:
        font_size -= 0.1
        text_width = c.stringWidth(text, font_name, font_size)
    return round(font_size, 2)


def get_position(x_start: Union[int, float], x_end: Union[int, float], y: Union[int, float], text: str, font_name: str,
                 font_size: int, c: canvas.Canvas) -> Tuple[float, float]:
    return (x_start + (x_end - x_start) / 2 - c.stringWidth(text, font_name, font_size) / 2), y


def process_header(c: canvas.Canvas) -> None:
    # Original
    original = '✓'
    original_font_size = get_font_size(original, 1.4 * cm - 1 * cm, FONT_SIZE - 2, FONT_NAME, c)
    original_text = c.beginText(*get_position(1 * cm, 1.4 * cm, 26.05 * cm, original, FONT_NAME, original_font_size, c))
    original_text.setFont(FONT_NAME, original_font_size, leading=None)
    original_text.textOut(original)
    c.drawText(original_text)

    # Page
    original = '1'
    original_font_size = get_font_size(original, 18.4 * cm - 17.2 * cm, FONT_SIZE, FONT_NAME, c)
    original_text = c.beginText(
        *get_position(17.2 * cm, 18.4 * cm, 25.7 * cm, original, FONT_NAME, original_font_size, c))
    original_text.setFont(FONT_NAME, original_font_size, leading=None)
    original_text.textOut(original)
    c.drawText(original_text)


def process_section_one(c: canvas.Canvas) -> None:
    c.drawString(8.75 * cm, 24.9 * cm, 'N')
    c.drawString(9.25 * cm, 24.9 * cm, 'B')
    c.drawString(9.75 * cm, 24.9 * cm, 'N')
    c.drawString(10.25 * cm, 24.9 * cm, 'R')


def process_section_two(c: canvas.Canvas) -> None:
    c.drawString(8.75 * cm, 24.9 * cm, 'N')


def process_section_three(shipping_request, c: canvas.Canvas) -> None:
    origin = shipping_request['origin']
    # Name
    section_three_name = origin['name'].upper()
    section_three_name_font_size = get_font_size(section_three_name, 20.9 * cm - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_three_name_text = c.beginText(
        *get_position(0.8 * cm, 20.9 * cm, 24.1 * cm, section_three_name, FONT_NAME, section_three_name_font_size, c))
    section_three_name_text.setFont(FONT_NAME, section_three_name_font_size, leading=None)
    section_three_name_text.textOut(section_three_name)
    c.drawText(section_three_name_text)

    # Address
    section_three_address = origin['address'].upper()
    section_three_address_font_size = get_font_size(section_three_address, 7.1 * cm - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_three_address_text = c.beginText(
        *get_position(0.8 * cm, 7.1 * cm, 23.25 * cm, section_three_address, FONT_NAME, section_three_address_font_size,
                      c))
    section_three_address_text.setFont(FONT_NAME, section_three_address_font_size, leading=None)
    section_three_address_text.textOut(section_three_address)
    c.drawText(section_three_address_text)

    # City
    section_three_city = origin['city'].upper()
    section_three_city_font_size = get_font_size(section_three_city, (8.5 * inch / 2) - 7.1 * cm, FONT_SIZE, FONT_NAME,
                                                 c)
    section_three_city_text = c.beginText(
        *get_position(7.1 * cm, (8.5 * inch / 2), 23.25 * cm, section_three_city, FONT_NAME,
                      section_three_city_font_size, c))
    section_three_city_text.setFont(FONT_NAME, section_three_city_font_size, leading=None)
    section_three_city_text.textOut(section_three_city)
    c.drawText(section_three_city_text)

    # Province
    section_three_province = Province.objects.get(code=origin['province'], country__code=origin['country']).name.upper()
    section_three_province_font_size = get_font_size(section_three_province, 17.4 * cm - (8.5 / 2 * inch), FONT_SIZE,
                                                     FONT_NAME, c)
    section_three_province_text = c.beginText(
        *get_position((8.5 / 2 * inch), 17.4 * cm, 23.25 * cm, section_three_province, FONT_NAME,
                      section_three_province_font_size, c))
    section_three_province_text.setFont(FONT_NAME, section_three_province_font_size, leading=None)
    section_three_province_text.textOut(section_three_province)
    c.drawText(section_three_province_text)

    # Postal Code
    section_three_postal = origin['postal_code'].upper()
    section_three_postal_font_size = get_font_size(section_three_postal, 20.9 * cm - 17.4 * cm, FONT_SIZE, FONT_NAME, c)
    section_three_postal_text = c.beginText(
        *get_position(17.4 * cm, 20.9 * cm, 23.25 * cm, section_three_postal, FONT_NAME, section_three_postal_font_size,
                      c))
    section_three_postal_text.setFont(FONT_NAME, section_three_postal_font_size, leading=None)
    section_three_postal_text.textOut(section_three_postal)
    c.drawText(section_three_postal_text)


def process_section_four(shipping_request, c: canvas.Canvas) -> None:
    destination = shipping_request['destination']
    # Name
    section_four_name = destination['name'].upper()
    section_four_name_font_size = get_font_size(section_four_name, 20.9 * cm - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_four_name_text = c.beginText(
        *get_position(0.8 * cm, 20.9 * cm, 22.4 * cm, section_four_name, FONT_NAME, section_four_name_font_size, c))
    section_four_name_text.setFont(FONT_NAME, section_four_name_font_size, leading=None)
    section_four_name_text.textOut(section_four_name)
    c.drawText(section_four_name_text)

    # Address
    section_four_address = destination['address'].upper()
    section_four_address_font_size = get_font_size(section_four_address, 20.9 * cm - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_four_address_text = c.beginText(
        *get_position(0.8 * cm, 20.9 * cm, 21.58 * cm, section_four_address, FONT_NAME, section_four_address_font_size,
                      c))
    section_four_address_text.setFont(FONT_NAME, section_four_address_font_size, leading=None)
    section_four_address_text.textOut(section_four_address)
    c.drawText(section_four_address_text)

    # City
    section_four_city = destination['city'].upper()
    section_four_city_font_size = get_font_size(section_four_city, (8.5 / 2 * inch) - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_four_city_text = c.beginText(
        *get_position(0.8 * cm, (8.5 / 2 * inch), 20.75 * cm, section_four_city, FONT_NAME, section_four_city_font_size,
                      c))
    section_four_city_text.setFont(FONT_NAME, section_four_city_font_size, leading=None)
    section_four_city_text.textOut(section_four_city)
    c.drawText(section_four_city_text)

    # Province
    section_four_province = '{}, {}'.format(
        Province.objects.get(code=destination['province'], country__code=destination['country']).name.upper(),
        Country.objects.get(code=destination['country']).name.upper())
    section_four_province_font_size = get_font_size(section_four_province, 17.4 * cm - (8.5 / 2 * inch), FONT_SIZE,
                                                    FONT_NAME, c)
    section_four_province_text = c.beginText(
        *get_position((8.5 / 2 * inch), 17.4 * cm, 20.75 * cm, section_four_province, FONT_NAME,
                      section_four_province_font_size, c))
    section_four_province_text.setFont(FONT_NAME, section_four_province_font_size, leading=None)
    section_four_province_text.textOut(section_four_province)
    c.drawText(section_four_province_text)

    # Postal Code
    section_four_postal = destination['postal_code'].upper()
    section_four_postal_font_size = get_font_size(section_four_postal, 20.9 * cm - 17.4 * cm, FONT_SIZE, FONT_NAME, c)
    section_four_postal_text = c.beginText(
        *get_position(17.4 * cm, 20.9 * cm, 20.75 * cm, section_four_postal, FONT_NAME, section_four_postal_font_size,
                      c))
    section_four_postal_text.setFont(FONT_NAME, section_four_postal_font_size, leading=None)
    section_four_postal_text.textOut(section_four_postal)
    c.drawText(section_four_postal_text)


def process_section_five(shipping_request, c: canvas.Canvas) -> None:
    destination = shipping_request['destination']
    section_five = Country.objects.get(code=destination['country']).name.upper()
    section_five_font_size = get_font_size(section_five, (8.5 / 2 * inch) - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_five_text = c.beginText(
        *get_position(0.8 * cm, (8.5 / 2 * inch), 19.9 * cm, section_five, FONT_NAME, section_five_font_size, c))
    section_five_text.setFont(FONT_NAME, section_five_font_size, leading=None)
    section_five_text.textOut(section_five)
    c.drawText(section_five_text)


def process_section_six(shipping_request, c: canvas.Canvas) -> None:
    section_six = Carrier.objects.get(code=shipping_request['carrier_id']).name.upper()
    section_six_font_size = get_font_size(section_six, (8.5 / 2 * inch) - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_six_text = c.beginText(
        *get_position(0.8 * cm, (8.5 / 2 * inch), 18.8 * cm, section_six, FONT_NAME, section_six_font_size, c))
    section_six_text.setFont(FONT_NAME, section_six_font_size, leading=None)
    section_six_text.textOut(section_six)
    c.drawText(section_six_text)


def process_section_seven(tracking_number, c: canvas.Canvas) -> None:
    section_seven = tracking_number
    section_seven_font_size = get_font_size(section_seven, (8.5 / 2 * inch) - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_seven_text = c.beginText(
        *get_position(0.8 * cm, (8.5 / 2 * inch), 17.9 * cm, section_seven, FONT_NAME, section_seven_font_size, c))
    section_seven_text.setFont(FONT_NAME, section_seven_font_size, leading=None)
    section_seven_text.textOut(section_seven)
    c.drawText(section_seven_text)


def process_section_eight(transport_mode, c: canvas.Canvas) -> None:
    section_eight = '✓'
    if transport_mode == ModeOfTransportation.road:
        start_x = 0.98 * cm
        start_y = 17.05 * cm
    elif transport_mode == ModeOfTransportation.rail:
        start_x = 3.2 * cm
        start_y = 17.05 * cm
    elif transport_mode == ModeOfTransportation.sea:
        start_x = 6.17 * cm
        start_y = 17.05 * cm
    elif transport_mode == ModeOfTransportation.air:
        start_x = 8.4 * cm
        start_y = 17.05 * cm
    else:
        start_x = 0.98 * cm
        start_y = 16.53 * cm
    end_x = start_x + 0.4 * cm
    section_eight_font_size = get_font_size(section_eight, end_x - start_x, FONT_SIZE - 2, FONT_NAME, c)
    section_eight_text = c.beginText(
        *get_position(start_x, end_x, start_y, section_eight, FONT_NAME, section_eight_font_size, c))
    section_eight_text.setFont(FONT_NAME, section_eight_font_size, leading=None)
    section_eight_text.textOut(section_eight)
    c.drawText(section_eight_text)


def process_section_nine(c: canvas.Canvas) -> None:
    c.drawString(8.75 * cm, 24.9 * cm, 'N')


def process_section_ten(c: canvas.Canvas) -> None:
    c.drawString(8.75 * cm, 24.9 * cm, 'N')


def process_section_eleven(c: canvas.Canvas) -> None:
    section_eleven = datetime.today().strftime('%Y/%m/%d')
    section_eleven_font_size = get_font_size(section_eleven, 20.9 * cm - (8.5 / 2 * inch), FONT_SIZE, FONT_NAME, c)
    section_eleven_text = c.beginText(
        *get_position((8.5 / 2 * inch), 20.9 * cm, 15.6 * cm, section_eleven, FONT_NAME, section_eleven_font_size, c))
    section_eleven_text.setFont(FONT_NAME, section_eleven_font_size, leading=None)
    section_eleven_text.textOut(section_eleven)
    c.drawText(section_eleven_text)


def process_section_twelve(shipping_request, c: canvas.Canvas) -> None:
    # No. Packages
    section_twelve_qty = str(sum(p.get('quantity', 1) for p in shipping_request['packages']))
    section_twelve_qty_font_size = get_font_size(section_twelve_qty, 3.8 * cm - 0.8 * cm, FONT_SIZE, FONT_NAME, c)
    section_twelve_qty_text = c.beginText(
        *get_position(0.8 * cm, 3.8 * cm, 14.75 * cm, section_twelve_qty, FONT_NAME, section_twelve_qty_font_size, c))
    section_twelve_qty_text.setFont(FONT_NAME, section_twelve_qty_font_size, leading=None)
    section_twelve_qty_text.textOut(section_twelve_qty)
    c.drawText(section_twelve_qty_text)

    # Type Of Packages
    package_types = {}
    for package in shipping_request['packages']:
        p_type = package.get('package_type', 'Box')
        package_types[p_type] = package_types.get(p_type, 0) + package.get('quantity', 0)
    section_twelve_type = ', '.join('{} {}'.format(v, k) for k, v in package_types.items()).upper()
    section_twelve_type_font_size = get_font_size(section_twelve_type, (8.5 / 2 * inch) - 3.8 * cm, FONT_SIZE,
                                                  FONT_NAME, c)
    section_twelve_type_text = c.beginText(
        *get_position(3.8 * cm, (8.5 / 2 * inch), 14.75 * cm, section_twelve_type, FONT_NAME,
                      section_twelve_type_font_size, c))
    section_twelve_type_text.setFont(FONT_NAME, section_twelve_type_font_size, leading=None)
    section_twelve_type_text.textOut(section_twelve_type)
    c.drawText(section_twelve_type_text)


def process_section_thirteen(shipping_request, c: canvas.Canvas) -> None:
    section_thirteen = shipping_request['origin']['city']
    section_thirteen_font_size = get_font_size(section_thirteen, 20.9 * cm - (8.5 / 2 * inch), FONT_SIZE, FONT_NAME, c)
    section_thirteen_text = c.beginText(
        *get_position((8.5 / 2 * inch), 20.9 * cm, 14.75 * cm, section_thirteen, FONT_NAME, section_thirteen_font_size,
                      c))
    section_thirteen_text.setFont(FONT_NAME, section_thirteen_font_size, leading=None)
    section_thirteen_text.textOut(section_thirteen)
    c.drawText(section_thirteen_text)


def process_section_fourteen(order_number, c: canvas.Canvas) -> None:
    section_fourteen = order_number
    section_fourteen_font_size = get_font_size(section_fourteen, 20.9 * cm - (8.5 / 2 * inch), FONT_SIZE, FONT_NAME, c)
    section_fourteen_text = c.beginText(
        *get_position((8.5 / 2 * inch), 20.9 * cm, 13.9 * cm, section_fourteen, FONT_NAME, section_fourteen_font_size,
                      c))
    section_fourteen_text.setFont(FONT_NAME, section_fourteen_font_size, leading=None)
    section_fourteen_text.textOut(section_fourteen)
    c.drawText(section_fourteen_text)


def process_section_fifteen(c: canvas.Canvas) -> None:
    c.drawString(8.75 * cm, 24.9 * cm, 'N')


def process_section_sixteen_through_twenty_three(shipping_request, order_number: str, c: canvas.Canvas) \
        -> List[io.BytesIO]:
    commodities = shipping_request['commodities'][:5]

    y = 11.1 * cm
    for commodity in commodities:
        # SECTION_SIXTEEN
        # Country
        section_sixteen_country = commodity['made_in_country_code']
        section_sixteen_country_font_size = get_font_size(section_sixteen_country, 2.3 * cm - 0.8 * cm, FONT_SIZE,
                                                          FONT_NAME, c)
        section_sixteen_country_text = c.beginText(
            *get_position(0.8 * cm, 2.3 * cm, y, section_sixteen_country, FONT_NAME, section_sixteen_country_font_size,
                          c))
        section_sixteen_country_text.setFont(FONT_NAME, section_sixteen_country_font_size, leading=None)
        section_sixteen_country_text.textOut(section_sixteen_country)
        c.drawText(section_sixteen_country_text)

        # Province
        # section_sixteen_province = commodity['made_in_country_code']
        # section_sixteen_province_font_size = \
        # get_font_size(section_sixteen_province, 3.8*cm-2.3*cm, FONT_SIZE, FONT_NAME, c)
        # section_sixteen_province_text = \
        # c.beginText(
        # *get_position(2.3*cm, 3.8*cm, y, section_sixteen_province, FONT_NAME, section_sixteen_province_font_size, c)
        # )
        # section_sixteen_province_text.setFont(FONT_NAME, section_sixteen_province_font_size, leading=None)
        # section_sixteen_province_text.textOut(section_sixteen_province)
        # c.drawText(section_sixteen_province_text)
        # SECTION_SIXTEEN

        # SECTION_SEVENTEEN
        section_seventeen = commodity['description']
        section_seventeen_font_size = get_font_size(section_seventeen, (8.5 / 2 * inch) - 3.8 * cm, FONT_SIZE,
                                                    FONT_NAME, c)
        section_seventeen_text = c.beginText(
            *get_position(3.8 * cm, (8.5 / 2 * inch), y, section_seventeen, FONT_NAME, section_seventeen_font_size, c))
        section_seventeen_text.setFont(FONT_NAME, section_seventeen_font_size, leading=None)
        section_seventeen_text.textOut(section_seventeen)
        c.drawText(section_seventeen_text)
        # SECTION_SEVENTEEN

        # SECTION_EIGHTEEN
        # SECTION_EIGHTEEN

        # SECTION_NINETEEN
        section_nineteen = '{} KGM'.format(commodity['total_weight'])
        section_nineteen_font_size = get_font_size(section_nineteen, 17.1 * cm - 14 * cm, FONT_SIZE, FONT_NAME, c)
        section_nineteen_text = c.beginText(
            *get_position(14 * cm, 17.1 * cm, y, section_nineteen, FONT_NAME, section_nineteen_font_size, c))
        section_nineteen_text.setFont(FONT_NAME, section_nineteen_font_size, leading=None)
        section_nineteen_text.textOut(section_nineteen)
        c.drawText(section_nineteen_text)
        # SECTION_NINETEEN

        # SECTION_TWENTY
        section_twenty = '{:.2f}'.format(float(commodity['unit_value']))
        section_twenty_font_size = get_font_size(section_twenty, 20.9 * cm - 17.1 * cm, FONT_SIZE, FONT_NAME, c)
        section_twenty_text = c.beginText(
            *get_position(17.1 * cm, 20.9 * cm, y, section_twenty, FONT_NAME, section_twenty_font_size, c))
        section_twenty_text.setFont(FONT_NAME, section_twenty_font_size, leading=None)
        section_twenty_text.textOut(section_twenty)
        c.drawText(section_twenty_text)
        # SECTION_TWENTY
        y -= 0.6 * cm

    # SECTION_TWENTY_THREE
    section_twenty_three = '{:.2f}'.format(sum(float(commodity['unit_value']) for commodity in commodities))
    section_twenty_three_font_size = get_font_size(section_twenty_three, 20.9 * cm - 17.1 * cm, FONT_SIZE, FONT_NAME, c)
    section_twenty_three_text = c.beginText(
        *get_position(17.1 * cm, 20.9 * cm, 7.75 * cm, section_twenty_three, FONT_NAME, section_twenty_three_font_size,
                      c))
    section_twenty_three_text.setFont(FONT_NAME, section_twenty_three_font_size, leading=None)
    section_twenty_three_text.textOut(section_twenty_three)
    c.drawText(section_twenty_three_text)
    # SECTION_TWENTY_THREE

    return process_additional_commodities(shipping_request['commodities'][5:], order_number)


def process_section_twenty_one(c: canvas.Canvas) -> None:
    section_twenty_one = 'CAD'
    section_twenty_one_font_size = get_font_size(section_twenty_one, (8.5 / 2 * inch) - 0.8 * cm, FONT_SIZE, FONT_NAME,
                                                 c)
    section_twenty_one_text = c.beginText(
        *get_position(0.8 * cm, (8.5 / 2 * inch), 7.75 * cm, section_twenty_one, FONT_NAME,
                      section_twenty_one_font_size, c))
    section_twenty_one_text.setFont(FONT_NAME, section_twenty_one_font_size, leading=None)
    section_twenty_one_text.textOut(section_twenty_one)
    c.drawText(section_twenty_one_text)


def process_section_twenty_two(shipping_request, c: canvas.Canvas) -> None:
    section_twenty_two = '{:.2f}KGM'.format(
        sum(float(p['weight']) * p['quantity'] for p in shipping_request['packages'][:5]))
    section_twenty_two_font_size = get_font_size(section_twenty_two, 14.1 * cm - (8.5 / 2 * inch), FONT_SIZE, FONT_NAME,
                                                 c)
    section_twenty_two_text = c.beginText(
        *get_position((8.5 / 2 * inch), 14.1 * cm, 7.75 * cm, section_twenty_two, FONT_NAME,
                      section_twenty_two_font_size, c))
    section_twenty_two_text.setFont(FONT_NAME, section_twenty_two_font_size, leading=None)
    section_twenty_two_text.textOut(section_twenty_two)
    c.drawText(section_twenty_two_text)


def process_section_twenty_four(total_shipping_cost: Decimal, c: canvas.Canvas) -> None:
    section_twenty_four = '{}'.format(total_shipping_cost.quantize(Decimal('0.01')))
    section_twenty_four_font_size = get_font_size(section_twenty_four, (8.5 / 2 * inch) - 0.8 * cm, FONT_SIZE,
                                                  FONT_NAME, c)
    section_twenty_four_text = c.beginText(
        *get_position(0.8 * cm, (8.5 / 2 * inch), 6.6 * cm, section_twenty_four, FONT_NAME,
                      section_twenty_four_font_size, c))
    section_twenty_four_text.setFont(FONT_NAME, section_twenty_four_font_size, leading=None)
    section_twenty_four_text.textOut(section_twenty_four)
    c.drawText(section_twenty_four_text)


def process_section_page_numbers(addl_pages: int, c: canvas.Canvas) -> None:
    section_twenty_four = str(addl_pages + 1)
    section_twenty_four_font_size = get_font_size(section_twenty_four, 20.9 * cm - 19.3 * cm, FONT_SIZE, FONT_NAME, c)
    section_twenty_four_text = c.beginText(
        *get_position(19.3 * cm, 20.9 * cm, 25.7 * cm, section_twenty_four, FONT_NAME, section_twenty_four_font_size,
                      c))
    section_twenty_four_text.setFont(FONT_NAME, section_twenty_four_font_size, leading=None)
    section_twenty_four_text.textOut(section_twenty_four)
    c.drawText(section_twenty_four_text)


def process_additional_commodities(commodities: List[Dict[str, Any]], order_number: str) -> List[io.BytesIO]:
    if not commodities:
        return []
    packets = []
    canvases = []
    for _ in range(len(commodities) // 19 + 1):
        p = io.BytesIO()
        c = canvas.Canvas(p)
        packets.append(p)
        canvases.append(c)
    y = 18.1 * cm

    for i, commodity in enumerate(commodities):
        canvas_idx = i // 19
        c = canvases[canvas_idx]
        if y < 7.3 * cm:
            y = 18.1 * cm
        # SECTION_SIXTEEN
        # Country
        section_sixteen_country = commodity['made_in_country_code']
        section_sixteen_country_font_size = get_font_size(section_sixteen_country, 2.3 * cm - 0.8 * cm, FONT_SIZE,
                                                          FONT_NAME, c)
        section_sixteen_country_text = c.beginText(
            *get_position(0.8 * cm, 2.3 * cm, y, section_sixteen_country, FONT_NAME, section_sixteen_country_font_size,
                          c))
        section_sixteen_country_text.setFont(FONT_NAME, section_sixteen_country_font_size, leading=None)
        section_sixteen_country_text.textOut(section_sixteen_country)
        c.drawText(section_sixteen_country_text)

        # Province
        # section_sixteen_province = commodity['MadeInCountryCode']
        # section_sixteen_province_font_size = \
        # get_font_size(section_sixteen_province, 3.8*cm-2.3*cm, FONT_SIZE, FONT_NAME, c)
        # section_sixteen_province_text = \
        # c.beginText(
        # *get_position(2.3*cm, 3.8*cm, y, section_sixteen_province, FONT_NAME, section_sixteen_province_font_size, c)
        # )
        # section_sixteen_province_text.setFont(FONT_NAME, section_sixteen_province_font_size, leading=None)
        # section_sixteen_province_text.textOut(section_sixteen_province)
        # c.drawText(section_sixteen_province_text)
        # SECTION_SIXTEEN

        # SECTION_SEVENTEEN
        section_seventeen = commodity['description']
        section_seventeen_font_size = get_font_size(section_seventeen, (8.5 / 2 * inch) - 3.8 * cm, FONT_SIZE,
                                                    FONT_NAME, c)
        section_seventeen_text = c.beginText(
            *get_position(3.8 * cm, (8.5 / 2 * inch), y, section_seventeen, FONT_NAME, section_seventeen_font_size, c))
        section_seventeen_text.setFont(FONT_NAME, section_seventeen_font_size, leading=None)
        section_seventeen_text.textOut(section_seventeen)
        c.drawText(section_seventeen_text)
        # SECTION_SEVENTEEN

        # SECTION_EIGHTEEN
        # SECTION_EIGHTEEN

        # SECTION_NINETEEN
        section_nineteen = '{} KGM'.format(commodity['total_weight'])
        section_nineteen_font_size = get_font_size(section_nineteen, 17.1 * cm - 14 * cm, FONT_SIZE, FONT_NAME, c)
        section_nineteen_text = c.beginText(
            *get_position(14 * cm, 17.1 * cm, y, section_nineteen, FONT_NAME, section_nineteen_font_size, c))
        section_nineteen_text.setFont(FONT_NAME, section_nineteen_font_size, leading=None)
        section_nineteen_text.textOut(section_nineteen)
        c.drawText(section_nineteen_text)
        # SECTION_NINETEEN

        # SECTION_TWENTY
        section_twenty = '{:.2f}'.format(float(commodity['unit_value']))
        section_twenty_font_size = get_font_size(section_twenty, 20.9 * cm - 17.1 * cm, FONT_SIZE, FONT_NAME, c)
        section_twenty_text = c.beginText(
            *get_position(17.1 * cm, 20.9 * cm, y, section_twenty, FONT_NAME, section_twenty_font_size, c))
        section_twenty_text.setFont(FONT_NAME, section_twenty_font_size, leading=None)
        section_twenty_text.textOut(section_twenty)
        c.drawText(section_twenty_text)
        # SECTION_TWENTY
        y -= 0.6 * cm

    num_pages = len(canvases) + 1
    for i, c in enumerate(canvases):
        # SECTION_PAGE_NUMBER
        # This page
        section_page_number = str(i + 2)
        section_page_number_font_size = get_font_size(section_page_number, 18 * cm - 16.3 * cm, FONT_SIZE, FONT_NAME, c)
        section_page_number_text = c.beginText(
            *get_position(16.3 * cm, 18 * cm, 25.05 * cm, section_page_number, FONT_NAME, section_page_number_font_size,
                          c))
        section_page_number_text.setFont(FONT_NAME, section_page_number_font_size, leading=None)
        section_page_number_text.textOut(section_page_number)
        c.drawText(section_page_number_text)

        # Total pages
        section_total_pages = str(num_pages)
        section_total_pages_font_size = get_font_size(section_total_pages, 20.9 * cm - 18.8 * cm, FONT_SIZE, FONT_NAME,
                                                      c)
        section_total_pages_text = c.beginText(
            *get_position(18.8 * cm, 20.9 * cm, 25.05 * cm, section_total_pages, FONT_NAME,
                          section_total_pages_font_size, c))
        section_total_pages_text.setFont(FONT_NAME, section_total_pages_font_size, leading=None)
        section_total_pages_text.textOut(section_total_pages)
        c.drawText(section_total_pages_text)
        # SECTION_PAGE_NUMBER

        # SECTION_FOURTEEN
        section_fourteen = order_number
        section_fourteen_font_size = get_font_size(section_fourteen, 5 * cm - 1.2 * cm, FONT_SIZE, FONT_NAME, c)
        section_fourteen_text = c.beginText(
            *get_position(1.2 * cm, 5 * cm, 21.8 * cm, section_fourteen, FONT_NAME, section_fourteen_font_size, c))
        section_fourteen_text.setFont(FONT_NAME, section_fourteen_font_size, leading=None)
        section_fourteen_text.textOut(section_fourteen)
        c.drawText(section_fourteen_text)
        # SECTION_FOURTEEN

        # SECTION_TWENTY_TWO
        section_twenty_two = '{:.2f} KGM'.format(
            sum(float(commodity['total_weight']) for commodity in commodities[19 * i:19 * (i + 1)]))
        section_twenty_two_font_size = get_font_size(section_twenty_two, 14 * cm - (8.5 / 2 * inch), FONT_SIZE,
                                                     FONT_NAME, c)
        section_twenty_two_text = c.beginText(
            *get_position((8.5 / 2 * inch), 14 * cm, 6.2 * cm, section_twenty_two, FONT_NAME,
                          section_twenty_two_font_size, c))
        section_twenty_two_text.setFont(FONT_NAME, section_twenty_two_font_size, leading=None)
        section_twenty_two_text.textOut(section_twenty_two)
        c.drawText(section_twenty_two_text)
        # SECTION_TWENTY_TWO

        # SECTION_TWENTY_THREE
        section_twenty_three = '{:.2f}'.format(
            sum(float(commodity['unit_value']) for commodity in commodities[19 * i:19 * (i + 1)]))
        section_twenty_three_font_size = get_font_size(section_twenty_three, 20.9 * cm - 17.1 * cm, FONT_SIZE,
                                                       FONT_NAME, c)
        section_twenty_three_text = c.beginText(
            *get_position(17.1 * cm, 20.9 * cm, 6.2 * cm, section_twenty_three, FONT_NAME,
                          section_twenty_three_font_size, c))
        section_twenty_three_text.setFont(FONT_NAME, section_twenty_three_font_size, leading=None)
        section_twenty_three_text.textOut(section_twenty_three)
        c.drawText(section_twenty_three_text)
        # SECTION_TWENTY_THREE

    for c in canvases:
        c.save()
    for p in packets:
        p.seek(0)
    return packets
