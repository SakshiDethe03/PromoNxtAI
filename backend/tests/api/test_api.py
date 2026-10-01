import sys
from pathlib import Path
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config.settings import settings
from app.main import app
from app.schemas.campaign import DecisionResult, ValidationResult

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_settings():
    settings.use_sample_data = True
    settings.image_mock = True
    settings.n8n_mock = True
    settings.llm_mock = True


def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "use_sample_data" in data
    assert "image_mock" in data
    assert "n8n_mock" in data


def test_create_campaign_happy_path():
    response = client.post(
        "/campaigns",
        json={"business_id": "biz_101", "goal": "Boost cake sales"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "awaiting_approval"
    assert "campaign_id" in data
    assert "preview" in data
    assert data["preview"]["final_caption"] is not None
    assert data["preview"]["image_url"] is not None


def test_create_campaign_business_not_found():
    response = client.post(
        "/campaigns",
        json={"business_id": "nonexistent_biz_999", "goal": "Boost sales"},
    )
    assert response.status_code == 404


def test_create_campaign_out_of_stock_forced():
    oos_decision = DecisionResult(
        product_id="prod_003",
        reason="Selected out of stock product",
        strategy="seasonal",
    )
    with patch("app.graph.workflow.decide_product", return_value=oos_decision):
        response = client.post(
            "/campaigns",
            json={"business_id": "biz_101", "goal": "Boost sweets"},
        )
    assert response.status_code == 422
    data = response.json()
    assert data["status"] == "failed"
    assert len(data["errors"]) > 0


def test_get_campaign_not_found():
    response = client.get("/campaigns/nonexistent_campaign_12345")
    assert response.status_code == 404


def test_approve_campaign_happy_path():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    get_res = client.get(f"/campaigns/{cid}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "awaiting_approval"

    approve_res = client.post(f"/campaigns/{cid}/approve", json={"action": "approve"})
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"


def test_approve_non_awaiting_campaign_conflict():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    client.post(f"/campaigns/{cid}/approve", json={"action": "approve"})
    second_approve = client.post(f"/campaigns/{cid}/approve", json={"action": "approve"})
    assert second_approve.status_code == 409


def test_approve_edit_with_bad_price_revalidates():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    bad_val = ValidationResult(passed=False, issues=["PRICE_MISMATCH: Invalid price 99999"])
    with patch("app.graph.workflow.run_validation", return_value=bad_val):
        edit_res = client.post(
            f"/campaigns/{cid}/approve",
            json={"action": "edit", "edited_caption": "Cake for 99999 INR!"},
        )

    assert edit_res.status_code == 200
    assert edit_res.json()["status"] == "failed"


def test_publish_campaign_not_approved_conflict():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    pub_res = client.post(f"/campaigns/{cid}/publish")
    assert pub_res.status_code == 409


def test_publish_campaign_happy_path():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    client.post(f"/campaigns/{cid}/approve", json={"action": "approve"})
    pub_res = client.post(f"/campaigns/{cid}/publish")

    assert pub_res.status_code == 202
    assert pub_res.json()["status"] == "publishing"


def test_publish_campaign_n8n_client_raises_502():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    client.post(f"/campaigns/{cid}/approve", json={"action": "approve"})

    with patch("app.api.campaigns.n8n_client.trigger_publish", side_effect=RuntimeError("Network error sending to n8n")):
        pub_res = client.post(f"/campaigns/{cid}/publish")

    assert pub_res.status_code == 502
    get_res = client.get(f"/campaigns/{cid}")
    assert get_res.json()["status"] == "failed"


def test_n8n_callback_wrong_secret_401():
    cb_res = client.post(
        "/n8n/callback",
        headers={"X-Webhook-Secret": "wrong_secret_val"},
        json={"campaign_id": "camp_123", "status": "published"},
    )
    assert cb_res.status_code == 401


def test_n8n_callback_published_happy_path():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    client.post(f"/campaigns/{cid}/approve", json={"action": "approve"})
    client.post(f"/campaigns/{cid}/publish")

    cb_res = client.post(
        "/n8n/callback",
        headers={"X-Webhook-Secret": settings.n8n_shared_secret},
        json={
            "campaign_id": cid,
            "status": "published",
            "instagram_post_id": "ig_post_999",
            "permalink": "https://instagram.com/p/test1234",
        },
    )
    assert cb_res.status_code == 200
    assert cb_res.json() == {"received": True}

    get_res = client.get(f"/campaigns/{cid}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "published"


def test_n8n_callback_not_in_publishing_status_conflict():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    cb_res = client.post(
        "/n8n/callback",
        headers={"X-Webhook-Secret": settings.n8n_shared_secret},
        json={"campaign_id": cid, "status": "published"},
    )
    assert cb_res.status_code == 409


def test_campaign_activity_log_full_flow():
    res = client.post("/campaigns", json={"business_id": "biz_101", "goal": "Boost cake sales"})
    cid = res.json()["campaign_id"]

    client.post(f"/campaigns/{cid}/approve", json={"action": "approve"})
    client.post(f"/campaigns/{cid}/publish")

    client.post(
        "/n8n/callback",
        headers={"X-Webhook-Secret": settings.n8n_shared_secret},
        json={"campaign_id": cid, "status": "published", "instagram_post_id": "ig_123"},
    )

    act_res = client.get(f"/campaigns/{cid}/activity")
    assert act_res.status_code == 200
    events = [item["event"] for item in act_res.json()]
    assert "campaign_started" in events
    assert "approval_approve" in events
    assert "published" in events
    assert events.index("campaign_started") < events.index("approval_approve") < events.index("published")
