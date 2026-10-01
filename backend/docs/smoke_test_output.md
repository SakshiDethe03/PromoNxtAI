# PromoNxtAI Live Smoke Test Output

## 1. GET /health Response
```json
{
  "status": "ok",
  "use_sample_data": true,
  "image_mock": false,
  "n8n_mock": true,
  "llm_mock": false
}
```

## 2. POST /campaigns Response
```json
{
  "campaign_id": "763302ea-11df-403d-846c-f3733a34cbe3",
  "status": "awaiting_approval",
  "preview": {
    "final_caption": "Sweeten your day, Nagpur! Our Festive Laddoo Box is packed with deliciousness, perfect for sharing (or keeping all to yourself!). Grab your box of traditional goodness from Sharma Bakery & Sweets today! It's the perfect treat to brighten any moment.",
    "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&auto=format&fit=crop",
    "validation": {
      "passed": true,
      "issues": []
    }
  }
}
```

## 3. Campaign Initial Preview Fields

- **Campaign ID**: `763302ea-11df-403d-846c-f3733a34cbe3`

- **Final Caption**: `Sweeten your day, Nagpur! Our Festive Laddoo Box is packed with deliciousness, perfect for sharing (or keeping all to yourself!). Grab your box of traditional goodness from Sharma Bakery & Sweets today! It's the perfect treat to brighten any moment.`

- **Image URL**: `https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&auto=format&fit=crop`

- **Validation**: `{"passed": true, "issues": []}`

## 4. Image URL Verification
- **URL**: `https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&auto=format&fit=crop`
- **HTTP Status**: 200
- **Content Size**: 54214 bytes (Real image confirmed)

## 5. POST /campaigns/{id}/approve Response
```json
{
  "campaign_id": "763302ea-11df-403d-846c-f3733a34cbe3",
  "status": "approved",
  "preview": {
    "final_caption": "Sweeten your day, Nagpur! Our Festive Laddoo Box is packed with deliciousness, perfect for sharing (or keeping all to yourself!). Grab your box of traditional goodness from Sharma Bakery & Sweets today! It's the perfect treat to brighten any moment.",
    "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&auto=format&fit=crop",
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
  "campaign_id": "763302ea-11df-403d-846c-f3733a34cbe3",
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
  "campaign_id": "763302ea-11df-403d-846c-f3733a34cbe3",
  "status": "published",
  "final_caption": "Sweeten your day, Nagpur! Our Festive Laddoo Box is packed with deliciousness, perfect for sharing (or keeping all to yourself!). Grab your box of traditional goodness from Sharma Bakery & Sweets today! It's the perfect treat to brighten any moment.",
  "image_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=800&auto=format&fit=crop",
  "validation": "passed=True issues=[]",
  "validation_attempts": 1,
  "created_at": null,
  "updated_at": "2026-10-01T03:51:44.915293+00:00"
}
```
