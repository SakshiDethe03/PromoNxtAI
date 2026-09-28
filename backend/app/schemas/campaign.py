import re
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class DecisionResult(BaseModel):
    """Result of decision node choosing the best product & campaign strategy."""
    product_id: str
    reason: str
    strategy: Literal["clear_overstock", "boost_bestseller", "seasonal", "reward_repeat"]
    offer_id: Optional[str] = None
    target_segment: Optional[str] = None


class GeneratedContent(BaseModel):
    """LLM creative generation output (template with placeholders, strictly no raw digits)."""
    caption_template: str
    cta: str
    hashtags: List[str] = Field(default_factory=list)
    creative_brief: str

    @field_validator("caption_template")
    @classmethod
    def check_no_digits_in_template(cls, v: str) -> str:
        if re.search(r"\d", v):
            raise ValueError(
                "caption_template must not contain raw digits; use placeholders like {price}, {offer_price}, {discount}, {valid_to}"
            )
        return v


class ValidationResult(BaseModel):
    """Fact check verification result against FactSheet database truth."""
    passed: bool
    issues: List[str] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    """Human-in-the-loop (HITL) approval input."""
    action: Literal["approve", "edit", "reject"]
    edited_caption: Optional[str] = None
    feedback: Optional[str] = None


class PublishPayload(BaseModel):
    """Payload sent to n8n webhook for publishing to Instagram."""
    campaign_id: str
    business_id: str
    final_caption: str
    image_url: str
    destination_channels: List[str] = Field(default_factory=lambda: ["Instagram"])
    published_at: Optional[str] = None


class PublishCallback(BaseModel):
    """Callback payload received from n8n after publishing attempt."""
    campaign_id: str
    status: Literal["success", "failed"]
    post_url: Optional[str] = None
    error: Optional[str] = None
