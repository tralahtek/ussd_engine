from marshmallow import Schema, fields, validates, ValidationError, validate
import typing


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


class UssdBaseScreenSchema(Schema):
    type = fields.Str(required=True)


class UssdTextSchema(Schema):
    text = UssdTextField(required=True)


class UssdContentBaseSchema(UssdBaseScreenSchema, UssdTextSchema):
    pass


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


class NextUssdScreenSchema(Schema):
    next_screen = NextUssdScreenField(required=True)

    @validates("next_screen")
    def validate_next_screen(self, value):
        for next_screen_config in value:
            next_screen = next_screen_config.get('next_screen')
            if not next_screen:
                raise ValidationError(
                    {'next_screen': ['This field is required.']}
                )
            if next_screen not in self.context.keys():
                raise ValidationError(
                    "{screen} is missing in ussd journey".format(screen=next_screen)
                )
        return value


class MenuOptionSchema(UssdTextSchema, NextUssdScreenSchema):
    input_value = fields.Str(required=False, validate=validate.Length(max=5))
    input_display = fields.Str(required=False, validate=validate.Length(max=5))


class MenuSchema(Schema):
    options = fields.List(fields.Nested(MenuOptionSchema), required=True)
