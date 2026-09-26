# Project 1 interview cheat sheet

## Architecture
VMware kubeadm + EKS · Jenkins CI · Git desired state · Argo CD · digest pins · MetalLB/ingress vs ALB · local-path vs EBS

## Five strongest experiments
1. Failed rollout `0.1.5` → Git rollback to `0.1.4` digest  
2. AWS worker + EBS recovery ~6.3 min  
3. Ingress SPOF → HA  
4. Argo ComparisonError (kustomize) fixed at source  
5. Snapshot restore + cross-ns lesson  

## Five numbers (lab, not SLAs)
~10s pod recreate · ~6s selfHeal · ~23s NS recovery · ~72s snap Ready · ~15s restore · ~6.3 min EBS worker

## Five decisions
Terraform AWS · EKS managed CP · GitOps CD · digest promote · ALB vs MetalLB split

## Five limitations
AWS obs Degraded (pod density) · AWS NP partial · Windows Ansible blocked · AWS Backup not restore-tested · no multi-region

## Five questions
Why not Jenkins kubectl deploy? Tag vs digest? EBS AZ? Running≠Ready? What did ComparisonError mean?
