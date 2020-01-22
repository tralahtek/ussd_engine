"""
Customer journey are stored in a document store.
Any engine that implements this interface can be integrated with journey store.
"""
import abc
import inspect
from copy import deepcopy
from ussd.utils.module_loading import import_string
import typing
from marshmallow.exceptions import ValidationError


class JourneyStore(object, metaclass=abc.ABCMeta):

    edit_mode_version = "edit_mode"

    @abc.abstractmethod
    def _get(self, name, version, screen_name, **kwargs):
        pass

    @abc.abstractmethod
    def _all(self, name):
        pass

    @abc.abstractmethod
    def _save(self, name, journey, version):
        pass

    @abc.abstractmethod
    def _delete(self, name, version=None):
        pass

    @abc.abstractmethod
    def flush(self):
        pass

    def get(self, name: str, version=None, screen_name=None, edit_mode=False, propagate_error=True):
        if edit_mode:
            version = self.edit_mode_version
        results = self._get(name, version, screen_name)

        if propagate_error and results is None:
            raise ValidationError(
                "Journey with name {0} and version {1} does not exist".format(name, version))
        return results

    def all(self, name: str):
        return self._all(name)

    def save(self, name: str, journey: dict, version=None, edit_mode=False):

        # version and editor mode should not be false
        if not (version or edit_mode):
            raise ValidationError("version is required if its not in editor mode")

        if edit_mode:
            version = self.edit_mode_version

        # check if this version already exists
        if self.get(name, version, propagate_error=False) is not None:
            if not edit_mode:
                raise ValidationError("journey already exists")

        # validate if its not in editing mode.
        if not edit_mode:
            from ussd.core import UssdEngine
            is_valid, errors = UssdEngine.validate_ussd_journey(journey)
            if not is_valid:
                raise ValidationError(errors, "journey")

        # now create journey
        return self._save(name, journey, version)

    def delete(self, name, version=None):
        return self._delete(name, version)


class JourneyStoreApi(object):

    def __init__(self, 
                 driver: typing.Mapping[str, typing.Any] = "ussd.store.journey_store.YamlJourneyStore.YamlJourneyStore",
                 driver_config: typing.Dict = None):
        
        self.driver_config = {} \
            if driver_config is None else driver_config
        self.driver = driver

        if not inspect.isclass(driver):
            if not isinstance(self.driver, str):
                raise ValidationError(
                    "driver should either be an instance of "
                    "driver store or a string pointing to the store")
            else:
                self.driver = import_string(self.driver)

        if not inspect.isclass(self.driver):
            raise ValidationError("driver should be a class ")

        # initiate the driver
        self.driver = self.driver(**self.driver_config)

    journey_method_names = ("save", "delete", "get", "all", "flush")

    def __getattr__(self, name):
        if name in JourneyStoreApi.journey_method_names:
            return self._actual_function(getattr(self.driver, name))
        else:
            return super(JourneyStoreApi, self).__getattribute__(name)

    def _actual_function(self, journey_store_method):
        def wrapper(*args, **kwargs):
            errors = self._parameter_validation(journey_store_method, *args, **kwargs)
            if errors:
                raise ValidationError(errors)
            return journey_store_method(*args, **kwargs)
        return wrapper

    def handle_action(self, **kwargs):

        action = kwargs.pop('action', '')

        if not action:
            raise ValidationError("This field is required", "action")

        # For easy development should accept post and convert it to save
        if action in ('post', 'put'):
            action = 'save'

        if action not in JourneyStoreApi.journey_method_names:
            raise ValidationError(
                "action '{0}' is not allowed, "
                "only this methods are allowed; {1}".format(
                    action,
                    ", ".join(JourneyStoreApi.journey_method_names),
                )
                , 'action')

        return getattr(self, action)(**kwargs)

    @staticmethod
    def _parameter_validation(method, *args, **kwargs) -> typing.Dict:

        assert inspect.isfunction(method) or inspect.ismethod(method)

        errors = {}

        parameters = list(inspect.signature(method).parameters.values())

        method_kwargs = deepcopy(kwargs)
        method_args = list(deepcopy(args))

        for i in parameters:
            if len(method_args) > 0:
                method_args = method_args[1:]
                continue
            if i.name not in method_kwargs.keys():
                if i.default == i.empty:
                    errors[i.name] = ["This field is required"]
            else:
                del method_kwargs[i.name]

        for i in method_kwargs:
            errors[i] = ["This field is not required"]

        return errors

