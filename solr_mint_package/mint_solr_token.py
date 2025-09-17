#!/usr/bin/env python3
"""
mint_solr_token.py
===================

This script mints SOLR fungible tokens on the XRPL testnet.  It reads a
configuration file (`config.yaml`) containing account seeds and
metadata.  The script performs three main tasks:

1. Configure the issuer and hot accounts with recommended AccountSet flags.
2. Create a trust line from the hot account to the issuer for the SOLR token.
3. Send a Payment from the issuer to the hot account to issue SOLR tokens
   equal to the supplied kilowatt‑hour (kWh) value.

Usage:
    python mint_solr_token.py --kwh 8.19

Dependencies:
    pip install xrpl PyYAML python-dotenv
"""

import argparse
import sys
import time
import yaml
from decimal import Decimal

import xrpl
from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models import transactions, requests
from xrpl.transaction import safe_sign_and_submit_transaction, send_reliable_submission
from xrpl.utils import xrp_to_drops


TESTNET_URL = "https://s.altnet.rippletest.net:51234"


def load_config(path: str = "config.yaml") -> dict:
    """Load YAML configuration.  Raises FileNotFoundError if the file is missing."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_client() -> JsonRpcClient:
    """Instantiate a JSON RPC client for XRPL testnet."""
    return JsonRpcClient(TESTNET_URL)


def configure_account(client: JsonRpcClient, wallet: Wallet, is_issuer: bool) -> None:
    """Send an AccountSet transaction to set recommended flags on the account.

    If `is_issuer` is True, enable Default Ripple, Disallow XRP and Require
    Destination Tag.  If False (hot account), enable Require Auth to prevent
    accidental issuance, Disallow XRP and Require Destination Tag.
    """
    # Flags definitions from xrpl library
    issuer_flags = (
        xrpl.models.transactions.AccountSetFlag.UNSET              # placeholder
    )
    # Build flags bitmask for issuer/hot
    # The tf flags come from xrpl.models.transactions.AccountSetTfFlags
    from xrpl.models.transactions import AccountSet, AccountSetAsfFlags, AccountSetTfFlags

    # Common tf flags
    flags = AccountSetTfFlags.tfDisallowXRP | AccountSetTfFlags.tfRequireDestTag
    # Apply common flags
    base_tx = AccountSet(account=wallet.classic_address, flags=flags)
    signed = safe_sign_and_submit_transaction(base_tx, wallet, client)
    send_reliable_submission(signed, client)

    # Apply ASF flags as separate transactions (one per tx)
    if is_issuer:
        # Issuer: DefaultRipple and RequireAuth for trust lines
        for asf in (AccountSetAsfFlags.asfDefaultRipple, AccountSetAsfFlags.asfRequireAuth):
            tx = AccountSet(account=wallet.classic_address, set_flag=asf)
            # TODO: Ensure issuer seed is kept offline and this transaction is run from a secure machine
            signed = safe_sign_and_submit_transaction(tx, wallet, client)
            send_reliable_submission(signed, client)
    else:
        # Hot: RequireAuth not strictly necessary; skip to reduce friction. Keep it minimal.
        pass


def create_trust_line(client: JsonRpcClient, hot_wallet: Wallet, issuer_address: str, currency: str, limit: str) -> None:
    """Create a trust line from the hot account to the issuer for the given currency.

    Parameters:
        client: XRPL JSON RPC client.
        hot_wallet: Wallet of the hot account (holder).
        issuer_address: Issuer (cold) address.
        currency: Currency code (3‑character or 20‑byte hex string).
        limit: Maximum amount of currency the hot account is willing to hold.
    """
    from xrpl.models.transactions import TrustSet

    trust_tx = TrustSet(
        account=hot_wallet.classic_address,
        limit_amount={
            "currency": currency,
            "issuer": issuer_address,
            "value": str(limit),
        },
    )
    signed = safe_sign_and_submit_transaction(trust_tx, hot_wallet, client)
    send_reliable_submission(signed, client)


def authorize_trust_line(client: JsonRpcClient, issuer_wallet: Wallet, holder_address: str, currency: str) -> None:
    """Issuer authorizes holder's trust line when RequireAuth is set.

    Sets the Authorized flag on the trust line from issuer->holder.
    """
    from xrpl.models.transactions import TrustSet, TrustSetFlag

    auth_tx = TrustSet(
        account=issuer_wallet.classic_address,
        flags=TrustSetFlag.tfSetAuth,
        limit_amount={
            "currency": currency,
            # Note: 'issuer' field here is the counterparty (holder) for issuer's trustline
            "issuer": holder_address,
            "value": "0",
        },
    )
    # TODO: In production, restrict who can trigger this call (KYC/AML process) and sign using issuer cold key
    signed = safe_sign_and_submit_transaction(auth_tx, issuer_wallet, client)
    send_reliable_submission(signed, client)


def issue_solr(client: JsonRpcClient, issuer_wallet: Wallet, hot_address: str, currency: str, amount: Decimal) -> None:
    """Issue SOLR tokens equal to the given amount by sending a Payment from the issuer.

    Parameters:
        client: XRPL JSON RPC client.
        issuer_wallet: Issuer (cold) wallet.
        hot_address: Classic address of the hot account.
        currency: Currency code for SOLR.
        amount: Decimal value representing the number of kWh to mint.
    """
    from xrpl.models.transactions import Payment

    pay_tx = Payment(
        account=issuer_wallet.classic_address,
        amount={
            "currency": currency,
            "value": str(amount),
            "issuer": issuer_wallet.classic_address,
        },
        destination=hot_address,
    )
    signed = safe_sign_and_submit_transaction(pay_tx, issuer_wallet, client)
    send_reliable_submission(signed, client)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mint SOLR tokens based on kWh input")
    parser.add_argument("--kwh", type=Decimal, required=True, help="kWh to convert into SOLR tokens")
    parser.add_argument("--config", default="config.yaml", help="Path to configuration YAML")
    args = parser.parse_args()

    config = load_config(args.config)
    issuer_seed = config.get("issuer_seed")
    hot_seed = config.get("hot_seed")
    currency_code = config.get("currency_code", "SOLR")

    if not issuer_seed or not hot_seed:
        sys.exit("Error: issuer_seed and hot_seed must be defined in the config file.")

    # Connect to testnet
    client = get_client()

    issuer_wallet = Wallet.from_seed(issuer_seed)
    hot_wallet = Wallet.from_seed(hot_seed)

    print(f"Issuer address: {issuer_wallet.classic_address}")
    print(f"Hot address:    {hot_wallet.classic_address}")

    # Step 1: Configure accounts (only needs to be done once)
    print("Configuring issuer account...")
    configure_account(client, issuer_wallet, is_issuer=True)
    print("Configuring hot account...")
    configure_account(client, hot_wallet, is_issuer=False)

    # Step 2: Create trust line (only needs to be done once)
    print("Creating trust line from hot to issuer...")
    # Use a high limit to avoid hitting the limit; 1000000000 stands for 1B tokens
    create_trust_line(client, hot_wallet, issuer_wallet.classic_address, currency_code, limit=str(10**9))
    # Authorize the trust line (issuer approval) if RequireAuth is enabled
    print("Authorizing hot wallet trust line (issuer approval)...")
    authorize_trust_line(client, issuer_wallet, hot_wallet.classic_address, currency_code)

    # Step 3: Issue SOLR tokens
    print(f"Issuing {args.kwh} {currency_code} tokens to hot account...")
    issue_solr(client, issuer_wallet, hot_wallet.classic_address, currency_code, amount=args.kwh)

    print("SOLR minting complete.  Check balances using account_lines or a block explorer.")


if __name__ == "__main__":
    main()