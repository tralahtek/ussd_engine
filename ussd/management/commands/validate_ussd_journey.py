import os
import json

from django.core.management.base import BaseCommand, CommandError

from ussd.core import UssdEngine
from ussd.store.journey_store.YamlJourneyStore import load_dict_from_yaml


class Command(BaseCommand):
    help = 'Validate ussd customer journey'

    def add_arguments(self, parser):
        parser.add_argument('ussd_configs', nargs='+', type=str)

    def handle(self, *args, **options):
        error_message = {}
        for ussd_config in options["ussd_configs"]:
            if not os.path.isfile(ussd_config):
                raise CommandError("The file path {} does not exist".format(ussd_config))

            ussd_screens = load_dict_from_yaml(ussd_config)

            is_valid, error_ussd_config_message = UssdEngine.validate_ussd_journey(
                ussd_screens)
            error_message[ussd_config] = dict(
                valid=is_valid,
                error_message=error_ussd_config_message
            )
            if not is_valid:
                raise CommandError(json.dumps(error_message))

        self.stdout.write(json.dumps(error_message))
