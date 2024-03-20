from pydantic import BaseModel
from typing import Optional, List

class ValueTypeNoID(BaseModel):
    type_name: str
    type_unit: str

class ValueType(ValueTypeNoID):
    id: int

class ValueNoID(BaseModel):
    value_type_id: int
    time: int
    value: float
    device_id: int

class Value(ValueNoID):
    id: int

    class Config:
        orm_mode = True

class ApiDescription(BaseModel):
    description: str = "This is the Api"
    value_type_link: str = "/type"
    value_link: str = "/value"

class DeviceBase(BaseModel):
    name: str
    description: Optional[str] = None
    location_id: Optional[int] = None

class Device(DeviceBase):
    id: int


    class Config:
        orm_mode = True

class LocationNoID(BaseModel):
    name: str

class Location(LocationNoID):
    id: int

    class Config:
        orm_mode = True
