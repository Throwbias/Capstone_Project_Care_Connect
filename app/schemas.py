from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Number = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=32)]
class PatientCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    record_number: Number
    first_name: Name
    last_name: Name
    date_of_birth: date
    email: EmailStr | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=32)
    status: Literal['active','inactive'] = 'active'
    @field_validator('date_of_birth')
    @classmethod
    def birth(cls, value):
        if value > date.today(): raise ValueError('Birth date cannot be in the future')
        return value

class PatientUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    first_name: Name | None = None
    last_name: Name | None = None
    date_of_birth: date | None = None
    email: EmailStr | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=32)
    status: Literal['active','inactive'] | None = None
    @field_validator('first_name','last_name','date_of_birth','status')
    @classmethod
    def required_if_supplied(cls, value):
        if value is None: raise ValueError('This field cannot be null')
        return value
    @field_validator('date_of_birth')
    @classmethod
    def birth(cls, value):
        return PatientCreate.birth(value)

class PatientRead(PatientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    inactive_at: datetime | None
