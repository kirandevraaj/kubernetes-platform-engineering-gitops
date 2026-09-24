# Common issues

Add an entry when a problem recurs. Include the symptom, the cause, and the fix that was actually used.

## Host cannot ping or SSH to 192.168.56.10–.12

**Symptom.** `ssh k8s-ctrl-01` hangs. `ping 192.168.56.10` gets no reply. `vmrun` still shows the VMs running, and VMware Tools reports guest addresses `192.168.56.10`, `.11`, and `.12`.

**Cause.** The nodes use host-only `VMnet1` (`192.168.56.0/24`). On 24 September 2026 the host adapter `VMware Network Adapter VMnet1` had fallen back to a `169.254.x.x` address, so Windows had no route to `192.168.56.0/24`. The guests themselves were up; their NAT interfaces on `192.168.50.0/24` still answered.

**Fix used.** Set a static address on the host adapter:

```text
netsh interface ipv4 set address name="VMware Network Adapter VMnet1" static 192.168.56.1 255.255.255.0
```

That command needs an elevated shell. After it, ping and SSH to `.10`, `.11`, and `.12` succeeded. The guest `lab0` addresses were already correct and were left unchanged.

## kubectl on the workstation talks to an unexpected cluster

**Symptom.** Commands succeed, but nodes or namespaces do not match the lab.

**Check.** `kubectl config current-context`. The lab context observed during bootstrap was `ckad-lab`. `docker-desktop` is also configured and points somewhere else. Confirm the context before any future write.
