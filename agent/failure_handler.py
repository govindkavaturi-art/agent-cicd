"""
Failure handler: email notification + GitHub issue creation.
Used by both test_staging.py and verify_production.py.
"""

import os
import requests

from config import GITHUB_REPO, NOTIFICATION_EMAIL, FROM_EMAIL


def handle_failure(title, body, commit, run_id):
    """Send failure email and create GitHub issue."""
    print(f"FAILURE: {title}")

    # Create GitHub issue
    _create_github_issue(title, body, commit, run_id)

    # Send email notification
    _send_email(title, body)


def _create_github_issue(title, body, commit, run_id):
    token = os.environ.get("BOT_GITHUB_TOKEN")
    if not token:
        print("WARNING: BOT_GITHUB_TOKEN not set, skipping issue creation")
        return

    issue_body = (
        f"{body}\n\n"
        f"---\n"
        f"Commit: `{commit}`\n"
        f"Run ID: `{run_id}`\n"
        f"Actions: https://github.com/{GITHUB_REPO}/actions/runs/{run_id}\n"
    )

    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/issues",
        headers={
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        },
        json={
            "title": f"[CI] {title}",
            "body": issue_body,
            "labels": ["bug", "ci-failure"],
        },
    )

    if resp.status_code == 201:
        print(f"Issue created: {resp.json()['html_url']}")
    else:
        print(f"Failed to create issue: {resp.status_code} {resp.text}")


def _send_email(title, body):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        print("WARNING: RESEND_API_KEY not set, skipping email")
        return

    resp = requests.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "from": FROM_EMAIL,
            "to": [NOTIFICATION_EMAIL],
            "subject": f"[CI FAILURE] {title}",
            "text": body,
        },
    )

    if resp.status_code == 200:
        print("Failure email sent.")
    else:
        print(f"Failed to send email: {resp.status_code} {resp.text}")
