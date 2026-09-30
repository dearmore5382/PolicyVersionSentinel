from pathlib import Path
import importlib
import json
import sys
from unittest.mock import patch

from gltest.direct import VMContext, create_address, deploy_contract

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "PolicyVersionSentinel.py"


def eth(value):
    if isinstance(value, bytes):
        return "0x" + bytes(value).hex()
    text = str(value)
    return "0x" + text[5:] if text.startswith("addr#") else text


def claim(ref="CLAIM-1"):
    return json.dumps({"schema": "refund-claim-v1", "claim_ref": ref,
        "purchase_date": "2026-09-20", "request_date": "2026-09-25",
        "event": "Service purchased but not consumed", "requested_remedy": "Full refund",
        "facts": ["Request filed within 14 days", "No usage recorded"]}, separators=(",", ":"))


def deploy():
    deployer, claimant, acknowledger, outsider = [create_address(x) for x in ("deployer", "claimant", "acknowledger", "outsider")]
    vm = VMContext(deployer)
    with patch("os.unlink", lambda _path: None), vm.activate():
        contract = deploy_contract(CONTRACT, vm)
        proxy = contract._instance.register_snapshot.__globals__["gl"]
        _ = proxy.nondet
        _ = proxy.vm
    sdk_root = str(Path(proxy._cached_gl.__file__).resolve().parents[2])
    if sdk_root not in sys.path:
        sys.path.insert(0, sdk_root)
    importlib.import_module("genlayer")
    return vm, contract, deployer, claimant, acknowledger, outsider


def sync(vm, contract):
    proxy = contract._instance.register_snapshot.__globals__["gl"]
    sender = vm.sender
    if isinstance(sender, bytes):
        sender = type(proxy.message.sender_address)(sender)
    proxy._cached_gl.message = proxy.message._replace(sender_address=sender, origin_address=sender,
        value=type(proxy.message.value)(vm.value))
    proxy._cached_gl.message_raw["sender_address"] = sender
    proxy._cached_gl.message_raw["origin_address"] = sender


def snapshot(vm, contract, actor):
    with vm.prank(actor):
        sync(vm, contract)
        return contract.register_snapshot("https://example.org/policy.txt", "REFUND-2026-01", "d" * 64, "2026-01-01")


def file_as(vm, contract, actor, acknowledger, snapshot_id=0, payload=None):
    with vm.prank(actor):
        sync(vm, contract)
        return contract.file_claim(snapshot_id, eth(acknowledger), payload or claim())


def adjudicate_as(vm, contract, actor, claim_id, outcome="ELIGIBLE"):
    reasons = {"ELIGIBLE": ["WITHIN_WINDOW"], "INELIGIBLE": ["OUTSIDE_WINDOW"],
        "AMBIGUOUS": ["MISSING_FACTS"]}[outcome]
    result = {"outcome": outcome, "policy_version": "REFUND-2026-01", "policy_digest": "d" * 64,
        "cited_clause_ids": [] if outcome == "AMBIGUOUS" else ["REFUND-1"], "reason_codes": reasons}
    module = contract._instance.register_snapshot.__globals__
    with vm.prank(actor), patch.dict(module, {"_adjudicate": lambda *_: result}):
        sync(vm, contract)
        return contract.adjudicate_claim(claim_id)


def test_permissionless_two_wallet_happy_path_and_deployer_has_no_role():
    vm, contract, deployer, claimant, acknowledger, outsider = deploy()
    assert snapshot(vm, contract, outsider) == 0
    claim_id = file_as(vm, contract, claimant, acknowledger)
    assert claim_id == 0
    assert adjudicate_as(vm, contract, outsider, claim_id) == "ELIGIBLE"
    record = json.loads(contract.get_claim(claim_id))
    with vm.prank(acknowledger):
        sync(vm, contract)
        assert contract.acknowledge(claim_id, record["claim_digest"], record["policy_digest"]) == "ACKNOWLEDGED_ELIGIBLE"
    assert eth(deployer) not in (record["claimant"], record["acknowledger"])


def test_same_wallet_and_wrong_acknowledger_fail_closed_without_mutation():
    vm, contract, _, claimant, acknowledger, outsider = deploy()
    snapshot(vm, contract, outsider)
    assert file_as(vm, contract, claimant, claimant) == "INDEPENDENT_ACKNOWLEDGER_REQUIRED"
    cid = file_as(vm, contract, claimant, acknowledger)
    adjudicate_as(vm, contract, outsider, cid)
    before = contract.get_claim(cid)
    record = json.loads(before)
    with vm.prank(outsider):
        sync(vm, contract)
        assert contract.acknowledge(cid, record["claim_digest"], record["policy_digest"]) == "ACKNOWLEDGER_ONLY"
    assert contract.get_claim(cid) == before


def test_ambiguous_and_ineligible_are_bounded_and_acknowledgeable():
    for outcome in ("AMBIGUOUS", "INELIGIBLE"):
        vm, contract, _, claimant, acknowledger, outsider = deploy()
        snapshot(vm, contract, outsider)
        cid = file_as(vm, contract, claimant, acknowledger)
        assert adjudicate_as(vm, contract, outsider, cid, outcome) == outcome
        record = json.loads(contract.get_claim(cid))
        assert record["state"] == "REVIEW_" + outcome


def test_premature_tampered_and_replayed_actions_do_not_mutate():
    vm, contract, _, claimant, acknowledger, outsider = deploy()
    snapshot(vm, contract, outsider)
    cid = file_as(vm, contract, claimant, acknowledger)
    before = contract.get_claim(cid)
    with vm.prank(acknowledger):
        sync(vm, contract)
        assert contract.acknowledge(cid, "x", "y") == "ACKNOWLEDGEMENT_NOT_ALLOWED"
    assert contract.get_claim(cid) == before
    adjudicate_as(vm, contract, outsider, cid)
    decided = contract.get_claim(cid)
    record = json.loads(decided)
    with vm.prank(acknowledger):
        sync(vm, contract)
        assert contract.acknowledge(cid, "0" * 64, record["policy_digest"]) == "COMMITMENT_MISMATCH"
        assert contract.get_claim(cid) == decided
        assert contract.acknowledge(cid, record["claim_digest"], record["policy_digest"]) == "ACKNOWLEDGED_ELIGIBLE"
        assert contract.acknowledge(cid, record["claim_digest"], record["policy_digest"]) == "ACKNOWLEDGEMENT_NOT_ALLOWED"


def test_invalid_snapshot_claim_and_missing_ids_rejected():
    vm, contract, _, claimant, acknowledger, outsider = deploy()
    with vm.prank(outsider):
        sync(vm, contract)
        assert contract.register_snapshot("http://bad", "v1", "d" * 64, "2026") == "INVALID_SNAPSHOT_METADATA"
        assert contract.register_snapshot("https://ok", "v1", "bad", "2026") == "INVALID_POLICY_DIGEST"
    assert file_as(vm, contract, claimant, acknowledger, 99) == "SNAPSHOT_NOT_FOUND"
    snapshot(vm, contract, outsider)
    assert file_as(vm, contract, claimant, acknowledger, payload="{}") == "INVALID_CLAIM"
    assert contract.adjudicate_claim(99) == "CLAIM_NOT_FOUND"


def test_verdict_schema_clause_grounding_and_strong_decision_rules():
    _, contract, *_ = deploy()
    module = contract._instance.register_snapshot.__globals__
    policy = "POLICY_START\nPOLICY_VERSION=V1\nCLAUSE_ID=REFUND-1\ntext\nPOLICY_END"
    good = module["_verdict"]({"outcome": "ELIGIBLE", "cited_clause_ids": ["REFUND-1"],
        "reason_codes": ["WITHIN_WINDOW"]}, policy, "V1", "d" * 64)
    assert good["outcome"] == "ELIGIBLE"
    for bad in (
        {"outcome": "ELIGIBLE", "cited_clause_ids": ["FAKE"], "reason_codes": ["WITHIN_WINDOW"]},
        {"outcome": "ELIGIBLE", "cited_clause_ids": [], "reason_codes": []},
        {"outcome": "UNKNOWN", "cited_clause_ids": [], "reason_codes": ["MISSING_FACTS"]},
    ):
        try:
            module["_verdict"](bad, policy, "V1", "d" * 64)
            assert False, "bad verdict accepted"
        except Exception:
            pass


def test_source_is_bounded_and_consensus_compares_consequential_fields():
    source = CONTRACT.read_text(encoding="utf-8")
    assert "source.find(POLICY_START)" in source
    assert "source.find(POLICY_END)" in source
    assert "MAX_POLICY_BYTES" in source
    for field in ("outcome", "policy_version", "policy_digest", "cited_clause_ids", "reason_codes"):
        assert 'leader.get("' + field + '")' in source


def test_public_manifest_separates_live_source_from_synthetic_fixtures():
    manifest = json.loads((ROOT / "verification" / "TEST_RESOURCE_MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["live_source"]["classification"] == "PUBLIC_LIVE_SOURCE"
    assert all(x["classification"] == "SYNTHETIC_FIXTURE" for x in manifest["fixtures"])
