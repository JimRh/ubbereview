from django.core.management import BaseCommand

from api.apis.business_central.business_central import BusinessCentral
from api.exceptions.project import ViewException


class Command(BaseCommand):

    def handle(self, *args, **options) -> None:

        try:
            bc_job_list = BusinessCentral().get_job_list(username="", is_all=True)
        except ViewException as e:
            print(e)
            bc_job_list = []

        print(bc_job_list)
