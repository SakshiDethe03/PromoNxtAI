import functools
import logging
from typing import Any

from app.config.settings import settings

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def get_client() -> Any:
    """
    Returns a cached Supabase Client instance using settings.supabase_url and settings.supabase_key.
    Should NOT be called at import time or when settings.use_sample_data is True.
    """
    try:
        from supabase import create_client
        logger.info(f"Initializing Supabase client for {settings.supabase_url}")
        return create_client(settings.supabase_url, settings.supabase_key)
    except ImportError as e:
        logger.error(f"Supabase library not installed: {e}")
        raise RuntimeError("supabase package is required to get a live Supabase client") from e
