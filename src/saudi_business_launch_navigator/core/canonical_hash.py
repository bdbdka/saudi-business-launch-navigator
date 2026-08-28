"""Stable canonical JSON hashing shared by runtime and governance modules."""

from __future__ import annotations

import hashlib
import json
import unicodedata


def compute_canonical_sha256(payload: object) -> str:
    """Hash NFC-normalized canonical JSON without changing the supplied value."""

    normalized_payload = _normalize_canonical_hash_value(payload)
    encoded = json.dumps(
        normalized_payload,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _normalize_canonical_hash_value(value: object) -> object:
    """Normalize string identity for hashing while preserving the source object."""

    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, dict):
        return {
            unicodedata.normalize("NFC", str(key)): _normalize_canonical_hash_value(item)
            for key, item in value.items()
        }
    if isinstance(value, list | tuple):
        return [_normalize_canonical_hash_value(item) for item in value]
    return value


__all__ = ["compute_canonical_sha256"]
