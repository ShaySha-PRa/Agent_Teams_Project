"""SHA-256 hash chain helper for AuditLog and StateTransition."""

from __future__ import annotations

import hashlib
import json


def compute_hash(data: dict | str, prev_hash: str | None = None) -> str:
    """Compute a SHA-256 hash incorporating the previous hash for chain integrity.

    Args:
        data: The current entry's data (dict will be JSON-serialised).
        prev_hash: The previous entry's hash, or None for the genesis entry.

    Returns:
        Hex-encoded SHA-256 digest.
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)

    payload = f"{prev_hash or 'GENESIS'}:{data}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_chain(entries: list[dict]) -> bool:
    """Verify the integrity of a hash chain.

    Each entry must have 'prev_hash' and 'current_hash' keys.
    Returns True if the chain is valid.
    """
    prev: str | None = None
    for entry in entries:
        expected = compute_hash(entry.get("data", ""), prev)
        if expected != entry.get("current_hash"):
            return False
        prev = expected
    return True
