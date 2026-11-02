import os
from pathlib import Path
import subprocess
import sys
from sqlalchemy import inspect
from app.database import make_engine

def test_fresh_migration_and_round_trip(tmp_path):
    url='sqlite:///'+str(tmp_path/'fresh.db')
    env=os.environ | {'DATABASE_URL':url}
    def alembic(*args):
        subprocess.run([sys.executable,'-m','alembic',*args],env=env,check=True,capture_output=True)
    alembic('upgrade','head')
    engine=make_engine(url)
    assert {'patient','vital_signs','care_plan','medication'} <= set(inspect(engine).get_table_names())
    engine.dispose()
    alembic('check')
    alembic('downgrade','base')
    alembic('upgrade','head')
