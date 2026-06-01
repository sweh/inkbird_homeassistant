# python3 -m venv venv
# venv/bin/pip install playwright
# venv/bin/playwright install chromium
# venv/bin/python get_cookie.py

from playwright.sync_api import sync_playwright

START_URL = "https://auth.tuya.com/?from=https%3A%2F%2Fauth.tuya.com%2Flogin%2Fsilent%3Ffrom%3Dhttps%253A%252F%252Feu.platform.tuya.com%252Fcloud%252Fdevice%252Fdetail%252F%253Fid%253Dp1780246545728yrxdss%2526sourceId%253Deu1780245563242Wvh5W%2526sourceType%253D4%2526region%253DEU%2526deviceKey%253DdeviceLogs%2526deviceId%253Dbfd54d796bf836a559gwpf"

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir="./tuya-browser-profile",
        headless=False,  # erster Lauf: manuell einloggen
    )

    page = ctx.new_page()
    page.goto(START_URL)
    page.wait_for_load_state("networkidle")

    input("Wenn du eingeloggt bist und die Geräteseite siehst: Enter drücken...")

    cookies = ctx.cookies("https://eu.platform.tuya.com")

    cookie_header = "; ".join(
        f"{c['name']}={c['value']}" for c in cookies
    )

    csrf = next(
        (c["value"] for c in cookies if c["name"] == "csrf-token"),
        None,
    )

    print("TUYA_COOKIE=", cookie_header)
    print("TUYA_CSRF_TOKEN=", csrf)

    ctx.close()
