"""Fresh v3 usage-veto lifecycle using the existing authenticated policy id 1."""
import json
from run_v3_live import ADDRESS, OUT, create_account, create_client, execution, keys, studionet, view, wait_final

RESULT=OUT.parent/("v3-ineligible-"+ADDRESS.lower()+".json")

def main():
    accounts=[create_account(account_private_key="0x"+k.removeprefix("0x")) for k in keys()]
    clients=[create_client(chain=studionet,account=a) for a in accounts];steps=[]
    def send(step,actor,method,args,expected,value=0,order=None):
        h=str(clients[actor].write_contract(address=ADDRESS,function_name=method,args=args,value=value,leader_only=False))
        item={"id":step,"actor":accounts[actor].address,"method":method,"args":args,"value":value,"expected":expected,"tx_hash":h,"explorer":"https://explorer-studio.genlayer.com/tx/"+h,"status":"SUBMITTED"};steps.append(item);RESULT.write_text(json.dumps({"contract":ADDRESS,"steps":steps},indent=2)+"\n",encoding="utf-8")
        tx=wait_final(h);leader,actual=execution(tx);after=None if order is None else json.loads(view("get_order",[order]))
        item.update({"return":actual,"status":tx.get("status"),"leader_execution":leader,"consensus":tx.get("result_name"),"readback":after});RESULT.write_text(json.dumps({"contract":ADDRESS,"steps":steps},indent=2)+"\n",encoding="utf-8")
        if actual!=expected or leader!="SUCCESS" or tx.get("result_name")!="MAJORITY_AGREE":raise RuntimeError(str(item))
        return actual
    observed=json.loads(view("get_order",[2]))
    if observed.get("order_ref")=="PVS-V3-USAGE-001" and observed.get("state")=="REFUND_REQUESTED":
        oid=2;steps.append({"id":"I3-request-observed-after-RPC-502","tx_hash":"UNRECOVERED_FROM_CLIENT","return":"REFUND_REQUESTED","readback":observed,"limitation":"Signed request finalized, but the submitting client lost its hash when the RPC polling endpoint returned HTTP 502."})
    else:
        oid=int(json.loads(view("get_counts"))["order_count"])
        send("I1-fund",0,"create_funded_order",[1,accounts[1].address,"PVS-V3-USAGE-001","AI source-code review subscription","2026-12-31T23:59:59Z",1],str(oid),1)
        send("I2-record-usage",0,"record_usage",[oid,1],"USAGE_RECORDED",order=oid)
        send("I3-request",1,"request_refund",[oid],"REFUND_REQUESTED",order=oid)
    send("I4-adjudicate",1,"adjudicate",[oid],"INELIGIBLE",order=oid)
    send("I5-settle",1,"settle",[oid],"RELEASED_TO_MERCHANT",order=oid)
    final=json.loads(view("get_order",[oid]));complete=final["state"]=="RELEASED_TO_MERCHANT" and final["semantic_relation"]=="COVERED" and final["usage_units"]==1 and final["paid_merchant"]==1
    RESULT.write_text(json.dumps({"contract":ADDRESS,"scenario":"DETERMINISTIC_USAGE_VETO","steps":steps,"final_order":final,"complete":complete},indent=2)+"\n",encoding="utf-8");print("INELIGIBLE_COMPLETE" if complete else "INELIGIBLE_INCOMPLETE",RESULT)

if __name__=="__main__":main()
