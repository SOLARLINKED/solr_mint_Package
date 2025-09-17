#!/usr/bin/env python3
"""
Compose NFTokenCreateOffer and NFTokenAcceptOffer tx JSON for use with Xumm payloads.
This is a skeleton: it builds TX JSON and either returns it or calls the Xumm client to create
server-side payloads.
"""
import argparse
import json
from xumm_client import create_payload, payload_sign_url_from_response, XummError


def make_create_offer_tx(nft_id: str, amount_drops: str, destination: str = None) -> dict:
    tx = {
        "TransactionType": "NFTokenCreateOffer",
        "NFTokenID": nft_id,
        "Amount": str(amount_drops),
    }
    if destination:
        tx["Destination"] = destination
    return tx


def make_accept_offer_tx(offer_index: str) -> dict:
    return {
        "TransactionType": "NFTokenAcceptOffer",
        "NFTokenSellOffer": offer_index,
    }


def main():
    parser = argparse.ArgumentParser(description="Build sell/accept offer tx JSON and optionally create Xumm payload")
    parser.add_argument("--cmd", choices=["create-offer","accept-offer"], required=True)
    parser.add_argument("--nft-id")
    parser.add_argument("--amount-drops")
    parser.add_argument("--offer-index")
    parser.add_argument("--destination")
    args = parser.parse_args()

    if args.cmd == "create-offer":
        tx = make_create_offer_tx(args.nft_id, args.amount_drops, args.destination)
        try:
            resp = create_payload(tx)
            print(payload_sign_url_from_response(resp))
        except XummError:
            print(json.dumps(tx))
    else:
        tx = make_accept_offer_tx(args.offer_index)
        try:
            resp = create_payload(tx)
            print(payload_sign_url_from_response(resp))
        except XummError:
            print(json.dumps(tx))

if __name__ == "__main__":
    main()
