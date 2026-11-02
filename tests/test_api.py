from fastapi.testclient import TestClient
from app.database import get_session
from app.main import app
from app.models import Patient
import pytest

DATA=dict(record_number='P001',first_name='Test',last_name='Person',date_of_birth='1980-01-01',email='test@example.org')
@pytest.fixture
def client(session):
    app.dependency_overrides[get_session]=lambda: session
    with TestClient(app) as client: yield client
    app.dependency_overrides.clear()

def test_crud_and_soft_delete(client,session):
    r=client.post('/api/v1/patients',json=DATA); assert r.status_code==201
    identifier=r.json()['id']; path='/api/v1/patients/'+identifier
    assert client.get(path).json()['first_name']=='Test'
    assert len(client.get('/api/v1/patients').json())==1
    assert client.patch(path,json={'first_name':'Updated','email':None}).json()['email'] is None
    assert client.delete(path).status_code==204
    assert client.get(path).status_code==404
    assert client.get('/api/v1/patients').json()==[]
    from uuid import UUID
    assert session.get(Patient,UUID(identifier)).inactive_at is not None

@pytest.mark.parametrize('change',[{'first_name':' '},{'date_of_birth':'2999-01-01'},{'email':'bad'},{'status':'wrong'},{'extra':1}])
def test_invalid_create(client,change):
    assert client.post('/api/v1/patients',json=DATA|change).status_code==422

def test_conflict_and_errors(client):
    r=client.post('/api/v1/patients',json=DATA); path='/api/v1/patients/'+r.json()['id']
    assert client.post('/api/v1/patients',json=DATA).status_code==409
    assert client.patch(path,json={'first_name':None}).status_code==422
    assert client.get('/api/v1/patients/not-a-uuid').status_code==422
    assert client.get('/api/v1/patients?limit=101').status_code==422
    assert client.get('/api/v1/patients/00000000-0000-0000-0000-000000000000').status_code==404
    assert client.get(path).headers['cache-control']=='no-store'

def test_openapi(client):
    assert client.get('/docs').status_code==200
    paths=client.get('/openapi.json').json()['paths']
    assert {'post','get'}<=paths['/api/v1/patients'].keys()
    assert {'get','patch','delete'}<=paths['/api/v1/patients/{patient_id}'].keys()
