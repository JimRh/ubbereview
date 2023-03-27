"""
    Title: Celery Logger
    Description: This file will contain functions for Celery Logger.
    Created: May 5, 2021
    Author: Carmichael
    Edited By:
    Edited Date:
"""

from api.globals.project import LOGGER
from brain.celery import app


class CeleryLogger:
    """
        Log issues in ubbe behind the scenes
    """

    @app.task(bind=True)
    def l_debug(self, location: str, message: str):
        LOGGER.debug(str(location) + ": " + str(message))

    @app.task(bind=True)
    def l_info(self, location: str, message: str):
        LOGGER.info(str(location) + ": " + str(message))

    @app.task(bind=True)
    def l_warning(self, location: str, message: str):
        LOGGER.warning(str(location) + ": " + str(message))

    @app.task(bind=True)
    def l_error(self, location: str, message: str):
        LOGGER.error(str(location) + ": " + str(message))

    @app.task(bind=True)
    def l_critical(self, location: str, message: str):
        LOGGER.critical(str(location) + ": " + str(message))
