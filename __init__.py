"""Apex Pipeline — Generator-only first public release."""
import logging

_LOG = logging.getLogger("ComfyUI")
try:
    from .generator_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except Exception:
    _LOG.exception("[Apex Pipeline] Failed to import Generator nodes. See traceback above.")
    raise

WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
