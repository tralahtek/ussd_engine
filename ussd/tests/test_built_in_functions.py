from ussd_version.version import VERSION
from ussd.tests import UssdTestCase


class TestScreenUsing(UssdTestCase.BaseUssdTestCase):
    validate_ussd = False

    def get_ussd_client(self):
        return self.ussd_client(
            generate_customer_journey=False,
            extra_payload={
                'journey_name': "sample_journey",
                'journey_version': "testing_using_built_in_functions"
            }
        )

    def test(self):
        client = self.get_ussd_client()
        # dial in
        response = client.send('1')

        self.assertEqual(
            "You are using this version v{version}".format(version=VERSION),
            response
        )
