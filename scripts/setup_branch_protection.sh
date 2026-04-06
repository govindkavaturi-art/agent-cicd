#!/bin/bash
# Usage: ./setup_branch_protection.sh owner/repo
# Requires: GitHub CLI (gh) installed and authenticated

REPO=$1

if [ -z "$REPO" ]; then
  echo "Usage: ./setup_branch_protection.sh owner/repo"
  exit 1
fi

echo "Setting up branch protection for $REPO on main..."

gh api \
  --method PUT \
  -H "Accept: application/vnd.github.v3+json" \
  "/repos/$REPO/branches/main/protection" \
  -f 'required_pull_request_reviews[dismiss_stale_reviews]=false' \
  -F 'required_pull_request_reviews[required_approving_review_count]=1' \
  -f 'required_status_checks=null' \
  -F 'enforce_admins=false' \
  -f 'restrictions=null' \
  -F 'allow_force_pushes=false' \
  -F 'allow_deletions=false' \
  -F 'block_creations=false' \
  -F 'required_linear_history=false'

echo "Branch protection configured for $REPO:main"
echo "  - 1 required PR review"
echo "  - Direct push blocked"
echo "  - Force push blocked"
echo "  - Branch deletion blocked"
