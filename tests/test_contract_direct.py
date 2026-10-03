from pathlib import Path
import hashlib, importlib, json, re, sys
from unittest.mock import patch
from gltest.direct import VMContext,create_address,deploy_contract

ROOT=Path(__file__).resolve().parents[1]; CONTRACT=ROOT/"contracts"/"PolicyVersionSentinel.py"
URL="https://merchant.example/refund-v3.txt"; DEADLINE="2099-12-31T23:59:59Z"

def eth(v):
    if isinstance(v,bytes):return "0x"+bytes(v).hex()
    s=str(v);return "0x"+s[5:] if s.startswith("addr#") else s

def policy_for(authority):
    return f"POLICY_START\nPOLICY_VERSION=REFUND-V3\nPOLICY_AUTHORITY={authority.lower()}\nCLAUSE_ID=COVERED-DIGITAL-TOOLS\nDeveloper productivity software subscriptions and source-code review tools are covered.\nCLAUSE_ID=EXCLUDED-CONSULTING\nConsulting and training services are excluded.\nPOLICY_END"

def deploy():
    merchant,buyer,outsider=[create_address(x) for x in ("merchant","buyer","outsider")];vm=VMContext(merchant)
    runtime=sys.modules.get("genlayer.gl.genvm_contracts")
    if runtime is not None and hasattr(runtime,"__known_contract__"):runtime.__known_contract__=None
    with patch("os.unlink",lambda _:None),vm.activate():
        c=deploy_contract(CONTRACT,vm,sdk_version="v0.2.16");p=c._instance.create_policy.__globals__["gl"];pgl=getattr(p,"_cached_gl",p);_=pgl.nondet;_=pgl.vm
        sdk=str(Path(pgl.__file__).resolve().parents[2]);runtime=sys.modules.get("genlayer.gl.genvm_contracts")
        if runtime is not None and hasattr(runtime,"__known_contract__"):runtime.__known_contract__=None
    if sdk not in sys.path:sys.path.insert(0,sdk)
    module=importlib.import_module("genlayer");module.gl=pgl;sys.modules["genlayer.gl"]=pgl;sys.modules["genlayer.gl.vm"]=pgl.vm
    return vm,c,merchant,buyer,outsider

def sync(vm,c):
    p=c._instance.create_policy.__globals__["gl"];pgl=getattr(p,"_cached_gl",p);sender=vm.sender
    sdk=str(Path(pgl.__file__).resolve().parents[2]);sys.path.insert(0,sdk) if sdk not in sys.path else None
    module=importlib.import_module("genlayer");module.gl=pgl;sys.modules["genlayer.gl"]=pgl;sys.modules["genlayer.gl.vm"]=pgl.vm
    if isinstance(sender,bytes):sender=type(pgl.message.sender_address)(sender)
    pgl.message=pgl.message._replace(sender_address=sender,origin_address=sender,value=type(pgl.message.value)(vm.value));pgl.message_raw["sender_address"]=sender;pgl.message_raw["origin_address"]=sender;pgl.message_raw["datetime"]=vm._datetime

def setup(vm,c,merchant,buyer,product="AI source-code review subscription",usage=0):
    policy=policy_for(eth(merchant));digest=hashlib.sha256(policy.encode()).hexdigest()
    with vm.activate():
        sync(vm,c);pid=c.create_policy(URL,"REFUND-V3",digest);vm.value=1000;sync(vm,c);oid=c.create_funded_order(pid,eth(buyer),"ORDER-1",product,DEADLINE,1000);vm.deal(vm._contract_address,1000);vm.value=0;sync(vm,c)
        if usage:c.record_usage(oid,usage)
    with vm.prank(buyer):sync(vm,c);assert c.request_refund(oid)=="REFUND_REQUESTED"
    vm._policy_body=policy;return oid

def mock(vm,relation,clause):
    vm.mock_web(re.escape(URL),{"status":200,"body":vm._policy_body.encode()});vm.mock_llm("(?s).*PRODUCT DESCRIPTION:.*",json.dumps({"relation":relation,"clause_id":clause}));assert vm._match_web_mock(URL)

def restore(c):
    p=c._instance.create_policy.__globals__["gl"];pgl=getattr(p,"_cached_gl",p);m=sys.modules["genlayer"];m.gl=pgl;sys.modules["genlayer.gl"]=pgl;sys.modules["genlayer.gl.vm"]=pgl.vm

def test_happy_path_refund_requires_counterparty_facts_and_consensus():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer);mock(vm,"COVERED","COVERED-DIGITAL-TOOLS");vm.strict_mocks=True
    with vm.activate():sync(vm,c);assert c.adjudicate(oid)=="ELIGIBLE";restore(c);assert vm.run_validator() is True;assert c.settle(oid)=="REFUNDED";assert c.settle(oid)=="SETTLEMENT_NOT_ALLOWED"
    r=json.loads(c.get_order(oid));assert r["state"]=="REFUNDED" and r["held"]==0 and r["paid_buyer"]==1000 and r["source_status"]=="VERIFIED"

def test_usage_is_deterministic_veto_even_if_ai_says_covered():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer,usage=2);mock(vm,"COVERED","COVERED-DIGITAL-TOOLS")
    with vm.activate():sync(vm,c);assert c.adjudicate(oid)=="INELIGIBLE";assert c.settle(oid)=="RELEASED_TO_MERCHANT"
    assert json.loads(c.get_order(oid))["paid_merchant"]==1000

def test_explicit_exclusion_releases_to_merchant():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer,"Custom training service");mock(vm,"EXCLUDED","EXCLUDED-CONSULTING")
    with vm.activate():sync(vm,c);assert c.adjudicate(oid)=="INELIGIBLE";assert c.settle(oid)=="RELEASED_TO_MERCHANT"

def test_buyer_cannot_manufacture_merchant_facts_or_policy():
    vm,c,merchant,buyer,outsider=deploy();policy=policy_for(eth(merchant));digest=hashlib.sha256(policy.encode()).hexdigest()
    with vm.activate():sync(vm,c);pid=c.create_policy(URL,"REFUND-V3",digest)
    with vm.prank(buyer):sync(vm,c);assert c.create_funded_order(pid,eth(outsider),"O","P",DEADLINE,1)=="POLICY_AUTHORITY_ONLY"
    vm.value=1000
    with vm.activate():sync(vm,c);oid=c.create_funded_order(pid,eth(buyer),"ORDER-1","AI review tool",DEADLINE,1000);vm.deal(vm._contract_address,1000);vm.value=0
    with vm.prank(buyer):sync(vm,c);assert c.record_usage(oid,1)=="MERCHANT_ONLY"

def test_malformed_or_unknown_output_is_nonbinding_and_custody_stays_held():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer);mock(vm,"PAY_NOW","FAKE")
    with vm.activate():sync(vm,c);assert c.adjudicate(oid)=="UNKNOWN";restore(c);assert vm.run_validator() is True;assert c.settle(oid)=="SETTLEMENT_NOT_ALLOWED"
    r=json.loads(c.get_order(oid));assert r["state"]=="REVIEW_UNKNOWN" and r["held"]==1000 and r["semantic_relation"]=="UNKNOWN"

def test_digest_substitution_and_unavailable_source_fail_closed_without_crash():
    vm,c,merchant,buyer,_=deploy();oid=setup(vm,c,merchant,buyer);vm.mock_web(re.escape(URL),{"status":200,"body":vm._policy_body.replace("covered","sometimes covered").encode()})
    with vm.activate():sync(vm,c);assert c.adjudicate(oid)=="UNKNOWN"
    r=json.loads(c.get_order(oid));assert r["source_status"]=="INTEGRITY_FAILURE" and r["held"]==1000

def test_wrong_value_and_role_guards():
    vm,c,merchant,buyer,outsider=deploy();policy=policy_for(eth(merchant));digest=hashlib.sha256(policy.encode()).hexdigest()
    with vm.activate():sync(vm,c);pid=c.create_policy(URL,"REFUND-V3",digest);vm.value=999;sync(vm,c)
    with vm.expect_revert("WRONG_ESCROW_VALUE"):c.create_funded_order(pid,eth(buyer),"O","AI review tool",DEADLINE,1000)
    vm.value=0
    with vm.prank(outsider):sync(vm,c);assert c.request_refund(0)=="ORDER_NOT_FOUND"
    oid=setup(vm,c,merchant,buyer)
    with vm.activate():sync(vm,c);assert c.recover_after_deadline(oid)=="DEADLINE_NOT_REACHED"

def test_only_merchant_can_grant_requested_refund():
    vm,c,merchant,buyer,outsider=deploy();oid=setup(vm,c,merchant,buyer)
    with vm.prank(outsider):sync(vm,c);assert c.merchant_grant_refund(oid)=="MERCHANT_ONLY"
    assert json.loads(c.get_order(oid))["held"]==1000

def test_contract_shape_and_version():
    _,c,*_=deploy();v=json.loads(c.get_contract_version());source=CONTRACT.read_text()
    assert v["version"]==3 and "SEMANTIC_COVERAGE_ONLY" in v["claim_boundary"]
    assert "@gl.public.write.payable" in source and "emit_transfer(value=amount)" in source and "Never decide dates, usage, eligibility, payment" in source
