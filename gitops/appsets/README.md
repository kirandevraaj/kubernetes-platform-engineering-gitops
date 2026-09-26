# ApplicationSets
#
# Advanced Argo CD patterns live here (Section 23).
#
# Steady-state ApplicationSets (VMware Argo CD / ckad-lab):
# - platform-advanced-set.yaml          List generator → argo-advanced-{dev,test,stage}
# - platform-advanced-env-set.yaml      Conceptual multi-env → advanced-platform-{vmware,aws}
# - platform-advanced-cluster-set.yaml  Cluster generator (label-selected lab Secret only)
#
# Experiment-only:
# - platform-advanced-git-set.yaml      Git directory generator (apply temporarily)
#
# Nested ApplicationSet (App-of-ApplicationSets):
# - kubernetes/argo-app-of-applicationsets/ (managed by platform-app-of-applicationsets)
