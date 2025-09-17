#!/usr/bin/env python3
"""
Xaman (Xumm) payload helpers for a Xaman-first demo.

- Creates a simple payment payload to pay the system owner in XRP drops.
- Prints the deeplink URL that Xaman can open.

Note: For production use the official Xumm SDK and API keys. Here we provide
client-side deep links for demo purposes without server roundtrips.
"""
import argparse
import json
import os
from urllib.parse import urlencode, quote
import os
from xumm_client import create_payload, payload_sign_url_from_response, XummError

# Xumm sign request deep link patterns documented by Xumm/Xaman
# In a production setting you would POST to Xumm API to create a payload
# and then use xumm:// or https://xumm.app/sign/<uuid>. For a wallet-agnostic demo,
# we embed a pre-filled tx JSON in a sign URL when possible.


def build_payment_json(account: str, destination: str, drops: str, memo_text: str = "SOLRAI-REC Testnet Purchase") -> dict:
    # Build a minimal XRP Payment transaction JSON
    tx = {
        "TransactionType": "Payment",
        "Account": account,          # sender fills in after opening Xumm if not provided
        "Destination": destination,
        "Amount": drops,
        "Memos": [{
            "Memo": {
                "MemoType": "74657874",  # 'text'
                "MemoData": memo_text.encode("utf-8").hex()
            }
        }]
    }
    return tx


def xumm_deeplink_from_tx(tx_json: dict) -> str:
    # Encode TX JSON into a sign link Xumm can open in app/web
    # Prefer https scheme for easy QR scanning
    # If XUMM API credentials are set, create a payload on the platform
    try:
        resp = create_payload(tx_json)
        return payload_sign_url_from_response(resp)
    except XummError:
        # Fallback: embed the txjson as a GET payload (not officially supported but useful for demo)
        payload = quote(json.dumps(tx_json, separators=(",", ":")))
        return f"https://xumm.app/sign?payload={payload}"


def main():
    parser = argparse.ArgumentParser(description="Generate a Xaman/Xumm payment deeplink")
    parser.add_argument("--destination", required=True, help="Destination classic address")
    parser.add_argument("--drops", required=True, help="Amount in drops")
    parser.add_argument("--account", default="", help="Optional sender account (leave empty to let wallet pick)")
    args = parser.parse_args()

    tx = build_payment_json(args.account, args.destination, args.drops)
    url = xumm_deeplink_from_tx(tx)
    print(url)


if __name__ == "__main__":
    main()
