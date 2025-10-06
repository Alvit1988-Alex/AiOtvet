"""Lightweight in-process notification dispatcher."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from threading import Lock
from typing import Callable, DefaultDict, Iterable


Callback = Callable[[dict], None]


@dataclass
class NotificationManager:
    """Dispatches notifications to subscribers."""

    _subscribers: DefaultDict[str, list[Callback]]
    _lock: Lock

    def __init__(self) -> None:
        self._subscribers = defaultdict(list)
        self._lock = Lock()

    def subscribe(self, event: str, callback: Callback) -> None:
        with self._lock:
            self._subscribers[event].append(callback)

    def broadcast(self, event: str, payload: dict) -> None:
        for callback in list(self._subscribers[event]):
            callback({"event": event, "payload": payload})
