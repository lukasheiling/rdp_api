from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from typing import List, Optional
from sqlalchemy import UniqueConstraint



class Base(DeclarativeBase):
    pass

class Device(Base):
    __tablename__ = "device"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    location_id: Mapped[int] = mapped_column(Integer, ForeignKey("location.id"))

    values: Mapped[List["Value"]] = relationship("Value", back_populates="device", cascade="all, delete-orphan")
    location: Mapped[Optional["Location"]] = relationship("Location", back_populates="devices", foreign_keys=[location_id], uselist=False)

    def __repr__(self) -> str:
        return f"Device(id={self.id!r}, name={self.name!r}, description={self.description!r}, , location_id={self.location_id!r})"

class ValueType(Base):
    __tablename__ = "value_type"
    id: Mapped[int] = mapped_column(primary_key=True)
    type_name: Mapped[str]
    type_unit: Mapped[str]

    values: Mapped[List["Value"]] = relationship(
        "Value", back_populates="value_type", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"ValueType(id={self.id!r}, type_name={self.type_name!r}, type_unit={self.type_unit!r})"

class Value(Base):
    __tablename__ = "value"
    id: Mapped[int] = mapped_column(primary_key=True)
    time: Mapped[int] = mapped_column()
    value: Mapped[float] = mapped_column()
    value_type_id: Mapped[int] = mapped_column(ForeignKey("value_type.id"))
    device_id: Mapped[int] = mapped_column(ForeignKey("device.id"), nullable=True)  # foreignkey auf device_id

    value_type: Mapped["ValueType"] = relationship("ValueType", back_populates="values")
    device: Mapped[Optional["Device"]] = relationship("Device", back_populates="values")

    __table_args__ = (
        UniqueConstraint("time", "value_type_id", "device_id", name="value integrity"),  # device_id hinzugefügt, für Unique
    )

    def __repr__(self) -> str:
        return f"Value(id={self.id!r}, time={self.time!r}, value_type={self.value_type.type_name!r}, device_id={self.device_id!r}, value={self.value!r})"


class Location(Base):
    __tablename__ = "location"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=True)

    devices: Mapped[List["Device"]] = relationship("Device", back_populates="location")

    def __repr__(self) -> str:
        return f"Location(id={self.id!r}, name={self.name!r})"
