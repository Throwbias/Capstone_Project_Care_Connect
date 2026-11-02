# CareConnect Sprint 1

Academic prototype for CSC5324, Aaron Tobias. Fictional records only.

## Setup

Use Python 3.12. From your clone or extracted project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Windows PowerShell: activate with `.venv\Scripts\Activate.ps1` instead.
Open http://127.0.0.1:8000/docs for interactive OpenAPI documentation.
The database starts empty. Create a fictional patient in `/docs` using:

```json
{"record_number":"DEMO001","first_name":"Alex","last_name":"Example","date_of_birth":"1980-01-01","email":"alex@example.org"}
```

The default SQLite database is `careconnect.db`. Override `DATABASE_URL` in your shell if needed; `.env` is an example only and is not automatically loaded. Database creation uses Alembic, not application startup.

## Patient API

| Method | Path | Result |
| --- | --- | --- |
| POST | /api/v1/patients | 201 created; unique record number |
| GET | /api/v1/patients | 200 list; limit 1–100, offset >= 0 |
| GET | /api/v1/patients/{patient_id} | 200 or 404 |
| PATCH | /api/v1/patients/{patient_id} | 200; supplied fields only |
| DELETE | /api/v1/patients/{patient_id} | 204; soft delete |

Invalid payloads return 422; duplicate record numbers return 409. PATCH can clear email/phone with null, but cannot clear required fields or change the record number. DELETE sets inactive_at and status, preserves related data, and hides the record from API reads. Setting status inactive alone represents account suspension and does not delete the record. No restore endpoint exists in Sprint 1.

## Verification

```bash
pytest -q
alembic check
```

Tests use isolated temporary SQLite files. Model tests cover all four models, database constraints, relationships, UTC handling, and cross-patient medication rejection. API tests cover CRUD, validation, conflict responses, soft deletion, and OpenAPI. Migration tests upgrade a fresh database, check metadata drift, downgrade, and upgrade again. CI runs the same suite on Python 3.12; remote CI status is not yet verified.

## Repository workflow

Use `main` for reviewed stable code, `feature/sprint-1-core-data` for this increment, and future `feature/<short-description>` branches with pull requests. The architecture document specifies GitHub but contains no explicit branch naming policy; this convention is newly recorded here. Clone the repository with:

```bash
git clone https://github.com/Throwbias/Capstone_Project_Care_Connect.git
cd Capstone_Project_Care_Connect
```

Run the setup commands above from that directory. Submit the repository URL after verifying the Sprint 1 files on main.

## Scope and limitations

Sprint 1 has Patient, VitalSigns, CarePlan, and Medication models. Only patient records have HTTP endpoints. See docs/design-deviations.md for changes from the October 19 design. Authentication, assignment authorization, audit events, Dash UI, plan publishing/versioning, dosing/adherence, alerts, and clinical bounds are deferred. No production security or HIPAA compliance claim is made. Routes are unauthenticated: bind to loopback and use synthetic data only. PostgreSQL remains the target; live PostgreSQL execution is not verified in this sprint.
