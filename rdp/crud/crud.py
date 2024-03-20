import logging
from typing import List

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.orm import Session

from .model import Base, Value, ValueType, Device
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

    


    def add_device(self, name: str, description: str = None) -> Device:
        """Fügt ein neues Gerät zur Datenbank hinzu.
        ...
        """
        with Session(self._engine) as session:
            new_device = Device(name=name, description=description)
            session.add(new_device)
            try:
                session.commit()
                return new_device  # Rückgabe des Device-Objekts nach dem Hinzufügen
            except IntegrityError:
                logging.error("Ein Fehler bei der Integritätsprüfung ist aufgetreten.")
                session.rollback()
                raise


    def update_device(self, device_id: int, name: str = None, description: str = None) -> None:
        """Aktualisiert ein vorhandenes Gerät in der Datenbank.

        Args:
            device_id (int): Die ID des zu aktualisierenden Geräts.
            name (str, optional): Der neue Name des Geräts.
            description (str, optional): Die neue Beschreibung des Geräts.
        """
        with Session(self._engine) as session:
            device = session.query(Device).filter(Device.id == device_id).one()
            if name is not None:
                device.name = name
            if description is not None:
                device.description = description

            try:
                session.commit()
            except IntegrityError:
                logging.error("Ein Fehler bei der Integritätsprüfung ist aufgetreten.")
                session.rollback()
                raise

    def get_device(self, device_id: int) -> Device:
        """Ruft ein spezifisches Gerät ab.

        Args:
            device_id (int): Die ID des Geräts.

        Returns:
            Device: Das abgerufene Gerät.
        """
        with Session(self._engine) as session:
            return session.query(Device).filter(Device.id == device_id).one()

    def get_all_devices(self) -> List[Device]:
        """Gibt alle Geräte zurück.

        Returns:
            List[Device]: Eine Liste von Geräten.
        """
        with Session(self._engine) as session:
            return session.query(Device).all()

    def delete_device(self, device_id: int) -> None:
        """Löscht ein Gerät anhand seiner ID.

        Args:
            device_id (int): Die ID des zu löschenden Geräts.
        """
        with Session(self._engine) as session:
            device = session.query(Device).filter(Device.id == device_id).one()
            session.delete(device)
            session.commit()

    def get_all_device_ids(self) -> List[int]:
        """Retrieve all device IDs from the database.

        Returns:
            List[int]: A list of all device IDs.
        """
        with Session(self._engine) as session:
            return [device.id for device in session.query(Device.id).all()]

    def get_devices_with_values(self):
        with Session(self._engine) as session:
            devices = session.query(Device).all()
            device_list = []
            for device in devices:
                device_data = {
                    "id": device.id,
                    "name": device.name,
                    "description": device.description,
                    "values": [
                        {
                            "id": value.id,
                            "time": value.time,
                            "value": value.value,
                            "value_type_id": value.value_type_id
                        }
                        for value in device.values
                    ]
                }
                device_list.append(device_data)
            return device_list


