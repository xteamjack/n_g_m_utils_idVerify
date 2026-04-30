import sys
import os
import logging
from .config import get_config
from .banner import print_error, print_status

logger = logging.getLogger("id-verify.config_check")

# Configuration keys required for the app to function
REQUIRED_CONFIG_KEYS = [
    "storage.docs.idVerify",
    "apps.idVerifyServer",
]

# Environment variables required for the app to function
REQUIRED_ENV_VARS = [
    "SANS_SERVER_CONFIG",
    "SANS_TENANT",
    "SANS_INSTANCE",
    "SANS_TARGET",
    "SANS_ENV"
]

def validate_config():
    """
    Validates that all required environment variables and configuration keys are present.
    Terminates the application if any validation fails.
    """
    print("  Validating configuration...")
    failed = False

    # 1. Check Environment Variables
    for var in REQUIRED_ENV_VARS:
        if not os.environ.get(var):
            print_status(f"Environment variable '{var}' is missing", success=False)
            failed = True
        else:
            # print_status(f"Environment variable '{var}' verified")
            pass

    if failed:
        print_error("Application failed to start due to missing environment variables.")
        sys.exit(1)

    # 2. Check Config Server Keys
    for key in REQUIRED_CONFIG_KEYS:
        value = get_config(key)
        if not value:
            print_status(f"Configuration key '{key}' could not be resolved from server", success=False)
            failed = True
        else:
            print_status(f"Configuration key '{key}' verified")

    if failed:
        print_error("Application failed to start due to missing configuration keys.")
        print("  Please ensure the Config Server is running and the keys are defined for this environment.")
        sys.exit(1)

    print_status("All configurations verified successfully.")
    print("")
