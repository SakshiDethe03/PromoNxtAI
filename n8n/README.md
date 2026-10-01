# n8n Integration & Handshake Guide

This directory contains the specifications, payload schemas, and integration guidelines for connecting the **PromoNxtAI** backend with **n8n** workflows for automated Instagram publishing.

---

## 1. Webhook Configuration

- **Environment Variable Name**: `N8N_WEBHOOK_URL`
- **Default Value**: `https://your-n8n-instance.com/webhook/instagram-publish`
- **Security Header**: All requests from the PromoNxtAI backend to n8n include the following header:
  ```http
  X-Webhook-Secret: <value from N8N_SHARED_SECRET in .env>
  ```
  *(Do NOT hardcode the secret value in workflow scripts or repositories).*

---

## 2. Publish Payload (Backend ➔ n8n)

When a shopkeeper approves a campaign and clicks **Publish**, the backend POSTs the following `PublishPayload` JSON to `N8N_WEBHOOK_URL`:

```json
{
  "campaign_id": "5f1b6997-00e1-4825-87a1-619af7313388",
  "business_id": "biz_101",
  "final_caption": "Treat yourself to fresh treats! Special offer at 382.5 INR!",
  "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop",
  "destination_channels": [
    "Instagram"
  ],
  "published_at": "2026-09-29T17:04:24.327465+00:00"
}
```

---

## 3. Callback Specifications (n8n ➔ Backend)

After attempting to publish to Instagram via Meta Graph API, n8n MUST POST back to the backend callback endpoint:

- **Endpoint URL**: `http://<backend-host>:8000/n8n/callback`
- **Required Header**:
  ```http
  X-Webhook-Secret: <matching N8N_SHARED_SECRET>
  ```

> [!IMPORTANT]
> **Idempotency & Replay Protection**:
> The backend accepts callbacks ONLY for campaigns currently in `"publishing"` status. If a callback is replayed or sent for a campaign not in `"publishing"` status, the server responds with **`HTTP 409 Conflict`**. Do not loop retries on 409 errors.

### Success Payload Example (`status: "published"`)
```json
{
  "campaign_id": "5f1b6997-00e1-4825-87a1-619af7313388",
  "status": "published",
  "instagram_post_id": "ig_post_987654321",
  "permalink": "https://www.instagram.com/p/Cxyz12345/"
}
```

### Failure Payload Example (`status: "failed"`)
```json
{
  "campaign_id": "5f1b6997-00e1-4825-87a1-619af7313388",
  "status": "failed",
  "error": "Meta Graph API token expired or permission denied."
}
```

---

## 4. Testing Webhook Callback with `curl`

To manually test the callback endpoint without running n8n:

### Test Success Callback:
```bash
curl -X POST "http://127.0.0.1:8000/n8n/callback" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your_n8n_shared_secret_here" \
  -d '{
    "campaign_id": "YOUR_CAMPAIGN_ID",
    "status": "published",
    "instagram_post_id": "ig_test_123",
    "permalink": "https://instagram.com/p/test1234"
  }'
```

### Test Failure Callback:
```bash
curl -X POST "http://127.0.0.1:8000/n8n/callback" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your_n8n_shared_secret_here" \
  -d '{
    "campaign_id": "YOUR_CAMPAIGN_ID",
    "status": "failed",
    "error": "Instagram API connection timeout"
  }'
```
