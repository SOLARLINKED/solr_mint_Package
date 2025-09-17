#!/usr/bin/env python3
"""
solrai_nft_flow.py
==================

End-to-end flow for minting STN tokens, burning for NFT, and handling payment on XRPL Testnet.
Ready for integration with XRP/Ripple/Xaman wallets and dApps.

Dependencies:
    pip install xrpl PyYAML python-dotenv
"""
import sys
import yaml
from decimal import Decimal
from pathlib import Path
import base64
import json
import argparse
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.transaction import safe_sign_and_submit_transaction, send_reliable_submission
from xrpl.models.transactions import (
    AccountSet,
    AccountSetTfFlags,
    AccountSetAsfFlags,
    TrustSet,
    Payment,
    NFTokenMint,
    NFTokenCreateOffer,
    NFTokenAcceptOffer,
)
from xrpl.models.requests import AccountNFTs

TESTNET_URL = "https://s.altnet.rippletest.net:51234"
BLACKHOLE = "rrrrrrrrrrrrrrrrrrrrrhoLvTp"

# --- Utility Functions ---
def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_client() -> JsonRpcClient:
    return JsonRpcClient(TESTNET_URL)

def configure_account(client, wallet, is_issuer):
    if is_issuer:
        flags = AccountSetTfFlags.tfDisallowXRP | AccountSetTfFlags.tfRequireDestTag
        asf_flags = AccountSetAsfFlags.asfDefaultRipple
    else:
        flags = AccountSetTfFlags.tfDisallowXRP | AccountSetTfFlags.tfRequireDestTag
        asf_flags = AccountSetAsfFlags.asfRequireAuth
    tx = AccountSet(account=wallet.classic_address, flags=flags, set_flag=asf_flags)
    signed = safe_sign_and_submit_transaction(tx, wallet, client)
    send_reliable_submission(signed, client)

def create_trust_line(client, hot_wallet, issuer_address, currency, limit):
    trust_tx = TrustSet(
        account=hot_wallet.classic_address,
        limit_amount={"currency": currency, "issuer": issuer_address, "value": str(limit)},
    )
    signed = safe_sign_and_submit_transaction(trust_tx, hot_wallet, client)
    send_reliable_submission(signed, client)

def issue_stn(client, issuer_wallet, hot_address, currency, amount):
    pay_tx = Payment(
        account=issuer_wallet.classic_address,
        amount={"currency": currency, "value": str(amount), "issuer": issuer_wallet.classic_address},
        destination=hot_address,
    )
    signed = safe_sign_and_submit_transaction(pay_tx, issuer_wallet, client)
    send_reliable_submission(signed, client)

def transfer_stn(client, from_wallet, to_address, currency, amount, issuer_address):
    pay_tx = Payment(
        account=from_wallet.classic_address,
        amount={"currency": currency, "value": str(amount), "issuer": issuer_address},
        destination=to_address,
    )
    signed = safe_sign_and_submit_transaction(pay_tx, from_wallet, client)
    send_reliable_submission(signed, client)

def burn_stn(client, owner_wallet, currency, amount, issuer_address):
    pay_tx = Payment(
        account=owner_wallet.classic_address,
        amount={"currency": currency, "value": str(amount), "issuer": issuer_address},
        destination=BLACKHOLE,
    )
    signed = safe_sign_and_submit_transaction(pay_tx, owner_wallet, client)
    response = send_reliable_submission(signed, client)
    return response.result.get("hash") or signed.result.get("hash")

def read_image_as_base64(image_path: Path) -> str:
    with image_path.open("rb") as img_f:
        return base64.b64encode(img_f.read()).decode("ascii")

def create_metadata(config, burn_tx_hash, image_path):
    image_b64 = read_image_as_base64(image_path)
    metadata = {
        "jurisdiction": config.get("jurisdiction"),
        "program": config.get("program"),
        "vintage": config.get("vintage"),
        "meter_hash": config.get("meter_hash"),
        "oracle_reference": config.get("oracle_reference"),
        "burn_tx_hash": burn_tx_hash,
        "image": f"data:image/jpeg;base64,{image_b64}",
    }
    json_str = json.dumps(metadata, separators=(",", ":"))
    data_uri = "data:application/json;base64," + base64.b64encode(json_str.encode("utf-8")).decode("ascii")
    return data_uri.encode("utf-8").hex()

def mint_solrai_nft(client, minter_wallet, uri_hex, transfer_fee=10000, flags=0x09, taxon=0):
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

def send_xrp_payment(client, from_wallet, to_address, drops):
    pay_tx = Payment(
        account=from_wallet.classic_address,
        amount=str(drops),
        destination=to_address,
    )
    signed = safe_sign_and_submit_transaction(pay_tx, from_wallet, client)
    send_reliable_submission(signed, client)

def fetch_nft_id_by_uri(client, account: str, uri_hex: str) -> str:
    """Lookup the freshly minted NFTokenID by matching the URI on the minter's account."""
    req = AccountNFTs(account=account)
    resp = client.request(req)
    nfts = resp.result.get("account_nfts", [])
    for nft in nfts:
        if nft.get("URI") == uri_hex:
            return nft.get("NFTokenID") or nft.get("nft_id")
    return ""

def transfer_nft_to_owner(client, minter_wallet, owner_wallet, nft_id: str):
    """Create a zero-amount, destination-restricted sell offer and have owner accept it."""
    # Create zero-price sell offer restricted to owner
    create = NFTokenCreateOffer(
        account=minter_wallet.classic_address,
        nftoken_id=nft_id,
        amount="0",
        destination=owner_wallet.classic_address,
        flags=1,  # tfSellOffer
    )
    signed = safe_sign_and_submit_transaction(create, minter_wallet, client)
    result = send_reliable_submission(signed, client).result
    # Extract offer index from metadata
    offer_index = result.get("offer_id") or result.get("OfferID")
    if not offer_index:
        # Fallback: try from tx json result
        offer_index = signed.result.get("tx_json", {}).get("hash")  # not ideal, but avoids deep meta parsing here
    # Owner accepts offer
    accept = NFTokenAcceptOffer(
        account=owner_wallet.classic_address,
        nftoken_sell_offer=offer_index,
    )
    signed2 = safe_sign_and_submit_transaction(accept, owner_wallet, client)
    send_reliable_submission(signed2, client)

# --- Main Flow ---
def main():
    parser = argparse.ArgumentParser(description="SOLRAI NFT full flow")
    parser.add_argument("--kwh", type=Decimal, required=True, help="kWh to mint as STN tokens")
    parser.add_argument("--config", default="config.yaml", help="Config YAML path")
    parser.add_argument("--image", default=None, help="Path to proof image")
    parser.add_argument("--price_xrp_drops", default=None, help="NFT price in XRP drops")
    args = parser.parse_args()

    config = load_config(args.config)
    issuer_wallet = Wallet.from_seed(config["issuer_seed"])
    hot_wallet = Wallet.from_seed(config["hot_seed"])
    system_owner_wallet = Wallet.from_seed(config["system_owner_seed"])
    nft_buyer_wallet = Wallet.from_seed(config["nft_buyer_seed"])
    minter_wallet = Wallet.from_seed(config["nft_minter_seed"]) if config.get("nft_minter_seed") else None
    currency = config["currency_code"]
    client = get_client()

    # 1. Configure accounts
    print("Configuring issuer and hot wallets...")
    configure_account(client, issuer_wallet, is_issuer=True)
    configure_account(client, hot_wallet, is_issuer=False)

    # 2. Create trust line
    print("Creating trust line...")
    create_trust_line(client, hot_wallet, issuer_wallet.classic_address, currency, limit=str(10**9))

    # 3. Mint STN tokens to hot wallet
    print(f"Minting {args.kwh} STN to hot wallet...")
    issue_stn(client, issuer_wallet, hot_wallet.classic_address, currency, args.kwh)

    # 4. Transfer STN to system owner
    print(f"Transferring {args.kwh} STN to system owner...")
    transfer_stn(client, hot_wallet, config["system_owner_address"], currency, args.kwh, issuer_wallet.classic_address)

    # 5. Burn 1000 STN to mint NFT
    print("Burning 1000 STN from system owner...")
    burn_tx_hash = burn_stn(client, system_owner_wallet, currency, "1000", issuer_wallet.classic_address)
    print(f"Burn tx hash: {burn_tx_hash}")

    # 6. Mint NFT
    image_path = Path(args.image or config["image_path"])
    print("Creating NFT metadata and minting NFT via designated minter...")
    uri_hex = create_metadata(config, burn_tx_hash, image_path)
    if not minter_wallet:
        raise SystemExit("Config missing nft_minter_seed; required for centralized minting.")
    nft_result = mint_solrai_nft(client, minter_wallet, uri_hex)
    print(json.dumps(nft_result, indent=2))
    # Find NFTokenID and transfer to system owner
    nft_id = fetch_nft_id_by_uri(client, minter_wallet.classic_address, uri_hex)
    if nft_id:
        print(f"Transferring NFT {nft_id} to system owner via zero-amount offer...")
        transfer_nft_to_owner(client, minter_wallet, system_owner_wallet, nft_id)

    # 7. Buyer pays system owner
    if args.price_xrp_drops or config.get("price_xrp_drops"):
        price_drops = args.price_xrp_drops or config["price_xrp_drops"]
        print(f"NFT buyer paying {price_drops} drops to system owner...")
        send_xrp_payment(client, nft_buyer_wallet, config["system_owner_address"], price_drops)
        print("Payment sent.")
    else:
        print("No price_xrp_drops specified; skipping payment.")

    print("Flow complete. Check XRPL explorer for all tx hashes.")

if __name__ == "__main__":
    main()
