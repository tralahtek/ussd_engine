"""
This test quit screen
"""
from ussd.tests import UssdTestCase


class TestQuitHandler(UssdTestCase.BaseUssdTestCase):
    validation_error_message = dict(
        example_of_quit_screen=dict(
            text=['This field is required.']
        )
    )

    def test(self):
        ussd_client = self.ussd_client()
        response = ussd_client.send('', raw=True)

        self.assertEqual(
            "Test getting variable from os environmen. variable_test",
            str(response)
        )

        self.assertFalse(response.status)
