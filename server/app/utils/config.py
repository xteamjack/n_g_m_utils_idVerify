import os
import json
import urllib.request
import logging

logger = logging.getLogger("id-verify.config")

_config_cache = {}

def get_config(key: str) -> any:
    """
    Fetches a configuration value from the SANS-Way Config Server.
    Uses environment variables for context (Tenant, Instance, Target, Env).
    """
    if key in _config_cache:
        return _config_cache[key]

    config_server = os.environ.get("SANS_SERVER_CONFIG")
    if not config_server:
        logger.error(f"SANS_SERVER_CONFIG environment variable is missing. Failed to resolve key: {key}")
        return None

    tenant = os.environ.get("SANS_TENANT")
    if not tenant:
        logger.error(f"SANS_TENANT environment variable is missing. Cannot fetch '{key}'")
        return None

    instance = os.environ.get("SANS_INSTANCE")
    if not instance:
        logger.error(f"SANS_INSTANCE environment variable is missing. Cannot fetch '{key}'")
        return None

    target = os.environ.get("SANS_TARGET")
    if not target:
        logger.error(f"SANS_TARGET environment variable is missing. Cannot fetch '{key}'")
        return None

    env = os.environ.get("SANS_ENV")
    if not env:
        logger.error(f"SANS_ENV environment variable is missing. Cannot fetch '{key}'")
        return None

    # Ensure config_server doesn't have a trailing slash for consistent URL building
    config_server = config_server.rstrip('/')

    # Construct the API URL
    url = f"{config_server}/api/key?key={key}&tenant={tenant}&target={target}&instance={instance}&env={env}"
    
    try:
        logger.info(f"Fetching config for '{key}' from {url}")
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            value = data.get("value")
            
            if value is not None:
                _config_cache[key] = value
                return value
            
            logger.warning(f"Config key '{key}' not found or has no value.")
    except Exception as e:
        logger.error(f"Failed to fetch config for '{key}': {e}")
    
    return None
