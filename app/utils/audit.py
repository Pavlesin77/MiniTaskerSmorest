from app.extensions import db
from app.models.audit_log import AuditLog


def create_audit_log(actor_id: int | None, target_id: int | None, action: str):
    """
    Kreira audit log zapis.

    :param actor_id: ID korisnika koji izvodi akciju (može biti None, npr. za sistemske ili neuspešne akcije)
    :param target_id: ID korisnika koji je meta akcije (može biti None)
    :param action: opis akcije
    """
    log = AuditLog(
        actor_user_id=actor_id,
        target_user_id=target_id,
        action=action
    )
    db.session.add(log)
    db.session.commit()
