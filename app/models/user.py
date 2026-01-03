from app.extensions import db  # povezivanje sa SQLAlchemy ekstenzijom
from sqlalchemy.sql import func


class User(db.Model):
    __tablename__ = "users"  # ime tabele u bazi

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_superadmin = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now(),
                           onupdate=func.now())


# Eksplicitna veza ka Task modelu
    tasks = db.relationship("Task", back_populates="user", lazy="dynamic", cascade="all, delete-orphan")

    # Soft delete
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    deleted_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Eksplicitna veza ka AuditLog modelu
    audit_logs_as_actor = db.relationship(
        "AuditLog",
        foreign_keys="AuditLog.actor_user_id",
        back_populates="actor",
        lazy="dynamic"
    )
    audit_logs_as_target = db.relationship(
        "AuditLog",
        foreign_keys="AuditLog.target_user_id",
        back_populates="target",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<User id={self.id}, username={self.username}, email={self.email}>"
