import typing
from marshmallow import fields


class UssdTextField(fields.Field):
    """
    Ussd text that's going to be displayed to the user.
    example

    text: This is the text that is going to be shown

    To display multi language

    text:
        en: This the text in english
        sw: this the text in swahili
        default: en
    """

    def _serialize(self, value, attr, obj, **kwargs):
        if not isinstance(value, dict):
            return {
                'en': value,
                'default': 'en'}
        return value


class WithItemField(fields.Field):

    def _deserialize(
        self,
        value: typing.Any,
        attr: typing.Optional[str],
        data: typing.Optional[typing.Mapping[str, typing.Any]],
        **kwargs
    ):
        if isinstance(value, list):
            return value
        return value


class WithDictField(fields.Field):

    def _deserialize(
            self,
            value: typing.Any,
            attr: typing.Optional[str],
            data: typing.Optional[typing.Mapping[str, typing.Any]],
            **kwargs
    ):
        if isinstance(value, dict):
            return value
        return value


class NextUssdScreenField(fields.Field):

    def _deserialize(
        self,
        value: typing.Any,
        attr: typing.Optional[str],
        data: typing.Optional[typing.Mapping[str, typing.Any]],
        **kwargs
    ):
        if not isinstance(value, list):
            return [{"condition": "true", "next_screen": value}]
        return value
