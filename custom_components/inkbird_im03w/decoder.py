"""Decoder for Inkbird IM-03-W sensor payload."""

import base64
import re
import struct
from typing import Any


class DecoderError(Exception):
    """Raised when decoding fails."""


def decode_inkbird_payload(raw_base64: str) -> dict[str, dict[str, float]]:
    """
    Decode Inkbird sensor payload from Base64.

    Args:
        raw_base64: Base64-encoded binary payload.

    Returns:
        Dictionary with sensor labels as keys and temperature/humidity dicts as values.
        Example:
        {
            "P03R_OUT": {"temperature": 20.7, "humidity": 0.0},
            "P03R_IN": {"temperature": 23.1, "humidity": 56.7}
        }

    Raises:
        DecoderError: If payload is invalid or cannot be decoded.
    """
    if not raw_base64:
        raise DecoderError("Empty payload")

    try:
        data = base64.b64decode(raw_base64)
    except Exception as e:
        raise DecoderError(f"Failed to decode Base64: {e}") from e

    if len(data) < 50:
        raise DecoderError(f"Payload too short: {len(data)} bytes")

    # Find all P03R_* labels in the payload
    pattern = rb"P03R_[A-Z]+"
    matches = list(re.finditer(pattern, data))

    if not matches:
        raise DecoderError("No P03R labels found in payload")

    result = {}

    for match in matches:
        label = match.group(0).decode("ascii", errors="ignore")
        pos = match.start()

        # Guard: ensure we have enough data before the label
        if pos < 27:
            continue

        try:
            # Temperature at offset -27 from label start (2 bytes, signed short, little-endian)
            temp_raw = struct.unpack_from("<h", data, pos - 27)[0]
            temp = temp_raw / 10.0

            # Humidity at offset -25 from label start (2 bytes, signed short, little-endian)
            humidity_raw = struct.unpack_from("<h", data, pos - 25)[0]
            humidity = humidity_raw / 10.0

            result[label] = {"temperature": temp, "humidity": humidity}
        except struct.error as e:
            raise DecoderError(f"Failed to unpack struct for {label}: {e}") from e

    if not result:
        raise DecoderError("No valid sensor data decoded")

    return result
