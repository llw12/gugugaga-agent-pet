import pytest

from app.security.permissions import PermissionDenied, RiskLevel, ensure_allowed


@pytest.mark.parametrize("risk_level", [RiskLevel.SAFE, RiskLevel.LOW])
def test_safe_and_low_are_allowed(risk_level):
    ensure_allowed(risk_level)


@pytest.mark.parametrize("risk_level", [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.BLOCKED])
def test_medium_high_and_blocked_are_denied(risk_level):
    with pytest.raises(PermissionDenied):
        ensure_allowed(risk_level)
