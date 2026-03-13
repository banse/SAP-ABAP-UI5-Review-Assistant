from collections.abc import AsyncIterator

import httpx
import pytest
from httpx import ASGITransport

from app.main import app


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
