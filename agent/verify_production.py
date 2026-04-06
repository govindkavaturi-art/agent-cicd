"""
AI Test Agent: Production Verification

Called by the CueAPI worker when a verify-production cue fires.
Checks that production is healthy after a deploy.
"""

import json
import os
import sys
import time
import requests

from config import (
    PRODUCTION_HEALTH_URL,
    PRODUCTION_SITES,
    HEALTH_CHECK_RETRIES,
    HEALTH_CHECK_INTERVAL_SECONDS,
)
from failure_handler import handle_failure


def get_payload():
    raw = os.environ.get("CUEAPI_PAYLOAD", "{}")
    return json.loads(raw)


def verify_health(expected_commit):
    """Check production health endpoint."""
    for i in range(HEALTH_CHECK_RETRIES):
        try:
            resp = requests.get(PRODUCTION_HEALTH_URL, timeout=10)
            data = resp.json()

            # Check commit
            deployed = data.get("commit", "")[:7]
            expected = expected_commit[:7]
            if deployed != expected:
                print(f"Attempt {i+1}: commit mismatch. Expected {expected}, got {deployed}")
                time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
                continue

            # Check services
            status = data.get("status", "unknown")
            if status != "ok":
                print(f"Attempt {i+1}: status is {status}, not ok")
                time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)
                continue

            print(f"Production health verified: commit {deployed}, status {status}")
            return True

        except Exception as e:
            print(f"Attempt {i+1}: health check error: {e}")
            time.sleep(HEALTH_CHECK_INTERVAL_SECONDS)

    return False


def verify_sites():
    """Check that all production sites are reachable."""
    failures = []
    for url in PRODUCTION_SITES:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                print(f"OK: {url}")
            else:
                print(f"WARN: {url} returned {resp.status_code}")
                failures.append(f"{url} returned {resp.status_code}")
        except Exception as e:
            print(f"FAIL: {url} - {e}")
            failures.append(f"{url} - {e}")
    return failures


def main():
    payload = get_payload()
    commit = payload.get("commit", "unknown")
    run_id = payload.get("run_id", "unknown")

    print(f"=== Verify Production ===")
    print(f"Commit: {commit}")

    # Verify health
    if not verify_health(commit):
        handle_failure(
            title=f"Production health check failed for {commit[:7]}",
            body=f"Production health endpoint did not return expected commit after {HEALTH_CHECK_RETRIES} attempts.",
            commit=commit,
            run_id=run_id,
        )
        sys.exit(1)

    # Verify sites
    site_failures = verify_sites()
    if site_failures:
        handle_failure(
            title=f"Production site verification failed for {commit[:7]}",
            body=f"The following sites failed:\n" + "\n".join(f"- {f}" for f in site_failures),
            commit=commit,
            run_id=run_id,
        )
        sys.exit(1)

    print("Production verification passed.")


if __name__ == "__main__":
    main()
