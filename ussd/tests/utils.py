import json

def sum_numbers(ussd_request):
    return int(ussd_request.session['first_number']) + \
           int(ussd_request.session['second_number'])


class MockResponse:
    def __init__(self, json_data, status=200):
        self.json_data = json_data
        self.status_code = status
        self.content = json.dumps(json_data).encode()

    def json(self):
        return self.json_data
