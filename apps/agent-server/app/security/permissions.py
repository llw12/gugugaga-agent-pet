from enum import Enum


class RiskLevel(str, Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


class PermissionDenied(RuntimeError):
    pass


def ensure_allowed(risk_level: RiskLevel) -> None:
    if risk_level in {RiskLevel.SAFE, RiskLevel.LOW}:
        return
    if risk_level is RiskLevel.MEDIUM:
        raise PermissionDenied("medium risk tools require approval and are not executable yet")
    if risk_level is RiskLevel.HIGH:
        raise PermissionDenied("high risk tools are disabled in the current phase")
    raise PermissionDenied("blocked tools cannot be executed")
