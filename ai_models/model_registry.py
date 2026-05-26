from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class LocalModelRegistry:
    def __init__(self, registry_dir: str = "ai_models/registry") -> None:
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

    def register(self, model_name: str, model_type: str, artifact_path: str, metrics: dict[str, Any], feature_order: list[str]) -> dict:
        version = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        manifest = {
            "model_name": model_name,
            "model_type": model_type,
            "version": version,
            "artifact_path": artifact_path,
            "metrics": metrics,
            "feature_order": feature_order,
            "registered_at": datetime.utcnow().isoformat(),
        }
        manifest_path = self.registry_dir / f"{model_name}-{version}.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        active_path = self.registry_dir / f"{model_name}_active.json"
        active_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    def active(self, model_name: str) -> dict | None:
        path = self.registry_dir / f"{model_name}_active.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
