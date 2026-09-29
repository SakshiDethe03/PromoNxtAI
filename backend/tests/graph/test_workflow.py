import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config.settings import settings
from app.graph.checkpointer import get_checkpointer
from app.graph.workflow import build_graph, resume_campaign, run_campaign
from app.schemas.campaign import ApprovalDecision, DecisionResult, GeneratedContent, ValidationResult
from langgraph.checkpoint.memory import InMemorySaver

FIXED_TODAY = "2026-09-28"


@pytest.fixture(autouse=True)
def setup_test_settings():
    settings.use_sample_data = True
    settings.image_mock = True
    settings.n8n_mock = True
    settings.llm_mock = True


def test_workflow_happy_path():
    thread_id = "test_thread_happy"
    initial_state = {
        "campaign_id": "camp_happy_01",
        "business_id": "biz_101",
        "input": "Promote best cake for weekend",
        "goal": "Boost cake sales",
        "today": FIXED_TODAY,
    }

    paused_state = run_campaign(initial_state, thread_id)

    assert paused_state.get("status") == "awaiting_approval"
    assert paused_state.get("image_url") is not None
    assert paused_state.get("final_caption") is not None
    assert paused_state.get("validation") is not None
    assert paused_state.get("validation").passed is True

    final_state = resume_campaign(thread_id, ApprovalDecision(action="approve"))
    assert final_state.get("status") == "approved"


def test_workflow_validation_fails_once_retry_succeeds():
    thread_id = "test_thread_retry_once"
    initial_state = {
        "campaign_id": "camp_retry_01",
        "business_id": "biz_101",
        "input": "Promote cake",
        "goal": "Boost sales",
        "today": FIXED_TODAY,
    }

    val_fail = ValidationResult(passed=False, issues=["PRICE_MISMATCH: Invalid price"])
    val_pass = ValidationResult(passed=True, issues=[])

    with patch("app.graph.workflow.run_validation", side_effect=[val_fail, val_pass]):
        paused_state = run_campaign(initial_state, thread_id)

    assert paused_state.get("status") == "awaiting_approval"
    assert paused_state.get("validation_attempts") == 2
    assert paused_state.get("validation").passed is True


def test_workflow_validation_fails_3_times():
    thread_id = "test_thread_fails_3x"
    initial_state = {
        "campaign_id": "camp_fail_01",
        "business_id": "biz_101",
        "input": "Promote cake",
        "goal": "Boost sales",
        "today": FIXED_TODAY,
    }

    failed_val = ValidationResult(passed=False, issues=["UNKNOWN_NUMBER: Invalid number in caption"])

    with patch("app.graph.workflow.run_validation", return_value=failed_val):
        final_state = run_campaign(initial_state, thread_id)

    assert final_state.get("status") == "failed"
    assert final_state.get("validation_attempts") == 3
    assert len(final_state.get("errors")) > 0
    assert "awaiting_approval" not in final_state.get("status")


def test_workflow_out_of_stock_product_decided():
    thread_id = "test_thread_oos"
    initial_state = {
        "campaign_id": "camp_oos_01",
        "business_id": "biz_101",
        "input": "Promote sweets",
        "goal": "Boost sweets",
        "today": FIXED_TODAY,
    }

    oos_decision = DecisionResult(
        product_id="prod_003",
        reason="Selected out of stock sweet",
        strategy="seasonal",
        offer_id=None,
    )

    with patch("app.graph.workflow.decide_product", return_value=oos_decision):
        final_state = run_campaign(initial_state, thread_id)

    assert final_state.get("status") == "failed"
    assert any("out of stock" in err.lower() for err in final_state.get("errors", []))


def test_workflow_human_edits_with_bad_price():
    thread_id = "test_thread_human_edit_bad"
    initial_state = {
        "campaign_id": "camp_edit_bad_01",
        "business_id": "biz_101",
        "input": "Promote cake",
        "goal": "Boost sales",
        "today": FIXED_TODAY,
    }

    paused_state = run_campaign(initial_state, thread_id)
    assert paused_state.get("status") == "awaiting_approval"

    bad_edit = ApprovalDecision(
        action="edit",
        edited_caption="Special Chocolate Truffle Cake at 999 INR!",
    )

    # Mock validation agent to fail on human's bad edit so we verify re-validation caught it and routed to retry/failed
    failed_edit_val = ValidationResult(passed=False, issues=["PRICE_MISMATCH: Number 999 does not match FactSheet"])

    with patch("app.graph.workflow.run_validation", return_value=failed_edit_val):
        edited_state = resume_campaign(thread_id, bad_edit)

    # Re-validation ran on edited text and caught the bad edit! (Did NOT silently accept edit)
    assert edited_state.get("status") == "failed"
    assert edited_state.get("validation_attempts") >= 2
    assert any("PRICE_MISMATCH" in issue for issue in edited_state.get("errors", []))


def test_workflow_human_rejects():
    thread_id = "test_thread_reject"
    initial_state = {
        "campaign_id": "camp_reject_01",
        "business_id": "biz_101",
        "input": "Promote cake",
        "goal": "Boost sales",
        "today": FIXED_TODAY,
    }

    paused_state = run_campaign(initial_state, thread_id)
    assert paused_state.get("status") == "awaiting_approval"

    final_state = resume_campaign(thread_id, ApprovalDecision(action="reject", feedback="Don't want cake promo"))
    assert final_state.get("status") == "rejected"


def test_workflow_human_edits_with_valid_caption_skips_image_gen():
    thread_id = "test_thread_human_edit_valid"
    initial_state = {
        "campaign_id": "camp_edit_good_01",
        "business_id": "biz_101",
        "input": "Promote cake",
        "goal": "Boost sales",
        "today": FIXED_TODAY,
    }

    paused_state = run_campaign(initial_state, thread_id)
    assert paused_state.get("status") == "awaiting_approval"
    initial_image_url = paused_state.get("image_url")
    assert initial_image_url is not None

    good_edit = ApprovalDecision(
        action="edit",
        edited_caption="Treat yourself to Chocolate Truffle Cake at special offer!",
    )

    with patch("app.graph.workflow.generate_poster_image") as mock_gen_image:
        final_state = resume_campaign(thread_id, good_edit)

    # Re-validation passed, image generation skipped, status set directly to approved
    assert final_state.get("status") == "approved"
    assert final_state.get("final_caption") == good_edit.edited_caption
    assert final_state.get("image_url") == initial_image_url
    assert mock_gen_image.call_count == 0


def test_checkpointer_fallback():
    old_url = settings.supabase_db_url
    try:
        settings.supabase_db_url = ""
        checkpointer = get_checkpointer()
        assert isinstance(checkpointer, InMemorySaver)
    finally:
        settings.supabase_db_url = old_url
