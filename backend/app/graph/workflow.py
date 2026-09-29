import logging
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Union
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from app.agents.content_agent import generate_content
from app.agents.decision_agent import decide_product
from app.agents.validation_agent import run_validation
from app.graph.checkpointer import get_checkpointer
from app.graph.state import CampaignState
from app.schemas.campaign import ApprovalDecision
from app.services import data_repository
from app.services.image_service import generate_poster_image
from app.tools.caption_renderer import render_caption
from app.tools.fact_sheet import build_fact_sheet
from app.tools.sales_analysis import analyze_sales

logger = logging.getLogger(__name__)


def _parse_today(state: CampaignState) -> date:
    raw_today = state.get("today")
    if isinstance(raw_today, date):
        return raw_today
    if isinstance(raw_today, str):
        try:
            return date.fromisoformat(raw_today)
        except ValueError:
            pass
    return date.today()


def fetch_context_node(state: CampaignState) -> Dict[str, Any]:
    business_id = state.get("business_id", "biz_101")
    today = _parse_today(state)

    business = data_repository.get_business(business_id)
    products = data_repository.get_products(business_id)
    product_ids = [p.product_id for p in products]
    offers = data_repository.get_offers(product_ids)

    since_date = today - timedelta(days=30)
    sales = data_repository.get_sales_records(business_id, since_date)
    summary = analyze_sales(sales, products, today, period_days=30, business_id=business_id)

    return {
        "sales_summary": summary,
        "today": today.isoformat(),
        "status": state.get("status") or "draft",
        "validation_attempts": 0,
        "errors": state.get("errors") or [],
    }


def decision_node(state: CampaignState) -> Dict[str, Any]:
    if state.get("status") == "failed":
        return {}

    sales_summary = state["sales_summary"]
    business_id = state.get("business_id", "biz_101")
    products = data_repository.get_products(business_id)
    product_ids = [p.product_id for p in products]
    offers = data_repository.get_offers(product_ids)
    goal = state.get("goal", "Boost sales")
    today = _parse_today(state)

    try:
        decision_result = decide_product(sales_summary, products, goal, today, offers=offers)
        return {"decision": decision_result}
    except ValueError as e:
        logger.error(f"decision node failed: {e}")
        errors = list(state.get("errors") or [])
        errors.append(f"decision failed: {e}")
        return {"status": "failed", "errors": errors}


def build_facts_node(state: CampaignState) -> Dict[str, Any]:
    if state.get("status") == "failed":
        return {}

    decision_res = state.get("decision")
    if not decision_res:
        errors = list(state.get("errors") or [])
        errors.append("build_facts failed: No decision found in state")
        return {"status": "failed", "errors": errors}

    business_id = state.get("business_id", "biz_101")
    today = _parse_today(state)

    business = data_repository.get_business(business_id)
    products = data_repository.get_products(business_id)
    offers = data_repository.get_offers([p.product_id for p in products])

    target_product = next((p for p in products if p.product_id == decision_res.product_id), None)
    if not target_product:
        errors = list(state.get("errors") or [])
        errors.append(f"build_facts failed: Product '{decision_res.product_id}' not found")
        return {"status": "failed", "errors": errors}

    try:
        fact_sheet = build_fact_sheet(business, target_product, offers, today)
        return {"fact_sheet": fact_sheet}
    except ValueError as e:
        logger.error(f"build_facts node failed: {e}")
        errors = list(state.get("errors") or [])
        errors.append(f"build_facts failed: {e}")
        return {"status": "failed", "errors": errors}


def content_node(state: CampaignState) -> Dict[str, Any]:
    if state.get("status") == "failed":
        return {}

    fact_sheet = state["fact_sheet"]
    business_id = state.get("business_id", "biz_101")
    business = data_repository.get_business(business_id)
    language = state.get("language") or (business.languages[0] if business.languages else "English")
    goal = state.get("goal", "Boost sales")

    validation = state.get("validation")
    attempts = state.get("validation_attempts", 0)

    if attempts > 0 and validation and not validation.passed:
        enhanced_goal = (
            f"{goal} (PREVIOUS VALIDATION FAILED WITH ISSUES: {', '.join(validation.issues)}. "
            f"Fix these in the new template!)"
        )
    else:
        enhanced_goal = goal

    generated_content = generate_content(fact_sheet, business, language, enhanced_goal)
    rendered_caption = render_caption(generated_content.caption_template, fact_sheet)

    return {
        "content": generated_content,
        "final_caption": rendered_caption,
    }


def validate_node(state: CampaignState) -> Dict[str, Any]:
    if state.get("status") == "failed":
        return {}

    final_caption = state.get("final_caption", "")
    content_obj = state.get("content")
    cta = content_obj.cta if content_obj else ""
    fact_sheet = state["fact_sheet"]
    today = _parse_today(state)

    val_result = run_validation(final_caption, cta, fact_sheet, today)
    next_attempts = state.get("validation_attempts", 0) + 1

    if not val_result.passed and next_attempts >= 3:
        return {
            "validation": val_result,
            "validation_attempts": next_attempts,
            "status": "failed",
            "errors": list(val_result.issues),
        }

    return {
        "validation": val_result,
        "validation_attempts": next_attempts,
    }


def route_after_validate(state: CampaignState) -> str:
    if state.get("status") == "failed":
        return END

    val_result = state.get("validation")
    attempts = state.get("validation_attempts", 0)

    if val_result and val_result.passed:
        if state.get("image_url"):
            return "mark_approved"
        return "generate_image"

    if attempts < 3:
        return "content"

    return END


def generate_image_node(state: CampaignState) -> Dict[str, Any]:
    if state.get("status") == "failed":
        return {}

    decision_res = state.get("decision")
    business_id = state.get("business_id", "biz_101")
    business = data_repository.get_business(business_id)
    products = data_repository.get_products(business_id)

    target_product = next((p for p in products if p.product_id == decision_res.product_id), products[0])
    image_url = generate_poster_image(target_product, business)

    return {
        "image_url": image_url,
        "status": "awaiting_approval",
    }


def human_approval_node(state: CampaignState) -> Dict[str, Any]:
    if state.get("status") == "failed":
        return {}

    approval_input = interrupt({
        "final_caption": state.get("final_caption"),
        "image_url": state.get("image_url"),
        "validation": state.get("validation"),
        "status": state.get("status"),
    })

    if isinstance(approval_input, dict):
        approval_obj = ApprovalDecision(**approval_input)
    else:
        approval_obj = approval_input

    res_dict: Dict[str, Any] = {"approval": approval_obj}
    if approval_obj.action == "approve":
        res_dict["status"] = "approved"
    elif approval_obj.action == "reject":
        res_dict["status"] = "rejected"
    elif approval_obj.action == "edit" and approval_obj.edited_caption:
        res_dict["final_caption"] = approval_obj.edited_caption

    return res_dict


def mark_approved_node(state: CampaignState) -> Dict[str, Any]:
    return {"status": "approved"}


def route_after_approval(state: CampaignState) -> str:
    approval = state.get("approval")
    if not approval:
        return END

    if approval.action in ("approve", "reject"):
        return END

    if approval.action == "edit":
        return "validate"

    return END


_compiled_app = None


def build_graph():
    """Builds and compiles the Campaign StateGraph with checkpointer."""
    checkpointer = get_checkpointer()
    builder = StateGraph(CampaignState)

    builder.add_node("fetch_context", fetch_context_node)
    builder.add_node("decision", decision_node)
    builder.add_node("build_facts", build_facts_node)
    builder.add_node("content", content_node)
    builder.add_node("validate", validate_node)
    builder.add_node("generate_image", generate_image_node)
    builder.add_node("human_approval", human_approval_node)
    builder.add_node("mark_approved", mark_approved_node)

    builder.add_edge(START, "fetch_context")
    builder.add_edge("fetch_context", "decision")
    builder.add_edge("decision", "build_facts")
    builder.add_edge("build_facts", "content")
    builder.add_edge("content", "validate")

    builder.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "generate_image": "generate_image",
            "content": "content",
            "mark_approved": "mark_approved",
            END: END,
        },
    )

    builder.add_edge("generate_image", "human_approval")
    builder.add_edge("mark_approved", END)

    builder.add_conditional_edges(
        "human_approval",
        route_after_approval,
        {
            "validate": "validate",
            END: END,
        },
    )

    return builder.compile(checkpointer=checkpointer)


def get_app():
    global _compiled_app
    if _compiled_app is None:
        _compiled_app = build_graph()
    return _compiled_app


def reset_app():
    """Resets the compiled graph cache (useful between tests)."""
    global _compiled_app
    _compiled_app = None


def run_campaign(initial_state: CampaignState, thread_id: str) -> CampaignState:
    """Runs campaign workflow until interrupt or completion."""
    app = get_app()
    config = {"configurable": {"thread_id": thread_id}}
    return app.invoke(initial_state, config=config)


def resume_campaign(thread_id: str, approval: Union[ApprovalDecision, dict]) -> CampaignState:
    """Resumes campaign workflow from interrupt using Command(resume=...)."""
    app = get_app()
    config = {"configurable": {"thread_id": thread_id}}
    if isinstance(approval, dict):
        approval_obj = ApprovalDecision(**approval)
    else:
        approval_obj = approval
    return app.invoke(Command(resume=approval_obj), config=config)
