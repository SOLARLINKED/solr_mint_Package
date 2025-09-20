SOLRAI – Investor Summary and Project README
Vision

SOLRAI transforms renewable energy production into instant, auditable, blockchain-native energy credits.
Built on the XRP Ledger (XRPL), SOLRAI enables solar farms, utilities, and system owners to convert each kilowatt-hour (kWh) of verified generation into a token, and every megawatt-hour (MWh) into a serialized SOLRAI NFT credit—ready to sell directly to corporate buyers.

The Problem

Slow & costly crediting: Today’s SREC/REC issuance is slow, fragmented, and often centralized, creating delays and fees for producers.

Opaque markets: Corporates demand trustworthy credits to meet ESG commitments, but struggle to verify provenance and compliance.

Under-monetized producers: Solar farms and distributed systems often receive less than fair value for their output due to middlemen and inefficient registries.

The SOLRAI Solution

STN/SOLR Tokens – 1 token = 1 kWh measured. Minted directly from smart-meter data via oracles.

Burn-to-Mint Model – Retire 1,000 SOLR → mint a SOLRAI NFT = 1 MWh, carrying jurisdiction, facility ID, vintage, and meter hash.

Direct Corporate Access – NFTs can be listed on-ledger and purchased instantly in RLUSD or XRP via Xaman/Xumm, creating a liquid marketplace for energy credits.

Compliance-First – Controlled issuance, RequireAuth trustlines, embedded metadata, and legal alignment with REC/SREC structures.

Market Opportunity

The global REC market exceeds $14 billion, growing double digits annually.

U.S. states like New Jersey price SRECs at $85–$300/MWh.

Emerging markets in Puerto Rico, Dominican Republic, and Latin America are seeking faster, cheaper credit frameworks.

SOLRAI is positioned to become the bridge between renewable producers and ESG-driven corporate buyers, with the XRP Ledger delivering speed, low cost, and carbon neutrality.

Business Model

Minting fees: 1–3% per NFT issued.

Marketplace fees: Small % per trade on XRPL.

Enterprise partnerships: White-label solutions for solar farms, utilities, and corporates.

Why XRPL, Why Us

XRPL-native: Fast, cheap, energy-efficient ledger with live NFT and AMM standards.

Wallet-first UX: One-click onboarding via Xumm/Xaman.

Experienced team: NABCEP-certified solar professionals and blockchain architects with deep ties to PR/DR energy transition.

Overview (Technical)

SOLRAI is a compliance-first demonstration platform that mints a renewable-energy fungible token (STN, sometimes shown as SOLR) representing measured kWh, and issues SOLRAI NFT SRECs when quantity thresholds (e.g., 1,000 STN) are burned. The project uses the XRP Ledger (XRPL) Testnet and integrates wallet-first UX via Xumm/Xaman deep links.

Objective for Repo

Demonstrate a technically robust, regulator-aligned path for converting verified renewable generation (smart-meter PoG) into on-chain, tradeable tokens and retired certificate NFTs (SRECs).

Show an Xaman/Xumm-first buyer experience that minimizes friction for wallets and marketplace flows.

Maintain issuer control to meet KYC/AML, governance, and Howey-aligned utility positioning.

Key Design Principles

Centralized issuance: Only authorized issuer accounts (operated by SOLR Energy & Technology, LLC) may mint STN tokens; additional issuer accounts can be added by governance.

Verified participants: Trust lines require explicit issuer authorization (RequireAuth), preventing unverified accounts from holding STN.

Designated NFT minter: NFTs are minted only by a controlled minter account after a validated 1,000 STN burn.

Xumm/Xaman-first UX: Buyers sign and pay via Xumm deep links; server-side payload creation recommended for production.

Auditable metadata: NFT metadata includes jurisdiction, program, vintage window, facility details, meter hash, oracle reference, and structured burn proof.

Architecture and Components

mint_solr_token.py — Trustline creation, authoritative issuance flow, and trustline authorization by issuer.

burn_and_mint_solrai_nft.py — Burns 1,000 STN and creates SOLRAI NFT metadata (base64-embedded image), minted by a designated minter.

solrai_nft_flow.py — End-to-end demo flow: configure accounts, issue STN, transfer to owner, burn, mint (minter), and transfer NFT to owner.

generate_rec_image.py — Renders a regulator-style certificate image (REC) embedding screenshot, compliance fields, and QR codes for burn proof and Xumm deeplink.

xumm_client.py — Minimal Xumm Platform wrapper for secure payload creation (server-side).

xumm_server.py — Flask skeleton to host payload creation endpoints for payments and offer acceptance (recommended for production).

xumm_offer_helper.py and nft_market.py — Helpers for creating and accepting NFToken sell offers.

requirements.txt — Pinned dependencies for a test/dev environment.

How it Works (Happy Path)

Issuer creates a token STN and configures RequireAuth on their account.

A site owner (system owner) proves generation to an oracle and requests STN issuance.

Issuer authorizes the owner’s trust line and issues STN to the owner via payment.

When 1,000 STN are ready, the owner burns them to the black-hole address.

The designated NFT minter mints a SOLRAI NFT with embedded metadata and the burn proof.

The minter transfers the NFT to the owner via a controlled zero-price offer that the owner accepts.

A marketplace flow: owner lists NFT for sale (NFTokenCreateOffer), buyer uses Xumm/Xaman deep link to pay, buyer accepts or owner fulfils transfer.

Running the Demo (Testnet)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


Copy config_example.yaml -> config.yaml and add your test seeds and addresses. DO NOT commit secrets.

Generate a REC certificate image (optional):

python generate_rec_image.py --kwh 1000 --burn-tx-hash <burn_hash>


Run the end-to-end demo flow (fill config.yaml first):

python solrai_nft_flow.py --kwh 1000 --price_xrp_drops 270000000


Use nft_market.py and xumm_server.py to create offers and payloads for buyers.

Compliance & Howey Alignment

Centralized issuance and RequireAuth are used to keep token distribution under program control (reduces securities risk under the Howey framework by emphasizing utility and controlled issuance).

NFTs are certificates tied to a verifiable burn event and include extensive metadata for audit.

This repo is a technical demonstration and does not constitute legal compliance—engage counsel to finalize program rules, user terms, and KYC/AML processes.

Investor Deliverables (MVP)

Testnet working flow: issue STN, authorized trustlines, burn 1,000 STN, mint SOLRAI NFT, show REC certificate, support Xumm buyer flows.

UI/UX: simple web page or CLI to invite onboarding, start KYC, and create offers (future work).

Ops: documented secure key handling, minimal Flask server for payloads, and scripts to transition to dev/mainnet.

Roadmap & Next Steps

Implement server-side Xumm payload creation with authentication and offer verification.

Add signed metadata (JWS) for stronger attestation of mint events and oracle signatures.

Build a lightweight dApp/xApp to walk owners through KYC/registration, issue requests, and NFT listing.

Integrate an off-chain marketplace or smart contract gateway to automate the ESG fee split.

Risks & Mitigations

Legal/Regulatory: Engage counsel. Repo is designed to reduce securities risk but legal review is required.

Key management: Use HSMs or cold wallets for issuer/minter keys.

UX: Wallet fragmentation—Xumm/Xaman-first UX helps, but plan fallbacks for other wallets.

Contact & Contributors

SOLR Energy & Technology, LLC — project maintainers
