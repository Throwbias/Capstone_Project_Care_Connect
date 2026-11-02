import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

def make_engine(url):
    engine = create_engine(url, connect_args={'check_same_thread': False} if url.startswith('sqlite') else {})
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine, 'connect')
        def foreign_keys(connection, _):
            connection.execute('PRAGMA foreign_keys=ON')
    return engine

engine = make_engine(os.getenv('DATABASE_URL', 'sqlite:///./careconnect.db'))
SessionLocal = sessionmaker(engine)

def get_session():
    with SessionLocal() as session:
        yield session
