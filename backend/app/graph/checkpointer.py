import logging
from typing import Any
from app.config.settings import settings
from langgraph.checkpoint.memory import InMemorySaver

logger = logging.getLogger(__name__)


def get_checkpointer() -> Any:
    """
    Returns a checkpointer instance for LangGraph workflow execution.
    Tries PostgresSaver if settings.supabase_db_url is set, otherwise falls back to InMemorySaver.
    """
    db_url = settings.supabase_db_url
    if db_url and db_url != "postgresql://postgres:password@db.your-project.supabase.co:5432/postgres":
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            saver = PostgresSaver.from_conn_string(db_url)
            return saver
        except Exception as e:
            logger.warning(f"Failed to connect to Postgres checkpointer: {e}")

    logger.warning("Using in-memory checkpointer — state will NOT survive a restart.")
    return InMemorySaver()
