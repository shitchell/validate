"""
Configuration and secrets loading.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

def load_env_file(filename: str = ".validate.env") -> None:
    """
    Load environment variables from a file.
    Searches in current directory, then ~/.config/validate/.
    """
    search_paths = [
        Path.cwd() / filename,
        Path.home() / ".config" / "validate" / filename,
        Path.home() / filename 
    ]

    for path in search_paths:
        if path.exists():
            logger.debug(f"Loading secrets from {path}")
            try:
                with open(path, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            key, value = line.split("=", 1)
                            # Remove quotes if present
                            value = value.strip().strip("'").strip('"')
                            if key not in os.environ:
                                os.environ[key] = value
            except Exception as e:
                logger.warning(f"Failed to load env file {path}: {e}")
            return  # Stop after finding the first one (precedence: local > global)

def load_config_file(filename: str = "config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML files.
    Merges config from ~/.config/validate/config.yaml and ./.validate.yaml (local overrides global).
    """
    config = {}
    
    # Global config
    global_path = Path.home() / ".config" / "validate" / filename
    if global_path.exists():
        try:
            with open(global_path, "r") as f:
                global_config = yaml.safe_load(f)
                if global_config:
                    config.update(global_config)
        except Exception as e:
            logger.warning(f"Failed to load global config {global_path}: {e}")

    # Local config (overrides)
    local_path = Path.cwd() / ".validate.yaml"
    if local_path.exists():
        try:
            with open(local_path, "r") as f:
                local_config = yaml.safe_load(f)
                if local_config:
                    # Deep merge would be better, but shallow update is okay for now
                    config.update(local_config)
        except Exception as e:
            logger.warning(f"Failed to load local config {local_path}: {e}")
            
    return config
