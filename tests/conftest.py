import pytest
from sqlalchemy.orm import Session
from app.database import Base, make_engine
import app.models

@pytest.fixture
def session(tmp_path):
    engine = make_engine('sqlite:///'+str(tmp_path/'test.db'))
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()
