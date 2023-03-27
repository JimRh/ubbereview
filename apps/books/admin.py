"""
Module for Books Admin
This module configures the book admin in django admin.
Authors: Kenneth Carmichael (kencar17)
Date: February 19th 2023
Version: 1.0
"""

from django.contrib.admin import ModelAdmin, register

from apps.books.models import SavedAddress, SavedContact


# Register your models here.


@register(SavedAddress)
class SavedAddressAdmin(ModelAdmin):
    list_display = (
        "account",
        "username",
        "name",
        "address",
        "is_origin",
        "is_destination",
        "is_vendor",
    )
    list_filter = (
        "account",
        "is_origin",
        "is_destination",
        "is_vendor",
        "address__has_shipping_bays",
    )
    search_fields = ("username", "name", "address__address", "address__city")
    autocomplete_fields = ("account", "address")

    def get_queryset(self, request):
        qs = super(SavedAddressAdmin, self).get_queryset(request)
        return qs.select_related("account", "address")


@register(SavedContact)
class SavedContactAdmin(ModelAdmin):
    list_display = (
        "account",
        "username",
        "contact",
        "is_origin",
        "is_destination",
        "is_vendor",
    )
    list_filter = (
        "account",
        "is_origin",
        "is_destination",
        "is_vendor",
    )
    search_fields = ("username", "contact__name", "contact__company_name", "contact__email")
    autocomplete_fields = ("account", "contact")

    def get_queryset(self, request):
        qs = super(SavedContactAdmin, self).get_queryset(request)
        return qs.select_related("account", "contact")

