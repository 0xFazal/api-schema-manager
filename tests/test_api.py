import json
import pytest
from fastapi.testclient import TestClient
from app.main import api  


client = TestClient(api)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    import os, shutil
    from app.db import init_db

    # Remove old data
    if os.path.exists("./data"):
        shutil.rmtree("./data")

    # Ensure folder exists
    os.makedirs("./data", exist_ok=True)

    # Initialize DB (tables)
    init_db()
    yield

def make_sample_spec_json():
    return {
        "openapi": "3.0.0",
        "info": {"title": "demo-json", "version": "1.0.0"},
        "paths": {}
    }


def make_sample_spec_yaml():
    return """
openapi: 3.0.0
info:
  title: demo-yaml
  version: 1.0.0
paths: {}
"""


def test_import_and_list_versions_json():
    spec = make_sample_spec_json()
    files = {"file": ("openapi.json", json.dumps(spec), "application/json")}

    # Import v1
    resp = client.post(
        "/api/v1/schemas/import",
        data={"application": "demoapp", "service": "svc1", "uploaded_by": "pytest"},
        files=files,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["application"] == "demoapp"
    assert body["service"] == "svc1"
    assert body["version"] == 1

    # Import again to create v2
    resp2 = client.post(
        "/api/v1/schemas/import",
        data={"application": "demoapp", "service": "svc1"},
        files=files,
    )
    assert resp2.status_code == 200
    assert resp2.json()["version"] == 2

    # List versions
    r = client.get("/api/v1/schemas/demoapp/svc1/versions")
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) == 2
    assert versions[0]["version"] == 2  # latest first


def test_import_and_list_versions_yaml():
    yaml_spec = make_sample_spec_yaml()
    files = {"file": ("openapi.yaml", yaml_spec, "application/x-yaml")}

    # Import YAML spec
    resp = client.post(
        "/api/v1/schemas/import",
        data={"application": "demoapp", "service": "svc2", "uploaded_by": "pytest"},
        files=files,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["service"] == "svc2"
    assert body["version"] == 1
    assert body["media_type"] == "yaml"

    # List versions
    r = client.get("/api/v1/schemas/demoapp/svc2/versions")
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) == 1
    assert versions[0]["media_type"] == "yaml"


def test_latest_and_download():
    # Latest JSON schema
    r = client.get("/api/v1/schemas/demoapp/svc1/latest")
    assert r.status_code == 200
    latest_json = r.json()
    assert latest_json["version"] == 2

    # Download version 1 JSON
    r2 = client.get("/api/v1/schemas/demoapp/svc1/versions/1/download")
    assert r2.status_code == 200
    assert r2.headers["content-disposition"].startswith("attachment; filename=")

    # Latest YAML schema
    r3 = client.get("/api/v1/schemas/demoapp/svc2/latest")
    assert r3.status_code == 200
    latest_yaml = r3.json()
    assert latest_yaml["media_type"] == "yaml"

    # Download version 1 YAML
    r4 = client.get("/api/v1/schemas/demoapp/svc2/versions/1/download")
    assert r4.status_code == 200
    assert r4.headers["content-disposition"].startswith("attachment; filename=")
