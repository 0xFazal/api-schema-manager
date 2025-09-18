import os
import json
import yaml
from typing import Tuple
from fastapi import UploadFile

DATA_DIR = os.getenv("DATA_DIR", "./data")
SCHEMA_BASE_DIR = os.path.join(DATA_DIR, "schemas")

def ensure_data_dirs():
    os.makedirs("./data/schemas", exist_ok=True)


def detect_media_type_and_load(content: bytes):
    text = content.decode("utf-8")
    try:
        spec = json.loads(text)
        return spec, "json"
    except json.JSONDecodeError:
        try:
            spec = yaml.safe_load(text)
            return spec, "yaml"
        except yaml.YAMLError:
            raise ValueError("Unsupported file format: must be JSON or YAML")


def validate_openapi_spec(parsed_obj: dict) -> Tuple[bool, str]:
    """Try to validate with openapi-spec-validator if available; otherwise do a minimal check."""
    try:
        from openapi_spec_validator import validate_spec
        validate_spec(parsed_obj)
        return True, "validated"
    except Exception as e:
        # If import failed or validation failed, fall back to mild checks
        if isinstance(e, ImportError):
            # weak validation
            if not (isinstance(parsed_obj, dict) and ("openapi" in parsed_obj or "swagger" in parsed_obj)):
                return False, "missing top-level 'openapi' or 'swagger' key"
            return True, "weak-validated"
        else:
            return False, str(e)


def persist_bytes(app_name: str, service_name: str | None, version: int, filename: str, raw_bytes: bytes) -> str:
    # Choose storage path
    svc_part = service_name if service_name else "_app"
    dir_path = os.path.join("./data/schemas", app_name, svc_part)
    os.makedirs(dir_path, exist_ok=True)
    # keep extension from filename if any
    store_name = f"v{version}__{filename}"
    path = os.path.join(dir_path, store_name)
    with open(path, "wb") as f:
        f.write(raw_bytes)
    return path


def save_uploaded_file(file, application: str, service: str, version: int):
    import os

    folder = f"./data/schemas/{application}/{service or 'root'}"
    os.makedirs(folder, exist_ok=True)
    dest_path = os.path.join(folder, f"v{version}__{file.filename}")

    content = file.file.read()
    file.file.seek(0)  # reset for later
    _, media_type = detect_media_type_and_load(content)

    with open(dest_path, "wb") as f:
        f.write(content)

    return dest_path, media_type