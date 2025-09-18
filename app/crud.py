from sqlalchemy.orm import Session
from . import models


def get_or_create_application(db: Session, name: str):
    app = db.query(models.Application).filter(models.Application.name == name).first()
    if app:
        return app
    app = models.Application(name=name)
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def get_or_create_service(db: Session, application: models.Application, service_name: str):
    svc = db.query(models.Service).filter(
        models.Service.application_id == application.id,
        models.Service.name == service_name,
    ).first()
    if svc:
        return svc
    svc = models.Service(name=service_name, application_id=application.id)
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


def next_version_for(db: Session, application_id: int, service_id: int | None):
    q = db.query(models.SchemaVersion).filter(models.SchemaVersion.application_id == application_id)
    if service_id is None:
        q = q.filter(models.SchemaVersion.service_id.is_(None))
    else:
        q = q.filter(models.SchemaVersion.service_id == service_id)
    last = q.order_by(models.SchemaVersion.version.desc()).first()
    return 1 if not last else last.version + 1


def save_schema_version(
    db: Session,
    app_id: int,
    svc_id: int | None,
    version: int,
    filename: str,
    file_path: str,
    media_type: str,
    uploaded_by: str | None = None,
):
    sv = models.SchemaVersion(
        application_id=app_id,
        service_id=svc_id,
        version=version,
        filename=filename,
        file_path=file_path,
        media_type=media_type,
        uploaded_by=uploaded_by,
        is_active=True,
    )
    # mark previous versions as not active
    q = db.query(models.SchemaVersion).filter(models.SchemaVersion.application_id == app_id)
    if svc_id is None:
        q = q.filter(models.SchemaVersion.service_id.is_(None))
    else:
        q = q.filter(models.SchemaVersion.service_id == svc_id)
    for prev in q.all():
        prev.is_active = False
    db.add(sv)
    db.commit()
    db.refresh(sv)
    return sv


def list_versions(db: Session, app_id: int, svc_id: int | None):
    q = db.query(models.SchemaVersion).filter(models.SchemaVersion.application_id == app_id)
    if svc_id is None:
        q = q.filter(models.SchemaVersion.service_id.is_(None))
    else:
        q = q.filter(models.SchemaVersion.service_id == svc_id)
    return q.order_by(models.SchemaVersion.version.desc()).all()


def get_next_version(db: Session, application_id: int, service_id: int | None) -> int:
    """
    Return the next version number for a given (application, service).
    If no previous versions exist, return 1.
    """
    q = db.query(models.SchemaVersion).filter_by(
        application_id=application_id, service_id=service_id
    )
    latest = q.order_by(models.SchemaVersion.version.desc()).first()
    return 1 if not latest else latest.version + 1


def get_latest_version(db: Session, application_id: int, service_id: int | None):
    """
    Fetch the latest (active) schema version for a given (application, service).
    """
    q = db.query(models.SchemaVersion).filter(models.SchemaVersion.application_id == application_id)
    if service_id is None:
        q = q.filter(models.SchemaVersion.service_id.is_(None))
    else:
        q = q.filter(models.SchemaVersion.service_id == service_id)
    return q.order_by(models.SchemaVersion.version.desc()).first()


def get_schema_version(db: Session, application_id: int, service_id: int | None, version: int):
    """
    Fetch a specific schema version for a given (application, service).
    """
    q = db.query(models.SchemaVersion).filter(
        models.SchemaVersion.application_id == application_id,
        models.SchemaVersion.version == version,
    )
    if service_id is None:
        q = q.filter(models.SchemaVersion.service_id.is_(None))
    else:
        q = q.filter(models.SchemaVersion.service_id == service_id)
    return q.first()
