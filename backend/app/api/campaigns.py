import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.graph import workflow
from app.schemas.campaign import ApprovalDecision, PublishPayload
from app.services import data_repository, n8n_client

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CreateCampaignRequest(BaseModel):
    business_id: str
    goal: str
    language: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
def create_campaign(req: CreateCampaignRequest):
    try:
        data_repository.get_business(req.business_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    campaign_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    initial_state = {
        "campaign_id": campaign_id,
        "business_id": req.business_id,
        "goal": req.goal,
        "language": req.language,
        "status": "draft",
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    resulting_state = workflow.run_campaign(initial_state, thread_id=campaign_id)
    resulting_state["updated_at"] = datetime.now(timezone.utc).isoformat()

    data_repository.save_campaign(campaign_id, resulting_state)
    data_repository.append_activity_log(
        campaign_id,
        "campaign_started",
        {"goal": req.goal, "business_id": req.business_id},
    )

    current_status = resulting_state.get("status")
    if current_status == "awaiting_approval":
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "campaign_id": campaign_id,
                "status": "awaiting_approval",
                "preview": {
                    "final_caption": resulting_state.get("final_caption"),
                    "image_url": resulting_state.get("image_url"),
                    "validation": (
                        resulting_state.get("validation").model_dump()
                        if hasattr(resulting_state.get("validation"), "model_dump")
                        else resulting_state.get("validation")
                    ),
                },
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "campaign_id": campaign_id,
                "status": current_status or "failed",
                "errors": resulting_state.get("errors", []),
            },
        )


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str):
    campaign_state = data_repository.get_campaign(campaign_id)
    if not campaign_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    validation = campaign_state.get("validation")
    if hasattr(validation, "model_dump"):
        validation = validation.model_dump()

    return {
        "campaign_id": campaign_id,
        "status": campaign_state.get("status"),
        "final_caption": campaign_state.get("final_caption"),
        "image_url": campaign_state.get("image_url"),
        "validation": validation,
        "validation_attempts": campaign_state.get("validation_attempts"),
        "created_at": campaign_state.get("created_at"),
        "updated_at": campaign_state.get("updated_at"),
    }


@router.post("/{campaign_id}/approve")
def approve_campaign(campaign_id: str, approval: ApprovalDecision):
    campaign_state = data_repository.get_campaign(campaign_id)
    if not campaign_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign_state.get("status") != "awaiting_approval":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Campaign is not awaiting approval (current status: '{campaign_state.get('status')}')",
        )

    resulting_state = workflow.resume_campaign(thread_id=campaign_id, approval=approval)
    resulting_state["updated_at"] = datetime.now(timezone.utc).isoformat()

    data_repository.save_campaign(campaign_id, resulting_state)
    data_repository.append_activity_log(
        campaign_id,
        f"approval_{approval.action}",
        {"action": approval.action, "status": resulting_state.get("status")},
    )

    validation = resulting_state.get("validation")
    if hasattr(validation, "model_dump"):
        validation = validation.model_dump()

    return {
        "campaign_id": campaign_id,
        "status": resulting_state.get("status"),
        "preview": {
            "final_caption": resulting_state.get("final_caption"),
            "image_url": resulting_state.get("image_url"),
            "validation": validation,
        },
        "errors": resulting_state.get("errors", []),
    }


@router.post("/{campaign_id}/publish")
def publish_campaign(campaign_id: str):
    campaign_state = data_repository.get_campaign(campaign_id)
    if not campaign_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if campaign_state.get("status") != "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Campaign is not approved (current status: '{campaign_state.get('status')}')",
        )

    campaign_state["status"] = "publishing"
    campaign_state["updated_at"] = datetime.now(timezone.utc).isoformat()
    data_repository.save_campaign(campaign_id, campaign_state)

    payload = PublishPayload(
        campaign_id=campaign_id,
        business_id=campaign_state.get("business_id", "biz_101"),
        final_caption=campaign_state.get("final_caption", ""),
        image_url=campaign_state.get("image_url", ""),
        published_at=datetime.now(timezone.utc).isoformat(),
    )

    try:
        n8n_client.trigger_publish(payload)
    except Exception as e:
        campaign_state["status"] = "failed"
        errors = list(campaign_state.get("errors") or [])
        errors.append(f"Publish error: {str(e)}")
        campaign_state["errors"] = errors
        campaign_state["updated_at"] = datetime.now(timezone.utc).isoformat()

        data_repository.save_campaign(campaign_id, campaign_state)
        data_repository.append_activity_log(campaign_id, "publish_failed", {"error": str(e)})

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Publish failed: {str(e)}",
        )

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={"campaign_id": campaign_id, "status": "publishing"},
    )
