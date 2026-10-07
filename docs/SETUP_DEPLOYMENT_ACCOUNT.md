# Son: create the restricted deployment account on `inspiron`

- **Audience:** the son / server administrator
- **Purpose:** create a dedicated `keeper-deploy` account that the owner (you) will use over SSH to run the deployment guide
- **Security model:** this account has **no `sudo`**, **no `docker` group membership**, and **no access to WordPress/Immich data**. All privileged operations (Docker, Nginx, Certbot, system packages, backups) are performed by the son using `sudo` in the main deployment guide.

> The main deployment guide (`docs/DEPLOYMENT_INSPIRON_STEP_BY_STEP.md`) assumes this account already exists. Run this first, then hand the SSH connection details to the owner.

## 1. Create the account (run as son with sudo)

```bash
# Create the account without a password (SSH key only)
sudo adduser --disabled-password --gecos '' keeper-deploy

# Verify it has no sudo access
sudo -l -U keeper-deploy
# Expected: "User keeper-deploy is not allowed to run sudo on inspiron."

# Verify it is NOT in the docker group
groups keeper-deploy
# Expected: only "keeper-deploy" (no "docker")
```

## 2. Create the SSH directory and authorized_keys (run as son with sudo)

```bash
# Create .ssh with correct ownership
sudo install -d -o keeper-deploy -g keeper-deploy -m 0700 /home/keeper-deploy/.ssh

# Paste the owner's PUBLIC key here (one per line).
# The owner must send you ONLY the .pub file (e.g., id_ed25519.pub).
# NEVER accept a private key, an authorized_keys file, or a key via chat/email.
sudo tee /home/keeper-deploy/.ssh/authorized_keys >/dev/null <<'EOF'
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI... owner@workstation
EOF

# Fix ownership and permissions (critical)
sudo chown keeper-deploy:keeper-deploy /home/keeper-deploy/.ssh/authorized_keys
sudo chmod 0600 /home/keeper-deploy/.ssh/authorized_keys
```

> **How to get the owner's public key:** the owner runs `cat ~/.ssh/id_ed25519.pub` (or `id_rsa.pub`) on their workstation and sends you **only that one line**. You paste it into the heredoc above. If they have multiple keys, add each on its own line.

## 3. Verify SSH works (owner tests from their workstation)

```bash
# Owner runs this from their PC
ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 keeper-deploy@inspiron "whoami && pwd"
# Expected output:
# keeper-deploy
# /home/keeper-deploy
```

If this fails, check:
- `inspiron` resolves to the correct IP (or use the IP directly)
- Port 22 is reachable (firewall/UFW allows SSH)
- The public key in `authorized_keys` matches the private key the owner is using
- `/home/keeper-deploy/.ssh` is `0700` and `authorized_keys` is `0600`, both owned by `keeper-deploy:keeper-deploy`

## 4. Create the deployment directory (run as son with sudo)

```bash
# The deployment guide clones the repo here
sudo install -d -o keeper-deploy -g keeper-deploy -m 0750 /srv/keeper-financial
```

## 5. Confirm the account is correctly restricted

```bash
# As son, verify the account cannot run sudo
sudo -u keeper-deploy sudo -n true 2>&1
# Expected: "sudo: a password is required" or "not allowed to run sudo"

# Verify no docker group access
sudo -u keeper-deploy docker ps 2>&1
# Expected: "permission denied" or "Cannot connect to the Docker daemon"

# Verify the account can read/write its own deployment directory
sudo -u keeper-deploy bash -c 'touch /srv/keeper-financial/test-write && rm /srv/keeper-financial/test-write && echo OK'
# Expected: OK
```

## 6. Hand off to the owner

Give the owner only:
- Hostname/IP: `inspiron` (or the public IP)
- SSH username: `keeper-deploy`
- SSH port: `22` (or your custom port)
- The path to the deployment directory: `/srv/keeper-financial`

Do **not** share:
- Any sudo password
- Any private keys
- WordPress or Immich credentials
- Docker socket access

The owner will now follow `docs/DEPLOYMENT_INSPIRON_STEP_BY_STEP.md` from their workstation, connecting as `keeper-deploy@inspiron`. The guide explicitly labels which commands the son (you) must run with `sudo` (`[SON/ROOT]`) and which the owner runs as `keeper-deploy` (`[DEPLOY]`).

## 7. (Optional) Restrict the SSH key to only the deployment directory

If you want defense-in-depth, you can restrict the key to only allow the commands needed for deployment. Add this prefix to the public key line in `authorized_keys`:

```text
restrict,command="cd /srv/keeper-financial && exec $SSH_ORIGINAL_COMMAND" ssh-ed25519 AAAA... owner@workstation
```

This forces every SSH session to `cd /srv/keeper-financial` first and prevents arbitrary command execution outside that directory. The owner can still run `git`, `docker compose`, `python`, etc. inside that tree.

> **Note:** The main deployment guide uses `sudo` for all privileged operations (Docker, Nginx, Certbot, system packages, backups). Those commands are run by you (the son) in labeled `[SON/ROOT]` sections. The `keeper-deploy` account only runs `git`, `docker compose config`, and non-privileged validation commands. This separation is intentional.