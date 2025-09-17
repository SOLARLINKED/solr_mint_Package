#!/usr/bin/env python3
"""
Minimal Xumm Platform client for creating payloads (Testnet/demo).

This helper calls the Xumm Platform payload endpoint to create a signable
payload and returns the sign URL/UUID. It expects `XUMM_API_KEY` and
`XUMM_API_SECRET` to be set in the environment. For production, keep
credentials secret and create server-side endpoints to create payloads.

Docs: https://xumm.readme.io/reference/xapps-jwt-endpoints
"""
import os
import requests
from typing import Dict, Any


XUMM_BASE = os.getenv("XUMM_API_BASE", "https://xumm.app/api/v1")


class XummError(RuntimeError):
    pass


def create_payload(tx_json: Dict[str, Any], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    """Create a Xumm payload using the platform API and return payload info.

    Returns a dict with keys including `uuid` and `next` (sign URLs).
    """
    api_key = os.getenv("XUMM_API_KEY")
    api_secret = os.getenv("XUMM_API_SECRET")
    if not api_key or not api_secret:
        raise XummError("XUMM_API_KEY and XUMM_API_SECRET must be set in environment")

    url = f"{XUMM_BASE}/platform/payload"
    body = {
        "txjson": tx_json,
        "options": {"submit": False},
    }
    if metadata:
        body["txjson"]["Memos"] = metadata.get("memos") or body["txjson"].get("Memos")

    headers = {
        "x-api-key": api_key,
        "x-api-secret": api_secret,
        "Content-Type": "application/json",
    }

    resp = requests.post(url, json=body, headers=headers, timeout=15)
    if resp.status_code >= 400:
        raise XummError(f"Xumm API error {resp.status_code}: {resp.text}")
    data = resp.json()
    # returned structure includes 'uuid' and 'next' with web and app links
    return data


def payload_sign_url_from_response(payload_response: Dict[str, Any]) -> str:
    """Extract a best-effort sign URL (web) from Xumm response."""
    if not payload_response:
        return ""
    next_obj = payload_response.get("next") or {}
    # prefer web link, fallback to always or to a constructed sign link
    for key in ("web", "always", "qr_png", "app"):
        if next_obj.get(key):
            return next_obj.get(key)
    uuid = payload_response.get("uuid")
    if uuid:
        return f"https://xumm.app/sign/{uuid}"
    return ""
