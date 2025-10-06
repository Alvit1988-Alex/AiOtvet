"""Admin bot HTTP client."""
from __future__ import annotations

import httpx


class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000/api") -> None:
        self._client = httpx.AsyncClient(base_url=base_url)

    async def list_waiting_dialogs(self) -> list[dict]:
        response = await self._client.get("/dialogs", params={"status": "waiting_operator"})
        response.raise_for_status()
        return response.json()
