# More information submission

Submission `DEB5D534-7819-4082-A67F-164D1C521986`

## Paste into “What did you change?” — under 1000 characters

Rebuilt PolicyVersion Sentinel as v3, not just its prompt. Policy authority is now the wallet that registers the exact version/digest and funds each order. The buyer only requests review; merchant-signed product, deadline, usage and escrow facts cannot be supplied by the refund beneficiary. Validators no longer decide payment: they return only COVERED, EXCLUDED or UNKNOWN plus a cited clause from fetched digest-bound bytes. Contract code enforces source status, zero usage, deadline, custody and replay protection before deriving eligibility and transferring funds. Exact source is deployed at 0x314BcBB694e3C9e6D2A97F2f4Ee3616e8bDf54c1. StudioNet evidence proves an eligible buyer refund and a COVERED-but-used veto releasing funds to merchant; wrong roles, early recovery, digest mismatch and replay fail closed. Source parity, transaction links, child transfers and limitations are documented in verification/EVIDENCE_PACKET.md and E2E_V3.md.

## Reviewer request mapped line by line

> Strong source-bound adjudication remains a nonbinding signal over unauthenticated policy authority and claimant-supplied facts.

| Reviewer requirement | Source-level remediation | Direct/live proof |
|---|---|---|
| Make source-bound adjudication consequential | Consensus produces `semantic_relation` and `cited_clause_id`; contract combines them with hard facts to derive `REVIEW_ELIGIBLE` or `REVIEW_INELIGIBLE`. Only those states can enter `settle`. | Happy adjudication [`0x4c9a…d388`](https://explorer-studio.genlayer.com/tx/0x4c9a0ae4363d6d656808700cdaa0f01a13cfbbadd1fad181d0c4b7a71d25d388) followed by buyer transfer [`0x4dda…99f8`](https://explorer-studio.genlayer.com/tx/0x4dda138d6cf25110ab5bad0b563393f39ad9093fc294342c6d3de407285099f8). |
| Authenticate policy authority | `create_policy` binds authority to `gl.message.sender`; only that same wallet can create and fund an order. Fetched policy must contain the same authority and version and match the committed digest. | Wrong wallet returns `POLICY_AUTHORITY_ONLY`: [`0xf3cf…d9e8`](https://explorer-studio.genlayer.com/tx/0xf3cfbcc28e12d53c2bc658a7a88ffa3d34e1a5d6bcad6fc71c0fcbd511bed9e8). Source parity and exact digest are in `DEPLOYMENT.json`. |
| Remove claimant-supplied decisive facts | Buyer can submit only `request_refund(order_id)`. Product description, deadline, usage and native escrow are signed/funded by the opposing merchant wallet; timestamps come from chain context. | Wrong request caller returns `BUYER_ONLY`: [`0x2b93…e41a`](https://explorer-studio.genlayer.com/tx/0x2b9330c6f7459d7e2375354a2abfb952b20fa50d06080320a8d16c671415e41a). Evidence Authority Matrix is in README. |
| Prevent AI from directly controlling money | Prompt forbids eligibility/payment decisions. Model output has two closed fields. Deterministic code requires verified source + COVERED + usage 0 + timely request; exact escrow/replay guards remain mandatory. | Order 4 is semantically `COVERED` but usage 1 forces `INELIGIBLE`; settlement sends 1 to merchant: [`0x10ba…5cee`](https://explorer-studio.genlayer.com/tx/0x10ba642d647e2dace130a48f049fa032393f3a6c7a20934278c97c07a2a25cee). |
| Fail safely on bad source/model output | Unavailable source, digest/version/authority mismatch, malformed output or unsupported clause normalize to `UNKNOWN`; unknown cannot settle and remains retryable. | Order 0 produced `INTEGRITY_FAILURE / UNKNOWN` with held escrow unchanged. Preserved in `v3-digest-control-*.json`; malformed/conflict behavior is covered by direct GenVM tests. |
| Preserve custody and recovery | Exact attached value is mandatory. Settlement marks held value zero before native transfer. Replay is rejected. Unknown can be retried or voluntarily refunded; expired unresolved orders recover to merchant. | Early recovery rejected unchanged: [`0x953e…1848`](https://explorer-studio.genlayer.com/tx/0x953ee3867078ac3c55a5b0103edfb3633256c3f120df3e4789e9122df3801848). Replay rejected: [`0x54fe…8903`](https://explorer-studio.genlayer.com/tx/0x54fe5d818eb7b4befaafb88dbced03b4cdd5c14d32ec732f17bf0b77bd7e8903). |

## Exact artifacts

- Production: https://policyversionsentinel.pages.dev/
- Contract: https://explorer-studio.genlayer.com/address/0x314BcBB694e3C9e6D2A97F2f4Ee3616e8bDf54c1
- Contract source SHA-256: `2d52099902646aa3fc713f135ba5724ae4e8060d81c73303152a348409b48e39`
- Bounded policy SHA-256: `0e0594441a4514e9867fc7d81608073d23eeb314c44f29dcf9036513566fd8b2`
- Machine happy journal: `v3-live-0x314bcbb694e3c9e6d2a97f2f4ee3616e8bdf54c1.json`
- Machine usage-veto journal: `v3-ineligible-0x314bcbb694e3c9e6d2a97f2f4ee3616e8bdf54c1.json`
- One-page verification: `EVIDENCE_PACKET.md`

## Honest limitations

- Wallet authority authenticates the merchant's offered terms, not its off-chain legal identity or domain ownership.
- Production bundle/address parity is verified, but a fresh injected-wallet browser write was not performed after this deployment.
- Post-deadline recovery is locally tested but cannot be exercised live until the signed deadline elapses; live early-recovery rejection is included.
