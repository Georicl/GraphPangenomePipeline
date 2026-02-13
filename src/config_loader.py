import tomllib
import logging
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigManager:
    """
    Configuration Manager for Graph Pangenome Pipeline.
    Handles loading TOML files and merging CLI overrides.
    """
    def __init__(self, config_path: Optional[str] = None):
        # Initialize with default structure
        self.config: Dict[str, Any] = {
            "Global": {},
            "Cactus": {"maxCores": 1, "singularityImage": ""},
            "CactusOutFormat": {"vcf": True, "gfa": True, "gbz": True},
            "VgStats": {"stats": True, "paths": True},
            "VgIndex": {"autoindex": True, "threads": 1},
            "Annotation": {"singularityImage": ""},
            "Gaf": {"Gaf": True},
            "ann": {"annotation": True},
            "wgs": {"Parallel_job": 1, "Threads": 1, "MinMapQ": 0},
            "call": {"Parallel_job": 1, "Threads": 1}
        }
        if config_path and Path(config_path).exists():
            self.load_config(config_path)

    def load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from a TOML file and merge into defaults."""
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        try:
            with open(config_path, "rb") as f:
                loaded_config = tomllib.load(f)
            self.config = self._deep_merge(self.config, loaded_config)
            logging.info(f"Configuration loaded and merged from {path}")
        except Exception as e:
            logging.error(f"Error loading TOML file: {e}")
            raise
        
        return self.config

    def update_config(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge overrides into the current configuration.
        Overrides should be a nested dictionary matching the TOML structure.
        """
        self.config = self._deep_merge(self.config, overrides)
        return self.config

    def _deep_merge(self, base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Recursive deep merge of two dictionaries."""
        for key, value in overrides.items():
            if value is None:
                continue
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                base[key] = self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def get_config(self) -> Dict[str, Any]:
        """Return the current configuration dictionary."""
        return self.config

    def validate(self, run_modules: Dict[str, bool]):
        """
        Validation of the configuration based on which modules are active.
        """
        if run_modules.get("cactus"):
            if not self.config.get("Cactus", {}).get("seqFile"):
                raise ValueError("Cactus module requires 'seqFile' (--cactus-seq)")
            if not self.config.get("Cactus", {}).get("reference"):
                raise ValueError("Cactus module requires 'reference' (--cactus-ref)")

        if run_modules.get("wgs"):
            if not self.config.get("wgs", {}).get("DataTable"):
                raise ValueError("WGS module requires 'DataTable' (--wgs-data)")

        return True
