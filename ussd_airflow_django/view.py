from rest_framework.views import APIView
from ussd.core import UssdRequest, UssdEngine, UssdResponse
from django.http import HttpResponse


class UssdView(APIView):
    """
    To create Ussd View requires the following things:
        - Inherit from **UssdView** (Mandatory)
            .. code-block:: python

                from ussd.core import UssdView

        - Define Http method either **get** or **post** (Mandatory)
            The http method should return Ussd Request

                .. autoclass:: ussd.core.UssdRequest

        - define this varialbe *customer_journey_conf*
            This is the path of the file that has ussd screens
            If you want your file to be dynamic implement the
            following method **get_customer_journey_conf** it
            will be called by request object

        - define this variable *customer_journey_namespace*
            Ussd_airflow uses this namespace to save the
            customer journey content in memory. If you want
            customer_journey_namespace to be dynamic implement
            this method **get_customer_journey_namespace** it
            will be called with request object

        - override HttpResponse
            In ussd airflow the http method return UssdRequest object
            not Http response. Then ussd view gets UssdResponse object
            and convert it to HttpResponse. The default HttpResponse
            returned is a normal HttpResponse with body being ussd text

            To override HttpResponse returned define this method.
            **ussd_response_handler** it will be called with
            **UssdResponse** object.

                .. autoclass:: ussd.core.UssdResponse

    Example of Ussd view

    .. code-block:: python

        from ussd.core import UssdView, UssdRequest


        class SampleOne(UssdView):

            def get(self, req):
                return UssdRequest(
                    phone_number=req.data['phoneNumber'].strip('+'),
                    session_id=req.data['sessionId'],
                    ussd_input=text,
                    service_code=req.data['serviceCode'],
                    language=req.data.get('language', 'en')
                )

    Example of Ussd View that defines its own HttpResponse.

    .. code-block:: python

        from ussd.core import UssdView, UssdRequest


        class SampleOne(UssdView):

            def get(self, req):
                return UssdRequest(
                    phone_number=req.data['phoneNumber'].strip('+'),
                    session_id=req.data['sessionId'],
                    ussd_input=text,
                    service_code=req.data['serviceCode'],
                    language=req.data.get('language', 'en')
                )

            def ussd_response_handler(self, ussd_response):
                    if ussd_response.status:
                        res = 'CON' + ' ' + str(ussd_response)
                        response = HttpResponse(res)
                    else:
                        res = 'END' + ' ' + str(ussd_response)
                        response = HttpResponse(res)
                    return response
    """

    def finalize_response(self, request, response, *args, **kwargs):

        if isinstance(response, UssdRequest):
            try:
                ussd_response = UssdEngine(response).ussd_dispatcher()
            except Exception as e:
                # if settings.DEBUG:
                ussd_response = UssdResponse(str(e))
            return self.ussd_response_handler(ussd_response)
        return super(UssdView, self).finalize_response(
            request, response, args, kwargs)

    def ussd_response_handler(self, ussd_response):
        return HttpResponse(str(ussd_response))
