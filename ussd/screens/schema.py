from marshmallow import Schema, fields, validates, ValidationError, validate
from ussd.screens.fields import UssdTextField, NextUssdScreenField, WithDictField, WithItemField


class UssdBaseScreenSchema(Schema):
    type = fields.Str(required=True)

    @validates("type")
    def validate_type(self, value):
        # to avoid cyclic import
        from ussd.core import _registered_ussd_handlers
        if value not in _registered_ussd_handlers.keys():
            raise ValidationError("Invalid screen type not supported")
        return value


class UssdTextSchema(Schema):
    text = UssdTextField(required=True)


class UssdContentBaseSchema(UssdBaseScreenSchema, UssdTextSchema):
    pass


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


class WithItemSchema(Schema):
    with_items = WithItemField(required=False, default=None)


class WithDictSchema(Schema):
    with_dict = WithDictField(required=False, default=None)
