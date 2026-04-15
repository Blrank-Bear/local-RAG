"""Generic HTTP API caller tool."""
from typing import Any, Optional

import httpx

from backend.tools.base import BaseTool


class APICallerTool(BaseTool):
    name = "api_caller"
    description = "Make an HTTP request to an external API. Supports GET and POST."

    async def run(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        body: Optional[dict] = None,
        timeout: float = 15.0,
    ) -> dict:
        method = method.upper()
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers or {},
                    params=params or {},
                    json=body,
                )
                try:
                    data = response.json()
                except Exception:
                    data = response.text
                return {
                    "status_code": response.status_code,
                    "data": data,
                    "url": url,
                }
        except httpx.TimeoutException:
            return {"error": "Request timed out", "url": url}
        except Exception as e:
            return {"error": str(e), "url": url}
