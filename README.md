# PolicyVersion Sentinel

PolicyVersion Sentinel v2 authenticates a policy authority at the wallet boundary, binds a bounded public policy source to that wallet and a SHA-256 digest, records purchase/request timestamps and merchant usage on-chain, and routes a funded native-token refund escrow based on GenLayer adjudication.

The deployed v1 contract and evidence are historical and do not prove v2 behavior. v2 is a new schema and requires a fresh contract deployment. Until that deployment and its public live lifecycle are recorded, do not claim v2 is deployed or submission-ready.

## Protocol lifecycle

1. The merchant publishes a policy file and sets `POLICY_AUTHORITY` to its lowercase wallet address. The merchant wallet calls `create_policy(url, version, digest)`; that transaction binds the address to the policy pointer.
2. The same wallet calls payable `create_funded_order(policy_id, buyer, order_ref, product_code, refund_amount)`. Transaction value must exactly equal `refund_amount`; buyer must be a distinct nonzero address.
3. Only the merchant records usage. Only the buyer may request a refund. Purchase and request times are copied from GenLayer transaction context; the buyer cannot submit either timestamp or arbitrary claim facts.
4. Anyone can call `adjudicate(order_id)`. Validators fetch the exact marked source, verify digest, version, and the exact `POLICY_AUTHORITY` line against the registered wallet, then return a bounded outcome with exact clause IDs and reason codes. Contradictory output is rejected.
5. Anyone may call `settle(order_id)` after an eligible or ineligible review. `ELIGIBLE` returns the held amount to the buyer; `INELIGIBLE` transfers it to the merchant; `AMBIGUOUS` leaves custody held. A state guard prevents replay.

Authority means the wallet signed the policy registration and created/funded orders using that policy. It does not independently prove the wallet holder's legal identity or prove control of a third-party domain. The protocol is deliberately scoped to that authenticated on-chain relationship. Source ownership, availability and applicable law remain external concerns.

## Policy source and digest

Start with [`samples/refund-policy-v2.txt`](samples/refund-policy-v2.txt), replace the authority placeholder with the merchant wallet in lowercase, publish the exact file at a stable HTTPS URL, then compute SHA-256 over the exact UTF-8 bytes from `POLICY_START` through `POLICY_END` inclusive (including newlines). The entire body must remain under 40,000 bytes; the bounded section must remain under 18,000 bytes. No trimming or newline conversion is allowed after hashing.

Example PowerShell command for a source file whose markers are the first and last lines:

```powershell
$raw = [System.IO.File]::ReadAllBytes("samples/refund-policy-v2.txt")
$sha = [System.Security.Cryptography.SHA256]::HashData($raw)
[Convert]::ToHexString($sha).ToLowerInvariant()
```

The sample is illustrative, not legal advice, and must not be represented as the policy of a real merchant without their authorization.

## Contract interface

- `create_policy(url, version, digest)` — signer becomes the policy authority.
- `create_funded_order(policy_id, buyer, order_ref, product_code, refund_amount)` — payable; same authority only; exact native value required.
- `record_usage(order_id, units)` — order merchant only.
- `request_refund(order_id)` — recorded buyer only.
- `adjudicate(order_id)` — public nondeterministic review over exact source and contract facts.
- `settle(order_id)` — public, guarded transfer based on settled outcome; ambiguous results cannot settle.
- `get_order(order_id)`, `get_counts()`, `get_contract_version()` — readback.

## Test evidence and source classes

`tests/test_contract_direct.py` uses synthetic deterministic web/LLM responses only for local contract behavior and validator conflict checks. These fixtures are not live evidence. `verification/E2E_EVIDENCE.md` contains historical v1 receipts only; `verification/E2E_V2.md` tracks v2's pending live deployment and evidence requirements.

Run locally:

```text
python -m pytest tests/test_contract_direct.py -q
genvm-lint contracts/PolicyVersionSentinel.py
npm ci
npm run build
```

### Current status

- v2 contract local direct suite: 9 tests passed.
- v2 linter: passed.
- v2 browser build and contract deployment: pending verification.
- v2 live StudioNet lifecycle and on-chain/explorer evidence: not yet available.
- Existing address `0x97E92D2784d26ac14dCFE6215F7Ede582DA1608F` is v1 and must not be configured in the v2 UI.
