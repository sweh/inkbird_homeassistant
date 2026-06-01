"""Config flow for Inkbird IM-03-W integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONF_COOKIE,
    CONF_CSRF_TOKEN,
    CONF_DEVICE_ID,
    CONF_POLL_INTERVAL,
    CONF_PROJECT_CODE,
    CONF_REGION,
    CONF_SOURCE_ID,
    DEFAULT_DEVICE_ID,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_PROJECT_CODE,
    DEFAULT_REGION,
    DEFAULT_SOURCE_ID,
    DOMAIN,
)
from .tuya_portal import AuthenticationError, TuyaPortalClient

_LOGGER = logging.getLogger(__name__)


class InkbirdConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Inkbird IM-03-W."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial user step."""
        errors = {}

        if user_input is not None:
            # Validate credentials
            try:
                await self._async_validate_auth(
                    user_input[CONF_COOKIE],
                    user_input[CONF_CSRF_TOKEN],
                    user_input[CONF_PROJECT_CODE],
                    user_input[CONF_SOURCE_ID],
                    user_input[CONF_DEVICE_ID],
                    user_input[CONF_REGION],
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception as e:
                _LOGGER.error("Unexpected error during validation: %s", e)
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Inkbird IM-03-W ({user_input[CONF_DEVICE_ID]})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COOKIE): str,
                    vol.Required(CONF_CSRF_TOKEN): str,
                    vol.Optional(
                        CONF_PROJECT_CODE, default=DEFAULT_PROJECT_CODE
                    ): str,
                    vol.Optional(CONF_SOURCE_ID, default=DEFAULT_SOURCE_ID): str,
                    vol.Optional(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): str,
                    vol.Optional(CONF_REGION, default=DEFAULT_REGION): str,
                    vol.Optional(
                        CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL
                    ): int,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauth flow."""
        config_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )

        if not config_entry:
            return self.async_abort(reason="reauth_failed")

        errors = {}

        if user_input is not None:
            try:
                await self._async_validate_auth(
                    user_input[CONF_COOKIE],
                    user_input[CONF_CSRF_TOKEN],
                    config_entry.data[CONF_PROJECT_CODE],
                    config_entry.data[CONF_SOURCE_ID],
                    config_entry.data[CONF_DEVICE_ID],
                    config_entry.data[CONF_REGION],
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except Exception as e:
                _LOGGER.error("Unexpected error during reauth validation: %s", e)
                errors["base"] = "unknown"

            if not errors:
                # Update the config entry with new credentials
                self.hass.config_entries.async_update_entry(
                    config_entry,
                    data={
                        **config_entry.data,
                        CONF_COOKIE: user_input[CONF_COOKIE],
                        CONF_CSRF_TOKEN: user_input[CONF_CSRF_TOKEN],
                    },
                )
                await self.hass.config_entries.async_reload(config_entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COOKIE): str,
                    vol.Required(CONF_CSRF_TOKEN): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "device_id": config_entry.data.get(CONF_DEVICE_ID, "unknown")
            },
        )

    async def _async_validate_auth(
        self,
        cookie: str,
        csrf_token: str,
        project_code: str,
        source_id: str,
        device_id: str,
        region: str,
    ) -> None:
        """Validate authentication by attempting to fetch logs."""
        client = TuyaPortalClient(
            self.hass.helpers.aiohttp.async_get_clientsession(),
            cookie,
            csrf_token,
            project_code,
            source_id,
            device_id,
            region,
        )

        # Try to fetch a log entry to validate credentials
        await client.fetch_latest_raw_log()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
