import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session

from .model import Base, Value, ValueType, Location, Device
from random import shuffle


class Crud:
    def __init__(self, engine):
        self._engine = engine
        self.IntegrityError = IntegrityError
        self.NoResultFound = NoResultFound

        Base.metadata.create_all(self._engine)

    def add_or_update_value_type(
        self,
        value_type_id: int = None,
        value_type_name: str = None,
        value_type_unit: str = None,
    ) -> None:
        """update or add a value type

        Args:
            value_type_id (int, optional): ValueType id to be modified (if None a new ValueType is added), Default to None.
            value_type_name (str, optional): Typename wich should be set or updated. Defaults to None.
            value_type_unit (str, optional): Unit of mesarument wich should be set or updated. Defaults to None.

        Returns:
            _type_: _description_
        """
        with Session(self._engine) as session:
            stmt = select(ValueType).where(ValueType.id == value_type_id)
            db_type = None
            for type in session.scalars(stmt):
                db_type = type
            if db_type is None:
                db_type = ValueType(id=value_type_id)
            if value_type_name:
                db_type.type_name = value_type_name
            elif not db_type.type_name:
                db_type.type_name = "TYPE_%d" % value_type_id
            if value_type_unit:
                db_type.type_unit = value_type_unit
            elif not db_type.type_unit:
                db_type.type_unit = "UNIT_%d" % value_type_id
            session.add_all([db_type])
            session.commit()
            return db_type

    def add_value(self, value_time: int, value_type: int, value_value: float, device_id: int = None) -> None:
        """Add a measurement point to the database, associated with a device.

        Args:
            value_time (int): Unix timestamp of the value.
            value_type (int): ValueType id of the given value.
            value_value (float): The measurement value as float.
            device_id (int, optional): ID of the device this value is associated with. Defaults to None.
        """        
        with Session(self._engine) as session:
            db_type = self.add_or_update_value_type(value_type)
            db_value = Value(time=value_time, value=value_value, value_type=db_type, device_id=device_id)

            session.add_all([db_type, db_value])
            try:
                session.commit()
            except IntegrityError:
                logging.error("Integrity Error occurred")
                raise


    def get_value_types(self) -> List[ValueType]:
        """Get all configured value types

        Returns:
            List[ValueType]: List of ValueType objects. 
        """
        with Session(self._engine) as session:
            stmt = select(ValueType)
            return session.scalars(stmt).all()

    def get_value_type(self, value_type_id: int) -> ValueType:
        """Get a special ValueType

        Args:
            value_type_id (int): the primary key of the ValueType

        Returns:
            ValueType: The ValueType object
        """
        with Session(self._engine) as session:
            stmt = select(ValueType).where(ValueType.id == value_type_id)
            return session.scalars(stmt).one()

    def get_values(
        self, value_type_id: int = None, start: int = None, end: int = None
    ) -> List[Value]:
        """Get Values from database.

        The result can be filtered by the following parameter:

        Args:
            value_type_id (int, optional): If set, only value of this given type will be returned. Defaults to None.
            start (int, optional): If set, only values with a timestamp at least as big as start are returned. Defaults to None.
            end (int, optional): If set, only values with a timestamp at most as big as end are returned. Defaults to None.

        Returns:
            List[Value]: List of Value objects.
        """
        with Session(self._engine) as session:
            stmt = select(Value)
            if value_type_id is not None:
                stmt = stmt.join(Value.value_type).where(ValueType.id == value_type_id)
            if start is not None:
                stmt = stmt.where(Value.time >= start)
            if end is not None:
                stmt = stmt.where(Value.time <= end)
            stmt = stmt.order_by(Value.time)
            return session.scalars(stmt).all()

    def create_location(self, name: str) -> Location:
        with Session(self._engine) as session:
            new_location = Location(name=name)
            session.add(new_location)
            try:
                session.commit()
                session.refresh(new_location)
                return new_location
            except IntegrityError as e:
                logging.error(f"Database error occurred while creating a new location: {e}")
                session.rollback()
                raise


    def add_device(self, name: str, description: str, location_id: int) -> Device:
        """Add a new device to the database.

        Args:
            name (str): The name of the device.
            description (str): The description of the device.

        Returns:
            Device: The newly created Device object.
        """
        with Session(self._engine) as session:
            new_device = Device(name=name, description=description, location_id=location_id)
            session.add(new_device)
            try:
                session.commit()
                device_id = new_device.id  
                device_name = new_device.name  
                device_description = new_device.description  
                device_location_id = new_device.location_id
            except IntegrityError:
                logging.error("IntegrityError while adding a new device.")
                session.rollback()
                raise
            return Device(id=device_id, name=device_name, description=device_description, location_id = location_id)

    def get_all_device_ids(self) -> List[int]:
        """Ruft alle Geräte-IDs aus der Datenbank ab.

        Returns:
            List[int]: Eine Liste aller Geräte-IDs.
        """
        with Session(self._engine) as session:
            stmt = select(Device.id)
            device_ids = session.scalars(stmt).all()
            return device_ids

    def get_device(self, device_id: int) -> Device:
        """Holt ein Gerät anhand seiner ID aus der Datenbank.

        Args:
            device_id (int): Die ID des gewünschten Geräts.

        Returns:
            Device: Das Gerät, wenn gefunden.
        
        Raises:
            NoResultFound: Wenn kein Gerät mit der gegebenen ID gefunden wird.
        """
        with Session(self._engine) as session:
            stmt = select(Device).where(Device.id == device_id)
            device = session.scalars(stmt).one()
            return device
    
    def get_all_locations(self) -> List[Location]:
        """Fetch all locations from the database."""
        with Session(self._engine) as session:
            stmt = select(Location)
            locations = session.scalars(stmt).all()
            return locations


