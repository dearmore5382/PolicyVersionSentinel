"""StudioNet source-parity and two-wallet lifecycle runner."""
import base64
import hashlib
import json
import time
from pathlib import Path

import requests
from genlayer_py import create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import studionet

ROOT = Path(__file__).resolve().parents[1]
ADDRESS = "0x97E92D2784d26ac14dCFE6215F7Ede582DA1608F"
RPC = "https://studio.genlayer.com/api"
KEY_SOURCE = ROOT.parent / "DAOProposalContextVerifier" / ".env.lifecycle"
POLICY_URL = "https://raw.githubusercontent.com/dearmore5382/PolicyVersionSentinel/main/samples/refund-policy-v1.txt"
POLICY_VERSION = "REFUND-2026-01"
POLICY_DIGEST = "484cf05dafedd618e83329a9080b74ed028e30819f3b2560d7bac3dc8736a394"
OUT = ROOT / "verification" / ("live-" + ADDRESS.lower() + ".json")


def rpc(method, params):
    response = requests.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=120)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(str(payload["error"]))
    return payload["result"]


def view(method, args=None):
    encoded = serialize([calldata.encode({"method": method, "args": args or []}), b"\x00"])
    raw = rpc("gen_call", [{"type": "read", "to": ADDRESS,
        "from": "0x0000000000000000000000000000000000000001", "value": "0x0",
        "data": encoded, "transaction_hash_variant": "latest-final"}])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))


def wait_final(tx_hash):
    deadline = time.monotonic() + 1500
    while time.monotonic() < deadline:
        tx = rpc("eth_getTransactionByHash", [tx_hash])
        if tx and tx.get("status") == "FINALIZED":
            return tx
        time.sleep(5)
    raise RuntimeError("FINALITY_TIMEOUT")


def tx_return(tx):
    receipts = (tx.get("consensus_data") or {}).get("leader_receipt") or []
    receipts = [receipts] if isinstance(receipts, dict) else receipts
    leaders = [item for item in receipts if item.get("mode") == "leader"]
    if not leaders or leaders[-1].get("execution_result") != "SUCCESS":
        raise RuntimeError("LEADER_EXECUTION_FAILED")
    raw = base64.b64decode(leaders[-1]["result"])
    try:
        return str(calldata.decode(raw))
    except Exception:
        if len(raw) > 1 and raw[0] == 0:
            return str(calldata.decode(raw[1:]))
        # typing.Any -> u256 is currently emitted as 0x00 followed by a compact
        # varint whose low three bits contain the scalar tag (ID << 3 | 1).
        if len(raw) == 2 and raw[0] == 0 and raw[1] & 7 == 1:
            return str(raw[1] >> 3)
        raise


def load_keys():
    values = {}
    for line in KEY_SOURCE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    keys = [values.get("WALLET_A_PRIVATE_KEY", ""), values.get("WALLET_B_PRIVATE_KEY", "")]
    if not all(keys) or keys[0] == keys[1]:
        raise RuntimeError("TWO_LOCAL_ROLE_KEYS_REQUIRED")
    return keys


def main():
    local = (ROOT / "contracts" / "PolicyVersionSentinel.py").read_bytes()
    deployed = base64.b64decode(rpc("gen_getContractCode", [ADDRESS]))
    if deployed != local:
        raise RuntimeError("SOURCE_PARITY_FAILED")
    source = requests.get(POLICY_URL, timeout=60)
    if source.status_code != 200 or "POLICY_START" not in source.text or "POLICY_END" not in source.text:
        raise RuntimeError("PUBLIC_POLICY_SOURCE_NOT_READY")
    accounts = [create_account(account_private_key="0x" + key.removeprefix("0x")) for key in load_keys()]
    clients = [create_client(chain=studionet, account=account) for account in accounts]
    journal = {"network": "studionet", "contract": ADDRESS,
        "source_sha256": hashlib.sha256(local).hexdigest(), "source_parity": True,
        "policy_url": POLICY_URL, "policy_digest": POLICY_DIGEST,
        "roles": {"claimant": accounts[0].address, "acknowledger": accounts[1].address},
        "steps": [], "complete": False}
    if OUT.exists():
        saved = json.loads(OUT.read_text(encoding="utf-8"))
        if saved.get("contract", "").lower() == ADDRESS.lower() and not saved.get("complete"):
            journal = saved

    def send(step, actor, method, args, expected, claim_id=None, unchanged=False):
        prior = next((item for item in journal["steps"] if item.get("id") == step
            and item.get("status") == "FINALIZED"
            and item.get("evidence_status") != "FINALIZED_AWAITING_RETURN_DECODE"), None)
        if prior is not None:
            return str(prior["return"])
        pending_index = next((i for i, item in enumerate(journal["steps"])
            if item.get("id") == step
            and item.get("evidence_status") == "FINALIZED_AWAITING_RETURN_DECODE"), None)
        if pending_index is not None:
            tx_hash = journal["steps"][pending_index]["tx_hash"]
            tx = rpc("eth_getTransactionByHash", [tx_hash])
            actual = tx_return(tx)
            after = None if claim_id is None else view("get_claim", [claim_id])
            entry = {"id": step, "actor": accounts[actor].address, "method": method,
                "return": actual, "expected": expected, "tx_hash": tx_hash,
                "explorer": "https://explorer-studio.genlayer.com/tx/" + tx_hash,
                "status": tx.get("status"), "consensus": tx.get("result_name"),
                "state_unchanged": True if unchanged else None,
                "readback": None if after is None else json.loads(after)}
            journal["steps"][pending_index] = entry
            OUT.write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
            if tx.get("result_name") != "MAJORITY_AGREE" or actual != expected:
                raise RuntimeError(step + ":UNEXPECTED:" + actual)
            return actual
        before = None if claim_id is None else view("get_claim", [claim_id])
        tx_hash = str(clients[actor].write_contract(address=ADDRESS, function_name=method,
            args=args, value=0, leader_only=False))
        tx = wait_final(tx_hash)
        # Persist the finalized hash before decoding so evidence survives an SDK
        # codec incompatibility and the transaction is never repeated blindly.
        journal["steps"].append({"id": step, "actor": accounts[actor].address,
            "method": method, "tx_hash": tx_hash,
            "explorer": "https://explorer-studio.genlayer.com/tx/" + tx_hash,
            "status": tx.get("status"), "consensus": tx.get("result_name"),
            "evidence_status": "FINALIZED_AWAITING_RETURN_DECODE"})
        OUT.write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
        actual = tx_return(tx)
        after = None if claim_id is None else view("get_claim", [claim_id])
        entry = {"id": step, "actor": accounts[actor].address, "method": method,
            "return": actual, "expected": expected, "tx_hash": tx_hash,
            "explorer": "https://explorer-studio.genlayer.com/tx/" + tx_hash,
            "status": tx.get("status"), "consensus": tx.get("result_name"),
            "state_unchanged": None if not unchanged else before == after,
            "readback": None if after is None else json.loads(after)}
        journal["steps"][-1] = entry
        OUT.write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
        if tx.get("result_name") != "MAJORITY_AGREE" or actual != expected:
            raise RuntimeError(step + ":UNEXPECTED:" + actual)
        if unchanged and before != after:
            raise RuntimeError(step + ":STATE_MUTATED")
        return actual

    counts = json.loads(view("get_counts"))
    snapshot_id = int(send("H1-register-snapshot", 0, "register_snapshot",
        [POLICY_URL, POLICY_VERSION, POLICY_DIGEST, "2026-01-01"], str(counts["snapshot_count"])))
    eligible = json.dumps({"schema": "refund-claim-v1", "claim_ref": "PVS-LIVE-001",
        "purchase_date": "2026-09-20", "request_date": "2026-09-25",
        "event": "Service purchased but not consumed", "requested_remedy": "Full refund",
        "facts": ["Request filed 5 days after purchase", "No service usage recorded"]}, separators=(",", ":"))
    send("F1-same-wallet", 0, "file_claim", [snapshot_id, accounts[0].address, eligible],
        "INDEPENDENT_ACKNOWLEDGER_REQUIRED")
    claim_id = int(send("H2-file-claim", 0, "file_claim", [snapshot_id, accounts[1].address, eligible],
        str(counts["claim_count"])))
    send("F2-premature-ack", 1, "acknowledge", [claim_id, "0" * 64, "0" * 64],
        "ACKNOWLEDGEMENT_NOT_ALLOWED", claim_id, unchanged=True)
    send("H3-adjudicate", 0, "adjudicate_claim", [claim_id], "ELIGIBLE", claim_id)
    send("F3-replay-adjudication", 0, "adjudicate_claim", [claim_id], "CLAIM_NOT_ADJUDICABLE", claim_id, unchanged=True)
    record = json.loads(view("get_claim", [claim_id]))
    send("F4-wrong-caller", 0, "acknowledge", [claim_id, record["claim_digest"], record["policy_digest"]],
        "ACKNOWLEDGER_ONLY", claim_id, unchanged=True)
    send("F5-tampered-commitment", 1, "acknowledge", [claim_id, "0" * 64, record["policy_digest"]],
        "COMMITMENT_MISMATCH", claim_id, unchanged=True)
    send("H4-acknowledge", 1, "acknowledge", [claim_id, record["claim_digest"], record["policy_digest"]],
        "ACKNOWLEDGED_ELIGIBLE", claim_id)
    send("F6-replay-ack", 1, "acknowledge", [claim_id, record["claim_digest"], record["policy_digest"]],
        "ACKNOWLEDGEMENT_NOT_ALLOWED", claim_id, unchanged=True)
    journal["final_claim"] = json.loads(view("get_claim", [claim_id]))
    journal["complete"] = journal["final_claim"]["state"] == "ACKNOWLEDGED_ELIGIBLE"
    OUT.write_text(json.dumps(journal, indent=2) + "\n", encoding="utf-8")
    print("E2E_COMPLETE" if journal["complete"] else "E2E_INCOMPLETE", OUT)


if __name__ == "__main__":
    main()
