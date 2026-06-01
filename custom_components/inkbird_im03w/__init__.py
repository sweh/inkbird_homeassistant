"""Inkbird IM-03-W Home Assistant Integration."""

import logging
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import aiohttp_client

from .const import (
    CONF_COOKIE,
    CONF_CSRF_TOKEN,
    CONF_DEVICE_ID,
    CONF_POLL_INTERVAL,
    CONF_PROJECT_CODE,
    CONF_REGION,
    CONF_SOURCE_ID,
    DOMAIN,
)
from .coordinator import InkbirdCoordinator
from .tuya_portal import AuthenticationError, TuyaPortalClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: Final[list[Platform]] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Inkbird integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    try:
        # Create Tuya Portal client
        client = TuyaPortalClient(
            aiohttp_client.async_get_clientsession(hass),
            entry.data[CONF_COOKIE],
            entry.data[CONF_CSRF_TOKEN],
            entry.data[CONF_PROJECT_CODE],
            entry.data[CONF_SOURCE_ID],
            entry.data[CONF_DEVICE_ID],
            entry.data[CONF_REGION],
        )

        # Create coordinator
        coordinator = InkbirdCoordinator(
            hass,
            client,
            entry.data.get(CONF_POLL_INTERVAL, 120),
        )

        # Perform initial data fetch
        await coordinator.async_config_entry_first_refresh()

        # Store coordinator for platforms to access
        hass.data[DOMAIN][entry.entry_id] = {
            "coordinator": coordinator,
            "client": client,
        }

    except AuthenticationError as e:
        raise ConfigEntryAuthFailed(f"Authentication failed: {e}") from e
    except Exception as e:
        _LOGGER.error("Failed to set up Inkbird integration: %s", e)
        raise ConfigEntryAuthFailed(e) from e

    # Set up sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
