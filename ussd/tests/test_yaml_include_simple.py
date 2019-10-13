"""
This test initial screen
"""
from ussd.tests import UssdTestCase


class TestInitialHandler(UssdTestCase.BaseUssdTestCase):
    expected_error = FileNotFoundError
    validation_error_message = {}
