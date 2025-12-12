from marshmallow import Schema, fields


class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    description = fields.Str()
    is_done = fields.Bool()
    user_id = fields.Int(required=True)
