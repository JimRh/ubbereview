"""
Module for custom pagination
This module sets the pagination parameters, limitations, and response structure for the project.
Authors: Kenneth Carmichael (kencar17)
Date: February 19th 2023
Version: 1.0
"""
from math import ceil

from rest_framework import pagination

from apps.common.globals.project import ZERO


class ApiPagination(pagination.PageNumberPagination):
    """
    Api Pagination
    """

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 250
    page_query_param = "page"

    def get_paginated_response(self, data) -> dict:
        """
        Format pagination into a standard format for ubbe response
        @param data: data to paginate
        @return: pagination
        """
        page_size = self.request.query_params.get("page_size", self.page_size)
        pages = ceil(self.page.paginator.count / int(page_size))

        return {
            "count": self.page.paginator.count,
            "pages": pages,
            "current": self.page.number,
            "previous": self.get_previous_link(),
            "next": self.get_next_link(),
            "data": data,
        }


def default_pagination(data: list) -> dict:
    """
    Default pagination for the project
    @param data: data to be returned, list
    @return: dict of default pagination results
    """

    return {
        "count": ZERO,
        "pages": ZERO,
        "current": ZERO,
        "previous": None,
        "next": None,
        "data": data,
    }
