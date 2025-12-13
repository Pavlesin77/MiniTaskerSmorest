from app.extensions import db  # povezivanje sa SQLAlchemy ekstenzijom


class User(db.Model):
    __tablename__ = "users"  # ime tabele u bazi

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    # is_superadmin = db.Column(db.Boolean, default=False, nullable=False)

    # Eksplicitna veza ka Task modelu
    tasks = db.relationship(
        "Task",
        back_populates="user",
        lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User id={self.id}, username={self.username}, email={self.email}>"



