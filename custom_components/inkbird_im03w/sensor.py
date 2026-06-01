"""Sensor platform for Inkbird IM-03-W integration."""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_DEVICE_ID, DOMAIN, MANUFACTURER, MODEL
from .coordinator import InkbirdCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities from a config entry."""
    coordinator: InkbirdCoordinator = hass.data[DOMAIN][config_entry.entry_id][
        "coordinator"
    ]
    device_id = config_entry.data[CONF_DEVICE_ID]

    sensors = [
        InkbirdTemperatureSensor(
            coordinator, device_id, "P03R_OUT", "Outlet Probe Temperature"
        ),
        InkbirdHumiditySensor(
            coordinator, device_id, "P03R_OUT", "Outlet Probe Humidity"
        ),
        InkbirdTemperatureSensor(
            coordinator, device_id, "P03R_IN", "Inlet/Gateway Temperature"
        ),
        InkbirdHumiditySensor(
            coordinator, device_id, "P03R_IN", "Inlet/Gateway Humidity"
        ),
    ]

    async_add_entities(sensors, update_before_add=True)


class InkbirdSensorBase(CoordinatorEntity):
    """Base class for Inkbird sensors."""

    def __init__(
        self,
        coordinator: InkbirdCoordinator,
        device_id: str,
        probe: str,
        sensor_name: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.probe = probe
        self.sensor_name = sensor_name

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.device_id)},
            "name": "Inkbird IM-03-W",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
        }


class InkbirdTemperatureSensor(InkbirdSensorBase, SensorEntity):
    """Temperature sensor for Inkbird probes."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: InkbirdCoordinator,
        device_id: str,
        probe: str,
        sensor_name: str,
    ):
        """Initialize temperature sensor."""
        super().__init__(coordinator, device_id, probe, sensor_name)
        probe_lower = probe.lower()
        self._attr_unique_id = f"{device_id}_{probe_lower}_temperature"
        self._attr_name = f"{sensor_name}"

    @property
    def native_value(self) -> float | None:
        """Return the current temperature value."""
        if not self.coordinator.data:
            return None

        probe_data = self.coordinator.data.get(self.probe)
        if not probe_data:
            return None

        return probe_data.get("temperature")


class InkbirdHumiditySensor(InkbirdSensorBase, SensorEntity):
    """Humidity sensor for Inkbird probes."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: InkbirdCoordinator,
        device_id: str,
        probe: str,
        sensor_name: str,
    ):
        """Initialize humidity sensor."""
        super().__init__(coordinator, device_id, probe, sensor_name)
        probe_lower = probe.lower()
        self._attr_unique_id = f"{device_id}_{probe_lower}_humidity"
        self._attr_name = f"{sensor_name}"

    @property
    def native_value(self) -> float | None:
        """Return the current humidity value."""
        if not self.coordinator.data:
            return None

        probe_data = self.coordinator.data.get(self.probe)
        if not probe_data:
            return None

        return probe_data.get("humidity")
