SOLRAI - Investor Summary and Project README
=============================================

Overview
--------
SOLRAI is a compliance-first demonstration platform that mints a renewable-energy fungible token (STN, sometimes shown as SOLR) representing measured kWh, and issues SOLRAI NFT SRECs when quantity thresholds (e.g., 1,000 STN) are burned. The project uses the XRP Ledger (XRPL) Testnet and integrates wallet-first UX via Xumm/Xaman deep links.

Objective for Investors
-----------------------
- Demonstrate a technically robust, regulator-aligned path for converting verified renewable generation (smart-meter PoG) into on-chain, tradeable tokens and retired certificate NFTs (SRECs).
- Show an Xaman/Xumm-first buyer experience that minimizes friction for wallets and marketplace flows.
- Maintain issuer control to meet KYC/AML, governance, and Howey-aligned utility positioning.

Key Design Principles
---------------------
- Centralized issuance: Only authorized issuer accounts (operated by SOLR Energy & Technology, LLC) may mint STN tokens; additional issuer accounts can be added by governance.
- Verified participants: Trust lines require explicit issuer authorization (`RequireAuth`), preventing unverified accounts from holding STN.
- Designated NFT minter: NFTs are minted only by a controlled minter account after a validated 1,000 STN burn.
- Xumm/Xaman-first UX: Buyers sign and pay via Xumm deep links; server-side payload creation recommended for production.
- Auditable metadata: NFT metadata includes jurisdiction, program, vintage window, facility details, meter hash, oracle reference, and structured burn proof.

Architecture and Components
---------------------------
- `mint_solr_token.py` — Trustline creation, authoritative issuance flow, and trustline authorization by issuer.
- `burn_and_mint_solrai_nft.py` — Burns 1,000 STN and creates SOLRAI NFT metadata (base64-embedded image), minted by a designated minter.
- `solrai_nft_flow.py` — End-to-end demo flow: configure accounts, issue STN, transfer to owner, burn, mint (minter), and transfer NFT to owner.
- `generate_rec_image.py` — Renders a regulator-style certificate image (REC) embedding screenshot, compliance fields, and QR codes for burn proof and Xumm deeplink.
- `xumm_client.py` — Minimal Xumm Platform wrapper for secure payload creation (server-side).
- `xumm_server.py` — Flask skeleton to host payload creation endpoints for payments and offer acceptance (recommended for production).
- `xumm_offer_helper.py` and `nft_market.py` — Helpers for creating and accepting NFToken sell offers
- `requirements.txt` — Pinned dependencies for a test/dev environment.

How it Works (happy path)
-------------------------
1. Issuer creates a token `STN` and configures `RequireAuth` on their account.
2. A site owner (system owner) proves generation to an oracle and requests STN issuance.
3. Issuer authorizes the owner’s trust line and issues STN to the owner via payment.
4. When 1,000 STN are ready, the owner burns them to the black-hole address.
5. The designated NFT minter mints a SOLRAI NFT with embedded metadata and the burn proof.
6. The minter transfers the NFT to the owner via a controlled zero-price offer that the owner accepts.
7. A marketplace flow: owner lists NFT for sale (NFTokenCreateOffer), buyer uses Xumm/Xaman deep link to pay, buyer accepts or owner fulfils transfer.

Running the Demo (testnet)
--------------------------
1. Install Python and create a virtualenv in the repo root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `config_example.yaml` -> `config.yaml` and add your test seeds and addresses. DO NOT commit secrets.

3. Generate a REC certificate image (optional):

```bash
python generate_rec_image.py --kwh 1000 --burn-tx-hash <burn_hash>
```

4. Run the end-to-end demo flow (fill `config.yaml` first):

```bash
python solrai_nft_flow.py --kwh 1000 --price_xrp_drops 270000000
```

5. Use `nft_market.py` and `xumm_server.py` to create offers and payloads for buyers.

Compliance & Howey Alignment
----------------------------
- Centralized issuance and RequireAuth are used to keep token distribution under program control (reduces securities risk under the Howey framework by emphasizing utility and controlled issuance).
- NFTs are certificates tied to a verifiable burn event and include extensive metadata for audit.
- This repo is a technical demonstration and does not constitute legal compliance—engage counsel to finalize program rules, user terms, and KYC/AML processes.

Investor Deliverables (MVP)
---------------------------
- Testnet working flow: issue STN, authorized trustlines, burn 1,000 STN, mint SOLRAI NFT, show REC certificate, support Xumm buyer flows.
- UI/UX: simple web page or CLI to invite onboarding, start KYC, and create offers (future work).
- Ops: documented secure key handling, minimal Flask server for payloads, and scripts to transition to dev/mainnet.

Roadmap & Next Steps
--------------------
- Implement server-side Xumm payload creation with authentication and offer verification (recommended next step).
- Add signed metadata (JWS) for stronger attestation of mint events and oracle signatures.
- Build a lightweight dApp/xApp to walk owners through KYC/registration, issue requests, and NFT listing.
- Integrate an off-chain marketplace or smart contract gateway to automate the ESG fee split.

Risks & Mitigations
-------------------
- Legal/Regulatory: Engage counsel. The repo is designed to reduce securities risk but legal review is required.
- Key management: Use HSMs or cold wallets for issuer/minter keys.
- UX: Wallet fragmentation—Xumm/Xaman-first UX helps, but plan fallbacks for other wallets.

Contact & Contributors
----------------------
SOLR Energy & Technology, LLC — project maintainers


---


