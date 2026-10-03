# PolicyVersion Sentinel v3 — E2E gate

**Status: local gates passed; fresh deployment and live lifecycle pending.** No v2 receipt proves v3 behavior.

## Superseded v2 observation

- Address: `0x5Ea83Be7737a63B57543d00CD2bFB92De4Ef2f96`
- Source parity was verified for v2.
- Policy creation, role rejection, funding and buyer request finalized.
- First adjudication finalized but leader execution returned `LEADER_EXECUTION_FAILED`; order 0 remained `REFUND_REQUESTED` with escrow held.
- v3 no longer asks the model for an overall outcome; malformed/provider failures normalize to nonbinding `UNKNOWN`.
- This is failure evidence, not v3 success evidence.

## Fresh v3 proof required

| Scenario | Required on-chain evidence | Status |
|---|---|---|
| Happy refund | merchant policy/funding → buyer request → `COVERED` consensus → code-derived `ELIGIBLE` → buyer child transfer | Pending deployment |
| Usage veto | usage > 0 + `COVERED` → code-derived `INELIGIBLE` → merchant transfer | Pending deployment |
| Explicit exclusion | cited `EXCLUDED` → merchant release | Pending deployment |
| Source failure | digest/authority/version/unavailable failure → `UNKNOWN`, held unchanged | Pending deployment |
| Adversarial output | malformed/unsupported clause → `UNKNOWN`, no positive state | Pending deployment |
| Consensus conflict | consequential relation/clause/digest mismatch rejected | Pending deployment |
| Authorization | wrong wallets cannot fund, record usage, request or grant refund | Pending deployment |
| Recovery/replay | early recovery blocked; expired unresolved case recovers once; duplicate settlement rejected | Pending deployment |
| Browser parity | wallet write, finality, leader success, consensus, reload and explorer agree | Pending deployment |

Record exact address/source hash, actor, args/value, transaction hash, FINALIZED status, leader execution, consensus result, return, post-state and child transfer. Receipt finality alone is insufficient.
