"""Checklist application errors kept separate from applicability outcomes."""


class ChecklistError(Exception):
    """Base class for deterministic checklist application errors."""


class UnsupportedActivityError(ChecklistError):
    """Raised when the requested activity is absent or inactive."""


class BusinessProfileError(ChecklistError):
    """Raised when profile facts do not match the governed fact vocabulary."""


class DuplicateFactCodeError(BusinessProfileError):
    """Raised when a pair-based input repeats one fact code."""


class RegulatoryCatalogError(ChecklistError):
    """Raised when governed database state cannot be evaluated safely."""


__all__ = [
    "BusinessProfileError",
    "ChecklistError",
    "DuplicateFactCodeError",
    "RegulatoryCatalogError",
    "UnsupportedActivityError",
]
