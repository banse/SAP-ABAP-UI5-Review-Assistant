"""API routes for the SAP ABAP/UI5 Review Assistant.

Endpoints:
    GET  /health        -- Health check with version
    POST /review        -- Submit code for review (placeholder)
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    """Return service health and version."""
    return {"status": "ok", "version": "0.1.0"}


@router.post("/review")
async def review(body: dict[str, Any]) -> dict[str, Any]:
    """Accept a review request and return a placeholder response.

    The real implementation will be added in WP-0.2.
    """
    return {
        "status": "ok",
        "message": "Review endpoint placeholder — implementation pending.",
        "input_keys": list(body.keys()),
        "findings": [],
    }
