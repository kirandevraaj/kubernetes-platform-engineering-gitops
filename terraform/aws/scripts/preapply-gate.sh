#!/usr/bin/env bash
set -euo pipefail
OUT=/tmp/preapply-gate-report.txt
: > "$OUT"
log() { echo "$@" | tee -a "$OUT"; }

log "=== B. ACCOUNT / REGION ==="
ACCT=$(aws sts get-caller-identity --query Account --output text)
ARN=$(aws sts get-caller-identity --query Arn --output text)
log "account=${ACCT}"
log "arn_suffix=${ARN##*:}"
log "region_env=${AWS_DEFAULT_REGION:-unset} AWS_REGION=${AWS_REGION:-unset}"
aws configure get region 2>/dev/null | awk '{print "configured_region="$0}' | tee -a "$OUT" || true
aws configure list 2>/dev/null | awk '
  /name/{print}
  /access_key/{print $1,$2,"<redacted>",$4,$5}
  /secret_key/{print $1,$2,"<redacted>",$4,$5}
  /region/{print}
' | tee -a "$OUT"
log "aws_dir_mount:"
ls -la /root/.aws 2>&1 | awk '{print $1,$9}' | tee -a "$OUT"
log "AZs:"
aws ec2 describe-availability-zones --region ap-south-1 --filters Name=state,Values=available \
  --query 'AvailabilityZones[].ZoneName' --output text | tee -a "$OUT"

log ""
log "=== C. READ-ONLY INVENTORY ap-south-1 ==="
log "-- VPCs --"
aws ec2 describe-vpcs --region ap-south-1 \
  --query 'Vpcs[].{VpcId:VpcId,Cidr:CidrBlock,IsDefault:IsDefault,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table | tee -a "$OUT"

log "-- CIDR overlap check vs 10.50.0.0/16 --"
aws ec2 describe-vpcs --region ap-south-1 --query 'Vpcs[].CidrBlock' --output text | tr '\t' '\n' | while read -r c; do
  if [[ "$c" == "10.50.0.0/16" ]]; then log "CONFLICT exact: $c"; fi
  # note simple string check for 10.50. overlap
  if [[ "$c" == 10.50.* ]]; then log "CONFLICT 10.50.* present: $c"; else log "ok existing: $c"; fi
done

log "-- Subnets (count + any 10.50) --"
aws ec2 describe-subnets --region ap-south-1 \
  --query 'length(Subnets)' --output text | awk '{print "subnet_count="$0}' | tee -a "$OUT"
aws ec2 describe-subnets --region ap-south-1 \
  --filters Name=cidr-block,Values=10.50.* \
  --query 'Subnets[].{Id:SubnetId,Cidr:CidrBlock,Az:AvailabilityZone,Vpc:VpcId}' \
  --output table | tee -a "$OUT" || true

log "-- IGW / NAT / EIP --"
aws ec2 describe-internet-gateways --region ap-south-1 --query 'length(InternetGateways)' --output text | awk '{print "igw_count="$0}' | tee -a "$OUT"
aws ec2 describe-nat-gateways --region ap-south-1 --filter Name=state,Values=available,pending \
  --query 'NatGateways[].{Id:NatGatewayId,State:State,Vpc:VpcId,Subnet:SubnetId}' --output table | tee -a "$OUT"
aws ec2 describe-addresses --region ap-south-1 \
  --query 'Addresses[].{PublicIp:PublicIp,Assoc:AssociationId,Alloc:AllocationId,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table | tee -a "$OUT"

log "-- EKS clusters --"
aws eks list-clusters --region ap-south-1 --output text | tee -a "$OUT"

log "-- EC2 instances (running/pending) --"
aws ec2 describe-instances --region ap-south-1 \
  --filters Name=instance-state-name,Values=running,pending \
  --query 'Reservations[].Instances[].{Id:InstanceId,Type:InstanceType,State:State.Name,Name:Tags[?Key==`Name`]|[0].Value}' \
  --output table | tee -a "$OUT"

log "-- ELBv2 / TargetGroups --"
aws elbv2 describe-load-balancers --region ap-south-1 \
  --query 'LoadBalancers[].{Name:LoadBalancerName,Type:Type,Scheme:Scheme,Arn:LoadBalancerArn}' \
  --output table | tee -a "$OUT"
aws elbv2 describe-target-groups --region ap-south-1 --query 'length(TargetGroups)' --output text | awk '{print "tg_count="$0}' | tee -a "$OUT"

log "-- IAM roles matching platform-lab --"
aws iam list-roles --query "Roles[?contains(RoleName, 'platform-lab') || contains(RoleName, 'platform_lab')].RoleName" --output text | tee -a "$OUT" || true
log "-- IAM roles matching aws-lbc / eks-node / eks-cluster prefixes --"
aws iam list-roles --query "Roles[?contains(RoleName, 'platform-lab-aws-lab')].RoleName" --output text | tee -a "$OUT" || true

log "-- Security groups named platform-lab --"
aws ec2 describe-security-groups --region ap-south-1 \
  --filters Name=group-name,Values='*platform-lab*' \
  --query 'SecurityGroups[].{Name:GroupName,Id:GroupId,Vpc:VpcId}' --output table | tee -a "$OUT" || true

log "-- Budgets (read-only) --"
if aws budgets describe-budgets --account-id "$ACCT" --max-results 20 --query 'Budgets[].BudgetName' --output text 2>>"$OUT"; then
  :
else
  log "budgets_query_failed_or_none"
fi

log ""
log "=== PUBLIC IP (for CIDR decision, not applied) ==="
PUBIP=$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')
log "workstation_public_ip=${PUBIP}"
log "suggested_cidr=${PUBIP}/32"
log "terraform.tfvars_exists=$(test -f /workspace/terraform/aws/terraform.tfvars && echo yes || echo no)"

log ""
log "=== F. TERRAFORM FMT/INIT/VALIDATE ==="
cd /workspace/terraform/aws
terraform fmt -check -recursive 2>&1 | tee -a "$OUT" || log "FMT_CHECK_EXIT=$?"
terraform init -input=false 2>&1 | tee -a "$OUT"
terraform validate 2>&1 | tee -a "$OUT"

log ""
log "=== G. TERRAFORM PLAN ==="
terraform plan -no-color -input=false \
  -var="cluster_endpoint_public_access_cidrs=[\"${PUBIP}/32\"]" \
  -out=/tmp/final-preapply.tfplan 2>&1 | tee /tmp/final-preapply.plan.txt | tee -a "$OUT"
grep -E '^Plan:|Error' /tmp/final-preapply.plan.txt | tee -a "$OUT"

terraform show -json /tmp/final-preapply.tfplan > /tmp/final-preapply.tfplan.json
python3 - <<'PY' | tee -a "$OUT"
import json
from collections import Counter
p=json.load(open("/tmp/final-preapply.tfplan.json"))
changes=p.get("resource_changes",[])
creates=[c for c in changes if "create" in c.get("change",{}).get("actions",[])]
updates=[c for c in changes if "update" in c.get("change",{}).get("actions",[])]
deletes=[c for c in changes if "delete" in c.get("change",{}).get("actions",[])]
print(f"create_count={len(creates)} update_count={len(updates)} delete_count={len(deletes)}")
types=Counter(c["type"] for c in creates)
print("create_types:")
for t,n in sorted(types.items()):
    print(f"  {t}: {n}")
print("create_addresses:")
for a in sorted(c["address"] for c in creates):
    print(a)
blob=" ".join(c["address"] for c in creates)
for u in ["aws_db_","aws_rds","aws_route53","aws_acm","aws_waf","aws_cloudfront","aws_ecr","aws_elasticsearch","aws_msk","aws_dynamodb","aws_elasticache"]:
    if u in blob:
        print("UNEXPECTED", u)
print("nat_gateway_count", sum(1 for c in creates if c["type"]=="aws_nat_gateway"))
print("eip_count", sum(1 for c in creates if c["type"]=="aws_eip"))
print("aws_lb_count", sum(1 for c in creates if c["type"]=="aws_lb"))
PY

log ""
log "REPORT_FILE=$OUT"
log "PLAN_DONE"
