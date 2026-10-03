# PolicyVersion Sentinel v2 — rule audit

## Reviewer request addressed

The reviewer identified three material weaknesses in v1: a nonbinding outcome, unauthenticated policy authority, and claimant-supplied facts. v2 changes the protocol boundary rather than merely changing copy:

| Reviewer concern | v2 enforcement |
|---|---|
| Nonbinding signal | Every order is funded with exact native value. `settle` routes it to buyer after `ELIGIBLE`, to merchant after `INELIGIBLE`, and refuses to move it after `AMBIGUOUS`. |
| Unauthenticated policy authority | `create_policy` stores the signer as authority; the bounded policy must contain the exact lowercase `POLICY_AUTHORITY`; only that wallet may create and fund orders under it. This proves wallet control inside the protocol, not legal identity or domain ownership. |
| Claimant-supplied facts | Buyer supplies no free-form facts or timestamps. Merchant records order/product and usage; the contract captures purchase/request transaction times; buyer only requests review. |

## Consensus and source rules

- HTTPS source only; URL length bounded.
- Exact SHA-256, version line, authority line and marker boundaries verified inside leader and validator execution.
- Response schema has exactly three keys; outcome, reasons and cited clause IDs are enumerated/bounded.
- Every clause ID must equal a standalone `CLAUSE_ID=` line from the bounded source.
- Outcome/reason contradictions are rejected.
- Validator recomputes the full source fetch, commitment checks, interpretation and result comparison.
- Malformed output, unavailable/substituted source, missing markers, digest/version/authority mismatch and validator disagreement fail before state mutation.

## Deterministic state and custody

- Policy signer and funded order merchant must match.
- Buyer must be a distinct nonzero address.
- Payable order value must exactly equal recorded refund amount; invalid payable creation reverts so value cannot be trapped.
- Usage is mutable only by the merchant and only before refund request.
- Refund request is buyer-only and single-transition.
- Adjudication is only from `REFUND_REQUESTED`; settlement is only from eligible/ineligible review states.
- Held balance is cleared before the external transfer and subsequent settlement attempts are rejected.
- Public readback exposes authority, source commitment, parties, chain times, usage, escrow accounting, outcome, clauses and reasons.

## Evidence classification

- `tests/test_contract_direct.py`: synthetic local control-flow/adversarial evidence.
- `verification/E2E_EVIDENCE.md`: historical v1 live evidence only.
- `verification/E2E_V2.md`: honest v2 status; pending new deployment and live transactions.
- UI screenshots are presentation evidence only and cannot replace contract readback or explorer receipts.

## Verified locally on 2026-10-03

- `genvm-lint contracts/PolicyVersionSentinel.py`: passed, 3 checks.
- `python -m pytest tests/test_contract_direct.py -q`: 9 passed.
- `npm run build`: passed.

No v2 StudioNet or Cloudflare verification is claimed until a fresh deployment address and live lifecycle exist.
