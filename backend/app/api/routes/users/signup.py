"""User signup endpoint (disabled)."""

from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/signup")
def register_user() -> Any:
    """Signup is currently disabled."""
    raise HTTPException(status_code=403, detail="Signups are currently disabled.")
