from .db import get_db, init_db
from . import crud, utils
from .models import Application, Service, SchemaVersion

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

api = FastAPI(title="API Schema Manager")

@api.on_event("startup")
def startup():
    utils.ensure_data_dirs()
    init_db()

@api.get("/")
def root():
    return {"status": "ok"}


@api.post("/api/v1/schemas/import")
def import_schema(
    application: str = Form(...),
    service: str = Form(None),
    uploaded_by: str = Form("cli"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Ensure application exists
    app_obj = crud.get_or_create_application(db, application)

    # Ensure service exists (if provided)
    svc_obj = None
    if service:
        svc_obj = crud.get_or_create_service(db, app_obj, service)

    next_version = crud.get_next_version(db, app_obj.id, svc_obj.id if svc_obj else None)
    saved_path, media_type = utils.save_uploaded_file(file, application, service, next_version)

    # validate schema
    content = file.file.read()
    file.file.seek(0)  # reset pointer after save
    spec, _ = utils.detect_media_type_and_load(content)
    utils.validate_openapi_spec(spec)

    # save DB row
    sv = crud.save_schema_version(
        db, app_obj.id, svc_obj.id if svc_obj else None,
        next_version, file.filename, saved_path, media_type, uploaded_by
    )

    return {
        "application": app_obj.name,
        "service": svc_obj.name if svc_obj else None,
        "version": sv.version,
        "filename": sv.filename,
        "file_path": sv.file_path,
        "media_type": sv.media_type,
    }


@api.get("/api/v1/schemas/{application}/{service}/latest")
def get_latest_schema(application: str, service: str, db: Session = Depends(get_db)):
    app_obj = db.query(Application).filter(Application.name == application).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="application not found")
    svc = db.query(Service).filter(Service.application_id == app_obj.id, Service.name == service).first()
    if not svc:
        raise HTTPException(status_code=404, detail="service not found")
    sv = (
        db.query(SchemaVersion)
        .filter(SchemaVersion.application_id == app_obj.id, SchemaVersion.service_id == svc.id)
        .order_by(SchemaVersion.version.desc())
        .first()
    )
    if not sv:
        raise HTTPException(status_code=404, detail="no schema versions found")
    return {
        "application": application,
        "service": service,
        "version": sv.version,
        "filename": sv.filename,
        "file_path": sv.file_path,
        "media_type": sv.media_type,
    }


@api.get("/api/v1/schemas/{application}/{service}/versions")
def list_versions(application: str, service: str, db: Session = Depends(get_db)):
    app_obj = db.query(Application).filter(Application.name == application).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="application not found")
    svc = db.query(Service).filter(Service.application_id == app_obj.id, Service.name == service).first()
    if not svc:
        raise HTTPException(status_code=404, detail="service not found")
    versions = crud.list_versions(db, app_obj.id, svc.id)
    return [
        {
            "version": v.version,
            "filename": v.filename,
            "media_type": v.media_type,
            "created_at": v.created_at.isoformat(),
        }
        for v in versions
    ]


@api.get("/api/v1/schemas/{application}/{service}/versions/{version}/download")
def download_version(application: str, service: str, version: int, db: Session = Depends(get_db)):
    app_obj = db.query(Application).filter(Application.name == application).first()
    if not app_obj:
        raise HTTPException(status_code=404, detail="application not found")
    svc = db.query(Service).filter(Service.application_id == app_obj.id, Service.name == service).first()
    if not svc:
        raise HTTPException(status_code=404, detail="service not found")
    sv = (
        db.query(SchemaVersion)
        .filter(
            SchemaVersion.application_id == app_obj.id,
            SchemaVersion.service_id == svc.id,
            SchemaVersion.version == version,
        )
        .first()
    )
    if not sv:
        raise HTTPException(status_code=404, detail="version not found")
    return FileResponse(path=sv.file_path, filename=sv.filename)
