"""Tuya Portal API client for Inkbird IM-03-W integration."""

import logging
from datetime import datetime, timedelta, timezone
import aiohttp
from typing import Any

from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)


class TuyaPortalError(Exception):
    """Base exception for Tuya Portal errors."""


class AuthenticationError(TuyaPortalError):
    """Raised when authentication fails."""


class TuyaPortalClient:
    """Async client for Tuya IoT Portal internal log API."""

    def __init__(
        self,
        session: ClientSession,
        cookie: str,
        csrf_token: str,
        project_code: str,
        source_id: str,
        device_id: str,
        region: str = "EU",
    ):
        """
        Initialize Tuya Portal client.

        Args:
            session: aiohttp ClientSession.
            cookie: Cookie header value from logged-in Tuya Portal session.
            csrf_token: CSRF token from Tuya Portal.
            project_code: Tuya project code.
            source_id: Tuya source ID.
            device_id: Device ID in Tuya system.
            region: Region (EU, US, etc.). Defaults to "EU".
        """
        self.session = session
        self.cookie = cookie
        self.csrf_token = csrf_token
        self.project_code = project_code
        self.source_id = source_id
        self.device_id = device_id
        self.region = region

    async def fetch_latest_raw_log(self) -> str:
        """
        Fetch latest sensor log from Tuya Portal.

        Returns:
            Base64-encoded raw event detail string from the latest log entry.

        Raises:
            AuthenticationError: If HTTP 401 or 403 is returned.
            TuyaPortalError: If API response is invalid or missing expected data.
        """
        # Calculate time range: last 24 hours
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=24)

        payload = {
            "startRowId": "",
            "pageNo": 1,
            "pageSize": 10,
            "code": "102",
            "type": "EVENT_TYPE_REPORT",
            "startTime": int(start_time.timestamp() * 1000),
            "endTime": int(now.timestamp() * 1000),
            "projectCode": self.project_code,
            "sourceId": self.source_id,
            "sourceType": "4",
            "deviceId": self.device_id,
            "pageStartRow": "",
            "region": self.region,
        }

        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://eu.platform.tuya.com",
            "Referer": f"https://eu.platform.tuya.com/cloud/device/detail/?id={self.project_code}",
            "X-Requested-With": "XMLHttpRequest",
            "csrf-token": self.csrf_token,
            "Cookie": self.cookie,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }

        url = "https://eu.platform.tuya.com/micro-app/cloud/api/v10/device/log/list"

        try:
            self.session._cookie_jar = aiohttp.DummyCookieJar()
            async with self.session.post(
                url, json=payload, headers=headers, ssl=True
            ) as resp:
                if resp.status == 401 or resp.status == 403:
                    raise AuthenticationError(
                        f"Authentication failed: HTTP {resp.status}"
                    )

                if resp.status != 200:
                    raise TuyaPortalError(
                        f"API returned HTTP {resp.status}: {await resp.text()}"
                    )

                data = await resp.json()

                if not isinstance(data, dict) or data.get("success") is not True:
                    raise TuyaPortalError(
                        f"API response success != true: {data.get('success')}"
                    )

                result = data.get("result", {})
                datas = result.get("datas", [])

                if not datas:
                    raise TuyaPortalError("No log entries in response")

                latest_entry = datas[0]
                event_detail = latest_entry.get("eventDetail")

                if not event_detail:
                    raise TuyaPortalError("Missing eventDetail in latest log entry")

                _LOGGER.debug(
                    "Fetched latest log entry with timestamp: %s",
                    latest_entry.get("createTime"),
                )

                return event_detail

        except (AuthenticationError, TuyaPortalError):
            raise
        except Exception as e:
            raise TuyaPortalError(f"Failed to fetch log from Tuya Portal: {e}") from e
