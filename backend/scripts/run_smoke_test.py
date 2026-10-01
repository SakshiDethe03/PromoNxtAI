import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import json
import requests

SERVER_URL = "http://127.0.0.1:8000"
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
DOCS_DIR.mkdir(parents=True, exist_ok=True)
SMOKE_TEST_FILE = DOCS_DIR / "smoke_test_output.md"


def main():
    transcript = []
    transcript.append("# PromoNxtAI Live Smoke Test Output\n")

    # 1. GET /health
    print("Step 1.1: Calling GET /health...")
    r_health = requests.get(f"{SERVER_URL}/health")
    assert r_health.status_code == 200, f"Health check failed: {r_health.text}"
    health_data = r_health.json()
    print("Health Data:", health_data)
    assert health_data["use_sample_data"] is True, f"Expected use_sample_data=True, got {health_data}"
    assert health_data["image_mock"] is False, f"Expected image_mock=False, got {health_data}"
    assert health_data["n8n_mock"] is True, f"Expected n8n_mock=True, got {health_data}"
    assert health_data["llm_mock"] is False, f"Expected llm_mock=False, got {health_data}"

    transcript.append("## 1. GET /health Response\n```json\n" + json.dumps(health_data, indent=2) + "\n```\n")

    # 2. POST /campaigns
    print("Step 1.2: Calling POST /campaigns...")
    payload_create = {
        "business_id": "biz_101",
        "goal": "clear excess stock",
        "language": "en",
    }
    r_create = requests.post(f"{SERVER_URL}/campaigns", json=payload_create)
    assert r_create.status_code == 201, f"Create campaign failed ({r_create.status_code}): {r_create.text}"
    create_data = r_create.json()
    campaign_id = create_data["campaign_id"]
    print(f"Campaign Created ID: {campaign_id}")

    # Load campaign state from data repository via GET /campaigns/{id} or direct data read to access raw decision and raw content
    r_get_init = requests.get(f"{SERVER_URL}/campaigns/{campaign_id}")
    get_init_data = r_get_init.json()

    # Load campaign dictionary from repository file or memory to extract decision & content
    from app.services import data_repository
    raw_campaign_state = data_repository.get_campaign(campaign_id) or {}

    decision_obj = raw_campaign_state.get("decision")
    content_obj = raw_campaign_state.get("content")

    print("\n--- REAL MODEL OUTPUT DETAILS ---")
    print("Decision (product_id, reason, strategy):")
    if hasattr(decision_obj, "model_dump"):
        print(json.dumps(decision_obj.model_dump(), indent=2))
    else:
        print(json.dumps(decision_obj, indent=2, default=str))

    print("\nGenerated Content BEFORE Rendering (caption_template, cta, hashtags, creative_brief):")
    if hasattr(content_obj, "model_dump"):
        print(json.dumps(content_obj.model_dump(), indent=2))
    else:
        print(json.dumps(content_obj, indent=2, default=str))

    print("\nFinal Rendered Caption AFTER Rendering:")
    print(raw_campaign_state.get("final_caption"))

    print("\nValidation Result:")
    val_obj = raw_campaign_state.get("validation")
    if hasattr(val_obj, "model_dump"):
        print(json.dumps(val_obj.model_dump(), indent=2))
    else:
        print(json.dumps(val_obj, indent=2, default=str))
    print("---------------------------------\n")

    transcript.append("## 2. POST /campaigns Response\n```json\n" + json.dumps(create_data, indent=2) + "\n```\n")
    transcript.append("## 3. Campaign Initial Preview Fields\n")
    transcript.append(f"- **Campaign ID**: `{campaign_id}`\n")
    transcript.append(f"- **Final Caption**: `{create_data['preview']['final_caption']}`\n")
    transcript.append(f"- **Image URL**: `{create_data['preview']['image_url']}`\n")
    transcript.append(f"- **Validation**: `{json.dumps(create_data['preview']['validation'])}`\n")

    # 4. Fetch image_url
    image_url = create_data["preview"]["image_url"]
    print(f"Step 1.4: Fetching Image URL: {image_url}...")
    r_img = requests.get(image_url, timeout=30)
    print(f"Image Fetch Status: {r_img.status_code}, Content-Length: {len(r_img.content)}")
    assert r_img.status_code == 200, f"Image fetch returned HTTP {r_img.status_code}"
    assert len(r_img.content) > 1000, f"Image content too short ({len(r_img.content)} bytes)"
    assert "placeholder" not in image_url, f"Image URL appears to be placeholder: {image_url}"

    transcript.append(f"## 4. Image URL Verification\n- **URL**: `{image_url}`\n- **HTTP Status**: {r_img.status_code}\n- **Content Size**: {len(r_img.content)} bytes (Real image confirmed)\n")

    # 5. POST /campaigns/{id}/approve
    print(f"Step 1.5: Approving Campaign {campaign_id}...")
    r_approve = requests.post(f"{SERVER_URL}/campaigns/{campaign_id}/approve", json={"action": "approve"})
    assert r_approve.status_code == 200, f"Approve failed ({r_approve.status_code}): {r_approve.text}"
    approve_data = r_approve.json()
    assert approve_data["status"] == "approved"
    print("Approve Response:", json.dumps(approve_data, indent=2))

    transcript.append("## 5. POST /campaigns/{id}/approve Response\n```json\n" + json.dumps(approve_data, indent=2) + "\n```\n")

    # 6. POST /campaigns/{id}/publish
    print(f"Step 1.6: Publishing Campaign {campaign_id}...")
    r_publish = requests.post(f"{SERVER_URL}/campaigns/{campaign_id}/publish")
    assert r_publish.status_code == 202, f"Publish failed ({r_publish.status_code}): {r_publish.text}"
    publish_data = r_publish.json()
    assert publish_data["status"] == "publishing"
    print("Publish Response:", json.dumps(publish_data, indent=2))

    transcript.append("## 6. POST /campaigns/{id}/publish Response\n```json\n" + json.dumps(publish_data, indent=2) + "\n```\n")

    # 7. POST /n8n/callback
    print("Step 1.7: Sending n8n Callback...")
    callback_payload = {
        "campaign_id": campaign_id,
        "status": "published",
        "instagram_post_id": "ig_live_smoke_98765",
        "permalink": "https://www.instagram.com/p/smoke_test_98765/",
    }
    r_cb = requests.post(
        f"{SERVER_URL}/n8n/callback",
        headers={"X-Webhook-Secret": "your_n8n_shared_secret_here"},
        json=callback_payload,
    )
    assert r_cb.status_code == 200, f"Callback failed ({r_cb.status_code}): {r_cb.text}"
    cb_data = r_cb.json()
    print("Callback Response:", json.dumps(cb_data, indent=2))

    transcript.append("## 7. POST /n8n/callback Response\n```json\n" + json.dumps(cb_data, indent=2) + "\n```\n")

    # 8. GET /campaigns/{id}
    print(f"Step 1.8: Verifying final status of {campaign_id}...")
    r_final = requests.get(f"{SERVER_URL}/campaigns/{campaign_id}")
    assert r_final.status_code == 200, f"Final GET failed: {r_final.text}"
    final_data = r_final.json()
    assert final_data["status"] == "published", f"Expected status='published', got '{final_data.get('status')}'"
    print("Final State:", json.dumps(final_data, indent=2))

    transcript.append("## 8. Final GET /campaigns/{id} State\n```json\n" + json.dumps(final_data, indent=2) + "\n```\n")

    # Save to docs/smoke_test_output.md
    with open(SMOKE_TEST_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(transcript))

    print(f"\nSUCCESS! Live smoke test passed cleanly. Transcript saved to {SMOKE_TEST_FILE}")


if __name__ == "__main__":
    main()
