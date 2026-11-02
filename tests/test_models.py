from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import configure_mappers
from app.models import Patient, VitalSigns, CarePlan, Medication

D = date(2026,1,1)
def patient(number='P001'):
    return Patient(record_number=number, first_name='Test', last_name='Person', date_of_birth=date(1980,1,1))
def plan(p):
    return CarePlan(patient=p, title='Test plan', starts_on=D)
def medication(p, cp):
    return Medication(patient=p, care_plan=cp, name='Fictional medication', dose_amount=Decimal('1.000'), dose_unit='unit', route='oral', frequency='daily', starts_on=D)
def vital(p):
    return VitalSigns(patient=p, measured_at=datetime(2026,1,1,tzinfo=timezone.utc),kind='weight',value=Decimal('70'),unit='kg')

def test_relationships_for_all_four_models(session):
    configure_mappers()
    p=patient(); cp=plan(p); m=medication(p,cp); v=vital(p)
    session.add(p); session.commit(); session.expire_all()
    assert v.patient is p and v in p.vital_signs
    assert cp.patient is p and cp in p.care_plans
    assert m.patient is p and m.care_plan is cp and m in cp.medications and m in p.medications
    assert v.measured_at.tzinfo is not None and m.dose_amount == Decimal('1.000')

@pytest.mark.parametrize('field,value',[('first_name',' '),('record_number','x'*33),('status','unknown'),('date_of_birth',date(2999,1,1))])
def test_patient_validation(field,value):
    with pytest.raises(ValueError): setattr(patient(),field,value)

def test_patient_unique_and_required(session):
    session.add(patient()); session.commit()
    session.add(patient())
    with pytest.raises(IntegrityError): session.commit()
    session.rollback()
    p=Patient(record_number='P002',first_name='Test',date_of_birth=D); session.add(p)
    with pytest.raises(IntegrityError): session.commit()

@pytest.mark.parametrize('value',['-1','NaN','Infinity','1.0001'])
def test_vital_validation(value):
    with pytest.raises(ValueError): VitalSigns(value=Decimal(value))

def test_vital_unit_and_timezone(session):
    p=patient(); v=vital(p); v.unit='wrong'; session.add(v)
    with pytest.raises(IntegrityError): session.commit()
    session.rollback()
    v=vital(patient()); v.measured_at=datetime(2026,1,1); session.add(v)
    with pytest.raises(StatementError): session.commit()

@pytest.mark.parametrize('changes',[{'status':'wrong'},{'title':' '},{'ends_on':date(2025,1,1)},{'review_on':date(2025,1,1)}])
def test_plan_validation(session,changes):
    cp=plan(patient())
    for k,v in changes.items(): setattr(cp,k,v)
    session.add(cp)
    with pytest.raises(IntegrityError): session.commit()

@pytest.mark.parametrize('changes',[{'dose_amount':0},{'name':' '},{'ends_on':date(2025,1,1)},{'frequency':''}])
def test_medication_validation(session,changes):
    p=patient(); m=medication(p,plan(p))
    for k,v in changes.items(): setattr(m,k,v)
    session.add(m)
    with pytest.raises(IntegrityError): session.commit()

def test_medication_cannot_link_other_patient_plan(session):
    p=patient(); cp=plan(p); other=patient('P002'); session.add_all([p,cp,other]); session.commit()
    session.add(Medication(patient_id=other.id,care_plan_id=cp.id,name='Test',dose_amount=1,dose_unit='unit',route='oral',frequency='daily',starts_on=D))
    with pytest.raises(IntegrityError): session.commit()

def test_nonexistent_patient_rejected(session):
    session.add(CarePlan(patient_id=uuid4(),title='Test',starts_on=D))
    with pytest.raises(IntegrityError): session.commit()
