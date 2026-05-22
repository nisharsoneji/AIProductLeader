import json
import os
from urllib.parse import quote

import requests
import urllib3


def getenv(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def password():
    if os.getenv("OGG_PASSWORD"):
        return os.environ["OGG_PASSWORD"]
    password_file = os.getenv("OGG_PASSWORD_FILE")
    if password_file:
        with open(password_file, encoding="utf-8") as handle:
            return handle.read().strip()
    raise SystemExit("Set OGG_PASSWORD or OGG_PASSWORD_FILE")


BASE_URL = getenv("OGG_BASE_URL", required=True).rstrip("/")
USERNAME = getenv("OGG_USERNAME", required=True)
PASSWORD = password()
VERIFY_TLS = getenv("OGG_VERIFY_TLS", "false").lower() == "true"

if not VERIFY_TLS:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def enc(value):
    return quote(value, safe="")


def request(method, path, payload=None):
    response = requests.request(
        method,
        BASE_URL + path,
        auth=(USERNAME, PASSWORD),
        json=payload,
        headers={"Accept": "application/json"},
        verify=VERIFY_TLS,
        timeout=60,
    )
    if not response.ok:
        raise SystemExit(f"{method} {path} failed: {response.status_code} {response.text}")
    if not response.text:
        return {}
    try:
        return response.json()
    except ValueError:
        return response.text


def dump(data):
    print(json.dumps(data, indent=2, sort_keys=True))

