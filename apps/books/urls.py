"""
Module for custom pagination
This module sets the pagination parameters, limitations, and response structure for the project.
Authors: Kenneth Carmichael (kencar17)
Date: February 19th 2023
Version: 1.0
"""

from django.urls import path

from apps.books.views import saved_address_api, saved_contact_api

urlpatterns = [

    # Saved Address
    path(
        "address", saved_address_api.SavedAddressApi.as_view(), name="SavedAddressApiV3"
    ),
    path(
        "address/<int:pk>",
        saved_address_api.SavedAddressDetailApi.as_view(),
        name="SavedAddressDetailApiV3",
    ),
    path(
        "address_upload",
        saved_address_api.SavedAddressUploadApi.as_view(),
        name="SavedAddressUploadApiV3",
    ),
    path(
        "address_process",
        saved_address_api.SavedAddressProcessApi.as_view(),
        name="SavedAddressProcessApiV3",
    ),

    # Saved Contact
    path(
        "contact", saved_contact_api.SavedContactApi.as_view(), name="SavedContactApiV3"
    ),
    path(
        "contact/<int:pk>",
        saved_contact_api.SavedContactDetailApi.as_view(),
        name="SavedContactDetailApiV3",
    ),
    path(
        "contact_upload",
        saved_contact_api.SavedContactUploadApi.as_view(),
        name="SavedContactUploadApiV3",
    ),
    path(
        "contact_process",
        saved_contact_api.SavedContactProcessApi.as_view(),
        name="SavedContactProcessApiV3",
    ),
]
