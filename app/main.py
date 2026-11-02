from datetime import datetime, timezone
from uuid import UUID
from fastapi import FastAPI, APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .database import get_session
from .models import Patient
from .schemas import PatientCreate, PatientUpdate, PatientRead

app = FastAPI(title='CareConnect Sprint 1', version='0.1.0', description='Local synthetic-data prototype. Authentication and assignment authorization are deferred. Bind to loopback only.')
router = APIRouter(prefix='/api/v1/patients', tags=['Patients'])

@app.middleware('http')
async def no_store(request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    return response

def find_patient(session, patient_id):
    patient = session.get(Patient, patient_id)
    if patient is None or patient.inactive_at is not None:
        raise HTTPException(404, 'Patient not found')
    return patient

def save(session, patient):
    try:
        session.add(patient)
        session.commit()
        session.refresh(patient)
    except IntegrityError:
        session.rollback()
        raise HTTPException(409, 'Patient record conflicts with existing data') from None
    return patient

@router.post('', response_model=PatientRead, status_code=201)
def create_patient(data: PatientCreate, session: Session = Depends(get_session)):
    return save(session, Patient(**data.model_dump()))

@router.get('', response_model=list[PatientRead])
def list_patients(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), session: Session = Depends(get_session)):
    return session.scalars(select(Patient).where(Patient.inactive_at.is_(None)).order_by(Patient.created_at, Patient.id).offset(offset).limit(limit)).all()

@router.get('/{patient_id}', response_model=PatientRead)
def read_patient(patient_id: UUID, session: Session = Depends(get_session)):
    return find_patient(session, patient_id)

@router.patch('/{patient_id}', response_model=PatientRead)
def update_patient(patient_id: UUID, data: PatientUpdate, session: Session = Depends(get_session)):
    patient = find_patient(session, patient_id)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(patient, key, value)
    return save(session, patient)

@router.delete('/{patient_id}', status_code=204)
def delete_patient(patient_id: UUID, session: Session = Depends(get_session)):
    patient = find_patient(session, patient_id)
    patient.status = 'inactive'
    patient.inactive_at = datetime.now(timezone.utc)
    save(session, patient)
    return Response(status_code=204)

app.include_router(router)
