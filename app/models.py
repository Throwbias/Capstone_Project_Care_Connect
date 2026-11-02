from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import CheckConstraint, ForeignKey, ForeignKeyConstraint, String, Date, DateTime, Numeric, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.types import TypeDecorator
from .database import Base

class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(DateTime(timezone=True))
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError('Timezone required')
        return value.astimezone(timezone.utc)
    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=timezone.utc) if value and value.tzinfo is None else value

class Identity:
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=lambda: datetime.now(timezone.utc))

class Patient(Identity, Base):
    __tablename__ = 'patient'
    record_number: Mapped[str] = mapped_column(String(32), unique=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    date_of_birth: Mapped[date] = mapped_column(Date)
    email: Mapped[str | None] = mapped_column(String(254))
    phone: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(16), default='active')
    inactive_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    vital_signs: Mapped[list['VitalSigns']] = relationship(back_populates='patient')
    care_plans: Mapped[list['CarePlan']] = relationship(back_populates='patient')
    medications: Mapped[list['Medication']] = relationship(back_populates='patient', foreign_keys='Medication.patient_id', overlaps='care_plan,medications')
    __table_args__ = (
        CheckConstraint("status IN ('active','inactive')", name='ck_patient_status'),
        CheckConstraint('length(trim(record_number)) BETWEEN 1 AND 32', name='ck_patient_number'),
        CheckConstraint('length(trim(first_name)) BETWEEN 1 AND 100', name='ck_patient_first'),
        CheckConstraint('length(trim(last_name)) BETWEEN 1 AND 100', name='ck_patient_last'),
    )
    @validates('first_name', 'last_name', 'record_number')
    def nonempty(self, key, value):
        limit = 32 if key == 'record_number' else 100
        if not isinstance(value, str) or not 1 <= len(value.strip()) <= limit:
            raise ValueError('Invalid '+key)
        return value.strip()
    @validates('status')
    def valid_status(self, key, value):
        if value not in ('active', 'inactive'): raise ValueError('Invalid status')
        return value
    @validates('date_of_birth')
    def valid_birth(self, key, value):
        if value > date.today(): raise ValueError('Future birth date')
        return value

class VitalSigns(Identity, Base):
    __tablename__ = 'vital_signs'
    patient_id: Mapped[UUID] = mapped_column(ForeignKey('patient.id', ondelete='RESTRICT'), index=True)
    measured_at: Mapped[datetime] = mapped_column(UTCDateTime())
    kind: Mapped[str] = mapped_column(String(16))
    value: Mapped[Decimal] = mapped_column(Numeric(12,3))
    unit: Mapped[str] = mapped_column(String(16))
    patient: Mapped[Patient] = relationship(back_populates='vital_signs')
    __table_args__ = (
        CheckConstraint('value > 0', name='ck_vital_positive'),
        CheckConstraint("(kind='heart_rate' AND unit='bpm') OR (kind='weight' AND unit='kg') OR (kind='glucose' AND unit='mg/dL') OR (kind IN ('systolic','diastolic') AND unit='mmHg')", name='ck_vital_unit'),
    )
    @validates('value')
    def positive(self, key, value):
        value = Decimal(str(value))
        if not value.is_finite() or value <= 0 or value >= Decimal('1000000000') or value.as_tuple().exponent < -3:
            raise ValueError('Positive finite value with at most three decimals required')
        return value

class CarePlan(Identity, Base):
    __tablename__ = 'care_plan'
    patient_id: Mapped[UUID] = mapped_column(ForeignKey('patient.id', ondelete='RESTRICT'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(16), default='draft')
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    review_on: Mapped[date | None] = mapped_column(Date)
    patient: Mapped[Patient] = relationship(back_populates='care_plans')
    medications: Mapped[list['Medication']] = relationship(back_populates='care_plan', overlaps='patient,medications')
    __table_args__ = (
        UniqueConstraint('id','patient_id', name='uq_plan_patient'),
        CheckConstraint("status IN ('draft','active','completed','archived')", name='ck_plan_status'),
        CheckConstraint('ends_on IS NULL OR ends_on >= starts_on', name='ck_plan_dates'),
        CheckConstraint('review_on IS NULL OR review_on >= starts_on', name='ck_plan_review'),
        CheckConstraint('length(trim(title)) BETWEEN 1 AND 200', name='ck_plan_title'),
    )

class Medication(Identity, Base):
    __tablename__ = 'medication'
    patient_id: Mapped[UUID] = mapped_column(ForeignKey('patient.id', ondelete='RESTRICT'), index=True)
    care_plan_id: Mapped[UUID] = mapped_column(Uuid, index=True)
    name: Mapped[str] = mapped_column(String(200))
    dose_amount: Mapped[Decimal] = mapped_column(Numeric(10,3))
    dose_unit: Mapped[str] = mapped_column(String(24))
    route: Mapped[str] = mapped_column(String(24))
    frequency: Mapped[str] = mapped_column(String(100))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date | None] = mapped_column(Date)
    patient: Mapped[Patient] = relationship(back_populates='medications', foreign_keys=[patient_id], overlaps='care_plan,medications')
    care_plan: Mapped[CarePlan] = relationship(back_populates='medications', overlaps='patient,medications')
    __table_args__ = (
        ForeignKeyConstraint(['care_plan_id','patient_id'], ['care_plan.id','care_plan.patient_id'], ondelete='RESTRICT', name='fk_medication_plan_patient'),
        CheckConstraint('dose_amount > 0', name='ck_medication_dose'),
        CheckConstraint('ends_on IS NULL OR ends_on >= starts_on', name='ck_medication_dates'),
        *[CheckConstraint(f'length(trim({field})) BETWEEN 1 AND {size}', name=f'ck_medication_{field}') for field,size in [('name',200),('dose_unit',24),('route',24),('frequency',100)]]
    )
