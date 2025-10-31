import json
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parents[1] / "data" / "registry.json"

def load_registry_services():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Compress to what's needed for prompting
    out = {}
    for sname, sdef in data.get("services", {}).items():
        out[sname] = {
            "base_path": sdef.get("base_path"),
            "entities": {
                ename: {
                    "key_fields": edef.get("key_fields", []),
                    "fields": edef.get("fields", []),
                } for ename, edef in sdef.get("entities", {}).items()
            }
        }
    return out
