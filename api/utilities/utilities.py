import math

from typing import Union

from django.http import JsonResponse
from rest_framework import status


class Utility:
    """
        Common utility functions across the project.
    """

    @staticmethod
    def json_response(data: Union[list, dict] = None):

        if data is None:
            data = []

        return JsonResponse(
            {
                "status": status.HTTP_200_OK,
                "is_error": False,
                "error": {},
                "content": data
            },
            status=status.HTTP_200_OK,
            safe=False
        )

    @staticmethod
    def json_error_response(data: Union[list, dict] = None, code: str = "", message: str = "", errors: list = None):

        if data is None:
            data = []

        if errors is None:
            errors = []

        return JsonResponse(
            {
                "status": status.HTTP_200_OK,
                "is_error": True,
                "error": {
                    "code": code,
                    "message": message,
                    "errors": errors
                },
                "content": data
            },
            status=status.HTTP_200_OK,
            safe=False
        )

    @staticmethod
    def throttled(wait: int = 60) -> dict:
        """
            Override Throttled response to be ubbe response format.
            :param wait: wait time to try again
            :return: dict
        """

        return {
            "status": status.HTTP_200_OK,
            "is_error": True,
            "error": {
                "code": "3",
                "message": "Request limited exceeded.",
                "errors": [{"throttled": f"Please try again in {math.ceil(wait)} seconds."}]
            },
            "content": {}
        }

    @staticmethod
    def permission(message) -> dict:
        """
            Override Throttled response to be ubbe response format.
            :param message: wait time to try again
            :return: dict
        """

        return {
            "status": status.HTTP_200_OK,
            "is_error": True,
            "error": {
                "code": "4",
                "message": "Permission denied.",
                "errors": [{"permission": message}]
            },
            "content": {}
        }
