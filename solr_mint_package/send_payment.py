#!/usr/bin/env python3
"""
send_payment.py
================

Send a simple XRP payment on the XRPL testnet.  This script reads the
sender’s seed from `config.yaml`, constructs a Payment transaction and
submits it.

Usage:
    python send_payment.py --to rDestination --drops 1000000 [--tag 123]

Parameters:
    --to    Destination classic address.
    --drops Amount of XRP to send expressed in drops (1 XRP = 1,000,000 drops).
    --tag   Optional destination tag (integer).

Dependencies:
    pip install xrpl PyYAML python-dotenv
"""

import argparse
import sys
import yaml
import json

import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models import transactions
from xrpl.transaction import safe_sign_and_submit_transaction, send_reliable_submission

TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_client() -> JsonRpcClient:
    return JsonRpcClient(TESTNET_URL)


def send_payment(
    client: JsonRpcClient,
    wallet: Wallet,
    destination: str,
    drops: str,
    dest_tag: int = None,
) -> dict:
    from xrpl.models.transactions import Payment

    payment_tx = Payment(
        account=wallet.classic_address,
        amount=str(drops),
        destination=destination,
        destination_tag=dest_tag,
    )
    signed = safe_sign_and_submit_transaction(payment_tx, wallet, client)
    result = send_reliable_submission(signed, client)
    return result.result


def main() -> None:
    parser = argparse.ArgumentParser(description="Send an XRP payment on the XRPL testnet")
    parser.add_argument("--to", required=True, help="Destination classic address")
    parser.add_argument("--drops", required=True, help="Amount to send in drops (1 XRP = 1,000,000 drops)")
    parser.add_argument("--tag", type=int, default=None, help="Optional destination tag")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration YAML file")
    args = parser.parse_args()

    config = load_config(args.config)
    # Default to sending from the hot account
    sender_seed = config.get("hot_seed")
    if not sender_seed:
        sys.exit("Error: hot_seed must be defined in the config file.")

    client = get_client()
    sender_wallet = Wallet.from_seed(sender_seed)

    print(f"Sending {args.drops} drops from {sender_wallet.classic_address} to {args.to}...")
    tx_result = send_payment(client, sender_wallet, args.to, args.drops, dest_tag=args.tag)
    print(json.dumps(tx_result, indent=4))
    print("Payment submitted.  Verify the transaction on the XRPL explorer.")


if __name__ == "__main__":
    main()