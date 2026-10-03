# PolicyVersion Sentinel v3 — live E2E

Contract: [`0x314Bc…54c1`](https://explorer-studio.genlayer.com/address/0x314BcBB694e3C9e6D2A97F2f4Ee3616e8bDf54c1) on StudioNet. Deployed source is byte-identical to repository source SHA-256 `2d52099902646aa3fc713f135ba5724ae4e8060d81c73303152a348409b48e39` and reports version 3.

## Happy refund — order 1

Every listed transaction is `FINALIZED`, leader execution `SUCCESS`, and `MAJORITY_AGREE`.

| Step | Result | Explorer |
|---|---|---|
| Merchant registers immutable policy | policy 1 | [tx](https://explorer-studio.genlayer.com/tx/0xb5c270c533fac2a31c1fd6b93c86c7dc8f488434cb8f97c4005963f1885da745) |
| Wrong wallet attempts funding | `POLICY_AUTHORITY_ONLY` | [tx](https://explorer-studio.genlayer.com/tx/0xf3cfbcc28e12d53c2bc658a7a88ffa3d34e1a5d6bcad6fc71c0fcbd511bed9e8) |
| Merchant funds order | order 1, 1 attoGEN | [tx](https://explorer-studio.genlayer.com/tx/0xd479e212b1ed46de8a6dad625655b8d1fa50e91a87badcb929afba24774c0387) |
| Wrong refund caller | `BUYER_ONLY`, unchanged | [tx](https://explorer-studio.genlayer.com/tx/0x2b9330c6f7459d7e2375354a2abfb952b20fa50d06080320a8d16c671415e41a) |
| Buyer requests | `REFUND_REQUESTED` | [tx](https://explorer-studio.genlayer.com/tx/0xb1fba5e6c241dc67d9d8d4cbf7004a5ccea1777272d2b91d8d49c1063848680f) |
| Early recovery | `DEADLINE_NOT_REACHED`, unchanged | [tx](https://explorer-studio.genlayer.com/tx/0x953ee3867078ac3c55a5b0103edfb3633256c3f120df3e4789e9122df3801848) |
| Consensus adjudication | `COVERED-DIGITAL-TOOLS`, code derives `ELIGIBLE` | [tx](https://explorer-studio.genlayer.com/tx/0x4c9a0ae4363d6d656808700cdaa0f01a13cfbbadd1fad181d0c4b7a71d25d388) |
| Settlement | `REFUNDED`; native message sends 1 to buyer | [tx](https://explorer-studio.genlayer.com/tx/0x4dda138d6cf25110ab5bad0b563393f39ad9093fc294342c6d3de407285099f8) |
| Replay | `SETTLEMENT_NOT_ALLOWED`, unchanged | [tx](https://explorer-studio.genlayer.com/tx/0x54fe5d818eb7b4befaafb88dbced03b4cdd5c14d32ec732f17bf0b77bd7e8903) |

Final readback: `REFUNDED`, held 0, paid buyer 1, paid merchant 0, source `VERIFIED`, relation `COVERED`, committed digest equals observed digest.

## Deterministic usage veto — order 4

The merchant records one usage unit. Validators still return `COVERED`, but deterministic code derives `INELIGIBLE`; AI cannot override the veto. Full machine-readable hashes are in the JSON evidence file. Settlement [tx](https://explorer-studio.genlayer.com/tx/0x10ba642d647e2dace130a48f049fa032393f3a6c7a20934278c97c07a2a25cee) emits a native message of 1 to merchant. Final state is `RELEASED_TO_MERCHANT`, held 0, paid merchant 1.

## Preserved failures and limitations

- Order 0 committed the whole-file hash rather than bounded policy hash. Adjudication safely returned `UNKNOWN / INTEGRITY_FAILURE`; escrow stayed held. This resource-preparation error is preserved in `v3-digest-control-*.json`.
- Orders 2 and 3 are successful usage-veto executions whose buyer-request polling encountered HTTP 502. Their readbacks prove the request finalized, but the clients did not persist that request hash; they are preserved as interrupted evidence and are not the canonical complete case.
- Order 4 is the canonical complete usage-veto case after the runner was corrected to journal hashes immediately after submission.
- Post-deadline recovery remains unexercised because the deadline has not elapsed. Early recovery rejection is live; direct contract tests cover the terminal rule locally.
- Production and immutable deployment URLs both return HTTP 200 and their bundles contain the exact v3 address/schema copy. A fresh injected-wallet browser write was not performed in this deployment session and is not claimed.
