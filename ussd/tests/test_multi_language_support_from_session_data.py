from ussd.tests import UssdTestCase


class TestMultiLanguage(UssdTestCase.BaseUssdTestCase):
    validate_ussd = False

    def test_multilanguage_support(self):
        ussd_client = self.ussd_client(
            language='sw',
            generate_customer_journey=False,
            extra_payload={
                "journey_name": "sample_journey",
                "journey_version": "valid_multi_language_support_from_session_data_conf"
            }
        )

        # Dial in
        response = ussd_client.send('')

        self.assertEqual(
            "Bienvenue\n1. Bienvenue\n",
            response
        )

        response = ussd_client.send('1')

        self.assertEqual(
            "Pour compléter, saisissez une valeur\n",
            response
        )

        response = ussd_client.send('1')

        self.assertEqual(
            "Au revoir",
            response
        )
