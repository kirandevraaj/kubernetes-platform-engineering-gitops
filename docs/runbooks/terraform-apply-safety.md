# Terraform Apply Safety

## Rule
Never make an irreversible change before understanding **target** and **impact**.

## Pattern
**Check → Plan → Confirm → Execute → Verify**

1. `fmt` / `validate`  
2. `terraform plan -out=...` and **read every resource**  
3. Confirm blast radius (EKS, VPC, NAT, ALB, node groups, EBS — high risk)  
4. Apply **saved plan only** when approved  
5. Verify with AWS/kubectl READ-ONLY checks  

## Destructive
`terraform destroy`, replacing stateful resources, AZ/node group wipes — **WARNING**, explicit target, confirmation, verification. **Not** normal Section 26 actions.

## Lab note
Local Terraform state is a **production gap** — remote state + locking recommended later ([production-gaps.md](../operations/production-gaps.md)).

## Related
[terraform-plan-failure.md](./terraform-plan-failure.md) · [operational-antipatterns.md](../operations/operational-antipatterns.md)
