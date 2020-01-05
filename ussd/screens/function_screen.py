from ussd.core import UssdHandlerAbstract
import importlib
from ussd.graph import Link, Vertex
from ussd.screens.schema import NextUssdScreenSchema
from marshmallow import fields, ValidationError, INCLUDE
import typing


class FunctionField(fields.Field):

    def _deserialize(
        self,
        value: typing.Any,
        attr: typing.Optional[str],
        data: typing.Optional[typing.Mapping[str, typing.Any]],
        **kwargs
    ):
        split_path = value.split('.')
        if len(split_path) <= 1:
            raise ValidationError(
                "Module name where function is located not given"
            )
        function_name = split_path[-1]
        module_name = '.'.join(value.split('.')[:-1])
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            raise ValidationError(
                "Module {0} does not exist".format(module_name)
            )

        if not hasattr(module, function_name):
            raise ValidationError(
                "Function {0} does not exist".format(value)
            )
        return module


class FunctionScreenSerializer(NextUssdScreenSchema):
    """
    Fields used to create this screen:

    1. function
        This is the function that will be called at this screen.
    2. session_key
        Once your function has been called the output of your function
        will be saved in ussd session using session_key
    3. next_screen
        Once your function has been called this it goes to the
        screen specified in next_screen
    """
    session_key = fields.Str(required=True)
    function = FunctionField(required=True)

    class Meta:
        unknown = INCLUDE


class FunctionScreen(UssdHandlerAbstract):
    """
    This screen is invisible to the user. Its used to if you want to call a function you
    have implemented.

    Its like a complement of http screen. In http screen you make a request to an
    external service to perform some logic.

    This screen on the contrary if the logic that you want to be executed is within
    your application you use this screen to execute it.

    Your function will be called with UssdRequest object.
    And it should return a dictionary that will be saved in ussd session

    Below is the UssdRequest that will be used.
        .. autoclass:: ussd.core.UssdRequest

    Screen specification
        .. autoclass:: ussd.screens.function_screen.FunctionScreenSerializer

    Examples of function screens:
        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_function_screen_conf.yml
    """
    screen_type = "function_screen"
    serializer = FunctionScreenSerializer

    def handle(self):
        split_path = self.screen_content['function'].split('.')
        function_name = split_path[-1]
        module_name = '.'.join(split_path[:-1])
        module = importlib.import_module(module_name)

        self.ussd_request.session[
            self.screen_content['session_key']
        ] = getattr(module, function_name)(self.ussd_request)

        return self.route_options()

    def show_ussd_content(self, **kwargs):
        return "function_screen\n{}".format(self.screen_content['function'])

    def get_next_screens(self):
        links = []
        screen_vertex = Vertex(self.handler)
        if isinstance(self.screen_content.get("next_screen"), list):
            for i in self.screen_content.get("next_screen", []):
                links.append(
                    Link(screen_vertex,
                         Vertex(i['next_screen'], ""),
                         i['condition'])
            )
        elif self.screen_content.get('next_screen'):
            links.append(
                Link(
                    screen_vertex,
                    Vertex(self.screen_content['next_screen']),
                    self.screen_content['session_key']
                )
            )

        if self.screen_content.get('default_next_screen'):
            links.append(
                Link(
                    screen_vertex,
                    Vertex(self.screen_content['default_next_screen'], ""),
                    self.screen_content['session_key']
                )
            )
        return links
