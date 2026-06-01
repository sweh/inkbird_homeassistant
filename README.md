# Inkbird IM-03-W Home Assistant Integration

[![HACS Default](https://img.shields.io/badge/HACS-Default-blue)](https://github.com/hacs/integration)

A Home Assistant custom integration for reading pool temperature and humidity from an **Inkbird IM-03-W gateway** with **IBS-P03R probe** via the Tuya IoT Portal internal log endpoint.

## ⚠️ Important Notice

This integration is **experimental** and uses the **Tuya IoT Portal internal log endpoint**, which is:
- Not an official public API
- Not guaranteed to be stable or maintained by Tuya
- Requires manual extraction of authentication credentials from your browser

This integration **does NOT use MQTT** — it polls the Tuya Portal API directly.

## Features

- ✅ Reads pool temperature from IBS-P03R probe (outlet)
- ✅ Reads humidity from both outlets (P03R_OUT) and inlets/gateway (P03R_IN)
- ✅ Supports reauthentication when credentials expire
- ✅ Configurable poll interval
- ✅ Production-quality async/await code

## Supported Devices

- **Gateway**: Inkbird IM-03-W
- **Probe**: Inkbird IBS-P03R (or compatible)

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click **Integrations**
3. Search for **"Inkbird IM-03-W"**
4. Click **Install**
5. Restart Home Assistant

### Manual Installation

1. Copy `custom_components/inkbird_im03w` to your Home Assistant `custom_components` directory:
   ```bash
   cp -r custom_components/inkbird_im03w ~/.homeassistant/custom_components/
   ```
2. Restart Home Assistant

## Configuration

### Prerequisites

You must manually extract your **Cookie** and **CSRF token** from an active Tuya IoT Portal session:

1. Open [Tuya IoT Portal](https://iot.tuya.com/) in your browser and log in
2. Navigate to **Cloud → Device Detail** for your device
3. Open **DevTools** (F12 or right-click → Inspect)
4. Go to **Network** tab
5. Call a device log endpoint (e.g., reload the page, or trigger a sensor read)
6. Find the request to `/micro-app/cloud/api/v10/device/log/list`
7. Copy the **Cookie** header value (the entire header, e.g., `lang=en; t=...`)
8. Copy the **csrf-token** header value
9. Note your **Project Code**, **Source ID**, and **Device ID** from the request payload or URL

### Configuration Steps

1. In Home Assistant, go to **Settings → Devices & Services → Integrations**
2. Click **Create Integration** and search for **"Inkbird IM-03-W"**
3. Fill in the form:
   - **Cookie**: Paste the entire Cookie header
   - **CSRF Token**: Paste the csrf-token header
   - **Project Code** (optional): Default: `p1780246545728yrxdss` (example, adjust if needed)
   - **Source ID** (optional): Default: `eu1780245563242Wvh5W` (example, adjust if needed)
   - **Device ID** (optional): Default: `bfd54d796bf836a559gwpf` (example, adjust if needed)
   - **Region** (optional): Default: `EU` (or `US`, `CN`, etc.)
   - **Poll Interval (seconds)** (optional): Default: `120`
4. Click **Submit**

If successful, the integration will create four sensors:
- `sensor.inkbird_im_03_w_outlet_probe_temperature`
- `sensor.inkbird_im_03_w_outlet_probe_humidity`
- `sensor.inkbird_im_03_w_inlet_gateway_temperature`
- `sensor.inkbird_im_03_w_inlet_gateway_humidity`

## Reauthentication

If the Tuya Portal authentication expires (typically due to Cookie/CSRF token expiry):

1. You will see a **notification in Home Assistant** requesting reauthentication
2. Go to **Settings → Devices & Services → Integrations**
3. Find the Inkbird integration and click on it
4. Click **Reconfigure** or the **reauthenticate** button
5. Provide new **Cookie** and **CSRF Token** (follow the extraction steps above)
6. The integration will reload automatically

## How to Extract Cookie and CSRF Token

### Detailed Guide

1. **Login to Tuya IoT Portal**
   - Visit https://iot.tuya.com/
   - Log in with your account

2. **Open DevTools**
   - Press `F12` on your keyboard
   - Or right-click and select **Inspect**

3. **Navigate to Network Tab**
   - Click the **Network** tab in DevTools
   - You may need to reload the page or trigger a device action

4. **Find the Log List Request**
   - Look for a POST request to `/micro-app/cloud/api/v10/device/log/list`
   - Click on it to view details

5. **Extract Headers**
   - In the **Request Headers** section, find:
     - **Cookie**: Copy the entire value
     - **csrf-token**: Copy the value

6. **Copy Payload Details (Optional)**
   - In the **Request Payload** section (or JSON body), note:
     - `projectCode`
     - `sourceId`
     - `deviceId`

### Example

```
Cookie: lang=en; t=abc123def456ghi789; session=xyz...
csrf-token: abc123def456ghi789xyz
projectCode: p1780246545728yrxdss
sourceId: eu1780245563242Wvh5W
deviceId: bfd54d796bf836a559gwpf
```

## Troubleshooting

### "Invalid Cookie or CSRF Token"

- Your Cookie or CSRF token is incorrect or has expired
- Repeat the extraction steps above and reconfigure
- Ensure you copied the **entire** Cookie header (it may contain multiple semicolon-separated parts)

### No Data / Sensors Unavailable

- Verify the **Device ID**, **Project Code**, and **Source ID** are correct
- Check Home Assistant logs: **Settings → System → Logs**
- Ensure your Tuya account has access to the device in the IoT Portal

### High Poll Interval

- If you're seeing stale data, reduce the **Poll Interval (seconds)**
- Default is 120 seconds; you can lower it to 60, 30, or even 10

## How It Works

1. **Data Retrieval**: Queries Tuya IoT Portal's internal log endpoint
2. **Base64 Decoding**: Decodes the binary event payload
3. **Structure Parsing**: Extracts temperature and humidity for P03R_OUT and P03R_IN labels
4. **Sensor Updates**: Updates Home Assistant sensor entities

### API Endpoint

```
POST https://eu.platform.tuya.com/micro-app/cloud/api/v10/device/log/list
```

### Request Payload Example

```json
{
  "startRowId": "",
  "pageNo": 1,
  "pageSize": 10,
  "code": "102",
  "type": "EVENT_TYPE_REPORT",
  "startTime": <milliseconds_24h_ago>,
  "endTime": <milliseconds_now>,
  "projectCode": "p1780246545728yrxdss",
  "sourceId": "eu1780245563242Wvh5W",
  "sourceType": "4",
  "deviceId": "bfd54d796bf836a559gwpf",
  "pageStartRow": "",
  "region": "EU"
}
```

## Limitations

- **Not an official API**: The Tuya IoT Portal log endpoint is internal and not documented
- **Rate limiting**: Avoid polling too frequently (minimum recommended: 30 seconds)
- **Authentication**: Requires manual credential extraction; expiration handling via reauth
- **No MQTT**: This integration does not support MQTT mode

## Development

### Testing Locally

```bash
# Clone the repository
git clone https://github.com/sweh/inkbird_homeassistant.git
cd inkbird_homeassistant

# Copy to Home Assistant dev setup
cp -r custom_components/inkbird_im03w /path/to/homeassistant/config/custom_components/

# Restart Home Assistant
```

### Code Quality

- Python 3.11+
- Type hints throughout
- Async/await only (no blocking calls)
- No external dependencies beyond Home Assistant

## License

This project is licensed under the MIT License. See `LICENSE` for details.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## Disclaimer

This integration uses an internal Tuya API endpoint that is not officially documented or supported by Tuya. Use at your own risk. The authors are not responsible for:
- Data loss or corruption
- Service interruptions due to API changes
- Account suspension or other issues related to Tuya ToS violations

Always ensure you comply with Tuya's Terms of Service when using this integration.

## Support

If you encounter issues, please:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review Home Assistant logs
3. Open an issue on [GitHub Issues](https://github.com/sweh/inkbird_homeassistant/issues)

---

**Enjoy monitoring your pool temperature with Home Assistant!** 🌡️
