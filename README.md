# PolicyVersion Sentinel v3

PolicyVersion Sentinel is a counterparty-grounded refund escrow. The merchant wallet authenticates an exact policy snapshot, product description, deadline, usage and funded amount. The buyer may request review but cannot supply the facts that unlock a refund. GenLayer validators decide only `COVERED | EXCLUDED | UNKNOWN`; deterministic contract code derives eligibility and moves custody.

## Why v3 exists

The superseded v2 contract asked AI for the overall refund outcome. Its first live adjudication reached finalized consensus but leader execution failed, and the architecture still risked treating authenticated statements as objective truth. v3 narrows the proof obligation:

- wallet authority proves who offered these terms—not legal identity or external truth;
- SHA-256 binds the fetched policy bytes, version and authority marker;
- the funding merchant, not refund beneficiary, fixes product, deadline and usage;
- validators classify only product-to-policy semantic coverage with one cited clause;
- code enforces source validity, deadline, zero usage, custody and replay protection;
- malformed output, unavailable source, digest mismatch and uncertainty become `UNKNOWN`, never a refund;
- the merchant may voluntarily refund an unresolved request; after deadline anyone can recover held funds to merchant.

## Lifecycle

1. Merchant calls `create_policy(url, version, digest)`.
2. Same merchant calls payable `create_funded_order(policy_id, buyer, order_ref, product_description, refund_deadline, refund_amount)` with exact native value.
3. Merchant may call `record_usage`; buyer alone calls `request_refund` before the signed deadline.
4. Anyone calls `adjudicate`. Validators re-fetch and authenticate policy, then return only `relation` and `clause_id`.
5. Contract derives `ELIGIBLE` only for verified `COVERED` + zero usage + timely request. `settle` transfers once. Unknown stays held and retryable.

## Evidence authority matrix

| Fact | Authority | Buyer can create alone? | Enforcement |
|---|---|---:|---|
| Policy/version/digest | Funding merchant wallet | No | signer + fetched digest + embedded authority/version |
| Product and deadline | Funding merchant wallet | No | immutable funded order |
| Usage | Funding merchant wallet | No | locked after request; refund requires zero |
| Request | Buyer wallet | Yes, but insufficient | only opens review |
| Product coverage | Independent validators over exact bytes | No | consensus on relation + clause |
| Payout | Contract | No | deterministic gates, exact escrow, replay guard |

The sample policy is synthetic and not proof of a real merchant policy. GitHub is only public transport. Live proof requires exact deployed source, finalized transactions, consensus, readback and child transfer.

## Local verification

```text
python -m pytest -q
npm ci
npm run build
```

Current local result: 9 direct GenVM tests pass; production frontend build passes. A fresh v3 deployment is required. Never submit the superseded v2 address `0x5Ea83Be7737a63B57543d00CD2bFB92De4Ef2f96` as v3.

See [`verification/E2E_V3.md`](verification/E2E_V3.md), [`verification/TEST_RESOURCE_MANIFEST.json`](verification/TEST_RESOURCE_MANIFEST.json), and [`verification/REMEDIATION.md`](verification/REMEDIATION.md).
