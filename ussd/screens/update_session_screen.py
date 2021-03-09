from ussd.core import UssdHandlerAbstract
from ussd.graph import Link, Vertex
import json
from marshmallow import Schema, fields
from ussd.screens.schema import UssdBaseScreenSchema, NextUssdScreenSchema, WithItemSchema, UnionField


class UpdateSessionExpressionSchema(Schema):
    expression = UnionField([fields.Str(), fields.Int(), fields.Bool()], required=False)
    key = fields.Str(required=True)
    value = UnionField([fields.Str(), fields.Int(), fields.Bool()], required=True)


class UpdateSessionSchema(UssdBaseScreenSchema, NextUssdScreenSchema, WithItemSchema):
    values_to_update = fields.List(
        fields.Nested(UpdateSessionExpressionSchema),
        required=True
    )



class UpdateSessionScreen(UssdHandlerAbstract):
    """
    This screen is invisible to the user. Sometimes you may want to save
    something to the session to use later in other screens.

    Fields used to create this screen:
        1. next_screen
            The screen to go after the session has been saved

        2. values_to_update
            This section defines the session to be saved.

            Inside this section should define the following fields

            i. key
                    the key to be used to save
            ii. value
                    the value to store with the key above
            iii. expression
                    sometimes you want a condition before you can save data in
                    section

    Example:
        .. literalinclude:: .././ussd/tests/sample_screen_definition/valid_update_session_screen_conf.yml

    """
    screen_type = "update_session_screen"
    serializer = UpdateSessionSchema

    def handle(self):

        loop_items = self.get_loop_items()

        values_to_update = self.screen_content["values_to_update"]

        for item in loop_items:
            # update extra context
            extra_context = {
                "item": item
            }
            if isinstance(loop_items, dict):
                extra_context.update(
                    dict(
                        key=item,
                        value=loop_items[item],
                        item={item: loop_items[item]}
                    )
                )

            for update_value in values_to_update:
                if not (update_value.get('expression') and
                            self.evaluate_jija_expression(
                                update_value['expression'],
                                session=self.ussd_request.session,
                                extra_context=extra_context)):
                    continue

                # evaluate key
                key = update_value['key'] \
                    if not UssdHandlerAbstract._contains_vars(
                    update_value['key']) \
                    else self.evaluate_jija_expression(
                    update_value['key'],
                    session=self.ussd_request.session,
                    extra_context=extra_context
                )

                value = self.evaluate_jija_expression(
                    update_value['value'],
                    session=self.ussd_request.session,
                    extra_context=extra_context
                ) or update_value['value']

                # save them in the session store
                self.ussd_request.session[key] = value
        return self.route_options()

    def show_ussd_content(self, **kwargs):
        results = json.dumps(self.screen_content, indent=2, sort_keys=True)
        results = results.replace('"', "'")
        return results

    def get_next_screens(self):
        return [
            Link(
                Vertex(self.handler),
                Vertex(self.screen_content['next_screen'],
                       ""
                       )
            )
        ]
