from base64 import b64encode

from Crypto.Random import get_random_bytes
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        key = get_random_bytes(256)
        plaintext = b64encode(key)
        self.stdout.write('Insert the following as DataKey in settings.ini:\n{}\n'.format(plaintext.decode('ascii')))
