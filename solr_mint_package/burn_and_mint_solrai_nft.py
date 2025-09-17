#!/usr/bin/env python3
"""
burn_and_mint_solrai_nft.py
===========================

This script burns 1 000 SOLR tokens and mints a jurisdiction‑tagged SOLRAI NFT on
the XRPL testnet.  It reads configuration values from `config.yaml`, burns
SOLR tokens by sending them back to the issuer, creates metadata (embedding
the supplied SolisCloud screenshot) and submits an `NFTokenMint` transaction.

Usage:
    python burn_and_mint_solrai_nft.py --burn-tx-hash <optional-burn-hash>

If `--burn-tx-hash` is omitted, the script will perform the burn and use the
returned transaction hash.  Otherwise, it will skip the burn step and use
the provided hash when constructing the metadata.

Dependencies:
    pip install xrpl PyYAML python-dotenv
"""

import argparse
import json
import sys
import base64
from pathlib import Path
import yaml
from typing import Optional

import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models import transactions, requests
from xrpl.transaction import safe_sign_and_submit_transaction, send_reliable_submission


TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_client() -> JsonRpcClient:
    return JsonRpcClient(TESTNET_URL)


def burn_solr(
    client: JsonRpcClient,
    hot_wallet: Wallet,
    issuer_address: str,
    currency: str,
    amount: str = "1000",
) -> str:
    """Burn SOLR by sending tokens back to the issuer.

    Returns the transaction hash.
    """
    from xrpl.models.transactions import Payment

    burn_tx = Payment(
        account=hot_wallet.classic_address,
        amount={
            "currency": currency,
            "value": amount,
            "issuer": issuer_address,
        },
        destination=issuer_address,
    )
    signed = safe_sign_and_submit_transaction(burn_tx, hot_wallet, client)
    response = send_reliable_submission(signed, client)
    tx_hash = response.result.get("hash") or signed.result.get("hash")
    return tx_hash


def read_image_as_base64(image_path: Path) -> str:
    """Read an image file and return its base64 representation (without prefix)."""
    with image_path.open("rb") as img_f:
        encoded = base64.b64encode(img_f.read()).decode("ascii")
    return encoded


def create_metadata(config: dict, burn_tx_hash: str, image_path: Path) -> str:
    """Construct metadata JSON and return a hex‑encoded data URI for the NFT.

    Parameters:
        config: configuration dictionary.
        burn_tx_hash: transaction hash of the burn operation.
        image_path: path to the screenshot to embed.

    Returns a hexadecimal string suitable for the `URI` field of an NFTokenMint
    transaction.
    """
    image_b64 = read_image_as_base64(image_path)
    metadata = {
        "$schema": "https://schema.solrai.energy/rec-nft-metadata.json#",
        "schema_version": config.get("schema_version", "1.0"),
        "jurisdiction": config.get("jurisdiction"),
        "program": config.get("program"),
        "vintage": config.get("vintage"),
        "vintage_start": config.get("vintage_start"),
        "vintage_end": config.get("vintage_end"),
        "facility": {
            "name": config.get("facility_name"),
            "location": config.get("facility_location"),
            "grid_region": config.get("grid_region"),
            "technology": config.get("technology", "Solar PV"),
        },
        "meter": {
            "meter_hash": config.get("meter_hash"),
            "oracle_reference": config.get("oracle_reference"),
        },
        "burn_proof": {
            "tx_hash": burn_tx_hash,
            "explorer": f"https://testnet.xrpl.org/transactions/{burn_tx_hash}" if burn_tx_hash else None,
            "amount_burned": "1000",
            "currency": config.get("currency_code", "STN"),
        },
        "attributes": [
            {"trait_type": "REC Serial Prefix", "value": config.get("rec_serial_prefix")},
            {"trait_type": "Transfer Fee (bps)", "value": 10000},
            {"trait_type": "Flags", "value": ["Transferable", "Burnable"]},
        ],
        "image": f"data:image/jpeg;base64,{image_b64}",
    }
    json_str = json.dumps(metadata, separators=(",", ":"))
    data_uri = "data:application/json;base64," + base64.b64encode(json_str.encode("utf-8")).decode("ascii")
    return data_uri.encode("utf-8").hex()


def mint_solrai_nft(
    client: JsonRpcClient,
    minter_wallet: Wallet,
    uri_hex: str,
    transfer_fee: int = 10000,
    flags: int = 0x09,
    taxon: int = 0,
) -> dict:
    """Mint a SOLRAI NFT with the provided URI and returns the transaction result."""
    from xrpl.models.transactions import NFTokenMint

    nft_mint_tx = NFTokenMint(
        account=minter_wallet.classic_address,
        uri=uri_hex,
        transfer_fee=transfer_fee,
        flags=flags,
        nftoken_taxon=taxon,
    )
    signed = safe_sign_and_submit_transaction(nft_mint_tx, minter_wallet, client)
    result = send_reliable_submission(signed, client)
    return result.result


def main() -> None:
    parser = argparse.ArgumentParser(description="Burn SOLR tokens and mint a SOLRAI NFT")
    parser.add_argument(
        "--burn-tx-hash",
        help="Transaction hash of a prior SOLR burn.  If omitted, this script will burn 1000 SOLR.",
        default=None,
    )
    parser.add_argument("--config", default="config.yaml", help="Path to configuration YAML file")
    parser.add_argument(
        "--image",
        default="IMG_A6FBCF8F-9700-4089-ADB0-5C914EF43766.jpeg",
        help="Relative path to the screenshot image used as proof",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    currency_code = config.get("currency_code", "SOLR")

    issuer_seed = config.get("issuer_seed")
    hot_seed = config.get("hot_seed")
    minter_seed = config.get("nft_minter_seed")
    if not issuer_seed or not hot_seed or not minter_seed:
        sys.exit("Error: issuer_seed, hot_seed, and nft_minter_seed must be defined in the config file.")

    client = get_client()
    issuer_wallet = Wallet.from_seed(issuer_seed)
    hot_wallet = Wallet.from_seed(hot_seed)
    minter_wallet = Wallet.from_seed(minter_seed)

    burn_tx_hash: Optional[str] = args.burn_tx_hash

    if not burn_tx_hash:
        print("Burning 1000 SOLR tokens...")
        burn_tx_hash = burn_solr(
            client,
            hot_wallet,
            issuer_wallet.classic_address,
            currency_code,
            amount="1000",
        )
        print(f"Burn transaction submitted. Hash: {burn_tx_hash}")
    else:
        print(f"Using provided burn transaction hash: {burn_tx_hash}")

    image_path = Path(args.image)
    if not image_path.exists():
        sys.exit(f"Error: image file {image_path} not found.")

    print("Constructing metadata and data URI...")
    uri_hex = create_metadata(config, burn_tx_hash, image_path)

    print("Minting SOLRAI NFT via designated minter...")
    tx_result = mint_solrai_nft(
        client,
        minter_wallet,
        uri_hex,
        transfer_fee=10000,  # 10% fee (8% marketplace + 2% ESG)
        flags=0x09,  # tfBurnable (1) + tfTransferable (8)
        taxon=0,
    )
    print(json.dumps(tx_result, indent=4))
    print("SOLRAI NFT minted.  Record the NFTokenID from the transaction metadata for future use.")


if __name__ == "__main__":
    main()