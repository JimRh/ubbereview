from decimal import Decimal


class Convert:
    _sig_fig = Decimal("0.01")
    _inch_to_cm_ratio = Decimal('2.54')
    _lbs_to_kg_ratio = Decimal('0.453592')
    _hundred = Decimal('100')
    _thousand = Decimal('1000')
    _cubic_feet_cons = Decimal('1728')
    _cubic_meter_cons = Decimal('61023.744')
    _square_feet_cons = Decimal('10.764')
    _rev_ton_cons = Decimal('2.5')

    def cms_to_inches(self, length) -> Decimal:
        length = Decimal(str(length))
        return (length / self._inch_to_cm_ratio).quantize(self._sig_fig)

    def convert_unit(self, value, is_dimension: bool = True, is_metric: bool = True) -> Decimal:
        if is_metric:
            return Decimal(str(value)).quantize(self._sig_fig)
        if is_dimension:
            return self.inches_to_cms(value)
        return self.lbs_to_kgs(value)

    def cubic_cms_to_cubic_feet(self, length) -> Decimal:
        length = Decimal(str(length))
        constant = Decimal('28317')
        return (length / constant).quantize(self._sig_fig)

    def inches_to_cms(self, length) -> Decimal:
        length = Decimal(str(length))
        return (length * self._inch_to_cm_ratio).quantize(self._sig_fig)

    def kgs_to_lbs(self, weight) -> Decimal:
        weight = Decimal(str(weight))
        return (weight / self._lbs_to_kg_ratio).quantize(self._sig_fig)

    def lbs_to_kgs(self, weight) -> Decimal:
        weight = Decimal(str(weight))
        return (weight * self._lbs_to_kg_ratio).quantize(self._sig_fig)

    def kg_to_rev_ton(self, weight) -> Decimal:
        return (weight / self._thousand).quantize(self._sig_fig)

    def cubage_cm(self, qty: int, length: Decimal, width: Decimal, height: Decimal):
        return ((length * width * height) * qty).quantize(self._sig_fig)

    def cubic_in(self, qty: int, length: Decimal, width: Decimal, height: Decimal):
        return ((length * width * height) * qty).quantize(self._sig_fig)

    def cubic_in_to_cubic_feet(self, value: Decimal):
        return (value / self._cubic_feet_cons).quantize(self._sig_fig)

    def cubic_in_to_cubic_meters(self, value: Decimal):
        return (value / self._cubic_meter_cons).quantize(self._sig_fig)

    def cms_to_square_meters(self, length: Decimal, width: Decimal):

        length_meter = length / self._hundred
        width_meter = width / self._hundred

        return (length_meter * width_meter).quantize(self._sig_fig)

    def square_meters_to_square_feet(self, value: Decimal):
        return (value * self._square_feet_cons).quantize(self._sig_fig)

    def dim_rev_ton(self, qty: int, length: Decimal, width: Decimal, height: Decimal):
        """

        :param qty:  Int
        :param length: Decimal - Units -> CM
        :param width:  Decimal - Units -> CM
        :param height: Decimal - Units -> CM
        :return: Revenue Ton
        """

        length_meter = length / self._hundred
        width_meter = width / self._hundred
        height_meter = height / self._hundred

        cbm = (length_meter * width_meter * height_meter) * qty

        return (cbm / self._rev_ton_cons ).quantize(self._sig_fig)
