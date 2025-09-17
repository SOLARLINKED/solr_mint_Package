# SOLR/SOLRAI Minting & Payment Walk‑Through

This guide outlines how to mint SOLR fungible tokens from renewable‑energy data, burn those tokens to create SOLRAI NFT‑SRECs and send a demonstration XRP payment on the XRP Ledger (XRPL) Testnet.  It follows the XRPL standards for tokens and NFTs and includes Python scripts that use the `xrpl` library.  **Do not run the scripts on mainnet with real funds until you understand the risks and adjust the configuration.**

## Overview of the SOLR Model

1. **Proof‑of‑Generation (PoG) token (SOLR).**  Smart‑meter data is signed by an oracle and every 1 kWh becomes a fungible SOLR token.  Fungible tokens on XRPL are issued via trust lines and payments.  The XRPL documentation explains that anyone can issue tokens by creating a trust line and sending payments between accounts【46225318886278†L152-L161】.
2. **Certificate issuance (SOLRAI NFT‑SREC).**  When 1 000 SOLR are accumulated they are burned to mint a non‑fungible token representing a Solar Renewable Energy Certificate (SREC).  The NFT includes metadata fields such as jurisdiction, program, vintage, meter hash and oracle references.  The NFT’s on‑chain `retire()` function is realised by the `NFTokenBurn` transaction (the NFT owner or issuer can burn it).  The `NFTokenMint` transaction supports flags like `tfTransferable` and `tfBurnable`【849498915099590†L340-L356】 so you can control whether the NFT can be transferred and whether the issuer can destroy it.  The URI field stores a link (or data URI) pointing to the metadata【849498915099590†L314-L321】.
3. **Fee structure.**  When a SOLRAI is sold, a 10 % fee (8 % marketplace + 2 % resilience treasury) should be taken.  XRPL NFTs support a `TransferFee` field in basis points (0–50 000 ≃ 0 %–50 %), which returns a percentage of the sale to the issuer【309617549307198†L183-L195】.  Since XRPL cannot split fees between multiple recipients natively, a custom off‑chain sale or separate payment may be required to route the 2 % ESG share.
4. **Demo payment.**  A simple payment of 1 XRP (testnet) is used for demonstration.  Payment transactions transfer value from one account to another and require an `Account` (sender), `Destination` (recipient) and `Amount` field【683224786263462†L258-L304】.  For XRP transfers, the `Amount` is a string representing the number of drops (1 XRP = 1 000 000 drops).

The following sections describe how to perform each step, followed by scripts that automate the process.

## 1. Prepare XRPL Accounts

### 1.1 Create and fund testnet accounts

You need the following funded XRPL accounts:

* **Issuer (cold) account(s)** – Controlled by SOLR Energy & Technology, LLC. These are the only accounts authorized to issue the SOLR/STN token and to set token policy. Treat as cold wallets.
* **Operational (hot) account** – Operated by SOLR for day‑to‑day distributions and flows.
* **Designated NFT minter** – A controlled account that mints SOLRAI NFTs after a validated burn event. End‑users never mint NFTs directly.

You can obtain testnet accounts from the [XRPL Testnet faucet](https://testnet.xrpl.org/faucet). Each account must hold enough XRP to meet the account reserve and trust‑line reserves (currently 10 XRP for the account plus 2 XRP per object such as trust lines or NFTs).  Save each account’s **secret seed** securely; the scripts require the seeds to sign transactions.

### 1.2 Issuer controls (RequireAuth + DefaultRipple)

Issuer accounts are configured to:

* **RequireAuth** – Only authorized trust lines can hold SOLR. This enforces KYC/AML and verified‑system gating.
* **Default Ripple** – Optional; enables liquidity via rippling if desired.
* **Disallow XRP** and **Require Destination Tags** – Operational hygiene.

Trust lines are created by users but must be explicitly authorized by the issuer before they can hold SOLR. This enforces that only verified participants can receive tokens.

### 1.3 Operational and minter settings

For the hot and designated minter accounts, enable **Disallow XRP** and **Require Destination Tags**, and set your domain for verification. End‑users do not mint tokens or NFTs; minting is centralized via the designated minter.

## 1.4 Governance, Issuance, and Compliance (Howey‑aligned)

To keep the model aligned with Howey considerations (see Cornell summary: https://www.law.cornell.edu/wex/howey_test and the included “SOLR_Howey_Test_Explainer.pdf”), this demo implements:

* **Centralized issuance** – Only SOLR Energy & Technology, LLC issuer accounts can issue SOLR/STN. Users cannot create or issue their own tokens.
* **KYC/AML gating** – Issuer trust lines use `RequireAuth`. Only verified, state‑registered systems are authorized to hold SOLR/STN.
* **NFTs minted by a designated minter** – The SOLRAI NFT is minted by a controlled minter account after validation of a 1,000 STN burn. Users do not mint NFTs directly.
* **Utility framing** – SOLR/STN is intended as a PoG unit for measured kWh and SREC creation, not a general investment instrument. The NFT represents a certificate tied to renewable generation and can be retired (burned).
* **Disclaimers** – This is a technical demo, not legal advice. Engage counsel to validate the final model for your jurisdiction and program.

## 2. Minting SOLR Tokens

### 2.1 Create a trust line

Before an account can hold a token, it must create a trust line to the issuer.  A trust line is a bidirectional accounting relationship that specifies a limit and settings【46225318886278†L152-L183】.  Use a `TrustSet` transaction from the hot account to the issuer with:

* **Limit** – maximum number of SOLR tokens the hot account is willing to hold (e.g., a large number).
* **Currency code** – choose a code up to 160 bits (often a 3‑character code such as `SOLR` or a 20‑byte hex string).  The code must be unique per issuer.

After the trust line is created, the issuer can send SOLR tokens.

### 2.2 Issue tokens

To mint SOLR tokens, the issuer (cold account) sends a `Payment` transaction to the hot account.  When the `Amount` field is an object containing the currency code, value and issuer, this payment creates new tokens【157694587131259†L714-L729】.  The `Payment` transaction should include:

* **Account** – issuer’s address.
* **Destination** – hot account’s address.
* **Amount** – an object: `{ "currency": "SOLR", "value": "<kWh>", "issuer": "<issuer_address>" }`.

The value is the number of kilowatt‑hours measured by the oracle.  For example, 8.19 kWh yields 8.19 SOLR.  Confirm the transaction is validated before proceeding.

## 3. Burning SOLR and Minting SOLRAI NFT‑SRECs

### 3.1 Burn 1 000 SOLR

To reduce the supply and prevent double counting, 1 000 SOLR tokens must be burned.  XRPL does not provide a direct burn transaction for fungible tokens.  A common pattern is to send the tokens either back to the issuer or to a well‑known “black‑hole” address (e.g., `rrrrrrrrrrrrrrrrrrrrrhoLvTp`) from which tokens cannot be recovered.  The script in this package sends 1 000 SOLR to `rrrrrrrrrrrrrrrrrrrrrhoLvTp`, effectively removing them from circulation.

### 3.2 Prepare NFT metadata

SOLRAI NFTs carry compliance metadata and proof of solar generation.  The `NFTokenMint` transaction has a `URI` field where you can place a link or a data URI containing a JSON document【849498915099590†L314-L321】.  The metadata should include:

* **Jurisdiction/program/vintage** – regulatory details for the SREC.
* **Meter hash & oracle references** – pointer to the signed smart‑meter data (PoG proof).  The included screenshot of your SolisCloud dashboard can be embedded as an image for demonstration.
* **Burn proof** – a record of the 1 000 SOLR burn transaction hash.
* **Attributes** – any additional fields required by your compliance framework.

In the example script, metadata is assembled as a JSON object and encoded into a base64 data URI.  The `NFTokenMint` transaction requires the `URI` to be a hex string【849498915099590†L314-L321】, so the data URI is hex‑encoded before signing.

### 3.3 Mint the NFT (Designated Minter)

Use an `NFTokenMint` transaction from the designated minter account to create the SOLRAI NFT. Important fields:

* **Account** – the minter’s address (designated minter).
* **URI** – hex‑encoded data URI pointing to the metadata.
* **Flags** – set to `tfTransferable` (8) so the NFT can be transferred, and optionally `tfBurnable` (1) if you want the issuer to be able to burn it【849498915099590†L340-L356】.
* **TransferFee** – set to `10000` (10.000 %) to implement the clean fee stack (8 % marketplace + 2 % resilience treasury)【309617549307198†L183-L195】.  Note that XRPL forwards the entire fee to the issuer; splitting it between multiple recipients requires off‑chain logic.
* **NFTokenTaxon** – an integer used to classify NFTs; set to `0` if unused.

After submitting, wait for validation and note the returned `NFTokenID`, which uniquely identifies the NFT. The NFT can be minted to issuer custody or directly to the system owner depending on your workflow. To retire the SREC, call `NFTokenBurn` from the NFT owner’s account. (Burning is the on‑chain retire() function.)

## 4. Demo Payment: Sending 1 XRP

A direct XRP payment uses a `Payment` transaction with the `Amount` field as a string of drops (1 XRP = 1 000 000 drops)【683224786263462†L258-L304】.  The script `send_payment.py` constructs and submits a payment.  Specify:

* **Account** – sender’s address.
* **Destination** – recipient’s address.
* **Amount** – `"1000000"` for 1 XRP.

You can include a `DestinationTag` if your counterparty requires it.

## 5. Scripts in this Package

The following Python scripts automate the process using the `xrpl` library.  **Install dependencies** with `pip install xrpl PyYAML python-dotenv`.

### 5.1 `config_example.yaml`

Template YAML file where you can store your account seeds and addresses:

```yaml
issuer_seed: "YOUR_ISSUER_SEED"
hot_seed:    "YOUR_HOT_SEED"
esg_treasury: "rExampleESGAddress"  # address to receive ESG share (for reference)
marketplace:  "rExampleMarketAddress"  # marketplace address (for reference)
currency_code: "SOLR"       # 3‑letter or 20‑byte currency code
jurisdiction: "US-NJ"
program: "NJ-SREC"
vintage: "2025"
meter_hash: "<hash-of-meter-data>"
oracle_reference: "<URL-or-hash-of-signed-data>"
```

Rename this file to `config.yaml` and fill in your values before running the scripts.  Never commit secrets to public repositories.

### 5.2 `mint_solr_token.py`

1. **configure_accounts()** – connects to the XRPL testnet and sends `AccountSet` transactions. Issuer is configured with `RequireAuth` and (optionally) `DefaultRipple`.
2. **create_trust_line()** – creates a trust line from the hot account to the issuer.
3. **authorize_trust_line()** – issuer explicitly authorizes the hot account’s trust line (enforcing KYC/AML).
4. **issue_solr()** – issues SOLR/STN equal to measured kWh by sending a `Payment` from issuer to hot【157694587131259†L714-L729】.

### 5.3 `burn_and_mint_solrai_nft.py`

1. **burn_solr()** – system owner burns 1,000 STN (to black‑hole or issuer) to reduce supply.
2. **create_metadata()** – builds a JSON metadata object including regulatory fields, facility details, vintage window, PoG proof, and burn proof; embeds the screenshot as a base64 data URI.
3. **mint_solrai_nft()** – executed by the designated minter account only, with metadata URI, flags, transfer fee and taxon.

### 5.4 `send_payment.py`

Sends 1 XRP from a specified account to a recipient.  Use this to demonstrate payment functionality or to distribute marketplace/ESG fees.  The script builds a `Payment` transaction with `Amount` set to `"1000000"` drops.

## 6. Using the Scripts

1. **Install dependencies**:

   ```bash
   pip install xrpl PyYAML python-dotenv
   ```

2. **Prepare `config.yaml`** by copying `config_example.yaml` and filling in your seeds, addresses and metadata values.

3. **Mint SOLR tokens**:

   ```bash
   python mint_solr_token.py --kwh 8.19
   ```

   This configures accounts (if not already done), creates the trust line and sends 8.19 SOLR from the issuer to the hot account.

4. **Burn SOLR and mint SOLRAI**:

   ```bash
   python burn_and_mint_solrai_nft.py --burn-tx-hash <hash-of-burn-tx>
   ```

   This burns 1 000 SOLR, composes the metadata (embedding the SolisCloud screenshot), and mints the SOLRAI NFT.

5. **Send a test payment**:

   ```bash
   python send_payment.py --to rDestinationAddress --drops 1000000
   ```

   Sends 1 XRP (1 000 000 drops) to the given address.

Always confirm transaction hashes on the [XRPL Testnet explorer](https://testnet.xrpl.org/).  If you encounter sequence or reserve errors, wait for prior transactions to finalize and ensure each account has sufficient XRP to cover reserves and fees.

## 7. NFT Proof Image

For demonstration, this package includes a screenshot of your SolisCloud plant dashboard (`IMG_A6FBCF8F-9700-4089-ADB0-5C914EF43766.jpeg`).  The metadata script embeds this image directly into the NFT as a base64 data URI.  For production, you can replace this with a signed PDF or image that cryptographically proves generation.

### 7.1 Generate a REC Certificate Image (PNG/JPEG)

Use the helper script `generate_rec_image.py` to render a clean, shareable REC certificate image with mock but valid-looking data, QR codes for burn-proof and pay-to-owner, and your screenshot embedded.

1. Install dependencies (if not already):

   ```bash
   pip install Pillow qrcode[pil] PyYAML
   ```

2. Generate the image (writes `SOLRAI_REC_SAMPLE.png` by default):

   ```bash
   python generate_rec_image.py \
     --kwh 1000 \
     --burn-tx-hash BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB \
     --output SOLRAI_REC_SAMPLE.png
   ```

   Flags:
   - `--image` to point to a different screenshot (defaults to `image_path` in `config.yaml`).
   - `--nft-id` to include an `NFTokenID` label if you already minted.

What’s included:
   - Left panel: Issuer, Hot, System Owner, Buyer addresses (shortened), jurisdiction/program/vintage.
   - Right panel: Production kWh, STN minted, 1,000 STN burned, price in XRP drops.
   - Center panel: Embedded screenshot.
   - Bottom row: QR to XRPL Testnet explorer for the burn tx, QR for a “pay owner” JSON payload (XRP drops).

Tip: You can attach the generated PNG to the NFT metadata as an alternate preview, while the JSON metadata (see Section 5.3) remains the canonical on-chain reference.

## 8. Further Considerations

* **Compliance** – Real‑world SREC programs have strict compliance and auditing requirements.  Ensure that your oracle delivers verifiable data and that regulators accept NFTs as proof.
* **Fee distribution** – XRPL’s transfer fee sends all proceeds to the issuer.  To split a fee between the marketplace and resilience treasury, handle the sale off‑chain or implement logic in your marketplace application to forward the appropriate shares.
* **Security** – Protect your seed phrases.  Use environment variables or secure vaults to provide them to the scripts.  Never hard‑code secrets into code or share them publicly.

With these scripts and instructions you can demonstrate the SOLR minting process, burn tokens to mint a jurisdiction‑tagged SOLRAI NFT and perform a simple XRP payment on testnet.  Adjust parameters for production deployment and consult the XRPL documentation for additional features and best practices.

## 9. Xaman‑First NFT Sale Flow (Compliance‑friendly)

This repository is set up to prioritize wallet UX with Xaman and add compliance‑style metadata.

1. Create a sell offer for your newly minted NFT (owner wallet by default):

   ```bash
   python nft_market.py create-sell --nft-id <NFTokenID> --amount-drops <price_drops>
   ```

   Capture the offer index from the transaction metadata.

2. Create a Xaman deeplink for an XRP payment (or for accepting an offer using a payload you host). For production, create payloads via the Xumm API and share the UUID sign URL.

   ```bash
   python xaman_payloads.py --destination rNeTREnTe9kXUoGqS2LH4kL8uQVgZzCH5a --drops 270000000
   ```

   This prints a URL you can share or embed as a QR. To embed into the REC image:

   ```bash
   python generate_rec_image.py --xumm-url "<printed-url>" --burn-tx-hash <burn_tx_hash> --kwh 1000
   ```

   Xumm API & environment
   -----------------------

   To use the Xumm Platform API to create payloads (recommended for production), set the following environment variables in your shell or CI environment:

   ```bash
   export XUMM_API_KEY="<your_xumm_api_key>"
   export XUMM_API_SECRET="<your_xumm_api_secret>"
   ```

   The helper `xumm_client.py` will call the platform endpoint and return the canonical `https://xumm.app/sign/<uuid>` URL which you can embed into the REC certificate QR. For local demo without API keys, the code falls back to a client-side encoded payload link for convenience.

   XApps / JWT note
   -----------------
   If you build an xApp or integrate via the Xumm XApp JWT endpoints, follow the Xumm docs for JWT creation and redirection from your app. The current demo focuses on creating signable payloads and deeplinks for wallet-first UX.

   ### Running the Xumm payload server (demo)

   1. Copy `.env.example` to `.env` and set your `XUMM_API_KEY` and `XUMM_API_SECRET`.

   2. Install Flask and the requirements:

   ```bash
   pip install -r requirements.txt
   ```

   3. Start the Flask server (test/dev only):

   ```bash
   export FLASK_APP=xumm_server.py
   flask run
   ```

   4. POST to the server to create payloads (example using curl):

   ```bash
   curl -X POST -H "Content-Type: application/json" \
      -d '{"destination":"rNeTREnTe9kXUoGqS2LH4kL8uQVgZzCH5a","drops":"270000000"}' \
      http://127.0.0.1:5000/payload/payment
   ```

   Security note: This server is a demo. In production, run behind HTTPS, add authentication, rate limiting, and host the Xumm keys in a secure vault (not in environment variables). Avoid exposing offer creation endpoints without authorization.

3. After buyer pays, the owner can transfer NFT or the buyer can accept the sell offer:

   ```bash
   python nft_market.py accept-sell --offer-index <OFFER_INDEX>
   ```

Compliance metadata: `burn_and_mint_solrai_nft.py` packs jurisdiction, program, vintage window, facility info, grid region, technology, meter hash, oracle link, a structured burn proof, and attributes including transfer fee and flags. The `generate_rec_image.py` renders these fields on a certificate image, suitable for presentations and regulator‑friendly summaries.