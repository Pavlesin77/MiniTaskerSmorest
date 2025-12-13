from marshmallow import Schema, fields, validate, validates, ValidationError
from app.models.user import User


class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str()
    email = fields.Email()
    is_admin = fields.Bool()
    is_superadmin = fields.Bool()


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

    @validates("username")
    def validate_unique_username(self, value, **kwargs):
        if User.query.filter_by(username=value).first():
            raise ValidationError("Username je već zauzet.")

    @validates("email")
    def validate_unique_email(self, value, **kwargs):
        if User.query.filter_by(email=value).first():
            raise ValidationError("Email je već zauzet.")


# Schema koja serijalizuje odgovor servera nakon azuriranja podataka
class UserUpdateResponseSchema(Schema):
    message = fields.Str()
    user = fields.Nested(UserSchema)


# class UserSchema(Schema):
#     id = fields.Int(dump_only=True)
#     username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
#     email = fields.Email(required=True)
#
#
# class UserCreateSchema(UserSchema):
#     password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6))
