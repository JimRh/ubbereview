"""
Module for custom exception handling
This module sets a standard for all exception handling into a common format, no matter the issue.
Authors: Kenneth Carmichael (kencar17)
Date: February 19th 2023
Version: 1.0
"""

from rest_framework import status
from rest_framework.views import exception_handler

from api.background_tasks.logger import CeleryLogger
from apps.common.utilities.utilities import json_response


def ubbe_exception_handler(exc, context):
    """
    Custom Exception Handling to ensure a default error response for ubbe api
    @param exc: Errors?
    @param context: Error context
    @return: response object
    """

    CeleryLogger().l_critical.delay(
        location="INTERNAL SERVER ERROR",
        message=f"{str(exc)}\n{str(context)}"
    )

    response = exception_handler(exc, context)

    if not response:
        return json_response(
            data={},
            message={"code": "-1", "message": "Internal Server Error", "errors": []},
            error=True,
        )

    if response.status_code in [
        status.HTTP_404_NOT_FOUND,
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    ]:
        exc = []
    else:
        exc = [exc]

    response.data = {
        "is_error": True,
        "error": {"message": response.data.get("detail", ""), "errors": exc},
        "content": {},
    }
    response.status_code = status.HTTP_200_OK

    return response
