# Steward remediation

The architecture was changed, not merely reworded.

| Steward concern | v3 invariant | Regression evidence |
|---|---|---|
| Source-bound result was nonbinding | Semantic relation is only a premise; code derives eligibility and payout | happy, usage-veto, exclusion tests |
| Policy authority was unauthenticated | Signer must register policy and fund each order; source repeats signer/version and matches digest | role/substitution tests |
| Facts were claimant supplied | Buyer supplies only request; merchant supplies facts that could benefit buyer | buyer-manufacture test |
| Trust-critical nondeterminism unsafe | Two closed fields; invalid/provider/source failures normalize to `UNKNOWN` | malformed/digest/conflict tests |
| Unknown could strand escrow | retry, merchant-granted refund, and post-deadline merchant recovery | contract recovery guards |

## Claim boundary

v3 proves only that a merchant-funded order satisfies that merchant wallet's committed refund terms. It does not prove legal identity, domain ownership, delivery, consumer harm or general policy validity.

The exact v3 source is now deployed at `0x314BcBB694e3C9e6D2A97F2f4Ee3616e8bDf54c1`. Fresh StudioNet evidence closes source parity, authority guards, happy refund, deterministic usage veto, digest failure, early-recovery rejection and replay. Remaining limitations are explicitly listed in `E2E_V3.md`; browser production parity and elapsed post-deadline recovery are not claimed yet.
