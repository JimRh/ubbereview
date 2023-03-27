"""
Module for utility functions
This module will contain any utility functions for the project that are used in multiple apps.
Authors: Kenneth Carmichael (kencar17)
Date: February 19th 2023
Version: 1.0
"""
from typing import Union

from django.http import JsonResponse
from rest_framework import status


def json_response(
    data: Union[list, dict] = None, error: bool = False, message: dict = None
) -> JsonResponse:
    """
    Format
    @param data: Response Data
    @param error: Is there an error
    @param message: Message dict of the error containing: code, message, errors.
    @return:
    """

    if data is None:
        data = {}

    if message is None:
        message = {}

    return JsonResponse(
        {"is_error": error, "error": message, "content": data},
        status=status.HTTP_200_OK,
        safe=False,
    )
