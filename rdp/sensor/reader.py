import logging
import struct
import threading
import time
from random import choice

from rdp.crud import Crud

logger = logging.getLogger("rdp.sensor")

class Reader:
    def __init__(self, crud: Crud, device: str = "/dev/rdp_cdev"):
        self._crud = crud
        self._device = device
        self._thread: threading.Thread = None
        self._device_ids = self._get_all_device_ids()

    def _get_all_device_ids(self):
        """Hilfsfunktion, um alle Geräte-IDs zu erhalten."""
        try:
            return self._crud.get_all_device_ids()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Geräte-IDs: {e}")
            return []

    def _get_all_location_ids(self):
        """Hilfsfunktion, um alle Geräte-IDs zu erhalten."""
        try:
            return self._crud.get_all_location_ids()
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Location-IDs: {e}")
            return []

    def start(self) -> None:
        self._crud.add_device(name="Device1", description="test", location_id=1)
        self._crud.add_device(name="Device2", description="jkk", location_id=2)
        self._thread = threading.Thread(target=self._run)
        self._thread.start()

    def stop(self):
        thread = self._thread
        self._thread = None
        thread.join()

    def _run(self) -> None:
        count = 0
        while self._thread is not None:
            device_id = choice(self._crud.get_all_device_ids())

            logger.info("A")
            with open(self._device, "rb") as f:
                test = f.read(16)
                value_time = 0
                for i in range(8):
                    value_time |= test[i] << 8 * i
                type_num = 0
                for i in range(4):
                    type_num |= test[i + 8] << 8 * i
                value = struct.unpack("f", test[-4::])[0]
                logger.debug(
                    "Read one time: %d type: %d and value: %f",
                    value_time,
                    type_num,
                    value,
                )
                try:
                    self._crud.add_value(value_time, type_num, value, device_id)
                except self._crud.IntegrityError:
                    logger.info("All Values read")
                    break

            time.sleep(0.1)
            count += 1
            if count % 100 == 0:
                logger.info("read 100 values")
                count = 0

