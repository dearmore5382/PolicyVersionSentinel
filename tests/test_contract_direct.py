from pathlib import Path
import hashlib, importlib, json, re, sys
from unittest.mock import patch
from gltest.direct import VMContext,create_address,deploy_contract

ROOT=Path(__file__).resolve().parents[1]; CONTRACT=ROOT/"contracts"/"PolicyVersionSentinel.py"
URL="https://merchant.example/refund-v2.txt"

def eth(v):
    if isinstance(v,bytes):return "0x"+bytes(v).hex()
    s=str(v);return "0x"+s[5:] if s.startswith("addr#") else s

def policy_for(authority):
    return f"POLICY_START\nPOLICY_VERSION=REFUND-V2\nPOLICY_AUTHORITY={authority.lower()}\nCLAUSE_ID=WINDOW-14\nEligible within 14 days.\nCLAUSE_ID=USED\nItems with usage are excluded.\nPOLICY_END"

def deploy():
    merchant,buyer,outsider=[create_address(x) for x in ("merchant","buyer","outsider")];vm=VMContext(merchant)
    with patch("os.unlink",lambda _:None),vm.activate():
        c=deploy_contract(CONTRACT,vm,sdk_version="v0.2.16");p=c._instance.create_policy.__globals__["gl"];pgl=getattr(p,"_cached_gl",p);_=pgl.nondet;_=pgl.vm
        sdk=str(Path(pgl.__file__).resolve().parents[2])
        runtime=sys.modules.get("genlayer.gl.genvm_contracts")
        if runtime is not None and hasattr(runtime,"__known_contract__"):runtime.__known_contract__=None
    sys.path.insert(0,sdk) if sdk not in sys.path else None
    module=importlib.import_module("genlayer");module.gl=pgl;sys.modules["genlayer.gl"]=pgl;sys.modules["genlayer.gl.vm"]=pgl.vm
    return vm,c,merchant,buyer,outsider

def sync(vm,c):
    p=c._instance.create_policy.__globals__["gl"];pgl=getattr(p,"_cached_gl",p);sender=vm.sender
    sdk=str(Path(pgl.__file__).resolve().parents[2]);sys.path.insert(0,sdk) if sdk not in sys.path else None
    module=importlib.import_module("genlayer");module.gl=pgl;sys.modules["genlayer.gl"]=pgl;sys.modules["genlayer.gl.vm"]=pgl.vm
    if isinstance(sender,bytes):sender=type(pgl.message.sender_address)(sender)
    pgl.message=pgl.message._replace(sender_address=sender,origin_address=sender,value=type(pgl.message.value)(vm.value));pgl.message_raw["sender_address"]=sender;pgl.message_raw["origin_address"]=sender;pgl.message_raw["datetime"]=vm._datetime

def setup(vm,c,merchant,buyer,usage=0,policy_authority=None):
    policy=policy_for(eth(policy_authority or merchant));digest=hashlib.sha256(policy.encode()).hexdigest()
    with vm.activate():
        sync(vm,c);pid=c.create_policy(URL,"REFUND-V2",digest);vm.value=1000;sync(vm,c);oid=c.create_funded_order(pid,eth(buyer),"ORDER-1","DIGITAL-SERVICE",1000);vm.deal(vm._contract_address,1000);vm.value=0;sync(vm,c)
        if usage:c.record_usage(oid,usage)
    with vm.prank(buyer):sync(vm,c);assert c.request_refund(oid)=="REFUND_REQUESTED"
    vm._policy_body=policy
    return oid

def mock(vm,outcome,clauses,reasons):
    vm.mock_web(re.escape(URL),{"status":200,"body":vm._policy_body.encode()})
    vm.mock_llm("(?s).*Facts=.*",json.dumps({"outcome":outcome,"cited_clause_ids":clauses,"reason_codes":reasons}))
    assert vm._match_web_mock(URL) is not None

def restore(c):
    p=c._instance.create_policy.__globals__["gl"];pgl=getattr(p,"_cached_gl",p);m=sys.modules["genlayer"];m.gl=pgl;sys.modules["genlayer.gl"]=pgl;sys.modules["genlayer.gl.vm"]=pgl.vm

def test_authority_funded_happy_path_executes_refund_and_validator():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer);assert json.loads(c.get_order(oid))["policy_url"]==URL;mock(vm,"ELIGIBLE",["WINDOW-14"],["WITHIN_WINDOW","UNUSED"]);vm.strict_mocks=True
    with vm.activate():sync(vm,c);assert c.adjudicate(oid)=="ELIGIBLE";restore(c);assert vm.run_validator() is True;assert c.settle(oid)=="REFUNDED";assert c.settle(oid)=="SETTLEMENT_NOT_ALLOWED"
    r=json.loads(c.get_order(oid));assert r["state"]=="REFUNDED" and r["held"]==0 and r["paid_buyer"]==1000

def test_ineligible_releases_escrow_to_authenticated_merchant():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer,2);mock(vm,"INELIGIBLE",["USED"],["USED"])
    with vm.activate():sync(vm,c);assert c.adjudicate(oid)=="INELIGIBLE";assert c.settle(oid)=="RELEASED_TO_MERCHANT"
    assert json.loads(c.get_order(oid))["paid_merchant"]==1000

def test_claimant_cannot_supply_or_mutate_facts_and_roles_hold():
    vm,c,merchant,buyer,outsider=deploy()
    digest=hashlib.sha256(policy_for(eth(merchant)).encode()).hexdigest()
    with vm.prank(outsider):sync(vm,c);assert c.create_funded_order(0,eth(buyer),"O","P",1)=="POLICY_NOT_FOUND"
    with vm.activate():sync(vm,c);pid=c.create_policy(URL,"REFUND-V2",digest)
    with vm.prank(outsider):sync(vm,c);assert c.create_funded_order(pid,eth(buyer),"O","P",1)=="POLICY_AUTHORITY_ONLY"
    # Only the funding merchant can instantiate an order under its policy.
    vm.value=1000
    with vm.activate():
        sync(vm,c);oid=c.create_funded_order(pid,eth(buyer),"ORDER-1","DIGITAL-SERVICE",1000);vm.deal(vm._contract_address,1000);vm.value=0
    with vm.prank(buyer):sync(vm,c);assert c.record_usage(oid,1)=="MERCHANT_ONLY"
    before=json.loads(c.get_order(oid))
    with vm.prank(outsider):sync(vm,c);assert c.record_usage(oid,1)=="MERCHANT_ONLY"
    assert json.loads(c.get_order(oid))["usage_units"]==before["usage_units"]==0

def test_ambiguous_never_moves_custody_and_poisoned_output_fails_closed():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer);mock(vm,"AMBIGUOUS",[],["MISSING_POLICY_RULE"])
    with vm.activate():sync(vm,c);assert c.adjudicate(oid)=="AMBIGUOUS";assert c.settle(oid)=="SETTLEMENT_NOT_ALLOWED";restore(c);assert vm.run_validator(leader_result={"outcome":"ELIGIBLE"}) is False
    assert json.loads(c.get_order(oid))["held"]==1000

def test_malformed_model_output_fails_closed():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer)
    vm.mock_web(re.escape(URL),{"status":200,"body":vm._policy_body.encode()});vm.mock_llm("(?s).*Facts=.*","PAY NOW")
    with vm.activate():
        sync(vm,c)
        try:c.adjudicate(oid);assert False
        except Exception:pass
    assert json.loads(c.get_order(oid))["state"]=="REFUND_REQUESTED"

def test_wrong_value_and_source_substitution_fail_closed():
    vm,c,merchant,buyer,_=deploy()
    with vm.activate():
        digest=hashlib.sha256(policy_for(eth(merchant)).encode()).hexdigest();sync(vm,c);pid=c.create_policy(URL,"REFUND-V2",digest);vm.value=999;sync(vm,c)
        with vm.expect_revert("WRONG_ESCROW_VALUE"):c.create_funded_order(pid,eth(buyer),"O","P",1000)
        vm.value=0
    oid=setup(vm,c,merchant,buyer);vm.mock_web(re.escape(URL),{"status":200,"body":vm._policy_body.replace("14","30").encode()});vm.mock_llm(".*",json.dumps({"outcome":"ELIGIBLE","cited_clause_ids":["WINDOW-14"],"reason_codes":["WITHIN_WINDOW"]}))
    with vm.activate():
        sync(vm,c)
        try:c.adjudicate(oid);assert False
        except Exception:pass
    assert json.loads(c.get_order(oid))["held"]==1000

def test_policy_authority_marker_and_outcome_reason_conflicts_fail_closed():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer,policy_authority=buyer);vm.mock_web(re.escape(URL),{"status":200,"body":vm._policy_body.encode()});vm.mock_llm("(?s).*Facts=.*",json.dumps({"outcome":"ELIGIBLE","cited_clause_ids":["WINDOW-14"],"reason_codes":["WITHIN_WINDOW"]}))
    with vm.activate():
        sync(vm,c)
        try:c.adjudicate(oid);assert False
        except Exception:pass
    assert json.loads(c.get_order(oid))["state"]=="REFUND_REQUESTED"

def test_outcome_and_reason_codes_cannot_contradict():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer)
    policy=json.loads(c.get_order(oid))["policy_version"]
    with vm.activate():
        sync(vm,c);validate=c._instance.adjudicate.__globals__["_verdict"]
        try:validate({"outcome":"ELIGIBLE","cited_clause_ids":["WINDOW-14"],"reason_codes":["USED"]},vm._policy_body,"REFUND-V2",hashlib.sha256(vm._policy_body.encode()).hexdigest());assert False
        except Exception:pass
    assert policy=="REFUND-V2" and json.loads(c.get_order(oid))["state"]=="REFUND_REQUESTED"

def test_version_and_contract_shape():
    _,c,*_=deploy();v=json.loads(c.get_contract_version());assert v["version"]==2 and "FUNDED_ORDER" in v["claim_boundary"]
    source=CONTRACT.read_text();assert "@gl.public.write.payable" in source and "emit_transfer(value=amount)" in source and "claim_text" not in source
