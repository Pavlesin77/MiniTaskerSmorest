from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.user import User


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    email = fields.Email()
    is_admin = fields.Bool()
    is_superadmin = fields.Bool()
    created_at = fields.DateTime(dump_only=True)  # novo polje
    updated_at = fields.DateTime(dump_only=True)  # novo polje


# Schema za registraciju korisnika
class UserCreateSchema(Schema):
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80)
    )
    email = fields.Email(required=True)
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=6)
    )


# Schema za serilizaciju (response)
class UserRegisterResponseSchema(Schema):
    message = fields.Str(required=True)
    user = fields.Nested(UserSchema, required=True)


# Schema za promenu statusa korisnika
class AdminStatusSchema(Schema):
    is_admin = fields.Boolean(required=True)


# Schema za prijavu registrovanog korisnika
class UserLoginSchema(Schema):
    login = fields.Str(required=True)  # može biti username ili email
    password = fields.Str(
        required=True,
        load_only=True,
        validate=validate.Length(min=6)
    )


# class UserLoginSchema(Schema):
#     username = fields.Str(
#         required=True,
#         validate=validate.Length(min=3, max=80)
#     )
#     password = fields.Str(
#         required=True,
#         load_only=True,
#         validate=validate.Length(min=6)
#     )


# Schema za odgovor klijentu nakon uspesne prijave
class UserLoginResponseSchema(Schema):
    access_token = fields.Str(required=True)
    message = fields.Str(required=True)
    user = fields.Nested(UserSchema, required=True)


# Schema za ulazne podatke za rutu koja vraca podatke iz pojedinacnog naloga (login parametar)
class UserLookupSchema(Schema):
    login = fields.Str(required=True, validate=validate.Length(min=3, max=80))


class UserLookupResponseSchema(Schema):
    message = fields.Str(required=True)
    user = fields.Nested(UserSchema, required=True)


class UserDeleteResponseSchema(Schema):
    message = fields.Str(required=True)


# Schema za ulazne podatke za rutu koja azurira podatke
class UserUpdateSchema(Schema):
    username = fields.Str(
        required=False,
        validate=validate.Length(min=3, max=50),
        metadata={"description": "Novi username korisnika"}
    )
    email = fields.Email(
        required=False,
        metadata={"description": "Nova email adresa korisnika"}
    )


# Schema koja serijalizuje odgovor servera nakon azuriranja podataka
class UserUpdateResponseSchema(Schema):
    message = fields.Str()
    user = fields.Nested(UserSchema)


# Ulazna schema za query parametre (tabela audit_logs)
class AuditLogQuerySchema(Schema):
    actor_user_id = fields.Int(required=False, allow_none=True)
    target_user_id = fields.Int(required=False, allow_none=True)
    date_from = fields.DateTime(required=False, allow_none=True)
    date_to = fields.DateTime(required=False, allow_none=True)


# Response schema za rutu koja vraća audit log zapise superadminu
class AuditLogResponseSchema(Schema):
    id = fields.Int(dump_only=True)
    actor_user_id = fields.Int(allow_none=True)
    target_user_id = fields.Int(allow_none=True)
    action = fields.Str()
    created_at = fields.DateTime()

# class UserSchema(Schema):
#     id = fields.Int(dump_only=True)
#     username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
#     email = fields.Email(required=True)
#
#
# class UserCreateSchema(UserSchema):
#     password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6))
