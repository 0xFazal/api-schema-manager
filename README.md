# API Schema Manager

A schema management service for JSON/YAML OpenAPI specs. It supports versioning, application/service hierarchy, and file persistence.

## Setup

1. Clone the repository and navigate to the repo.

```bash
cd api-schema-manager
```

2. Create and activate a Python virtual environment:

```bash
python -m venv venv
# For Linux/macOS
source venv/bin/activate  
# For Windows 
.\venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start the FastAPI server:

```bash
uvicorn app.main:api --reload
```

The APIs will be available at `http://localhost:8000/`.

5. Visit [http://localhost:8000/docs](http://localhost:8000/docs) to try it with SwaggerUI.

---

## API Endpoints

### 1. Import Schema (JSON or YAML)

Upload an OpenAPI spec to an application/service.

```
POST /api/v1/schemas/import
```

**Form Data:**

* `application` (string, required)
* `service` (string, optional)
* `uploaded_by` (string, optional, default="cli")
* `file` (OpenAPI JSON/YAML file)

**Example:**

```bash
curl -X POST "http://localhost:8000/api/v1/schemas/import" \
  -F "application=my-app" \
  -F "service=orders" \
  -F "uploaded_by=local-test" \
  -F "file=@./openapi.json"
```

**Response:**

```json
{
  "application": "my-app",
  "service": "orders",
  "version": 1,
  "filename": "openapi.json",
  "file_path": "./data/schemas/my-app/orders/v1__openapi.json",
  "media_type": "json"
}
```

---

### 2. Get Latest Schema Metadata

Retrieve the latest schema metadata for an application/service.

```
GET /api/v1/schemas/{application}/{service}/latest
```

**Example:**

```bash
curl http://localhost:8000/api/v1/schemas/my-app/orders/latest
```

**Response:**

```json
{
  "application": "my-app",
  "service": "orders",
  "version": 2,
  "filename": "openapi.json",
  "file_path": "./data/schemas/my-app/orders/v2__openapi.json",
  "media_type": "json"
}
```

---

### 3. List All Versions

List all schema versions for an application/service.

```
GET /api/v1/schemas/{application}/{service}/versions
```

**Example:**

```bash
curl http://localhost:8000/api/v1/schemas/my-app/orders/versions
```

**Response:**

```json
[
  {"version": 2, "filename": "openapi.json", "media_type": "json", "created_at": "2025-09-08T11:17:59"},
  {"version": 1, "filename": "openapi.json", "media_type": "json", "created_at": "2025-09-08T11:17:03"}
]
```

---

### 4. Download a Specific Version

Download a schema file for a specific version.

```
GET /api/v1/schemas/{application}/{service}/versions/{version}/download
```

**Example:**

```bash
curl -L http://localhost:8000/api/v1/schemas/my-app/orders/versions/1/download -o schema-v1.json
```

This will save the file locally as `schema-v1.json`.

---

## Testing

All tests use `pytest` and FastAPI `TestClient`.

1. Ensure you are in the virtual environment.
2. Run the tests:

```bash
pytest -v tests/test_api.py
```

* Tests cover JSON and YAML imports, versioning, latest schema retrieval, and downloads.
* The `./data` folder and DB are cleaned before each test module.

---

## Project Structure

```
/api-schema-manager
├── app
│   ├── main.py          # FastAPI app
│   ├── crud.py          # DB CRUD operations
│   ├── models.py        # SQLAlchemy models
│   ├── utils.py         # File and schema utilities
│   └── db.py            # DB engine and session
├── data                 # Uploaded schemas (auto-created)
├── tests
│   └── test_api.py      # Pytest tests
├── requirements.txt
└── README.txt           # This file
```

---

## Notes

* Supports JSON and YAML OpenAPI specs.
* Application-level and service-level schemas.
* Versioning ensures previous schemas are retained.
* Files are stored on disk under `./data/schemas/{application}/{service}/`.
* SQLite database (`schema_metadata.db`) stores metadata.

---