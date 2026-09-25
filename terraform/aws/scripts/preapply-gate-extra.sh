#!/usr/bin/env bash
set -euo pipefail
echo "=== EIP detail ==="
aws ec2 describe-addresses --region ap-south-1 --output json | python3 -c 'import sys,json; d=json.load(sys.stdin); print("eip_count",len(d.get("Addresses",[])))'
echo "=== NAT count ==="
aws ec2 describe-nat-gateways --region ap-south-1 --query 'length(NatGateways)' --output text
echo "=== LB count ==="
aws elbv2 describe-load-balancers --region ap-south-1 --query 'length(LoadBalancers)' --output text
echo "=== Target groups ==="
aws elbv2 describe-target-groups --region ap-south-1 --query 'TargetGroups[].{Name:TargetGroupName,Proto:Protocol,Port:Port,Vpc:VpcId}' --output table
ACCT=$(aws sts get-caller-identity --query Account --output text)
echo "=== Budgets ==="
aws budgets describe-budgets --account-id "$ACCT" --query 'Budgets[].{Name:BudgetName,Type:BudgetType,Amount:BudgetLimit.Amount,Unit:BudgetLimit.Unit}' --output table || echo budgets_failed
cd /workspace/terraform/aws
terraform fmt -check -recursive
echo "FMT_EXIT:$?"
python3 - <<'PY'
import re
text=open('/tmp/final-preapply.plan.txt',encoding='utf-8',errors='ignore').read()
# public_access_cidrs snippet
m=re.search(r'public_access_cidrs\s*=\s*\[(.*?)\]', text, re.S)
print('public_access_cidrs_match=', (m.group(0).replace('\n',' ')[:200] if m else 'NONE'))
# private subnet map_public
for line in text.splitlines():
    if 'map_public_ip_on_launch' in line:
        print(line.strip())
PY
