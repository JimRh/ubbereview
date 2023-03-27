from django.core.exceptions import ObjectDoesNotExist, ValidationError
from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope
from rest_framework.exceptions import Throttled, PermissionDenied, NotAuthenticated

from api.exceptions.project import ViewException
from api.models import SubAccount
from api.permissions.api_permissions import HasApiPermission, IsPrivate
from api.throttling.throttling import NoThrottle, BasicThrottle, ProfessionalThrottle, PremiereThrottle, \
    EnterpriseThrottle
from api.utilities.utilities import Utility


class UbbeMixin:
    """
        Mixin should be applied to all api views as the mixin is responsible for determining permissions
        and throttling restrictions.
    """
    _sub_account = None
    _errors = []

    def get_sub_account(self):
        """
            Get ubbe sub account for request.
        """

        try:
            self._sub_account = SubAccount.objects.get(subaccount_number=self.request.headers.get("ubbe-account", ""))
        except ObjectDoesNotExist:
            self._errors.append({"ubbe-account": "'ubbe-account' must be in headers."})
            raise ViewException(code="1", message="Missing 'ubbe-account' in headers.", errors=self._errors)

    def get_permissions(self):
        """
           Override
           Instantiates and returns the list of permissions that this view requires.
        """

        if self.request.META["PATH_INFO"] == "/redoc/":
            permission_classes = (IsPrivate,)
        else:
            try:
                self._sub_account = SubAccount.objects.select_related(
                    "tier",
                    "markup"
                ).get(subaccount_number=self.request.headers.get("ubbe-account"))
            except (ObjectDoesNotExist, ValidationError):
                raise PermissionDenied(detail="Missing 'ubbe-account' in headers.")

            if self._sub_account.tier.code in ["ubbe", "public"]:
                self.throttle_classes = [NoThrottle]
            elif self._sub_account.tier.code == "basic":
                self.throttle_classes = [BasicThrottle]
            elif self._sub_account.tier.code == "professional":
                self.throttle_classes = [ProfessionalThrottle]
            elif self._sub_account.tier.code == "premiere":
                self.throttle_classes = [PremiereThrottle]
            elif self._sub_account.tier.code == "enterprise":
                self.throttle_classes = [EnterpriseThrottle]
            else:
                # No permission added

                raise PermissionDenied(detail="Permission denied, please contact Customer Service.")

            permission_classes = (HasApiPermission, TokenHasReadWriteScope)

        return [permission() for permission in permission_classes]

    def permission_denied(self, request, message=None, code=None):
        """
            Override permission denied response to be ubbe response format.
        """

        if request.authenticators and not request.successful_authenticator:
            raise NotAuthenticated()

        raise PermissionDenied(detail=message, code=code)

    # def throttled(self, request, wait):
    #     """
    #         Override throttled response to be ubbe response format.
    #     """
    #     raise Throttled(detail=Utility.throttled(wait=wait))
