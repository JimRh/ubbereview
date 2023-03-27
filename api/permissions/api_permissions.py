from django.core.exceptions import ObjectDoesNotExist
from django.views import View
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request


class IsPrivate(BasePermission):
    def has_permission(self, request: Request, view: View) -> bool:
        tier = request.user.user_user_tier.tier
        view_name = view.get_view_name().strip().replace(' ', '_').lower()
        request_name = f"{view_name}_{request.method.lower()}"

        try:
            permission = tier.permissions.get(permissions=request_name)
        except ObjectDoesNotExist:
            return False

        if not permission.is_active:
            return False

        if permission.is_admin:
            return False

        return True


class HasApiPermission(BasePermission):

    def has_permission(self, request: Request, view: View) -> bool:
        """
            Determine if the sub account has access to the endpoint.
            :param request: Api Request
            :param view: Api view
        """
        sub_account = view._sub_account
        view_name = view.get_view_name().strip().replace(' ', '_').lower()
        request_name = f"{view_name}_{request.method.lower()}"

        try:
            permission = sub_account.tier.permissions.get(permissions=request_name)
        except ObjectDoesNotExist:
            raise PermissionDenied(detail="You do not have access to this endpoint")

        if not permission.is_active:
            raise PermissionDenied(detail=f"'{permission.name}' is currently inactive.")

        if permission.is_admin and not sub_account.is_bbe:
            raise PermissionDenied(detail=f"You do not have access to this endpoint.")

        return True
