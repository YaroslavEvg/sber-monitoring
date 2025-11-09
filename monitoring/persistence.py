"""Потокобезопасная запись результатов мониторинга."""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict

from .types import HttpRouteConfig


class ResultWriter:
    """Хранит последние результаты проверок для чтения агентом Zabbix."""

    def __init__(self, output_path: str, schema_version: int = 1) -> None:
        self._raw_path = output_path
        self.base_path = Path(output_path).expanduser()
        self._lock = threading.Lock()
        self.schema_version = schema_version
        self._directory_mode = self._detect_directory_mode()

        if self._directory_mode:
            self.base_path.mkdir(parents=True, exist_ok=True)
        else:
            self.base_path.parent.mkdir(parents=True, exist_ok=True)

    def write_result(self, route_config: HttpRouteConfig, payload: Dict[str, Any]) -> None:
        target_file = self._target_file(route_config)
        with self._lock:
            state = self._safe_read(target_file)
            state.setdefault("routes", {})
            state["routes"][route_config.name] = payload
            state["last_updated"] = payload.get("timestamp")
            state["schema_version"] = self.schema_version
            target_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _detect_directory_mode(self) -> bool:
        if self.base_path.exists():
            return self.base_path.is_dir()
        raw = str(self._raw_path)
        separators = {os.sep}
        if os.altsep:
            separators.add(os.altsep)
        return any(raw.endswith(sep) for sep in separators)

    def _target_file(self, route_config: HttpRouteConfig) -> Path:
        if not self._directory_mode:
            return self.base_path

        if not route_config.source_path:
            target_dir = self.base_path
            target_dir.mkdir(parents=True, exist_ok=True)
            return target_dir / "monitoring_results.json"

        relative = Path(route_config.source_path)
        target_dir = self.base_path / relative.parent
        target_dir.mkdir(parents=True, exist_ok=True)
        stem = relative.stem if relative.suffix else relative.name
        filename = f"{stem}.json"
        return target_dir / filename

    def _safe_read(self, file_path: Path) -> Dict[str, Any]:
        if not file_path.exists():
            return {"routes": {}, "schema_version": self.schema_version}
        try:
            return json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"routes": {}, "schema_version": self.schema_version}
