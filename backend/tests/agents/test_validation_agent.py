import sys
from datetime import date
from pathlib import Path
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.validation_agent import run_validation
from app.schemas.campaign import ValidationResult
from app.schemas.product import FactSheet

FIXED_TODAY = date(2026, 9, 28)


@pytest.fixture
def validation_fact_sheet():
    return FactSheet(
        business_name="Sharma Bakery & Sweets",
        product_id="prod_001",
        product_name="Chocolate Truffle Cake (500g)",
        price=450.0,
        currency="INR",
        stock_qty=12,
        discount_percent=15.0,
        offer_price=382.5,
        offer_valid_to="2026-10-10",
    )


def test_validation_agent_deterministic_primacy_over_llm_tone_opinion(validation_fact_sheet):
    wrong_price_caption = "Treat yourself to Chocolate Truffle Cake (500g)! Special offer at 500 INR valid until 2026-10-10."
    cta = "Order on WhatsApp now"

    fake_llm_approval = ValidationResult(passed=True, issues=[])

    result = run_validation(
        caption=wrong_price_caption,
        cta=cta,
        fact_sheet=validation_fact_sheet,
        today=FIXED_TODAY,
        llm_mock_responses=[fake_llm_approval],
    )

    assert result.passed is False
    assert any("PRICE_MISMATCH" in issue for issue in result.issues)


def test_validation_agent_adds_llm_soft_tone_issue(validation_fact_sheet):
    correct_caption = "Treat yourself to Chocolate Truffle Cake (500g)! Special offer at 382.5 INR (15% off) valid until 2026-10-10."
    cta = "Order on WhatsApp now"

    llm_soft_issue = ValidationResult(
        passed=False,
        issues=["SOFT_TONE_ISSUE: Caption tone feels slightly aggressive for local bakery"],
    )

    result = run_validation(
        caption=correct_caption,
        cta=cta,
        fact_sheet=validation_fact_sheet,
        today=FIXED_TODAY,
        llm_mock_responses=[llm_soft_issue],
    )

    assert result.passed is False
    assert any("SOFT_TONE_ISSUE" in issue for issue in result.issues)


def test_validation_agent_clean_pass(validation_fact_sheet):
    correct_caption = "Treat yourself to Chocolate Truffle Cake (500g)! Special offer at 382.5 INR (15% off) valid until 2026-10-10."
    cta = "Order on WhatsApp now"

    clean_llm = ValidationResult(passed=True, issues=[])

    result = run_validation(
        caption=correct_caption,
        cta=cta,
        fact_sheet=validation_fact_sheet,
        today=FIXED_TODAY,
        llm_mock_responses=[clean_llm],
    )

    assert result.passed is True
    assert len(result.issues) == 0
