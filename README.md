# PolicyVersion Sentinel

PolicyVersion Sentinel binds one refund claim to one exact public policy snapshot and records a clause-grounded GenLayer consensus outcome.

It does **not** order a payment, promise a refund, or provide a legal ruling. `ELIGIBLE`, `INELIGIBLE`, and `AMBIGUOUS` are bounded review signals for the exact claim and policy version.

## Proof obligation

**Claim:** Given locked claim facts `C` and bounded policy snapshot `P@V`, which allowed outcome is supported by cited clauses in that exact snapshot?

**Falsifiers:** An eligibility result is falsified by an applicable exclusion or missed deadline. An ineligibility result is falsified by an express covering clause. Missing consequential facts or conflicting clauses require `AMBIGUOUS`.

**Evidence:** The canonical claim JSON and the exact bytes between `POLICY_START` and `POLICY_END` at the committed HTTPS source.

**Consequence:** The nominated acknowledger may record receipt of the exact result after commitment recheck. No funds move and no external merchant is compelled to act.

## Architecture

```text
Public HTTPS policy
  -> permissionless snapshot registry (URL + version + SHA-256)
  -> immutable claim registry (facts + separate acknowledger)
  -> permissionless GenLayer adjudication
  -> REVIEW_ELIGIBLE | REVIEW_INELIGIBLE | REVIEW_AMBIGUOUS
  -> exact-commitment acknowledgement by nominated wallet
```

The deployer has no workflow privilege. Any funded StudioNet wallet can register a snapshot, file a claim, or request adjudication. A claimant must nominate a different acknowledger, so an external tester can perform the lifecycle with any two funded wallets.

## Consensus boundary

Leader and validators independently:

1. fetch the committed HTTPS source;
2. bound it using explicit markers;
3. verify SHA-256 and `POLICY_VERSION`;
4. classify the locked claim;
5. verify every cited clause ID appears in the bounded policy.

Exact consensus covers outcome, policy version, digest, cited clause IDs, and bounded reason codes. Arbitrary prose is neither requested nor stored.

## Public API

- `register_snapshot(policy_url, version, policy_digest, effective_date)`
- `file_claim(snapshot_id, acknowledger, claim_text)`
- `adjudicate_claim(claim_id)`
- `acknowledge(claim_id, claim_digest, policy_digest)`
- `get_snapshot(snapshot_id)`
- `get_claim(claim_id)`
- `get_counts()`
- `get_contract_version()`

## Demonstration source

The public demonstration policy is [`samples/refund-policy-v1.txt`](samples/refund-policy-v1.txt). Its bounded SHA-256 is:

```text
484cf05dafedd618e83329a9080b74ed028e30819f3b2560d7bac3dc8736a394
```

This is project-published demonstration policy text, not law and not an external merchant's policy. Synthetic claim fixtures are explicitly separated in `verification/TEST_RESOURCE_MANIFEST.json`.

## Local verification

```text
python -m pytest tests -q
genvm-lint contracts/PolicyVersionSentinel.py
npm install
npm run build
```

## Verified StudioNet deployment

- Website: [policyversionsentinel.pages.dev](https://policyversionsentinel.pages.dev/)
- Contract: [`0x97E92D2784d26ac14dCFE6215F7Ede582DA1608F`](https://explorer-studio.genlayer.com/address/0x97E92D2784d26ac14dCFE6215F7Ede582DA1608F)
- Source parity: passed byte-for-byte against `contracts/PolicyVersionSentinel.py`
- Two-wallet lifecycle: `ACKNOWLEDGED_ELIGIBLE`
- Live receipts and authoritative readbacks: [`verification/live-0x97e92d2784d26ac14dcfe6215f7ede582da1608f.json`](verification/live-0x97e92d2784d26ac14dcfe6215f7ede582da1608f.json)
- Full outcome and adversarial audit: [`verification/full-audit-0x97e92d2784d26ac14dcfe6215f7ede582da1608f.json`](verification/full-audit-0x97e92d2784d26ac14dcfe6215f7ede582da1608f.json)
- Browser/on-chain parity manifest: [`verification/UI_STATE_PARITY.json`](verification/UI_STATE_PARITY.json)

The evidence journal includes finalized explorer links for snapshot registration, role-separation rejection, claim filing, premature acknowledgement rejection, adjudication, replay rejection, wrong-caller rejection, commitment-tampering rejection, valid acknowledgement, and acknowledgement replay rejection.

The extended audit additionally proves live `INELIGIBLE` and `AMBIGUOUS` terminal states, malformed input rejection, missing identifier rejection, fail-closed validator conflict, and rejection of policy digest, version, and boundary-marker attacks. The production UI was rendered against claims `0` through `3`; screenshots and the parity manifest show exact agreement with authoritative `get_claim` readback. The UI also checks consensus and execution results before claiming a successful transition.

## Limitations

- Availability and stability of the committed HTTPS source affect adjudication.
- The contract does not establish that a snapshot creator speaks for a third-party merchant.
- The effective date is committed metadata; policy applicability still depends on the locked facts and semantic result.
- Ambiguous evidence always remains fail-closed.
