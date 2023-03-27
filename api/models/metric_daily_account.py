"""
    Title: Metric account Model
    Description: This file will contain views that only related to Metric Account Model.
    Created: Sept 23, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from decimal import Decimal

from django.db.models import DateTimeField, IntegerField, DecimalField, ForeignKey, PROTECT
from django.utils.timezone import now

from api.globals.project import BASE_TEN, PRICE_PRECISION, PERCENTAGE_PRECISION, MAX_PRICE_DIGITS, WEIGHT_PRECISION, \
    MAX_WEIGHT_DIGITS
from api.models import SubAccount
from api.models.base_table import BaseTable


class MetricAccount(BaseTable):
    """
        Database table to hold daily metric for an sub account.
    """

    _cost_sig_fig = Decimal(str(BASE_TEN ** (PRICE_PRECISION * -1)))
    _percentage_sig_fig = Decimal(str(BASE_TEN ** (PERCENTAGE_PRECISION * -1)))

    sub_account = ForeignKey(SubAccount, on_delete=PROTECT, null=True, help_text="Metric account.")
    creation_date = DateTimeField(default=now, help_text="Metric creation date")

    # Unmanaged Shipments Stats

    quotes = IntegerField(default=0, help_text="Number of total quotes for a day")
    shipped_quotes = IntegerField(default=0, help_text="Number of shipped quotes for a day")
    shipments = IntegerField(default=0, help_text="Number of total shipments for a day")
    air_legs = IntegerField(default=0, help_text="Number of total air legs for a day")
    ltl_legs = IntegerField(default=0, help_text="Number of total ltl legs for a day")
    ftl_legs = IntegerField(default=0, help_text="Number of total ftl legs for a day")
    courier_legs = IntegerField(default=0, help_text="Number of total courier legs for a day")
    sea_legs = IntegerField(default=0, help_text="Number of total sea legs for a day")
    quantity = IntegerField(default=0, help_text="Number of total package for a day")
    weight = DecimalField(
        decimal_places=WEIGHT_PRECISION, max_digits=MAX_WEIGHT_DIGITS, help_text="Number of total weight for a day"
    )
    revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily revenue."
    )
    expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily expense."
    )
    net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily net profit."
    )
    air_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily revenue for air legs."
    )
    air_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily expense for air legs."
    )
    air_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily net for air legs."
    )
    ltl_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily revenue for ltl legs."
    )
    ltl_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily expense for ltl legs."
    )
    ltl_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily net for ltl legs."
    )
    ftl_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily revenue for ftl legs."
    )
    ftl_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily expense for ftl legs."
    )
    ftl_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily net for ftl legs."
    )
    courier_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily revenue for cou legs."
    )
    courier_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily expense for cou legs."
    )
    courier_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily net for cou legs."
    )
    sea_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily revenue for sea legs."
    )
    sea_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily expense for sea legs."
    )
    sea_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily net for sea legs."
    )

    # Managed Shipments Stats

    managed_shipments = IntegerField(default=0, help_text="Number of total shipments for a day")
    managed_air_legs = IntegerField(default=0, help_text="Number of total air legs for a day")
    managed_ltl_legs = IntegerField(default=0, help_text="Number of total ltl legs for a day")
    managed_ftl_legs = IntegerField(default=0, help_text="Number of total ftl legs for a day")
    managed_courier_legs = IntegerField(default=0, help_text="Number of total courier legs for a day")
    managed_sea_legs = IntegerField(default=0, help_text="Number of total sea legs for a day")
    managed_quantity = IntegerField(default=0, help_text="Number of total package for a day")
    managed_weight = DecimalField(
        default=Decimal("0"), decimal_places=WEIGHT_PRECISION, max_digits=MAX_WEIGHT_DIGITS, help_text="Number of total weight for a day"
    )
    managed_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily revenue."
    )
    managed_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily expense."
    )
    managed_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS, help_text="Daily net profit."
    )
    managed_air_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily revenue for air legs."
    )
    managed_air_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily expense for air legs."
    )
    managed_air_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily net for air legs."
    )
    managed_ltl_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily revenue for ltl legs."
    )
    managed_ltl_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily expense for ltl legs."
    )
    managed_ltl_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily net for ltl legs."
    )
    managed_ftl_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily revenue for ftl legs."
    )
    managed_ftl_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily expense for ftl legs."
    )
    managed_ftl_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily net for ftl legs."
    )
    managed_courier_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily revenue for cou legs."
    )
    managed_courier_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily expense for cou legs."
    )
    managed_courier_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily net for cou legs."
    )
    managed_sea_revenue = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily revenue for sea legs."
    )
    managed_sea_expense = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily expense for sea legs."
    )
    managed_sea_net_profit = DecimalField(
        default=Decimal("0"), decimal_places=PRICE_PRECISION, max_digits=MAX_PRICE_DIGITS,
        help_text="Daily net for sea legs."
    )

    class Meta:
        verbose_name = 'Metric Account'
        verbose_name_plural = 'Metric Account\'s'
        ordering = ["creation_date", "sub_account"]

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create RateLog from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: RateLog Object
        """

        obj = cls()
        if param_dict is not None:
            obj.set_values(param_dict)
            obj.sub_account = param_dict.get('sub_account')
        return obj

    # Override
    def save(self, *args, **kwargs) -> None:
        self.weight = self.weight.quantize(self._cost_sig_fig)
        self.revenue = self.revenue.quantize(self._cost_sig_fig)
        self.expense = self.expense.quantize(self._cost_sig_fig)
        self.net_profit = self.net_profit.quantize(self._percentage_sig_fig)
        self.air_revenue = self.air_revenue.quantize(self._cost_sig_fig)
        self.ltl_revenue = self.ltl_revenue.quantize(self._cost_sig_fig)
        self.ftl_revenue = self.ftl_revenue.quantize(self._cost_sig_fig)
        self.courier_revenue = self.courier_revenue.quantize(self._cost_sig_fig)
        self.sea_revenue = self.sea_revenue.quantize(self._cost_sig_fig)
        self.air_expense = self.air_expense.quantize(self._cost_sig_fig)
        self.ltl_expense = self.ltl_expense.quantize(self._cost_sig_fig)
        self.ftl_expense = self.ftl_expense.quantize(self._cost_sig_fig)
        self.courier_expense = self.courier_expense.quantize(self._cost_sig_fig)
        self.sea_expense = self.sea_expense.quantize(self._cost_sig_fig)
        self.air_net_profit = self.air_net_profit.quantize(self._cost_sig_fig)
        self.ltl_net_profit = self.ltl_net_profit.quantize(self._cost_sig_fig)
        self.ftl_net_profit = self.ftl_net_profit.quantize(self._cost_sig_fig)
        self.courier_net_profit = self.courier_net_profit.quantize(self._cost_sig_fig)
        self.sea_net_profit = self.sea_net_profit.quantize(self._cost_sig_fig)

        self.managed_weight = self.managed_weight.quantize(self._cost_sig_fig)
        self.managed_revenue = self.managed_revenue.quantize(self._cost_sig_fig)
        self.managed_expense = self.managed_expense.quantize(self._cost_sig_fig)
        self.managed_net_profit = self.managed_net_profit.quantize(self._percentage_sig_fig)
        self.managed_air_revenue = self.managed_air_revenue.quantize(self._cost_sig_fig)
        self.managed_ltl_revenue = self.managed_ltl_revenue.quantize(self._cost_sig_fig)
        self.managed_ftl_revenue = self.managed_ftl_revenue.quantize(self._cost_sig_fig)
        self.managed_courier_revenue = self.managed_courier_revenue.quantize(self._cost_sig_fig)
        self.managed_sea_revenue = self.managed_sea_revenue.quantize(self._cost_sig_fig)
        self.managed_air_expense = self.managed_air_expense.quantize(self._cost_sig_fig)
        self.managed_ltl_expense = self.managed_ltl_expense.quantize(self._cost_sig_fig)
        self.managed_ftl_expense = self.managed_ftl_expense.quantize(self._cost_sig_fig)
        self.managed_courier_expense = self.managed_courier_expense.quantize(self._cost_sig_fig)
        self.managed_sea_expense = self.managed_sea_expense.quantize(self._cost_sig_fig)
        self.managed_air_net_profit = self.managed_air_net_profit.quantize(self._cost_sig_fig)
        self.managed_ltl_net_profit = self.managed_ltl_net_profit.quantize(self._cost_sig_fig)
        self.managed_ftl_net_profit = self.managed_ftl_net_profit.quantize(self._cost_sig_fig)
        self.managed_courier_net_profit = self.managed_courier_net_profit.quantize(self._cost_sig_fig)
        self.managed_sea_net_profit = self.managed_sea_net_profit.quantize(self._cost_sig_fig)
        self.clean_fields()
        super().save(*args, **kwargs)

    # Override
    def __repr__(self) -> str:
        return f"< MetricAccount ({self.creation_date}, {self.sub_account}) >"

    # Override
    def __str__(self) -> str:
        return f"{self.creation_date} - {self.sub_account}"
