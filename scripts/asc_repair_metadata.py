#!/usr/bin/env python3
"""One-shot App Store Connect metadata repair.

The script is intentionally narrow and deterministic:
- finds iOS version 1.0 for the configured app;
- finds build 41 and attaches it to that version;
- creates en-US localizations for the two known subscriptions when absent.

It performs writes only when ASC_APPLY=true. Secret material is never printed.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import jwt
import requests

BASE = "https://api.appstoreconnect.apple.com/v1"
APP_ID = os.environ.get("ASC_APP_ID", "6802760553")
BUILD_NUMBER = os.environ.get("ASC_BUILD_NUMBER", "41")
APPLY = os.environ.get("ASC_APPLY", "false").lower() == "true"

SUBSCRIPTIONS = {
    "6803000242": {
        "name": "SleepRise Pro Monthly",
        "description": "Ad-free sleep sounds and unlimited Pro missions.",
    },
    "6803006192": {
        "name": "SleepRise Pro Yearly",
        "description": "Ad-free sleep sounds and Pro missions for a year.",
    },
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def make_token() -> str:
    issuer = os.environ.get("APPSTORE_ISSUER_ID")
    key_id = os.environ.get("APPSTORE_API_KEY_ID")
    private_key = os.environ.get("APPSTORE_API_PRIVATE_KEY")
    if not issuer or not key_id or not private_key:
        fail("Missing App Store Connect API environment configuration")
    now = int(time.time())
    payload = {
        "iss": issuer,
        "iat": now,
        "exp": now + 1199,
        "aud": "appstoreconnect-v1",
    }
    return jwt.encode(
        payload,
        private_key,
        algorithm="ES256",
        headers={"kid": key_id, "typ": "JWT"},
    )


def response_error(resp: requests.Response) -> str:
    try:
        body: Any = resp.json()
        errors = body.get("errors") if isinstance(body, dict) else None
        if errors:
            return json.dumps(errors, ensure_ascii=False)[:1200]
        return json.dumps(body, ensure_ascii=False)[:1200]
    except Exception:
        return resp.text[:1200]


def request(method: str, path: str, token: str, **kwargs: Any) -> requests.Response:
    headers = kwargs.pop("headers", {})
    headers.update({"Authorization": f"Bearer {token}", "Accept": "application/json"})
    if method in {"POST", "PATCH"}:
        headers["Content-Type"] = "application/json"
    resp = requests.request(method, BASE + path, headers=headers, timeout=45, **kwargs)
    print(f"{method} {path} -> {resp.status_code}")
    return resp


def get_version(token: str) -> str:
    resp = request(
        "GET",
        f"/apps/{APP_ID}/appStoreVersions?filter[versionString]=1.0&filter[platform]=IOS&limit=50",
        token,
    )
    if resp.status_code != 200:
        fail(f"Cannot list app store versions: {response_error(resp)}")
    items = resp.json().get("data", [])
    for item in items:
        attrs = item.get("attributes", {})
        if attrs.get("versionString") == "1.0" and attrs.get("platform") == "IOS":
            print(f"version 1.0 resource: {item['id']}")
            return item["id"]
    fail("iOS version 1.0 resource not found")


def find_build(token: str) -> str:
    resp = request(
        "GET",
        f"/builds?filter[app]={APP_ID}&sort=-uploadedDate&limit=200",
        token,
    )
    if resp.status_code != 200:
        fail(f"Cannot list builds: {response_error(resp)}")
    for item in resp.json().get("data", []):
        attrs = item.get("attributes", {})
        if str(attrs.get("version")) == str(BUILD_NUMBER):
            state = attrs.get("processingState")
            print(f"build {BUILD_NUMBER} resource: {item['id']} (processingState={state})")
            if state not in (None, "VALID"):
                fail(f"Build {BUILD_NUMBER} is not VALID: {state}")
            return item["id"]
    fail(f"Build {BUILD_NUMBER} resource not found")


def current_build(token: str, version_id: str) -> str | None:
    resp = request("GET", f"/appStoreVersions/{version_id}/relationships/build", token)
    if resp.status_code != 200:
        fail(f"Cannot read current version build: {response_error(resp)}")
    data = resp.json().get("data")
    return data.get("id") if isinstance(data, dict) else None


def attach_build(token: str, version_id: str, build_id: str) -> None:
    existing = current_build(token, version_id)
    print(f"current build resource: {existing or 'none'}")
    if existing == build_id:
        print("Build 41 is already attached; no write needed.")
        return
    body = {"data": {"type": "builds", "id": build_id}}
    if not APPLY:
        print(f"DRY RUN: would attach build {BUILD_NUMBER} to version 1.0")
        return
    resp = request("PATCH", f"/appStoreVersions/{version_id}/relationships/build", token, json=body)
    if resp.status_code != 204:
        fail(f"Cannot attach build {BUILD_NUMBER}: {response_error(resp)}")
    print(f"Attached build {BUILD_NUMBER} to version 1.0")


def subscription_localizations(token: str, subscription_id: str) -> list[dict[str, Any]]:
    resp = request(
        "GET",
        f"/subscriptions/{subscription_id}/subscriptionLocalizations?limit=200",
        token,
    )
    if resp.status_code != 200:
        fail(f"Cannot list localizations for subscription {subscription_id}: {response_error(resp)}")
    return resp.json().get("data", [])


def ensure_localization(token: str, subscription_id: str, values: dict[str, str]) -> None:
    items = subscription_localizations(token, subscription_id)
    for item in items:
        attrs = item.get("attributes", {})
        if attrs.get("locale") == "en-US":
            print(f"subscription {subscription_id}: en-US localization already exists")
            return
    body = {
        "data": {
            "type": "subscriptionLocalizations",
            "attributes": {
                "name": values["name"],
                "locale": "en-US",
                "description": values["description"],
            },
            "relationships": {
                "subscription": {
                    "data": {"type": "subscriptions", "id": subscription_id}
                }
            },
        }
    }
    if not APPLY:
        print(f"DRY RUN: would create en-US localization for subscription {subscription_id}")
        return
    resp = request("POST", "/subscriptionLocalizations", token, json=body)
    if resp.status_code not in (200, 201):
        fail(f"Cannot create localization for subscription {subscription_id}: {response_error(resp)}")
    print(f"Created en-US localization for subscription {subscription_id}")


def main() -> int:
    token = make_token()
    print(f"ASC repair start: app={APP_ID}, build={BUILD_NUMBER}, apply={APPLY}")
    errors: list[str] = []
    try:
        version_id = get_version(token)
        build_id = find_build(token)
        attach_build(token, version_id, build_id)
    except Exception as exc:
        errors.append(str(exc))
        print(f"BUILD REPAIR ERROR: {exc}")

    for subscription_id, values in SUBSCRIPTIONS.items():
        try:
            ensure_localization(token, subscription_id, values)
        except Exception as exc:
            errors.append(str(exc))
            print(f"LOCALIZATION ERROR ({subscription_id}): {exc}")

    if errors:
        print("ASC repair finished with errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("ASC repair finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
