"""Data coordinator for Inkbird IM-03-W integration."""

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .decoder import DecoderError, decode_inkbird_payload
from .tuya_portal import AuthenticationError, TuyaPortalClient, TuyaPortalError

_LOGGER = logging.getLogger(__name__)


class InkbirdCoordinator(DataUpdateCoordinator):
    """Coordinator for fetching and decoding Inkbird data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: TuyaPortalClient,
        update_interval_seconds: int = 120,
    ):
        """
        Initialize the coordinator.

        Args:
            hass: Home Assistant instance.
            client: TuyaPortalClient instance.
            update_interval_seconds: Poll interval in seconds.
        """
        super().__init__(
            hass,
            _LOGGER,
            name="Inkbird IM-03-W",
            update_interval=timedelta(seconds=update_interval_seconds),
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, dict[str, float]]:
        """
        Fetch and decode the latest sensor data.

        Returns:
            Dictionary with decoded sensor data.

        Raises:
            ConfigEntryAuthFailed: If authentication fails.
            UpdateFailed: If any other error occurs.
        """
        try:
            # Fetch raw Base64 payload from Tuya Portal
            raw_log = await self.client.fetch_latest_raw_log()

            # Decode the payload
            decoded = decode_inkbird_payload(raw_log)

            _LOGGER.debug("Successfully fetched and decoded sensor data: %s", decoded)

            return decoded

        except AuthenticationError as e:
            # Will be handled by __init__.py and converted to ConfigEntryAuthFailed
            raise e
        except (TuyaPortalError, DecoderError) as e:
            raise UpdateFailed(f"Failed to update Inkbird data: {e}") from e
