from django.apps import AppConfig
import pkgutil
from ussd.patch import *


class UssdConfig(AppConfig):
    name = 'ussd'

    def ready(self):
        pass
