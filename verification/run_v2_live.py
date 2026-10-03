"""Reproducible two-wallet StudioNet happy/failure lifecycle for contract v2."""
import base64, hashlib, json, time
from pathlib import Path
import requests
from genlayer_py import create_account, create_client
from genlayer_py.abi import calldata
from genlayer_py.abi.transactions import serialize
from genlayer_py.chains import studionet

ROOT=Path(__file__).resolve().parents[1]
ADDRESS="0x5Ea83Be7737a63B57543d00CD2bFB92De4Ef2f96"
RPC="https://studio.genlayer.com/api"
POLICY_URL="https://raw.githubusercontent.com/dearmore5382/PolicyVersionSentinel/main/samples/refund-policy-v2.txt"
KEY_SOURCE=ROOT.parent/"DAOProposalContextVerifier"/".env.lifecycle"
OUT=ROOT/"verification"/("v2-live-"+ADDRESS.lower()+".json")

def rpc(method,params):
    r=requests.post(RPC,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout=120);r.raise_for_status();p=r.json()
    if "error" in p:raise RuntimeError(str(p["error"]))
    return p["result"]

def view(method,args=None):
    data=serialize([calldata.encode({"method":method,"args":args or []}),b"\x00"])
    raw=rpc("gen_call",[{"type":"read","to":ADDRESS,"from":"0x0000000000000000000000000000000000000001","value":"0x0","data":data,"transaction_hash_variant":"latest-final"}])
    return str(calldata.decode(bytes.fromhex(raw.removeprefix("0x"))))

def wait_final(tx_hash):
    deadline=time.monotonic()+1500
    while time.monotonic()<deadline:
        tx=rpc("eth_getTransactionByHash",[tx_hash])
        if tx and tx.get("status")=="FINALIZED":return tx
        time.sleep(5)
    raise RuntimeError("FINALITY_TIMEOUT")

def tx_return(tx):
    receipts=(tx.get("consensus_data") or {}).get("leader_receipt") or [];receipts=[receipts] if isinstance(receipts,dict) else receipts
    leaders=[x for x in receipts if x.get("mode")=="leader"]
    if not leaders or leaders[-1].get("execution_result")!="SUCCESS":raise RuntimeError("LEADER_EXECUTION_FAILED")
    raw=base64.b64decode(leaders[-1]["result"])
    try:return str(calldata.decode(raw))
    except Exception:
        if len(raw)>1 and raw[0]==0:return str(calldata.decode(raw[1:]))
        raise

def keys():
    values={}
    for line in KEY_SOURCE.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k,v=line.split("=",1);values[k.strip()]=v.strip()
    return [values["WALLET_A_PRIVATE_KEY"],values["WALLET_B_PRIVATE_KEY"]]

def main():
    local=(ROOT/"contracts"/"PolicyVersionSentinel.py").read_bytes();deployed=base64.b64decode(rpc("gen_getContractCode",[ADDRESS]))
    if local!=deployed:raise RuntimeError("SOURCE_PARITY_FAILED")
    policy=requests.get(POLICY_URL,timeout=60);policy.raise_for_status();digest=hashlib.sha256(policy.content).hexdigest()
    accounts=[create_account(account_private_key="0x"+k.removeprefix("0x")) for k in keys()];clients=[create_client(chain=studionet,account=a) for a in accounts]
    journal={"network":"studionet","contract":ADDRESS,"contract_source_sha256":hashlib.sha256(local).hexdigest(),"source_parity":True,"policy_url":POLICY_URL,"policy_digest":digest,"roles":{"merchant":accounts[0].address,"buyer":accounts[1].address},"steps":[],"complete":False}
    def send(step,actor,method,args,expected,value=0,order_id=None,unchanged=False):
        before=None if order_id is None else view("get_order",[order_id])
        h=str(clients[actor].write_contract(address=ADDRESS,function_name=method,args=args,value=value,leader_only=False));tx=wait_final(h);actual=tx_return(tx);after=None if order_id is None else view("get_order",[order_id])
        e={"id":step,"actor":accounts[actor].address,"method":method,"args":args,"value":value,"return":actual,"expected":expected,"tx_hash":h,"explorer":"https://explorer-studio.genlayer.com/tx/"+h,"status":tx.get("status"),"consensus":tx.get("result_name"),"state_unchanged":before==after if unchanged else None,"readback":json.loads(after) if after and after!="NOT_FOUND" else after};journal["steps"].append(e);OUT.write_text(json.dumps(journal,indent=2)+"\n",encoding="utf-8")
        if tx.get("result_name")!="MAJORITY_AGREE" or actual!=expected or (unchanged and before!=after):raise RuntimeError(step+":UNEXPECTED:"+actual)
        return actual
    counts=json.loads(view("get_counts"));pid=int(send("H1-create-policy",0,"create_policy",[POLICY_URL,"REFUND-V2",digest],str(counts["policy_count"])))
    send("F1-wrong-authority",1,"create_funded_order",[pid,accounts[1].address,"PVS-V2-FAIL","DIGITAL-SERVICE",1],"POLICY_AUTHORITY_ONLY")
    counts=json.loads(view("get_counts"));oid=int(send("H2-create-funded-order",0,"create_funded_order",[pid,accounts[1].address,"PVS-V2-LIVE-001","DIGITAL-SERVICE",1],str(counts["order_count"]),value=1))
    send("F2-wrong-refund-caller",0,"request_refund",[oid],"BUYER_ONLY",order_id=oid,unchanged=True)
    send("H3-buyer-request",1,"request_refund",[oid],"REFUND_REQUESTED",order_id=oid)
    send("H4-adjudicate",0,"adjudicate",[oid],"ELIGIBLE",order_id=oid)
    send("H5-settle",0,"settle",[oid],"REFUNDED",order_id=oid)
    send("F3-settle-replay",0,"settle",[oid],"SETTLEMENT_NOT_ALLOWED",order_id=oid,unchanged=True)
    journal["final_order"]=json.loads(view("get_order",[oid]));journal["complete"]=journal["final_order"]["state"]=="REFUNDED" and int(journal["final_order"]["held"])==0 and int(journal["final_order"]["paid_buyer"])==1;OUT.write_text(json.dumps(journal,indent=2)+"\n",encoding="utf-8");print("E2E_COMPLETE" if journal["complete"] else "E2E_INCOMPLETE",OUT)

if __name__=="__main__":main()
