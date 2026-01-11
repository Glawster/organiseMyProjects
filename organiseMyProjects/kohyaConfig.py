from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def getConfigPath() -> Path:
    return Path.home() / ".config" / "kohya" / "kohyaConfig.json"


def loadConfig() -> dict[str, Any]:
    configPath = getConfigPath()
    if not configPath.exists():
        return {}

    try:
        with configPath.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def saveConfig(config: dict[str, Any]) -> None:
    configPath = getConfigPath()
    configPath.parent.mkdir(parents=True, exist_ok=True)
    with configPath.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2, sort_keys=True)


def updateConfigFromArgs(config: dict[str, Any], updates: dict[str, Any]) -> bool:
    """
    Apply shallow updates into config. Returns True if changes were made.
    """
    changed = False
    for k, v in updates.items():
        if config.get(k) != v:
            config[k] = v
            changed = True
    return changed
