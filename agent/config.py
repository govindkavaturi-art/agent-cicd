"""
Configuration for the AI test agent.
Update these values for your setup.
"""

# Your staging environment
STAGING_URL = "https://staging.yourapp.com"
STAGING_HEALTH_URL = f"{STAGING_URL}/health"

# Your production environment
PRODUCTION_URL = "https://yourapp.com"
PRODUCTION_HEALTH_URL = f"{PRODUCTION_URL}/health"

# Additional production sites to verify (add your docs, dashboard, etc.)
PRODUCTION_SITES = [
    PRODUCTION_URL,
    # "https://docs.yourapp.com",
    # "https://dashboard.yourapp.com",
]

# GitHub
GITHUB_REPO = "your-org/your-repo"  # owner/repo format
BOT_USERNAME = "your-bot-account"

# Notifications
NOTIFICATION_EMAIL = "you@yourdomain.com"
FROM_EMAIL = "ci@yourdomain.com"

# Timeouts
TEST_TIMEOUT_MINUTES = 40
HEALTH_CHECK_RETRIES = 5
HEALTH_CHECK_INTERVAL_SECONDS = 30
