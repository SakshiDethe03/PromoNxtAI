from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, status
from fastapi.responses import JSONResponse

from app.config.settings import settings
from app.schemas.campaign import PublishCallback
from app.services import data_repository

router = APIRouter(prefix="/n8n", tags=["n8n"])


@router.post("/callback", status_code=status.HTTP_200_OK)
def n8n_callback(
    callback: PublishCallback,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
):
    if x_webhook_secret != settings.n8n_shared_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook secret",
        )

    campaign_state = data_repository.get_campaign(callback.campaign_id)
    if not campaign_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign_state.get("status") != "publishing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Campaign is not in 'publishing' status (current status: '{campaign_state.get('status')}')",
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    if callback.status in ("published", "success"):
        campaign_state["status"] = "published"
        post_id = callback.instagram_post_id or callback.post_url
        link = callback.permalink or callback.post_url
        if post_id:
            campaign_state["instagram_post_id"] = post_id
        if link:
            campaign_state["permalink"] = link
        campaign_state["updated_at"] = now_iso

        data_repository.save_campaign(callback.campaign_id, campaign_state)
        data_repository.append_activity_log(
            callback.campaign_id,
            "published",
            {"instagram_post_id": post_id, "permalink": link},
        )
    else:
        campaign_state["status"] = "failed"
        errors = list(campaign_state.get("errors") or [])
        if callback.error:
            errors.append(callback.error)
        campaign_state["errors"] = errors
        campaign_state["updated_at"] = now_iso

        data_repository.save_campaign(callback.campaign_id, campaign_state)
        data_repository.append_activity_log(
            callback.campaign_id,
            "publish_failed_callback",
            {"error": callback.error},
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content={"received": True})
