# Design deviations and Sprint 1 boundary

Baseline: Aaron Tobias, CareConnect Data Model and Schema Document, October 19 2026 (28 tables); System Architecture Document, October 2 2026.

| Baseline | Sprint 1 implementation | Reason and consequence |
| --- | --- | --- |
| Patient linked to app_user; account owns display name and contact fields | Patient stores first/last name, DOB, optional email/phone, unique record_number and status | Four-model increment can run independently; identity migration and name/contact reconciliation required later. Email is not unique because contacts may be shared. |
| vital_reading plus vital_component and metric_catalog | VitalSigns has one numeric scalar, kind, canonical unit and measured_at | Meets core timestamped-reading model; paired blood pressure, glucose meal context, configurable bounds and source attribution remain deferred. |
| Versioned care_plan with immutable published history and one-active-plan index | CarePlan has title, patient, status, start/end/review dates | Establishes assignment and dates only. No publish API, versioning, one-active-plan enforcement, goals or tasks yet. |
| medication_catalog, medication_order and plan_medication membership | Medication stores regimen fields and one required plan link | Four-model boundary; cannot reuse one order across plan versions. Composite FK ensures patient ownership matches plan. Frequency is descriptive text, not an executable schedule. |
| Lifecycle actor/reason and audit history | UUID and created_at on all models; patient inactive_at soft deletion | Preserves records but does not implement baseline attribution or append-only auditing. |
| Assignment-scoped protected API with cursor pagination and custom errors | Local unauthenticated patient CRUD, bounded offset pagination, standard FastAPI errors | Sprint 1 functional surface only; protected multiuser operation deferred. |

SQLAlchemy uses UUID keys, explicit relationships, non-null fields, foreign keys with RESTRICT, status/date/positive-value checks, fixed-precision numeric declarations, and indexes for FK lookup. SQLite foreign keys are enabled per connection. UTC adapter rejects naive timestamps. SQLite numeric storage is not equivalent to PostgreSQL fixed decimal enforcement; ORM vital validation limits finite positive values to three decimal places. Medication precision and non-patient writes need service validation before future public endpoints.

No clinical validity, regulatory compliance, full baseline implementation, remote CI pass, or live PostgreSQL pass is implied by local tests. All four core models are functional persistence objects; APIs for the other three entities are outside Sprint 1.
