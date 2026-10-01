# PromoNxtAI Live Smoke Test Output

## 1. GET /health Response
```json
{
  "status": "ok",
  "use_sample_data": true,
  "image_mock": false,
  "n8n_mock": true
}
```

## 2. POST /campaigns Response
```json
{
  "campaign_id": "5f1b6997-00e1-4825-87a1-619af7313388",
  "status": "awaiting_approval",
  "preview": {
    "final_caption": "Treat yourself to fresh treats! Special offer at 382.5 INR!",
    "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop",
    "validation": {
      "passed": true,
      "issues": []
    }
  }
}
```

## 3. Campaign Initial Preview Fields
- **Campaign ID**: `5f1b6997-00e1-4825-87a1-619af7313388`
- **Final Caption**: `Treat yourself to fresh treats! Special offer at 382.5 INR!`
- **Image URL**: `https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop`
- **Validation**: `{"passed": true, "issues": []}`

## 4. Image URL Verification
- **URL**: `https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop`
- **HTTP Status**: 200
- **Content Size**: 108006 bytes (Real high-res visual confirmed)

## 5. POST /campaigns/{id}/approve Response
```json
{
  "campaign_id": "5f1b6997-00e1-4825-87a1-619af7313388",
  "status": "approved",
  "preview": {
    "final_caption": "Treat yourself to fresh treats! Special offer at 382.5 INR!",
    "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop",
    "validation": {
      "passed": true,
      "issues": []
    }
  },
  "errors": []
}
```

## 6. POST /campaigns/{id}/publish Response
```json
{
  "campaign_id": "5f1b6997-00e1-4825-87a1-619af7313388",
  "status": "publishing"
}
```

## 7. POST /n8n/callback Response
```json
{
  "received": true
}
```

## 8. Final GET /campaigns/{id} State
```json
{
  "campaign_id": "5f1b6997-00e1-4825-87a1-619af7313388",
  "status": "published",
  "final_caption": "Treat yourself to fresh treats! Special offer at 382.5 INR!",
  "image_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=800&auto=format&fit=crop",
  "instagram_post_id": "ig_live_smoke_98765",
  "permalink": "https://www.instagram.com/p/smoke_test_98765/",
  "validation": "passed=True issues=[]",
  "validation_attempts": 1,
  "updated_at": "2026-09-29T17:04:24.327465+00:00"
}
```
