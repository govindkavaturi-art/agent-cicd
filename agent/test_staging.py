"""
AI Test Agent: Staging Integration Test Runner

This script is called by the CueAPI worker when a test-staging cue fires.
It runs integration tests against the live staging environment, and either
opens a PR to promote staging to main (on pass) or files a GitHub issue (on fail).

Usage: The CueAPI worker calls this script when it claims a test-staging task.
       Set CUEAPI_PAYLOAD as an environment variable with the cue payload JSON.
"""

import json
import os
import subprocess
import sys
import time
import requests

from config import (
    STAGING_URL,
    STAGING_HEALTH_URL,
    GITHUB_REPO,
    BOT_USERNAME,
    TEST_TIMEOUT_MINUTES,
    HEALTH_CHECK_RETRIES,
    HEALTH_CHECK_INTERVAL_SECONDS,
)
from failure_handler import handle_failure


def get_payload():
    raw = os.environ.get("CUEAPI_PAYLOAD", "{}")
    return json.loads(raw)


def preflight_check(expected_commit):
    """Verify staging has the expected commit deployed."""
    for i in range(HEALTH_CHECK_RETRIES):
        try:
            resp = requests.get(STAGING_HEALTH_URL, timeout=10)
            data = resp.json()
            deployed = data.get("commit", "")[:7]
            expected = expected_commit[:7]
            if deployed == expected:
                print(f"Pre-flight passed: {deployed} matches expected {expected}")
                return True
            print(f"Attempt {i+1}: expected {expected}, got {deployed}")
        except Exception as e:
            print(f"Attempt {i+1}: health check error: {e}")
        time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
    return False


def run_integration_tests():
    """Run your integration tests against staging.

    Replace the command below with your actual integration test command.
    The STAGING_URL environment variable is available for your tests to use.
    """
    result = subprocess.run(
        # Replace with your integration test command:
        # ["pytest", "integration_tests/", "-v", "--tb=short"],
        # ["npm", "run", "test:integration"],
        ["echo", "TODO: Replace with YOUR_INTEGRATION_TEST_COMMAND"],
        capture_output=True,
        text=True,
        timeout=TEST_TIMEOUT_MINUTES * 60,
        env={**os.environ, "STAGING_URL": STAGING_URL},
    )
    return result


def open_promotion_pr(commit_sha, test_output):
    """Open a PR from staging to main."""
    token = os.environ.get("BOT_GITHUB_TOKEN")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Count tests from output (customize parsing for your test framework).
    # pytest outputs "X passed" in the summary line. Other frameworks differ:
    #   - jest: "Tests: X passed, Y total"
    #   - go test: "ok" or "FAIL" per package
    # Adjust the parsing below to match your test runner's output format.
    test_count = "all"
    for line in test_output.split("\n"):
        if "passed" in line.lower():
            test_count = line.strip()
            break

    resp = requests.post(
        f"https://api.github.com/repos/{GITHUB_REPO}/pulls",
        headers=headers,
        json={
            "title": f"Agent auto-deploy: {test_count} tests passed",
            "head": "staging",
            "base": "main",
            "body": (
                f"Automated promotion from staging to main.\n\n"
                f"Commit: {commit_sha}\n"
                f"Tests: {test_count}\n\n"
                f"This PR was opened by the AI test agent after all "
                f"integration tests passed against staging."
            ),
        },
    )

    if resp.status_code == 201:
        print(f"PR opened: {resp.json()['html_url']}")
        return True
    elif resp.status_code == 422:
        print("PR already exists or no diff between staging and main.")
        return True
    else:
        print(f"Failed to open PR: {resp.status_code} {resp.text}")
        return False


def main():
    payload = get_payload()
    commit = payload.get("commit", "unknown")
    run_id = payload.get("run_id", "unknown")

    print(f"=== Test Staging Agent ===")
    print(f"Commit: {commit}")
    print(f"Run ID: {run_id}")

    # Pre-flight
    if not preflight_check(commit):
        handle_failure(
            title=f"Pre-flight failed: staging commit mismatch",
            body=f"Expected commit {commit[:7]} but staging has a different version deployed.",
            commit=commit,
            run_id=run_id,
        )
        sys.exit(1)

    # Run integration tests
    print("Running integration tests...")
    result = run_integration_tests()

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    if result.returncode == 0:
        print("All tests passed. Opening promotion PR...")
        open_promotion_pr(commit, result.stdout)
    else:
        handle_failure(
            title=f"Staging tests failed for {commit[:7]}",
            body=f"Integration tests failed.\n\nStdout:\n```\n{result.stdout[-2000:]}\n```\n\nStderr:\n```\n{result.stderr[-2000:]}\n```",
            commit=commit,
            run_id=run_id,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
