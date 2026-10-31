"""Apex Pipeline — isolated V2 Generator candidate."""
import logging

_LOG = logging.getLogger("ComfyUI")
try:
    from .generator_nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
except Exception:
    _LOG.exception("[Apex Pipeline] Failed to import Generator nodes. See traceback above.")
    raise

try:
    from .lora_trigger_lookup import register_route
    register_route()
except Exception:
    _LOG.exception("[Apex Pipeline] Could not enable the on-demand LoRA trigger lookup.")

WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
