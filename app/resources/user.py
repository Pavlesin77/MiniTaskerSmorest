from flask.views import MethodView
from flask import request
from flask_smorest import Blueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.extensions import db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.user_schema import (UserCreateSchema, AdminStatusSchema, UserRegisterResponseSchema, UserLoginSchema,
                                     UserLoginResponseSchema, UserSchema, UserUpdateSchema, UserUpdateResponseSchema,
                                     UserDeleteResponseSchema, UserLookupSchema, UserLookupResponseSchema,
                                     AuditLogQuerySchema, AuditLogResponseSchema)
from app.utils.audit import create_audit_log
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

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
        if user.is_deleted:
            abort(400, message="Cannot change admin status of a deactivated user.")

        # user.is_admin = True
        user.is_admin = data["is_admin"]
        db.session.commit()

        create_audit_log(
            actor_id=get_jwt_identity(),  # superadmin koji menja status
            target_id=user.id,  # korisnik kome se menja status
            action=f"Superadmin je postavio '{user.username}' na {'admin' if user.is_admin else 'regular user'}."
        )

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

        # Audit log za registraciju korisnika
        create_audit_log(
            actor_id=new_user.id,
            target_id=new_user.id,
            action=f"Korisnik '{new_user.username}' je registrovan."
        )

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

        # Provera statusa naloga korisnika (soft delete)
        if user.is_deleted:
            abort(403, message="This account has been deactivated.")

        # Generisanje JWT tokena
        token = create_access_token(identity=str(user.id))

        create_audit_log(
            actor_id=user.id,  # korisnik koji se prijavio
            target_id=user.id,  # cilj je isti korisnik
            action=f"Korisnik '{user.username}' se prijavio."
        )

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

        # Vraćamo sve korisnike ciji je nalog aktivan
        users = User.query.filter_by(is_deleted=False).all()
        return users


@blp.route("/deleted")
class DeletedUsers(MethodView):

    @jwt_required()
    @blp.response(200, UserSchema(many=True))
    def get(self):
        current_user_id = get_jwt_identity()
        current_user = User.query.get_or_404(current_user_id)

        if not current_user.is_superadmin:
            abort(403, message="Pristup dozvoljen samo superadministratoru.")

        users = User.query.filter_by(is_deleted=True).all()
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

        create_audit_log(
            actor_id=user.id,
            target_id=user.id,
            action=f"Korisnik '{user.username}' je pregledao svoje podatke."
        )

        # vraćamo podatke o ulogovanom korisniku
        return user

    @jwt_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserUpdateResponseSchema)
    def patch(self, update_data):
        """
        Ažuriranje podataka naloga prijavljenog korisnika.
        """
        user_id = get_jwt_identity()
        user = User.query.get_or_404(user_id)

        # Provera jedinstvenosti username-a
        if "username" in update_data:
            existing = User.query.filter_by(username=update_data["username"]).first()
            if existing and existing.id != user.id:
                abort(400, message="Username je već zauzet.")
            user.username = update_data["username"]

        # Provera jedinstvenosti email-a
        if "email" in update_data:
            existing = User.query.filter_by(email=update_data["email"]).first()
            if existing and existing.id != user.id:
                abort(400, message="Email je već zauzet.")
            user.email = update_data["email"]

        db.session.commit()

        create_audit_log(
            actor_id=user.id,  # korisnik koji menja svoj profil
            target_id=user.id,  # cilj je sam korisnik
            action=f"Korisnik '{user.username}' je ažurirao svoj profil: {update_data}"
        )

        return {
            "message": f"Nalog korisnika {user.id} je ažuriran.",
            "user": user
        }


@blp.route("/lookup")
class UserLookup(MethodView):

    @jwt_required()
    @blp.arguments(UserLookupSchema, location="query")  # ubacujemo schemu za query parametar
    @blp.response(200, UserLookupResponseSchema)
    def get(self, args):
        # args["login"] sadrži username ili email korisnika kojeg admin želi da preuzme
        login_value = args["login"]

        # Dobavljanje prijavljenog korisnika
        user_id = get_jwt_identity()
        current_user = User.query.get(user_id)
        if not current_user:
            abort(401, message="Prijavljeni korisnik nije pronađen.")

        # Provera pristupa
        if not (current_user.is_admin or current_user.is_superadmin):
            abort(403, message="Pristup dozvoljen samo administratoru.")

        # Pretraga korisnika
        user = User.query.filter(
            (User.username == login_value) | (User.email == login_value)
        ).first()

        if not user:
            abort(404, message="Korisnik nije pronađen.")

        if user.is_deleted:
            abort(410, message="User account is deactivated.")

        create_audit_log(
            actor_id=current_user.id,  # admin koji preuzima nalog
            target_id=user.id,  # korisnik čiji se nalog preuzima
            action=f"Admin '{current_user.username}' je preuzeo nalog korisnika '{user.username}'."
        )

        return {
            "message": f"Nalog korisnika {user.username}:",
            "user": user
        }


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

        # Ako je korisnik već obrisan
        if target_user.is_deleted:
            abort(400, message="User account is already deleted.")

        # Ako nije admin → sme da obriše samo sebe
        if not current_user.is_admin:
            if current_user_id != user_id:
                abort(403, message="You cannot delete accounts of other users.")

        # Soft delete
        target_user.is_deleted = True
        target_user.deleted_at = datetime.now(timezone.utc)

        # Ako jeste admin → može obrisati bilo koga
        # db.session.delete(target_user)

        db.session.commit()

        return {
            "message": f"User '{target_user.username}' has been deleted."
        }, 200


@blp.route("/audit-logs")
class UserAuditLogs(MethodView):

    @jwt_required()
    @blp.arguments(AuditLogQuerySchema, location="query")
    @blp.response(200, AuditLogResponseSchema(many=True))
    def get(self, args):
        # 1. Provera korisnika
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            abort(401, message="Korisnik ne postoji.")

        if not user.is_superadmin:
            abort(403, message="Pristup dozvoljen samo superadministratoru.")

        # 2. Osnovni query
        query = AuditLog.query

        # 3. Filtriranje po query parametrima
        if args.get("actor_user_id") is not None:
            query = query.filter(AuditLog.actor_user_id == args["actor_user_id"])

        if args.get("target_user_id") is not None:
            query = query.filter(AuditLog.target_user_id == args["target_user_id"])

        if args.get("date_from") is not None:
            query = query.filter(AuditLog.created_at >= args["date_from"])

        if args.get("date_to") is not None:
            query = query.filter(AuditLog.created_at <= args["date_to"])

        # 4. Vraćanje rezultata
        return query.order_by(AuditLog.created_at.desc()).all()
