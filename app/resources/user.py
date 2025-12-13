from flask.views import MethodView
from flask import request
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.extensions import db
from app.models.user import User
from app.schemas.user_schema import (UserCreateSchema, AdminStatusSchema, UserRegisterResponseSchema, UserLoginSchema,
                                     UserLoginResponseSchema, UserSchema, UserUpdateSchema, UserUpdateResponseSchema,
                                     UserDeleteResponseSchema)
from werkzeug.security import generate_password_hash, check_password_hash

blp = Blueprint("users", __name__, url_prefix="/users")


# Dekorator koji proverava da li korisnik ima privilegiju admina
def super_admin_required(fn):
    @jwt_required()
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_superadmin:
            abort(403, message="Admin rights required.")
        return fn(*args, **kwargs)

    return wrapper


# Ruta i klasa koja menja status korisnika
@blp.route("/<int:user_id>/make_admin")
class AdminStatus(MethodView):

    @super_admin_required
    @blp.arguments(AdminStatusSchema)
    def patch(self, data, user_id):
        """
        Menja admin status korisnika.
        data = {"is_admin": true/false}
        """
        user = User.query.get_or_404(user_id)
        # user.is_admin = True
        user.is_admin = data["is_admin"]
        db.session.commit()
        # return {"message": f"User {user.username} is now an admin."}, 200
        return {"message": f"User {user.username} is now {'admin' if user.is_admin else 'regular user'}."}, 200


# # Ruta i klasa koja menja status korisnika bez marshmallow schema
# @blp.route("/<int:user_id>/admin")
# class AdminStatus(MethodView):
#
#     @admin_required
#     def patch(self, user_id):
#         """
#         Menja admin status korisnika. Body zahteva treba da sadrži:
#         {"is_admin": true} ili {"is_admin": false}
#         """
#         from flask import request
#
#         user = User.query.get_or_404(user_id)
#
#         data = request.get_json()
#         if not data or "is_admin" not in data:
#             abort(400, message="is_admin field is required.")
#
#         user.is_admin = bool(data["is_admin"])
#         db.session.commit()
#
#         status = "admin" if user.is_admin else "regular user"
#         return {"message": f"User {user.username} is now a {status}."}, 200


@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserCreateSchema)
    @blp.response(201, UserRegisterResponseSchema)
    def post(self, user_data):
        """
        Registracija novog korisnika.
        user_data je već validiran dict.
        """
        if User.query.filter(
                (User.username == user_data["username"]) | (User.email == user_data["email"])
        ).first():
            return {"message": "Korisnik sa tim username-om ili email-om već postoji."}, 400

        # Ako je prvi korisnik → superadmin
        is_first_user = User.query.count() == 0

        new_user = User(
            username=user_data["username"],
            email=user_data["email"],
            password_hash=generate_password_hash(user_data["password"]),
            is_admin=is_first_user,
            is_superadmin=is_first_user
        )

        db.session.add(new_user)
        db.session.commit()

        return {
            "message": f"Korisnik {new_user.username} je uspešno registrovan.",
            "user": new_user
        }, 201


@blp.route("/login")
class UserLogin(MethodView):

    @blp.arguments(UserLoginSchema)
    @blp.response(200, UserLoginResponseSchema)
    def post(self, login_data):
        """
        Preuzimanje podataka iz prijave korisnika (username ili email + password).
        """
        login_value = login_data["login"]
        password = login_data["password"]

        # Provera da li je korisnik uneo email ili username
        if "@" in login_value:
            user = User.query.filter_by(email=login_value).first()
        else:
            user = User.query.filter_by(username=login_value).first()

        if not user:
            abort(401, message="Proverite da li ste pravilno uneli email/username i lozinku.")

        if not check_password_hash(user.password_hash, password):
            abort(401, message="Proverite da li ste pravilno uneli email/username i lozinku.")

        # Generisanje JWT tokena
        token = create_access_token(identity=str(user.id))

        return {
            "message": f"Uspešna prijava. Dobrodošao {user.username}.",
            "access_token": token,
            "user": user
        }, 200


@blp.route("/")
class Users(MethodView):

    @jwt_required()
    @blp.response(200, UserSchema(many=True))
    def get(self):
        # Preuzimanje identiteta korisnika iz JWT tokena
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        # Provera administratorskih privilegija
        if not user or not user.is_admin:
            abort(403, message="Pristup dozvoljen samo administratorima.")

        # Vraćamo sve korisnike
        users = User.query.all()
        return users


@blp.route("/me")
class UserSelf(MethodView):

    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self):
        # preuzimanje ID-a iz JWT tokena
        user_id = get_jwt_identity()

        # pronalazenje korisnika u bazi
        user = User.query.get_or_404(user_id)

        # vraćamo podatke o ulogovanom korisniku
        return user


@blp.route("/lookup")
class UserLookup(MethodView):

    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self):
        # 1. Dobavljanje prijavljenog korisnika
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        if not current_user:
            abort(401, message="Prijavljeni korisnik nije pronađen.")

        # 2. Čitanje query parametra
        login_value = request.args.get("login")
        if not login_value:
            abort(400, message="login query parameter is required.")

        # 3. Provera pristupa
        allowed = (
                current_user.is_admin or
                login_value == current_user.username or
                login_value == current_user.email
        )

        if not allowed:
            abort(403, message="Pristup dozvoljen samo vlasniku naloga ili administratoru.")

        # 4. Pretraga korisnika
        user = User.query.filter(
            (User.username == login_value) | (User.email == login_value)
        ).first()

        if not user:
            abort(404, message="Korisnik nije pronađen.")

        return user


# @blp.route("/lookup")
# class UserLookup(MethodView):
#
#     @jwt_required()
#     @blp.arguments(UserLookupSchema)
#     @blp.response(200, UserSchema)
#     def post(self, user_data):
#         """
#         Pristup podacima korisnika preko login parametra (username ili email).
#         Pristup imaju prijavljeni korisnici: vlasnik naloga ili administrator.
#         """
#         login_value = user_data["login"]
#
#         # Pronalazak korisnika u bazi po username ili email
#         user = User.query.filter(
#             (User.username == login_value) | (User.email == login_value)
#         ).first()
#
#         if not user:
#             abort(404, message="Korisnik nije pronađen.")
#
#         # Preuzimanje ID-ja trenutno prijavljenog korisnika
#         current_user_id = get_jwt_identity()
#         current_user = User.query.get(current_user_id)
#
#         # Provera prava pristupa: vlasnik naloga ili admin
#         if current_user.id != user.id and not current_user.is_admin:
#             abort(403, message="Pristup dozvoljen samo vlasniku naloga ili administratoru.")
#
#         return user


@blp.route("/<int:user_id>")
class UserDelete(MethodView):

    @jwt_required()
    @blp.response(200, UserDeleteResponseSchema)
    def delete(self, user_id):
        """
        Brisanje korisničkog naloga.
        - Admin može da obriše bilo koga.
        - Običan korisnik može obrisati samo svoj nalog.
        """

        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        target_user = User.query.get_or_404(user_id)

        # Ako nije admin → sme da obriše samo sebe
        if not current_user.is_admin:
            if current_user_id != user_id:
                abort(403, message="You cannot delete accounts of other users.")

        # Ako jeste admin → može obrisati bilo koga
        db.session.delete(target_user)
        db.session.commit()

        return {
            "message": f"User '{target_user.username}' has been deleted."
        }, 200


@blp.route("/me")
class UserUpdate(MethodView):

    @jwt_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserUpdateResponseSchema)
    def patch(self, update_data):
        """
        Ažuriranje podataka naloga prijavljenog korisnika.
        """
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        # Ažuriranje polja samo ako su poslata
        if "username" in update_data:
            user.username = update_data["username"]

        if "email" in update_data:
            user.email = update_data["email"]

        db.session.commit()

        return {
            "message": f"Nalog korisnika {user.id} je ažuriran.",
            "user": user
        }
