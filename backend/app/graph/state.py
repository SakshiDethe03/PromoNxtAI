from typing import Any, Dict, List, Literal, Optional, Union
from typing_extensions import TypedDict

from app.schemas.business import SalesSummary
from app.schemas.campaign import (
    ApprovalDecision,
    DecisionResult,
    GeneratedContent,
    ValidationResult,
)
from app.schemas.product import FactSheet

CampaignStatus = Literal[
    "draft",
    "validated",
    "awaiting_approval",
    "approved",
    "publishing",
    "published",
    "failed",
]


class CampaignState(TypedDict, total=False):
    """LangGraph state structure representing a campaign's complete workflow state."""
    campaign_id: str
    business_id: str
    input: Union[str, Dict[str, Any]]
    language: str
    goal: str
    sales_summary: Optional[SalesSummary]
    decision: Optional[DecisionResult]
    fact_sheet: Optional[FactSheet]
    content: Optional[GeneratedContent]
    final_caption: Optional[str]
    image_url: Optional[str]
    validation: Optional[ValidationResult]
    validation_attempts: int
    approval: Optional[ApprovalDecision]
    status: CampaignStatus
    errors: List[str]
