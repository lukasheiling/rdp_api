from typing import Union, List
from random import shuffle


from fastapi import FastAPI, HTTPException

from rdp.sensor import Reader
from rdp.crud import create_engine, Crud
from . import api_types as ApiTypes
import logging

logger = logging.getLogger("rdp.api")
app = FastAPI()

@app.get("/")
def read_root() -> ApiTypes.ApiDescription:
    """This url returns a simple description of the api

    Returns:
        ApiTypes.ApiDescription: the Api description in json format 
    """    
    return ApiTypes.ApiDescription()

@app.get("/type/")
def read_types() -> List[ApiTypes.ValueType]:
    """Implements the get of all value types

    Returns:
        List[ApiTypes.ValueType]: list of available valuetypes. 
    """    
    global crud
    return crud.get_value_types()

@app.get("/type/{id}/")
def read_type(id: int) -> ApiTypes.ValueType:
    """returns an explicit value type identified by id

    Args:
        id (int): primary key of the desired value type

    Raises:
        HTTPException: Thrown it a value type with the given id cannot be accessed

    Returns:
        ApiTypes.ValueType: the desired value type 
    """
    global crud
    try:
         return crud.get_value_type(id)
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Item not found") 
    return value_type 

@app.put("/type/{id}/")
def put_type(id, value_type: ApiTypes.ValueTypeNoID) -> ApiTypes.ValueType:
    """PUT request to a specail valuetype. This api call is used to change a value type object.

    Args:
        id (int): primary key of the requested value type
        value_type (ApiTypes.ValueTypeNoID): json object representing the new state of the value type. 

    Raises:
        HTTPException: Thrown if a value type with the given id cannot be accessed 

    Returns:
        ApiTypes.ValueType: the requested value type after persisted in the database. 
    """
    global crud
    try:
        crud.add_or_update_value_type(id, value_type_name=value_type.type_name, value_type_unit=value_type.type_unit)
        return read_type(id)
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Item not found")

@app.get("/value/")
def get_values(type_id:int=None, start:int=None, end:int=None) -> List[ApiTypes.Value]:
    """Get values from the database. The default is to return all available values. This result can be filtered.

    Args:
        type_id (int, optional): If set, only values of this type are returned. Defaults to None.
        start (int, optional): If set, only values at least as new are returned. Defaults to None.
        end (int, optional): If set, only values not newer than this are returned. Defaults to None.

    Raises:
        HTTPException: _description_

    Returns:
        List[ApiTypes.Value]: _description_
    """
    global crud
    try:
        values = crud.get_values(type_id, start, end)
        return values
    except crud.NoResultFound:
        raise HTTPException(status_code=404, deltail="Item not found")

@app.on_event("startup")
async def startup_event() -> None:
    """start the character device reader
    """    
    logger.info("STARTUP: Sensor reader!")
    global reader, crud
    engine = create_engine("sqlite:///rdb.test.db")
    crud = Crud(engine)
    reader = Reader(crud)
    reader.start()
    logger.debug("STARTUP: Sensore reader completed!")

@app.on_event("shutdown")
async def startup_event():
    """stop the character device reader
    """    
    global reader
    logger.debug("SHUTDOWN: Sensor reader!")
    reader.stop()
    logger.info("SHUTDOWN: Sensor reader completed!")


@app.post("/device/", response_model=ApiTypes.Device)
def create_device(device: ApiTypes.DeviceCreate):
    """Endpoint zum Hinzufügen eines neuen Geräts"""
    return crud.add_device(name=device.name, description=device.description)

@app.get("/device/{device_id}", response_model=ApiTypes.Device)
def get_device(device_id: int):
    """Endpoint zum Abrufen eines spezifischen Geräts"""
    try:
        return crud.get_device(device_id=device_id)
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")

@app.put("/device/{device_id}", response_model=ApiTypes.Device)
def update_device(device_id: int, device: ApiTypes.DeviceUpdate):
    """Endpoint zum Aktualisieren eines spezifischen Geräts"""
    try:
        return crud.update_device(device_id=device_id, name=device.name, description=device.description)
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")

@app.delete("/device/{device_id}")
def delete_device(device_id: int):
    """Endpoint zum Löschen eines spezifischen Geräts"""
    try:
        crud.delete_device(device_id=device_id)
        return {"detail": "Gerät erfolgreich gelöscht"}
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Gerät nicht gefunden")

@app.post("/assign-values/")
async def assign_values() -> dict:
    """Zufällige und gleichmäßige Zuordnung der Werte zu Geräten"""
    try:
        devices = crud.get_all_devices()
        values = crud.get_values()  # Annahme: Diese Funktion akzeptiert keine Argumente und gibt alle Werte zurück
        if not devices or not values:
            raise HTTPException(status_code=404, detail="Devices or Values not found")

        # Berechnung, wie viele Werte maximal pro Gerät zugeordnet werden können
        values_per_device = len(values) // len(devices)
        # Sicherstellen, dass Werte und Geräte zufällig gemischt werden
        shuffle(values)

        assignments = {device.name: [] for device in devices}
        for value in values:
            # Zufälliges Gerät auswählen und Wert zuweisen, bis das Limit erreicht ist
            for device in devices:
                if len(assignments[device.name]) < values_per_device:
                    assignments[device.name].append(value.value)
                    break  # Weiter zum nächsten Wert, sobald ein Gerät gefunden wurde

        # Umwandlung der Listen in kommagetrennte Strings für eine übersichtlichere Ausgabe
        for device_name in assignments:
            assignments[device_name] = ', '.join(map(str, assignments[device_name]))

        return {"assignments": assignments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


