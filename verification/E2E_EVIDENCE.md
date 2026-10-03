# PolicyVersion Sentinel — Live E2E Evidence

> Historical v1 evidence only. The v1 snapshot/claim/acknowledgement contract does not demonstrate the v2 authority-funded escrow protocol. See [`E2E_V2.md`](E2E_V2.md); no v2 live transactions are claimed yet.

This document summarizes reproducible **live StudioNet evidence** for the deployed contract. Synthetic fixtures are not represented as on-chain evidence.

## Deployment

- Website: https://policyversionsentinel.pages.dev/
- Repository: https://github.com/dearmore5382/PolicyVersionSentinel
- Contract: https://explorer-studio.genlayer.com/address/0x97E92D2784d26ac14dCFE6215F7Ede582DA1608F
- Contract address: `0x97E92D2784d26ac14dCFE6215F7Ede582DA1608F`
- Source parity: byte-for-byte verified
- Claimant wallet: `0x736A168247e3f0C52F7907c9a8fDac572DF9c8bB`
- Acknowledger wallet: `0xA63DE24e30C88FB1019E8956654730316e36eDBE`
- Public policy digest: `484cf05dafedd618e83329a9080b74ed028e30819f3b2560d7bac3dc8736a394`

## Happy path — ELIGIBLE

| Step | Final return | Finality | Explorer |
|---|---|---|---|
| Register policy snapshot | `3` | `FINALIZED / MAJORITY_AGREE` | [tx](https://explorer-studio.genlayer.com/tx/0xfce602fe16d90bab25546553421618cde239daffb501dcdbeb80fc8b9cf5edff) |
| File immutable claim | `0` | `FINALIZED / MAJORITY_AGREE` | [tx](https://explorer-studio.genlayer.com/tx/0xd1f63117938354a9dc7d11d42204ed3154cf92369327903b4bc281f2756bb69c) |
| Adjudicate | `ELIGIBLE` | `FINALIZED / MAJORITY_AGREE` | [tx](https://explorer-studio.genlayer.com/tx/0xd19b9df9ffc8a0f12b695a9807975b43ca28532ccb0a48f79f4f06510c50da3b) |
| Acknowledge exact commitments | `ACKNOWLEDGED_ELIGIBLE` | `FINALIZED / MAJORITY_AGREE` | [tx](https://explorer-studio.genlayer.com/tx/0xd7fcf51edf4bbea7c1148987cc1fe51b8be936d4d3a222cc011b3ddc72d66b98) |

Authoritative claim `0` readback contains outcome `ELIGIBLE`, state `ACKNOWLEDGED_ELIGIBLE`, cited clause `REFUND-1`, and reason codes `COVERED_EVENT` and `WITHIN_WINDOW`.

## Failure and replay paths

Every protected-state comparison below remained unchanged.

| Attack | Contract return | Explorer |
|---|---|---|
| Claimant nominates itself | `INDEPENDENT_ACKNOWLEDGER_REQUIRED` | [tx](https://explorer-studio.genlayer.com/tx/0x0f3f81d6d77a05d7109ff18e7e0ae2180c3b22fafffbc4a9148f539177d63221) |
| Premature acknowledgement | `ACKNOWLEDGEMENT_NOT_ALLOWED` | [tx](https://explorer-studio.genlayer.com/tx/0x2608dedb21302e8a42b62b2c18ff49885f4a1fb9524d2435d3154b88229eafa1) |
| Replay adjudication | `CLAIM_NOT_ADJUDICABLE` | [tx](https://explorer-studio.genlayer.com/tx/0xe92239adac1b283e8af6a65f1372db379cf3a925b889b8cf4a77822d8ea57b6c) |
| Wrong acknowledgement caller | `ACKNOWLEDGER_ONLY` | [tx](https://explorer-studio.genlayer.com/tx/0xe0d520807c0d87c06c9b1b288e998596a2e75a807718056ec13f3c87f21600dd) |
| Tampered claim commitment | `COMMITMENT_MISMATCH` | [tx](https://explorer-studio.genlayer.com/tx/0xf64b34f660ca103bf8526428bcae591b1141a7a1b664806b514fe67e26baaa4f) |
| Replay acknowledgement | `ACKNOWLEDGEMENT_NOT_ALLOWED` | [tx](https://explorer-studio.genlayer.com/tx/0xf20d87708fed06eecc040b4adcd0770f9194ac6c11a9f53dc5d84cf19e6c51cf) |

## Live outcome coverage

| Claim | Outcome | Terminal state | Adjudication | Acknowledgement |
|---|---|---|---|---|
| `0` | `ELIGIBLE` | `ACKNOWLEDGED_ELIGIBLE` | [tx](https://explorer-studio.genlayer.com/tx/0xd19b9df9ffc8a0f12b695a9807975b43ca28532ccb0a48f79f4f06510c50da3b) | [tx](https://explorer-studio.genlayer.com/tx/0xd7fcf51edf4bbea7c1148987cc1fe51b8be936d4d3a222cc011b3ddc72d66b98) |
| `1` | `INELIGIBLE` | `ACKNOWLEDGED_INELIGIBLE` | [tx](https://explorer-studio.genlayer.com/tx/0x861b151fb6389ce1d54880f76437e4fcd55b142bd7fc55d574707985947a599a) | [tx](https://explorer-studio.genlayer.com/tx/0x320c57bc77f45264e488abedce586171443e6d5cc6a3d95764c9a9a46468c79e) |
| `3` | `AMBIGUOUS` | `ACKNOWLEDGED_AMBIGUOUS` | [tx](https://explorer-studio.genlayer.com/tx/0xa87602291bc3b54d838c7d55bfc465de31456546437e868009b1d300290e23d4) | [tx](https://explorer-studio.genlayer.com/tx/0x426efc1057dbd4721ecb775d15ae43cd742f8382096d422691bc0789a31d74f3) |

## Validator conflict — fail closed

Claim `2` deliberately combines opposing policy clauses and an instruction-injection sentence inside the untrusted claim facts. The leader proposed `AMBIGUOUS`, but exact validator consensus was not reached.

- Result: `FINALIZED / MAJORITY_DISAGREE`
- Transaction: [0x34a117…](https://explorer-studio.genlayer.com/tx/0x34a117daef0aa670c741bf0d5a4d79b30ca4ec920699dcbe563756a0cd4f77a4)
- Authoritative state after finality: `CLAIM_FILED / PENDING`
- Safety property: no unsupported outcome was committed

## Malformed input and missing identifiers

| Attack | Return | State unchanged | Explorer |
|---|---|---|---|
| Non-HTTPS snapshot URL | `INVALID_SNAPSHOT_METADATA` | yes | [tx](https://explorer-studio.genlayer.com/tx/0xcd5ef47faedcc5fdf7a2f60bc316da9bf74665b6472a1fd92085c7859f3776ca) |
| Invalid digest format | `INVALID_POLICY_DIGEST` | yes | [tx](https://explorer-studio.genlayer.com/tx/0x26014ca92f4ff1b36280199a80be3f44b6f7f828c976d3d855a923a394479243) |
| Missing snapshot | `SNAPSHOT_NOT_FOUND` | yes | [tx](https://explorer-studio.genlayer.com/tx/0x2c7d4f0f12804b34430407c58e13b7fcde5b6d4470a7ad218aaf218f719e47a9) |
| Invalid claim schema | `INVALID_CLAIM` | yes | [tx](https://explorer-studio.genlayer.com/tx/0x70daafd779a846dbf47e5f4ed93c39ec7a3d0eda39e50ed5ece328c8a4186cc9) |
| Missing claim adjudication | `CLAIM_NOT_FOUND` | yes | [tx](https://explorer-studio.genlayer.com/tx/0x94ba225977a5c92f94732cd1c7daeea2e5ad6c2843898913d8abd498b7c9ecc7) |
| Missing claim acknowledgement | `CLAIM_NOT_FOUND` | yes | [tx](https://explorer-studio.genlayer.com/tx/0x4c324a2007ea950fd24a3ef15523ab5e39746b3d93222781fb3afb854b0ced3c) |

## Source-integrity attacks

Each transaction finalized without changing the associated claim from `CLAIM_FILED`.

| Attack | Observed error | Consensus behavior | Explorer |
|---|---|---|---|
| Wrong bounded policy digest | `POLICY_DIGEST_MISMATCH` | `MAJORITY_DISAGREE`, execution error, fail closed | [tx](https://explorer-studio.genlayer.com/tx/0x1f0249604dd87436e1275fc228a0873f844c0f3e69f18f21784ff0adc955ae41) |
| Wrong policy version | `POLICY_VERSION_MISMATCH` | `MAJORITY_DISAGREE`, execution error, fail closed | [tx](https://explorer-studio.genlayer.com/tx/0xbff0754e7aacdf3833f5b7cd6ab3e1de2e214860aba19304b8f6f81006c258ff) |
| Missing policy boundary markers | `POLICY_MARKERS_MISSING` | `MAJORITY_DISAGREE`, execution error, fail closed | [tx](https://explorer-studio.genlayer.com/tx/0x142c88dc9f1c9f203af575d847355ccd31d26c75936ed4bc9e4081cba4800f3e) |

## UI ↔ on-chain parity

The production Vite build loaded each claim through `get_claim()` without a wallet. The UI waits for `FINALIZED`, requires `MAJORITY_AGREE` plus `FINISHED_WITH_RETURN` before claiming success, and reloads authoritative state after writes.

| Screenshot | Expected and observed state |
|---|---|
| [claim 0](ui-claim-0.png) | `ACKNOWLEDGED_ELIGIBLE` |
| [claim 1](ui-claim-1.png) | `ACKNOWLEDGED_INELIGIBLE` |
| [claim 2](ui-claim-2.png) | `CLAIM_FILED / PENDING` after validator disagreement |
| [claim 3](ui-claim-3.png) | `ACKNOWLEDGED_AMBIGUOUS` |

Machine-readable parity: [`UI_STATE_PARITY.json`](UI_STATE_PARITY.json)

## Reproduction commands

```bash
pytest -q
npm run build
python verification/run_live.py
python verification/run_full_audit.py
```

The live scripts load two auxiliary keys from an ignored external environment file. No private key, Cloudflare token, or `.env` file is committed.

## Raw evidence

- [`live-0x97e92d2784d26ac14dcfe6215f7ede582da1608f.json`](live-0x97e92d2784d26ac14dcfe6215f7ede582da1608f.json)
- [`full-audit-0x97e92d2784d26ac14dcfe6215f7ede582da1608f.json`](full-audit-0x97e92d2784d26ac14dcfe6215f7ede582da1608f.json)
- [`DEPLOYMENT.json`](DEPLOYMENT.json)
- [`CLOUDFLARE_DEPLOYMENT.json`](CLOUDFLARE_DEPLOYMENT.json)
- [`TEST_RESOURCE_MANIFEST.json`](TEST_RESOURCE_MANIFEST.json)

## Evidence boundary

The repository policies are project-published demonstration sources, not merchant policies or law. Synthetic JSON fixtures are test inputs and are explicitly separated from live finalized StudioNet receipts.
