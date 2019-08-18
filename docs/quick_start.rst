=====
Setup
=====

- Run the following command to install

.. code-block:: text

    pip install ussd_airflow

- Add **ussd_airflow** to `INSTALLED_APPS` in your settings file

    .. code-block:: python

        INSTALLED_APPS = [
        'ussd.apps.UssdConfig',
        ]

- Change session serializer to pickle serializer

    .. code-block:: python

        SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

- Add USSD view to handle USSD requests.
    - To use an existing USSD view that is implemented to handle
      AfricasTalking USSD gateway, add this to your `urls.py` file

        .. code-block:: python

            from ussd.views import AfricasTalkingUssdGateway

            urlpatterns = [
                url(r'^africastalking_gateway',
                    AfricasTalkingUssdGateway.as_view(),
                    name='africastalking_url')
                ]

      To use this view to serve your USSD screens, create a yaml file and add your USSD screens to it.
      Learn more on how to create USSD screens here :doc:`tutorial`.
      For a quick start, copy the below yaml and save it to a location within your application's codebase

        .. literalinclude:: .././ussd/tests/sample_screen_definition/sample_customer_journey.yml

      Next, add `DEFAULT_USSD_SCREEN_JOURNEY` to your settings file so as to indicate where your ussd screens
      files are located.  This should be the location you saved the previously created yaml file

        .. code-block:: python

            DEFAULT_USSD_SCREEN_JOURNEY = "/file/path/of/the/screen"

      Run the below command to validate your USSD screen file

        .. code-block:: text

            python manage.py validate_ussd_journey /file/path

      To test your USSD view, you can use cURL as shown below
      (you can also use an application such as Postman for this).

      .. code-block:: text

        curl -X POST -H "Content-Type: application/json"
        -H "Cache-Control: no-cache"
        -H "Postman-Token: 3e3f3fb9-99b9-b47d-a358-618900d486c6"
        -d '{"phoneNumber": "400","sessionId": "105","text":"1",
        "serviceCode": "312"}'
        "http://{your_host}/{you_path}/africastalking_gateway"

    - To create your own USSD view, you can use this as an example.
            .. autoclass:: ussd.core.UssdView

