# Rule audit — version-bound refund review v1

## Authority map

| Fact | Authority | Binding | Consequential |
|---|---|---|---|
| Policy bytes | public HTTPS source | bounded SHA-256 | yes |
| Policy version | bounded policy marker | exact marker + stored version | yes |
| Claim facts | claimant transaction | canonical JSON + SHA-256 | yes |
| Semantic outcome | GenLayer validator consensus | three-value enum | yes |
| Clause grounding | bounded policy | every returned ID must occur | yes |
| Acknowledger | claimant nomination | sender-enforced and distinct | yes |

## Invariants

- Deployer has no workflow authority.
- Snapshot registration and adjudication are permissionless.
- Claimant and acknowledger must differ.
- Claim and snapshot are immutable after creation.
- Only one semantic adjudication can mutate a claim.
- Acknowledgement requires the exact claim and policy commitments.
- Replay, wrong caller, malformed data and premature actions leave protected state unchanged.
- No semantic outcome transfers value or guarantees a refund.

## Evidence status

- Direct contract regression matrix: required before deployment.
- Frontend production build: required before deployment.
- StudioNet source parity and two-wallet lifecycle: pending manual deployment.
- Live evidence: must not be claimed until finalized receipts exist.
