# Setup Guide

## Step 1: Copy the files

Copy `.github/workflows/`, `agent/`, and `scripts/` to your repo.

## Step 2: Generate GitHub tokens

Recommended: Use fine-grained personal access tokens for minimum required permissions.

**From your main account (DEPLOY_TOKEN):**
- Go to Settings → Developer settings → Personal access tokens → Fine-grained tokens
- Repository access: select your repo only
- Permissions needed: Contents (read/write), Pull requests (read/write), Workflows (read/write)

**From the bot account (BOT_GITHUB_TOKEN):**
- Same path: Fine-grained token
- Repository access: select your repo only
- Permissions needed: Contents (read/write), Pull requests (read/write), Issues (read/write)

If fine-grained tokens don't work for your org, classic PATs with `repo` scope will also work but grant broader access than needed.

## Step 3: Set up GitHub secrets

Add these secrets to your repo (Settings → Secrets and variables → Actions):

| Secret | Value |
|--------|-------|
| `DEPLOY_TOKEN` | Your main account fine-grained PAT |
| `BOT_GITHUB_TOKEN` | Bot account fine-grained PAT |
| `CUEAPI_API_KEY` | CueAPI API key |
| `HEALTH_ENDPOINT_URL` | Your staging health endpoint URL |
| `RESEND_API_KEY` | (Optional) Resend API key for failure emails |

## Step 4: Configure branch protection

```bash
./scripts/setup_branch_protection.sh your-org/your-repo
```

## Step 5: Create the staging branch

```bash
git checkout -b staging
git push origin staging
```

## Step 6: Customize the workflow files

Replace the TODO placeholders in each workflow file with your actual commands (test command, deploy command, environment setup).

## Step 7: Update agent/config.py

Set your staging URL, production URL, GitHub repo, and bot username.
