MODEL — SOLR → SOLRAI (High-level)
====================================

Overview
--------
This describes the simple, compliant flow from renewable generation to a consumable certificate.

Actors
------
- Issuer (SOLR Energy & Technology, LLC): only accounts authorized to issue STN/SOLR.
- System Owner: the site owner/operator who produces kWh and, after verification, receives STN.
- Designated NFT Minter: a controlled account that mints SOLRAI NFTs after validated burns.
- Buyer / Marketplace: a purchaser who acquires SOLRAI NFTs and may retire them (burn) to claim the certificate.

Flow
----
1. Measurement & Oracle: A metered generation event is signed by a trusted oracle.
2. Issue STN: Issuer issues STN tokens (1 STN = 1 kWh) to verified system owner after trustline authorization.
3. Accumulate & Burn: When system owner accumulates 1,000 STN, they burn them to prove retirement.
4. Mint NFT: Designated NFT minter mints a SOLRAI NFT embedding the burn proof and regulatory metadata.
5. Transfer / Sell: NFT owner lists or transfers the NFT; buyers pay via Xumm/Xaman deep link or other channels.
6. Retirement: Buyer or owner can burn the NFT (NFTokenBurn) to retire the SREC on-chain.

Compliance Notes
----------------
- All trust lines require issuer authorization (KYC/AML gating).
- NFTs are minted centrally by controlled minter account only after a verifiable burn.
- Metadata includes meter hash, oracle reference, jurisdiction, and vintage to ensure auditability.

*** End Patch
