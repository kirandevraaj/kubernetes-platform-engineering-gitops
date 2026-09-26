# Encrypting vault_example_plaintext.yml (FAKE secrets only)

Ansible Vault encrypts variable files at rest. Collections and ansible-core
do not ship your secrets — you encrypt files you own.

## Create a lab password file (never commit)

```bash
# From automation/ansible/
echo lab-vault-password > .vault_pass_lab.txt
```

Add `.vault_pass_lab.txt` and any `*.vault` password files to `.gitignore`.

## Encrypt (non-interactive)

```bash
ansible-vault encrypt vars/vault_example_plaintext.yml \
  --vault-password-file .vault_pass_lab.txt \
  --output vars/vault_example.yml
```

**Windows note:** Native Windows control nodes often cannot run `ansible-vault` / `ansible-playbook` because ansible-core imports Unix `fcntl` and may hit stdin blocking-IO errors. Prefer **WSL**, a Linux VM, or a CI Linux agent as the Ansible controller. Keep this tree and the plaintext FAKE file in Git; create `vars/vault_example.yml` on a Unix controller with the command above. Playbook `14_vault_example.yml` falls back to `vault_example_plaintext.yml` when the encrypted file is absent.

Or copy then encrypt in place:

```bash
cp vars/vault_example_plaintext.yml vars/vault_example.yml
ansible-vault encrypt vars/vault_example.yml --vault-password-file .vault_pass_lab.txt
```

Lab password for this exercise only: `lab-vault-password`

## View / edit

```bash
ansible-vault view vars/vault_example.yml --vault-password-file .vault_pass_lab.txt
ansible-vault edit vars/vault_example.yml --vault-password-file .vault_pass_lab.txt
```

## Playbook

```bash
ansible-playbook playbooks/14_vault_example.yml --vault-password-file .vault_pass_lab.txt
```

## Rules

- `lab_dummy_password: "not-a-real-secret"` is intentional fake data.
- Never commit real AWS keys, cluster credentials, or production passwords.
- Prefer AWS IAM roles / kubeconfig outside Git over vaulted cloud keys in-repo.
