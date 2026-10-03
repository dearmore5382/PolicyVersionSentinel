# PolicyVersion Sentinel v2 — E2E evidence status

**Status: pending fresh v2 deployment.** This file is intentionally not a fabricated transaction report. Contract-local mocks do not satisfy live evidence requirements.

## Deployment record

- Contract address: not deployed
- Exact source SHA-256: pending
- Deployment transaction: pending
- Explorer contract URL: pending
- Website/build URL: pending

## Required live lifecycle

Use the policy authority/merchant wallet for policy registration and funded-order creation, and a separate buyer wallet for refund requests. A judge can use their own wallets on the same public v2 contract.

| Scenario | Required on-chain proof | Status |
|---|---|---|
| Eligible refund | `create_policy` → payable `create_funded_order` → buyer `request_refund` → `adjudicate=ELIGIBLE` → `settle=REFUNDED`; order readback shows held `0`, buyer paid exact escrow | Pending |
| Ineligible release | Funded order with contract-recorded usage or expired window → `INELIGIBLE` → `RELEASED_TO_MERCHANT`; merchant paid exact escrow | Pending |
| Ambiguous | Conflict/missing policy facts → `AMBIGUOUS`; held value unchanged and settlement rejected | Pending |
| Role failures | Wrong-wallet funding/usage/request attempts; no protected state changes | Pending |
| Source attacks | Digest, version, exact authority marker, malformed markers and unavailable URL; no decision or settlement on invalid source | Pending |
| Adversarial outputs | Prompt injection, malformed JSON, unknown reasons, unsupported clause IDs, and outcome/reason contradiction rejected or validator conflict fails closed | Pending |
| Replay / UI parity | Repeat adjudication/settlement rejected; browser refreshes from `get_order`; every signed transaction links to its explorer receipt | Pending |

For each live write, record the exact method and arguments, signer role, transaction hash, explorer link, finality/result, return value, pre/post `get_order` readback, and whether escrow moved. Do not mark a row complete from UI screenshots or simulated mocks.

## Historical v1

[`E2E_EVIDENCE.md`](E2E_EVIDENCE.md) is preserved as historical evidence for contract `0x97E92D2784d26ac14dCFE6215F7Ede582DA1608F` (v1). Its snapshot/claim/acknowledgement transactions do not prove v2 policy authority or escrow behavior.
