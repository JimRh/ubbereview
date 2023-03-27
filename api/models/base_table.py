"""
    Title: Base Table
    Description: All models inherits this class. Comes witth basic functions
    Created: February 5, 2019
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.db import models


class BaseTable(models.Model):
    class Meta:
        abstract = True

    @classmethod
    def create(cls, param_dict: dict = None):
        """
            Create model object from passeed in params
            :param param_dict: dict - Params for a model
            :return: model object
        """
        obj = cls()

        if param_dict is not None:
            obj.set_values(param_dict)

        return obj

    def set_values(self, pairs: dict) -> list:
        """
            Set a list of key values for a model
            :param pairs: list - key values
            :return: list of keys set
        """

        ret = []

        for key, value in pairs.items():
            if not hasattr(self, key):
                continue
            setattr(self, key, value)
            ret.append(key)

        return ret

    # Override
    def save(self, *args, **kwargs) -> None:
        self.clean_fields()
        super().save(*args, **kwargs)
