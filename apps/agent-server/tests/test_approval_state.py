import time

from app.main import create_pending_approval, pending_approvals, record_approval_result


def setup_function():
    pending_approvals.clear()


def test_unknown_request_rejected():
    accepted, message = record_approval_result("missing", approved=True)

    assert accepted is False
    assert message


def test_expired_request_rejected_and_removed():
    approval = create_pending_approval("mock.medium_approval", "medium")
    approval.expires_at = time.time() - 1

    accepted, message = record_approval_result(approval.request_id, approved=True)

    assert accepted is False
    assert message
    assert approval.request_id not in pending_approvals


def test_duplicate_request_rejected():
    approval = create_pending_approval("mock.medium_approval", "medium")

    first_accepted, first_message = record_approval_result(approval.request_id, approved=True)
    second_accepted, second_message = record_approval_result(approval.request_id, approved=False)

    assert first_accepted is True
    assert first_message
    assert pending_approvals[approval.request_id].handled is True
    assert second_accepted is False
    assert second_message


def test_valid_request_accepted_but_not_executed():
    approval = create_pending_approval("mock.medium_approval", "medium")

    accepted, message = record_approval_result(approval.request_id, approved=True)

    assert accepted is True
    assert message
    assert pending_approvals[approval.request_id].handled is True
