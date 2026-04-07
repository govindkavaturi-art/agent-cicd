# Setup Guide

This guide walks you through setting up the agent-cicd pipeline from scratch. Follow it top to bottom and the pipeline will be running at the end.

## Prerequisites

Before you start, you need:

- A GitHub repo with a test suite
- Two GitHub accounts: your main account and a bot account (the AI test agent's identity)
- A CueAPI account (free tier works) or self-hosted CueAPI instance, or an alternative scheduling layer
- A Resend account for failure notification emails (optional)
- A deploy target (Railway, Render, Fly, Vercel, anywhere) with a health endpoint that returns the current git commit hash
- A machine to run the AI test agent on (any cloud VM, Mac Mini, Raspberry Pi, or laptop)

## Step 1: Create a bot GitHub account

This is your AI test agent's identity on GitHub. Sign up for a new GitHub account, then invite it as a collaborator to your repo with write access. Note the username, you'll need it later.

## Step 2: Generate GitHub tokens

Recommended: Use fine-grained personal access tokens for minimum required permissions.

**From your main account (DEPLOY_TOKEN):**
- Settings → Developer settings → Personal access tokens → Fine-grained tokens
- Repository access: select your repo only
- Permissions: Contents (read/write), Pull requests (read/write), Workflows (read/write)

**From the bot account (BOT_GITHUB_TOKEN):**
- Same path: Fine-grained token
- Repository access: select your repo only
- Permissions: Contents (read/write), Pull requests (read/write), Issues (read/write)

If fine-grained tokens don't work for your org, classic PATs with `repo` scope will also work but grant broader access than needed.

## Step 3: Set up CueAPI

**Option A: Hosted**

Sign up at [cueapi.ai](https://cueapi.ai). Free tier gives you everything this pipeline needs. Create an API key from the dashboard. Save it as `CUEAPI_API_KEY`.

**Option B: Self-hosted**

CueAPI is open source. Clone and run your own instance from [cueapi/cueapi-core](https://github.com/cueapi/cueapi-core). You'll need Postgres and Redis. Create an API key from your instance.

**Option C: Skip CueAPI entirely**

See the "Using this pipeline without CueAPI" section in the README for alternatives (webhooks, polling, or self-hosted message queue).

## Step 4: Set up the AI test agent machine

The AI test agent is a Python process that polls CueAPI for tasks and runs your tests when they fire. See the "The AI test agent" section in the README for the full picture of what it does and how to set it up.

For the minimum viable setup, you need a machine that:
- Has Python 3.9 or newer installed
- Can reach the public internet (to poll CueAPI and call GitHub APIs)
- Can stay running continuously

You can run this on a spare Mac Mini, a small cloud VM, a Raspberry Pi, or your laptop for testing.

On that machine:
```bash
pip install cueapi-worker
export CUEAPI_API_KEY=your_key_here
```

You'll start the worker in Step 8 after copying the agent files. For production, run the worker as a systemd service, launchd job, or Docker container so it restarts on failure. See the "Running the worker as a service" section at the bottom of this file.

## Step 5: Set up Resend (optional)

If you want failure notifications by email:

1. Sign up at [resend.com](https://resend.com)
2. Get an API key
3. Verify your sending domain (or use their test domain for development)
4. Save the key as `RESEND_API_KEY`

## Step 6: Add a health endpoint to your app

Your application must expose a health endpoint that returns JSON with at minimum the current commit hash. The pipeline uses this to verify deploys completed correctly.

**FastAPI:**
```python
import os
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {
        "commit": os.environ.get("GIT_COMMIT_SHA", "unknown"),
        "status": "ok"
    }
```

**Express:**
```javascript
app.get('/health', (req, res) => {
  res.json({
    commit: process.env.GIT_COMMIT_SHA || 'unknown',
    status: 'ok'
  });
});
```

**Flask:**
```python
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify(
        commit=os.environ.get('GIT_COMMIT_SHA', 'unknown'),
        status='ok'
    )
```

Most hosting platforms (Railway, Render, Fly, Heroku, Vercel) automatically expose the git commit SHA as an environment variable. Check your platform's docs for the exact variable name.

## Step 7: Copy the workflow files

Copy `.github/workflows/` from this repo into your repo's `.github/workflows/` directory.

Open each workflow file and customize:

- **feature-to-staging.yml**: Replace `YOUR_TEST_COMMAND` with your actual test command (`pytest tests/`, `npm test`, `go test ./...`, etc.)
- **staging-deploy.yml**: Replace `YOUR_TEST_COMMAND`, `YOUR_DEPLOY_COMMAND`, and add your deploy target. If your platform auto-deploys from the staging branch (Railway, Render, Vercel, Fly), you can leave the deploy step as a no-op and rely on the health check to verify the deploy completed. If your platform requires an explicit deploy command, add it here.
- **auto-approve-merge.yml**: Replace `YOUR_BOT_USERNAME` with your bot account's GitHub username from Step 1
- **production-verify.yml**: No changes needed unless you want to customize the wait time

**Important**: Remove the `if: false` line from each job. That line is only there because this template repo doesn't run the workflows itself.

## Step 8: Copy the agent files and start the worker

Copy the `agent/` directory to the machine you set up in Step 4.

Update `agent/config.py`:
```python
STAGING_URL = "https://staging.yourapp.com"
PRODUCTION_URL = "https://yourapp.com"
PRODUCTION_SITES = [PRODUCTION_URL, "https://docs.yourapp.com"]
GITHUB_REPO = "your-org/your-repo"
BOT_USERNAME = "your-bot-account"
NOTIFICATION_EMAIL = "you@yourdomain.com"
FROM_EMAIL = "ci@yourdomain.com"
```

Update `agent/test_staging.py`: replace `YOUR_INTEGRATION_TEST_COMMAND` with your actual integration test command.

Install dependencies and start the worker:
```bash
cd agent
pip install -r requirements.txt
cueapi-worker
```

The worker should start polling CueAPI and waiting for cues.

## Step 9: Configure branch protection
```bash
chmod +x scripts/setup_branch_protection.sh
./scripts/setup_branch_protection.sh your-org/your-repo
```

This requires the GitHub CLI (`gh`) installed and authenticated. The script blocks direct pushes to main, requires PR reviews, and blocks force pushes.

## Step 10: Add GitHub secrets

Go to your repo Settings → Secrets and variables → Actions → New repository secret. Add:

| Secret | Value |
|--------|-------|
| `DEPLOY_TOKEN` | Your main account fine-grained PAT from Step 2 |
| `BOT_GITHUB_TOKEN` | Bot account fine-grained PAT from Step 2 |
| `CUEAPI_API_KEY` | From Step 3 |
| `RESEND_API_KEY` | From Step 5 (optional) |
| `HEALTH_ENDPOINT_URL` | Your staging health endpoint URL |

## Step 11: Create the staging branch
```bash
git checkout main
git checkout -b staging
git push origin staging
```

## Step 12: Test the pipeline

Create a feature branch, make a small change, open a PR to staging. Watch the Actions tab. You should see:

1. `feature-to-staging.yml` runs your tests
2. On pass, the PR auto-merges to staging
3. `staging-deploy.yml` deploys and creates a CueAPI cue
4. Your AI agent claims the cue, runs integration tests against staging
5. On pass, the agent opens a PR from staging to main
6. `auto-approve-merge.yml` auto-approves and merges the PR
7. `production-verify.yml` creates a verify-production cue
8. Your agent verifies production health

If any step fails, check the troubleshooting section below.

## Troubleshooting

**Tests pass but PR doesn't auto-merge**
Check that `DEPLOY_TOKEN` has `repo` and `workflow` scopes (or the equivalent fine-grained permissions).

**CueAPI cue created but agent doesn't claim it**
Check that the CueAPI worker is running on your agent's machine and polling with the correct API key. Run `cueapi-worker --debug` to see polling activity.

**Agent can't open promotion PR**
Check that `BOT_GITHUB_TOKEN` has `repo` scope and the bot account has write access to the repo. Verify the bot username in `auto-approve-merge.yml` matches the actual bot account.

**Health check fails after deploy**
Make sure your deploy process sets the `GIT_COMMIT_SHA` environment variable. Most platforms set this automatically. The health endpoint must return the current commit, not a cached or stale value.

**Branch protection script fails**
Install GitHub CLI: [cli.github.com](https://cli.github.com), then run `gh auth login`. The script needs admin access to the repo.

**Workflows show as "skipped" or "failed" on GitHub**
If you forgot to remove the `if: false` line from a workflow file, the job will skip. Remove that line and push again.

## Running the worker as a service

For production, run the CueAPI worker as a background service so it survives reboots and restarts on failure.

**Linux (systemd):**

Create `/etc/systemd/system/cueapi-worker.service`:
```ini
[Unit]
Description=CueAPI Worker for agent-cicd
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/agent-cicd/agent
Environment="CUEAPI_API_KEY=your_key_here"
Environment="BOT_GITHUB_TOKEN=your_token_here"
Environment="RESEND_API_KEY=your_resend_key"
ExecStart=/usr/local/bin/cueapi-worker
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable cueapi-worker
sudo systemctl start cueapi-worker
sudo systemctl status cueapi-worker
```

**macOS (launchd):**

Create `~/Library/LaunchAgents/com.cueapi.worker.plist` with similar content using `<key>` blocks. See Apple's launchd documentation.

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /agent
COPY agent/ .
RUN pip install -r requirements.txt cueapi-worker
CMD ["cueapi-worker"]
```

Pass secrets via `docker run -e CUEAPI_API_KEY=... -e BOT_GITHUB_TOKEN=...`
