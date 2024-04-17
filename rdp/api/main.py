from typing import Union, List
from random import shuffle
from .api_types import Device, DeviceCreate  # Make sure Device is imported


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
async def shutdown_event():
    """stop the character device reader
    """    
    global reader
    logger.debug("SHUTDOWN: Sensor reader!")
    reader.stop()
    logger.info("SHUTDOWN: Sensor reader completed!")


@app.post("/create_location/", response_model=ApiTypes.Location)
def create_location(location_data: ApiTypes.LocationNoID):
    """Create a new location with the given name.
    Args:
        location_data (ApiTypes.LocationNoID): The name of the new location.

    Returns:
        ApiTypes.Location: The created location with its ID and name.
    """
    try:
        new_location = crud.create_location(name=location_data.name)
        return ApiTypes.Location(id=new_location.id, name=new_location.name)
    except crud.IntegrityError as e:
        logger.error(f"Failed to create a new location: {e}")
        raise HTTPException(status_code=400, detail="Failed to create a new location due to a database error.")


@app.get("/device/{device_id}/", response_model=ApiTypes.Device)
def get_device(device_id: int):
    """API-Endpunkt, um ein Gerät anhand seiner ID zu holen.

    Args:
        device_id (int): Die ID des gewünschten Geräts.

    Returns:
        ApiTypes.Device: Die Details des Geräts, wenn gefunden.

    Raises:
        HTTPException: Wenn kein Gerät mit der angegebenen ID gefunden wird.
    """
    global crud
    try:
        device = crud.get_device(device_id)
        return ApiTypes.Device(
            id=device.id, 
            name=device.name, 
            description=device.description, 
            location_id=device.location_id
        )
    except crud.NoResultFound:
        raise HTTPException(status_code=404, detail="Device not found")


@app.get("/locations/", response_model=List[ApiTypes.Location])
def read_locations():
    """API-Endpunkt, um alle Locations zu erhalten.

    Returns:
        List[ApiTypes.Location]: Die Liste aller Locations.
    """
    try:
        locations = crud.get_all_locations()
        return [ApiTypes.Location.from_orm(location) for location in locations]
    except Exception as e:
        logger.error(f"Failed to fetch locations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch locations")



@app.post("/devices/", response_model=Device)
def create_device(device_data: DeviceCreate):
    """Create a new device with the provided details.

    Args:
        device_data (DeviceCreate): The data needed to create a new device.

    Returns:
        Device: The created device with its ID and other details.
    """
    try:
        new_device = crud.add_device(name=device_data.name, description=device_data.description, location_id=device_data.location_id)
        return Device(
            id=new_device.id,
            name=new_device.name,
            description=new_device.description,
            location_id=new_device.location_id
        )
    except crud.IntegrityError as e:
        logger.error(f"Failed to create a new device: {e}")
        raise HTTPException(status_code=400, detail="Failed to create a new device due to a database error.")