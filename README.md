SOLR Proof-of-Generation Standard (PoG v1)

Canonical rule:

1 kWh of verified solar generation = 1.000 SOLR (up to 3 decimal places).

This section defines how raw meter data becomes on-chain, auditable SOLR tokens, how those tokens convert into compliance certificates (SOLRAI NFTs), and how lifecycle, security, and settlement are enforced.

1) Deterministic Issuance

Precision & rounding

Unit: kWh (permits 0.001 kWh resolution = 1 Wh).

Rounding: banker’s rounding at the interval level; daily/period totals are sums of rounded intervals.

Negative or zero intervals mint 0. Estimated intervals are flagged est:true and MAY be quarantined by policy.

Measurement basis

Declare for each site whether issuance uses gross PV output, net exported, or net of losses.

Put the basis into both the attestation payload and the SOLR issuance record.

Deterministic formula

mintable_kWh(period) =
  Σ round_to_0.001_kWh(interval_kWh[i]) over all attested intervals in period
  − already_minted_kWh_for(period, site_id)


Idempotency

Every issuance request carries a globally unique issuance_id (UUIDv7).

The issuance transaction MUST record issuance_id on-chain (XRPL Memo).

Retrying the same issuance_id MUST NOT mint extra SOLR.

Recommended XRPL memo (hex-encoded JSON)

{
  "std": "SOLR-PoG-v1",
  "site_id": "SITE-PR-MAO-0001",
  "period": "2025-08-01/2025-08-31",
  "issuance_id": "018f1a48-5f51-7b8b-a0f0-91f1f2b5df82",
  "kwh": 29423.000,
  "basis": "net_exported",
  "oracle_claim_hash": "bafkreihq... (multihash/IPFS CID)",
  "jurisdiction": "PR-IREC"
}

2) Metering Attestation Spec (MAS v1)

Purpose: Convert raw meter readings into a signed, tamper-evident claim that authorizes SOLR minting.

Payload (canonical JSON, UTF-8, RFC 3339 timestamps)

{
  "version": "MAS-1.0",
  "site_id": "SITE-PR-MAO-0001",
  "meter_id": "MTR-12345678",
  "timezone": "America/Puerto_Rico",
  "window_start": "2025-08-01T00:00:00-04:00",
  "window_end": "2025-08-31T23:59:59-04:00",
  "interval_minutes": 15,
  "basis": "net_exported",           // enum: gross | net_exported | net_of_losses
  "jurisdiction": "PR-IREC",
  "firmware_rev": "v3.2.1",
  "location": { "lat": 19.551, "lon": -71.082, "geofence_km": 0.2 },
  "readings": [
    { "ts": "2025-08-01T00:15:00-04:00", "kwh": 0.000, "est": false },
    { "ts": "2025-08-01T00:30:00-04:00", "kwh": 0.000, "est": false }
    // ... 15-min series
  ],
  "quality": { "missing_intervals": 0, "inverter_ok": true },
  "issuance_id": "018f1a48-5f51-7b8b-a0f0-91f1f2b5df82",
  "raw_export_hash": "sha256:0b9c...e7a"
}


Signature (JWS detached)

Header example:

{"alg":"EdDSA","kid":"oracle-key-2025Q3","typ":"JWT","b64":true,"crit":["b64"]}


Sign the exact canonical JSON bytes.

Publish oracle-key-2025Q3 and rotation policy in your security doc.

On-chain reference

Store oracle_claim_hash (IPFS/Arweave CID) and issuance_id in the XRPL memo.

Keep a public attestation index (site_id → list of claim CIDs).

3) Lifecycle State Machine
flowchart LR
  A[Measured (MAS)] -->|mint SOLR with issuance_id| B(Minted SOLR)
  B -->|aggregate exact 1,000.000 SOLR by site/vintage| C[Aggregated Lot]
  C -->|burn 1,000.000 SOLR; include proofs| D{Validator Checks}
  D -->|pass| E(Mint SOLRAI NFT)
  D -->|fail| F[Reject + Log]
  E -->|trade/transfer| E
  E -->|retire| G[Retired]


Guards

Cannot mint SOLRAI unless:

Burn tx equals 1,000.000 SOLR exactly,

Burn set maps to specific issuance_id(s) for a single site/vintage,

Merkle proof binds NFT to those issuance claims and burn tx.

4) JSON Schemas

SOLR Issuance Record (SOLR-Record.schema.json)

{
  "$id": "https://solr.energy/schemas/SOLR-Record.schema.json",
  "type": "object",
  "required": ["std","site_id","period","issuance_id","kwh","basis","oracle_claim_cid","jurisdiction"],
  "properties": {
    "std": { "const": "SOLR-PoG-v1" },
    "site_id": { "type": "string" },
    "period": { "type": "string", "pattern": "^[0-9T:\\-+:/]+/[0-9T:\\-+:/]+$" },
    "issuance_id": { "type": "string", "format": "uuid" },
    "kwh": { "type": "number" },
    "precision": { "type": "integer", "enum": [3] },
    "basis": { "type": "string", "enum": ["gross","net_exported","net_of_losses"] },
    "oracle_claim_cid": { "type": "string" },
    "jurisdiction": { "type": "string" },
    "readings_merkle_root": { "type": "string" }
  }
}


SOLRAI NFT Metadata (SOLRAI-NFT.schema.json)

{
  "$id": "https://solr.energy/schemas/SOLRAI-NFT.schema.json",
  "type": "object",
  "required": ["std","site_id","vintage","jurisdiction","unit_kwh","burn_tx","issuance_ids_root","lot_id"],
  "properties": {
    "std": { "const": "SOLRAI-PoG-v1" },
    "site_id": { "type": "string" },
    "vintage": { "type": "string", "pattern": "^[0-9]{4}-[0-9]{2}$" },
    "jurisdiction": { "type": "string" },
    "unit_kwh": { "type": "number", "const": 1000.000 },
    "lot_id": { "type": "string" },
    "burn_tx": { "type": "string" },                     // XRPL hash
    "issuance_ids_root": { "type": "string" },           // Merkle root over issuance_ids included
    "oracle_claims_root": { "type": "string" },          // Merkle root over claim CIDs
    "basis": { "type": "string", "enum": ["gross","net_exported","net_of_losses"] },
    "proofs_cid": { "type": "string" }                   // bundle with membership proofs
  }
}

5) Jurisdiction Profiles (template)
Code	Registry / Program	Vintage Rule	Basis Requirement	Notes
PR-IREC	IREC Puerto Rico	Calendar month (UTC offset)	Net exported	Example placeholder
DO-…	(TBD)	(TBD)	(TBD)	(TBD)
US-PJM	PJM GATS	Calendar month	Net exported	(TBD)

Include the profile code in both the attestation and issuance/NFT metadata.

Validator MUST enforce profile-specific rules before minting SOLRAI.

6) Proof Bundling

Goal: Tie each SOLRAI NFT to the exact SOLR that was burned and to the underlying attestations.

Build a Merkle tree over the set of issuance_id values included in the 1,000 SOLR burn.

Build a Merkle tree over the set of attestation CIDs (oracle_claim_cid).

Store both roots in the NFT metadata + publish a proofs_cid bundle (JSON with membership proofs for auditors).

7) Storage & Persistence Policy

Publish all JSON artifacts (attestations, issuance records, proof bundles) to IPFS or Arweave; pin to multiple providers.

Reference CIDs in XRPL memos / NFT URIs.

Keep a public index for discoverability: https://data.solr.energy/{site_id}/index.json.

8) Fee Routing (Market Mechanics)

XRPL TransferFee pays the issuer only. To implement 8% marketplace + 2% resilience shares on secondary sales:

Use an escrowed marketplace (or post-trade settlement job) that splits proceeds: seller 90% / marketplace 8% / resilience 2%.

Publish daily settlement reports with tx hashes and amounts.

Define primary vs. secondary sale rules and display them in marketplace UI.

9) Security Playbook (XRPL)

Accounts & roles

ISSUER (cold): rippled account with no regular activity; multi-sig 2-of-3.

MINTER (SOLRAI): separate multi-sig 2-of-3.

HOT (ops): limited permissions; rotate regular keys quarterly.

Flags & protections

Set DefaultRipple, RequireAuth as needed for trustline control.

Use SignerListSet; remove master keys after setup.

Monitor reserve levels; auto-alert on low reserve or sequence anomalies.

Key rotation & audit

Versioned kids, HSM or hardware wallets, published rotation policy, incident response runbook.

10) Mainnet Readiness: Runbook & Test Vectors

Golden test (reproducible):

Input: sample MAS (15-min intervals for a 13 kW system, one month).

Expected issuance: 29,423.000 SOLR (example).

XRPL payment: mint with issuance_id, memo JSON.

Aggregate 1,000.000 SOLR lots → burn → validator checks pass.

Mint one SOLRAI NFT with unit_kwh=1000.000, embed burn_tx, issuance_ids_root, oracle_claims_root.

Publish proofs_cid bundle and explorer links.

Artifacts to include in tests/fixtures/:

/mas/2025-08-SITE-PR-MAO-0001.json
/issuance/2025-08-SITE-PR-MAO-0001.json
/proofs/2025-08-SITE-PR-MAO-0001-merkle.json
/nft/2025-08-LOT-0001.json

11) Minimal Validator (pseudocode)
def validate_burn_and_mint(burn_tx, issuance_ids, claim_cids, site_id, vintage):
    assert burn_tx.amount == Decimal("1000.000") and burn_tx.currency == "SOLR"
    assert all(get_site(iid) == site_id for iid in issuance_ids)
    assert all(get_vintage(iid) == vintage for iid in issuance_ids)

    # No double-spend: each issuance_id not previously consumed
    for iid in issuance_ids:
        assert not is_consumed(iid)

    root_ids = merkle_root(sorted(issuance_ids))
    root_claims = merkle_root(sorted(claim_cids))

    assert burn_tx.memo["issuance_ids_root"] == root_ids
    # Optional: cross-check claim roots via stored issuance records
    return True

12) Compliance & Claims

Publicly state the basis (gross/net) and jurisdiction profile on every artifact.

Provide an auditor checklist linking: attestation → issuance → burn → NFT → retirement.

For retirements, store a signed retirement certificate (JSON) with beneficiary, date, NFT id, and finality hash.

13) Governance Notes

Publish an open standard version (PoG v1) and track changes via CHANGELOG.md.

Maintain a public Key Registry (active KIDs, algorithms, valid from/until).

Document dispute resolution and data-quality escalation pathways.

Quick Checklist (copy into issues)

 MAS v1 implemented with JWS + key rotation

 Deterministic issuance + idempotency (issuance_id in XRPL memo)

 Precision/rounding policy (0.001 kWh)

 Lifecycle validator + Merkle proofs

 JSON Schemas published + CI validation

 Jurisdiction Profiles enforced

 Storage pinned (IPFS/Arweave) + public index

 Fee routing (8%/2%) settlement reports

 Security (multisig, flags, regular keys off)

 Golden test vectors + explorer links
