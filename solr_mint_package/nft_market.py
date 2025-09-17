#!/usr/bin/env python3
"""
XRPL NFT market utilities (Testnet): create/accept sell offers for Xaman-first demo.

Prereqs:
  pip install xrpl PyYAML python-dotenv

Notes:
- XRPL NFT offers: NFTokenCreateOffer, NFTokenAcceptOffer.
- Xaman users can sign these txs via deep links (see xaman_payloads.py for quick links).
"""
import argparse
import json
import sys
import yaml
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import safe_sign_and_submit_transaction, send_reliable_submission
from xrpl.models.transactions import NFTokenCreateOffer, NFTokenAcceptOffer

TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_client() -> JsonRpcClient:
    return JsonRpcClient(TESTNET_URL)


def create_sell_offer(wallet: Wallet, client: JsonRpcClient, nftoken_id: str, amount_drops: str, destination: str = None) -> dict:
    tx = NFTokenCreateOffer(
        account=wallet.classic_address,
        amount=amount_drops,
        nftoken_id=nftoken_id,
        destination=destination,  # optional: restrict buyer
        flags=1  # tfSellOffer
    )
    signed = safe_sign_and_submit_transaction(tx, wallet, client)
    result = send_reliable_submission(signed, client)
    return result.result


def accept_sell_offer(wallet: Wallet, client: JsonRpcClient, sell_offer_index: str) -> dict:
    tx = NFTokenAcceptOffer(
        account=wallet.classic_address,
        nftoken_sell_offer=sell_offer_index,
    )
    signed = safe_sign_and_submit_transaction(tx, wallet, client)
    result = send_reliable_submission(signed, client)
    return result.result


def main():
    parser = argparse.ArgumentParser(description="XRPL NFT offer helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create-sell")
    p_create.add_argument("--config", default="config.yaml")
    p_create.add_argument("--wallet", choices=["issuer", "hot", "owner", "buyer"], default="owner")
    p_create.add_argument("--nft-id", required=True)
    p_create.add_argument("--amount-drops", required=True)
    p_create.add_argument("--destination", default=None)

    p_accept = sub.add_parser("accept-sell")
    p_accept.add_argument("--config", default="config.yaml")
    p_accept.add_argument("--wallet", choices=["issuer", "hot", "owner", "buyer"], default="buyer")
    p_accept.add_argument("--offer-index", required=True)

    args = parser.parse_args()
    cfg = load_config(args.config)

    client = get_client()

    wallet_map = {
        "issuer": Wallet.from_seed(cfg["issuer_seed"]),
        "hot": Wallet.from_seed(cfg["hot_seed"]),
        "owner": Wallet.from_seed(cfg["system_owner_seed"]),
        "buyer": Wallet.from_seed(cfg["nft_buyer_seed"]),
    }
    wallet = wallet_map[args.wallet]

    if args.cmd == "create-sell":
        res = create_sell_offer(wallet, client, args.nft_id, args.amount_drops, destination=args.destination)
        print(json.dumps(res, indent=2))
        print("Note: capture offer index from metadata to share via Xaman.")
    elif args.cmd == "accept-sell":
        res = accept_sell_offer(wallet, client, args.offer_index)
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
