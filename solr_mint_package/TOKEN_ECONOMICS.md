TOKEN ECONOMICS (Lite)
======================

Key assumptions
---------------
- Fungible token: `STN` (SOLR) represents 1 kWh measured and verified by oracle.
- NFT certificate: `SOLRAI` minted when 1,000 STN are burned; each SOLRAI represents a 1 MWh certificate.

Supply & Minting
----------------
- Issuer-controlled minting: Only authorized issuer accounts mint STN based on metered production.
- No predefined total cap in MVP; supply is driven by verifiable generation.

Burn & NFT issuance
-------------------
- Burn threshold: 1,000 STN required to mint 1 SOLRAI NFT.
- Burn address: Black-hole address (`rrrrrrrrrrrrrrrrrrrrrhoLvTp`) or issuer custody before minter validation.

Value accrual and fees
----------------------
- Retail price target (example): $90 per SOLRAI certificate.
- Transfer fee: 10% (8% marketplace + 2% resilience treasury) implemented via NFT `TransferFee` (basis points) — note XRPL forwards fee to issuer; off-chain split will be handled by marketplace logic.

Incentives & staking (optional)
-------------------------------
- Staking rewards: future program consideration to incentivize long-term locking of SOLRAI or STN.

Simple economic checks
----------------------
- Example: 1 MWh (1 SOLRAI) at $90 gross; marketplace operator fee 8% = $7.20, resilience treasury 2% = $1.80 (handled off-chain), net to seller ≈ $81.

Governance
----------
- Initial governance: SOLR Energy & Technology holds issuer and minter roles; governance model to be developed during pilot and token economics workshops.

*** End Patch
