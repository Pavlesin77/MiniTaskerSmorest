from sqlalchemy.sql import func
from app.extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    actor_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=func.now())
    # created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    # Relacije
    actor = db.relationship(
        "User",
        foreign_keys=[actor_user_id],
        back_populates="audit_logs_as_actor",
        passive_deletes=True
    )

    target = db.relationship(
        "User",
        foreign_keys=[target_user_id],
        back_populates="audit_logs_as_target",
        passive_deletes=True
    )
