"""Вспомогательные фабрики для потоков мониторинга."""
from __future__ import annotations

from threading import Event
from typing import List, Sequence

from monitoring.persistence import ResultWriter
from monitoring.types import HttpRouteConfig
from threads.http_route import HttpRouteMonitor

MonitorList = List[HttpRouteMonitor]


def _http_builder(
    cfg: HttpRouteConfig, writer: ResultWriter, stop_event: Event, one_shot: bool
) -> HttpRouteMonitor:
    return HttpRouteMonitor(cfg, writer, stop_event, one_shot=one_shot)


BUILDERS = {
    "http": _http_builder,
}


def build_monitors(
    routes: Sequence[HttpRouteConfig], writer: ResultWriter, stop_event: Event, one_shot: bool = False
) -> MonitorList:
    monitors: MonitorList = []
    for cfg in routes:
        builder = BUILDERS.get(cfg.monitor_type)
        if not builder:
            raise ValueError(f"Неподдерживаемый тип монитора: {cfg.monitor_type}")
        monitors.append(builder(cfg, writer, stop_event, one_shot))
    return monitors


__all__ = ["build_monitors"]
