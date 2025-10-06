"""HTTP client used by bots to communicate with the core API."""
from __future__ import annotations

import httpx


class ApiClient:
    def __init__(self, base_url: str = "http://localhost:8000/api") -> None:
        self.base_url = base_url
        self._client = httpx.AsyncClient(base_url=base_url)

    async def ensure_dialog(self, tg_user_id: int, message: str) -> dict:
        # TODO: expose dedicated endpoint for bot interactions.
        response = await self._client.post(
            "/dialogs",
            json={"tg_user_id": tg_user_id, "message": message},
        )
        response.raise_for_status()
        return response.json()
