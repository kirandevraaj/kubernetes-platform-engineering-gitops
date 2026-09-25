#!/usr/bin/env bash
set -euo pipefail
cd /workspace/terraform/aws

echo "== AWS identity (account only) =="
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
echo "account=${ACCOUNT}"

echo "== Public IP for API CIDR =="
PUBIP="$(curl -fsS https://checkip.amazonaws.com | tr -d '[:space:]')"
echo "cidr=${PUBIP}/32"

echo "== terraform plan =="
terraform plan -no-color -input=false \
  -var="cluster_endpoint_public_access_cidrs=[\"${PUBIP}/32\"]" \
  -out=/tmp/platform-lab.tfplan | tee /tmp/tfplan.out

echo "== plan summary =="
terraform show -no-color /tmp/platform-lab.tfplan | awk '
  /^Plan:/{print; found=1}
  /^  # /{c++}
  END{print "resource_blocks_approx=" c}
'
grep -E '^Plan:|Error|Warning:' /tmp/tfplan.out || true

echo "== resource addresses to create =="
terraform show -json /tmp/platform-lab.tfplan > /tmp/platform-lab.tfplan.json
python3 - <<'PY'
import json
p=json.load(open("/tmp/platform-lab.tfplan.json"))
changes=p.get("resource_changes",[])
creates=[c["address"] for c in changes if "create" in c.get("change",{}).get("actions",[])]
print(f"create_count={len(creates)}")
for a in sorted(creates):
    print(a)
PY
