import datetime

from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter(name='add_class')
def add_class(value, arg):
    return value.as_widget(attrs={'class': arg})


@register.filter(name='add_id')
def add_id(value, arg):
    return value.as_widget(attrs={'id': arg})


@register.filter(name='has_group')
def has_group(user, group_name):
    try:
        group = Group.objects.get(name=group_name)
        return group in user.groups.all()
    except:
        return False


@register.filter(name='has_groups')
def has_groups(user, groups):
    groups_list = str(groups).split('|')
    groups_query = Group.objects.filter(name__in=groups_list)
    if set(user.groups.all()).intersection(set(groups_query)):
        return True
    return False


@register.filter(name='get_group')
def get_group(user):
    roles = {"admin", "accounting", "management", "freight_forwarder", "carrier_management", "sales"}
    groups = user.groups.values_list('name', flat=True)[::1]
    try:
        return roles.intersection(set(groups)).pop()
    except KeyError:
        return "No Role"


@register.filter(name='ubbe_date')
def ubbe_date(value):

    try:
        obj = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return obj.strftime("%Y-%m-%d")
    except ValueError:
        obj = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        return obj.strftime("%Y-%m-%d")


@register.filter(name='ubbe_time')
def ubbe_time(value):

    try:
        obj = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return obj.strftime("%H:%M")
    except ValueError:
        obj = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
        return obj.strftime("%H:%M")
