from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    validates_schema,
    ValidationError,
)

class CreateOrderRequestSchema(Schema):
    order_id = fields.Str(validate=validate.Length(max=32))
    reference_code = fields.Str(required=True)
    amount = fields.Int(required=True)
    description = fields.Str(required=True)
    session_time = fields.Int(default=4)
    expiry_order = fields.Str(required=True)
    created_date = fields.Str(required=True)
    order_status = fields.Str(validate=validate.Length(max=25))

    @validates('order_id')
    def validate_order_id(self, value):
        if len(value) > 32:
            raise ValidationError('Longer than maximum length 32.')

    @validates('amount')
    def validate_amount(self, value):
        if value < 1000 or value > 10000000:
            raise ValidationError('\'amount\' must be in range 1.000 - 10.000.000.')

    @validates('reference_code')
    def validate_reference_code(self, value):
        if len(value) > 50:
            raise ValidationError('Longer than maximum length 50.')
            
    @validates('session_time')
    def validate_session_time(self, value):
        if value < 1 or value > 1440:
            raise ValidationError('\'session_time\' must be in range 1 - 1440.')

    @validates('description')
    def validate_description(self, value):
        if len(value) > 255:
            raise ValidationError('Longer than maximum length 255.')

