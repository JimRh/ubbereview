"""
    Title: SubAccount Model
    Description: This file will contain functions for SubAccount Model.
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
import secrets
import uuid

from django.db.models.deletion import PROTECT, CASCADE
from django.db.models.fields import CharField, BooleanField, UUIDField, IntegerField, DateTimeField
from django.db.models.fields.related import ForeignKey

from api.globals.project import DEFAULT_CHAR_LEN, LETTER_MAPPING_LEN, DEFAULT_KEY_LENGTH, CURRENCY_CODE_LEN
from api.models import Account, Address, Contact, Markup, AccountTier
from api.models.base_table import BaseTable


class SubAccount(BaseTable):
    """
        SubAccount Model
    """
    _TYPES = (
        ("NO", "No File"),
        ("NF", "New File"),
        ("UF", "Update Monthly File"),
    )

    # Future move to DB?
    _SYSTEM = (
        ("UB", "ubbe"),
        ("FE", "Fetchable"),
        ("DE", "DeliverEase"),
        ("TP", "Third Party"),  # Public Api Clients or just set them to ubbe?
    )

    creation_date = DateTimeField(auto_now_add=True, editable=True, help_text="Date account was created.")
    system = CharField(
        max_length=LETTER_MAPPING_LEN * 2, choices=_SYSTEM, default="UB", help_text="System Account belongs to."
    )
    client_account = ForeignKey(Account, on_delete=CASCADE, related_name='subaccount_client_account')
    address = ForeignKey(Address, on_delete=PROTECT, related_name='subaccount_address')
    contact = ForeignKey(Contact, on_delete=PROTECT, related_name='subaccount_contact')
    markup = ForeignKey(Markup, on_delete=CASCADE, related_name='subaccount_markup', null=True, blank=True)
    tier = ForeignKey(AccountTier, on_delete=CASCADE, related_name='subaccount_tier', null=True, blank=True)
    is_default = BooleanField(default=False)
    subaccount_number = UUIDField(unique=True, editable=False)
    # TODO - Add "editable=False" and remove "null=True" after populating details.
    webhook_key = CharField(
        unique=True, max_length=DEFAULT_KEY_LENGTH, help_text="Webhook key to be used in with webhooks", null=True
    )
    currency_code = CharField(default="CAD", max_length=CURRENCY_CODE_LEN, help_text="Account Currency Code")
    bc_type = CharField(max_length=LETTER_MAPPING_LEN * 2, choices=_TYPES, default="NO", help_text="BC - Push Type.")
    bc_customer_code = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="BC - Customer Code.")
    bc_customer_name = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="BC - Customer Name.")
    bc_job_number = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="BC - Job Number")
    bc_location_code = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="BC - Location Code.")
    bc_line_type = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="BC - Line Type")
    bc_item = CharField(blank=True, max_length=DEFAULT_CHAR_LEN, help_text="BC - Item")
    bc_file_owner = CharField(default="BBEX\\VNATARAJAN", max_length=DEFAULT_CHAR_LEN, help_text="BC - Item")
    is_bc_push = BooleanField(default=False)
    is_account_id = BooleanField(default=False, help_text="Is allowed to create account id?")
    id_prefix = CharField(
        default="", null=True, blank=True, max_length=DEFAULT_CHAR_LEN, help_text="Prefix for Shipment Account id."
    )
    id_counter = IntegerField(default=1, help_text="Shipment Account id counter.")

    is_dangerous_good = BooleanField(default=False, help_text="Is the account allowed dangerous goods?")
    is_pharma = BooleanField(default=False, help_text="Is the account allowed pharma goods?")

    is_metric_included = BooleanField(default=True, help_text="Is the account included in metrics?")
    is_bbe = BooleanField(default=False, help_text="Is the account BBE?")
    is_public = BooleanField(default=False, help_text="Is the account public?")

    class Meta:
        verbose_name = "SubAccount"
        verbose_name_plural = "Account - Sub Account's"

    @property
    def account_name(self):
        return self.contact.company_name

    @property
    def address_city(self):
        return self.address.city

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create SubAccount from passed in param dict
            :param param_dict: dict - Dictionary of keys
            :return: SubAccount Object
        """

        sub_account = cls()
        if param_dict is not None:
            sub_account.set_values(param_dict)
            sub_account.client_account = param_dict.get("client_account")
            sub_account.address = param_dict.get("address")
            sub_account.contact = param_dict.get("contact")
            sub_account.markup = param_dict.get("markup")
        return sub_account

    def get_uuid(self) -> uuid.UUID:
        number = self.subaccount_number or uuid.uuid4()
        while SubAccount.objects.filter(subaccount_number=number).exists():
            number = uuid.uuid4()
        return number

    def get_webhook(self) -> uuid.UUID:
        number = secrets.token_hex(32)
        while SubAccount.objects.filter(webhook_key=number).exists():
            number = secrets.token_hex(32)
        return number

    def save(self, *args, **kwargs) -> None:

        if not self.pk:
            self.subaccount_number = self.get_uuid()
            self.webhook_key = self.get_webhook()

        self.clean_fields()
        super().save(*args, **kwargs)

    def __repr__(self) -> str:
        return f'< SubAccount ({str(self.subaccount_number)}) >'

    def __str__(self) -> str:
        return str(self.contact.company_name)
