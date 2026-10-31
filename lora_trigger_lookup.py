"""On-demand, read-only LoRA trigger lookup for Apex V2's small frontend helper."""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
from threading import RLock
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import quote

import folder_paths

_LOG = logging.getLogger("ComfyUI")
_CACHE: dict[tuple[str, int, int], dict] = {}
_CACHE_LOCK = RLock()
_MAX_CACHE = 256
_METADATA_KEYS = (
    "ss_trigger_words", "trigger_words", "trainedwords", "trained_words",
    "modelspec.trigger_phrase", "modelspec.tags", "civitai:trainedwords",
    "civitai:trained_words",
)


def _normalize_words(value) -> list[str]:
    if isinstance(value, str):
        source = value.strip()
        if not source:
            return []
        try:
            decoded = json.loads(source)
        except (TypeError, ValueError):
            decoded = None
        if isinstance(decoded, (list, tuple)):
            value = decoded
        else:
            value = [part.strip() for part in source.replace("\n", ",").replace("|", ",").split(",")]
    if not isinstance(value, (list, tuple)):
        return []
    result, seen = [], set()
    for entry in value:
        if not isinstance(entry, str):
            continue
        word = " ".join(entry.split()).strip(" ,\t\r\n")
        key = word.casefold()
        if word and len(word) <= 180 and key not in seen:
            seen.add(key)
            result.append(word)
        if len(result) >= 32:
            break
    return result


def _local_trigger_words(path: str) -> list[str]:
    if not path.lower().endswith(".safetensors"):
        return []
    try:
        from safetensors import safe_open

        with safe_open(path, framework="pt", device="cpu") as model_file:
            metadata = model_file.metadata() or {}
    except Exception as exc:
        _LOG.debug("[Apex] Could not read LoRA safetensors metadata for trigger words: %s", exc)
        return []
    for key, value in metadata.items():
        lowered = str(key).casefold()
        if lowered in _METADATA_KEYS or "trigger_word" in lowered or lowered.endswith("trigger_phrase"):
            words = _normalize_words(value)
            if words:
                return words
    return []


def _civitai_trigger_words(path: str) -> list[str]:
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(4 * 1024 * 1024), b""):
            digest.update(block)
    url = "https://civitai.com/api/v1/model-versions/by-hash/" + quote(digest.hexdigest(), safe="")
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "ApexPipeline/2 trigger lookup"})
    with urlopen(request, timeout=12) as response:
        data = json.loads(response.read(2 * 1024 * 1024).decode("utf-8"))
    return _normalize_words(data.get("trainedWords"))


def _resolved_local_path(name: str) -> str:
    if not isinstance(name, str) or not name or len(name) > 1024:
        raise ValueError("Choose a LoRA from the Apex picker first.")
    available = folder_paths.get_filename_list("loras") or []
    if name not in available:
        raise ValueError("The selected LoRA is no longer in ComfyUI's indexed LoRA list. Refresh the model list and try again.")
    path = folder_paths.get_full_path("loras", name)
    if not path or not os.path.isfile(path):
        raise FileNotFoundError("ComfyUI could not resolve the selected LoRA file.")
    resolved = os.path.realpath(path)
    roots = [os.path.realpath(root) for root in folder_paths.get_folder_paths("loras")]
    if not any(os.path.commonpath((resolved, root)) == root for root in roots):
        raise ValueError("The selected path is outside ComfyUI's registered LoRA folders.")
    return resolved


def _lookup(path: str) -> dict:
    stat = os.stat(path)
    cache_key = (path, int(stat.st_size), int(stat.st_mtime_ns))
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None:
            return dict(cached)

    words = _local_trigger_words(path)
    source = "local metadata" if words else "none"
    if not words:
        try:
            words = _civitai_trigger_words(path)
            source = "Civitai SHA-256" if words else "Civitai has no trigger words"
        except HTTPError as exc:
            source = "no Civitai match" if exc.code == 404 else "Civitai lookup unavailable"
            if exc.code != 404:
                _LOG.info("[Apex] Civitai LoRA trigger lookup returned HTTP %s", exc.code)
        except (TimeoutError, URLError, OSError, ValueError, json.JSONDecodeError) as exc:
            source = "Civitai lookup unavailable"
            _LOG.info("[Apex] Civitai LoRA trigger lookup unavailable: %s", exc)
    result = {"words": words, "source": source}
    with _CACHE_LOCK:
        if len(_CACHE) >= _MAX_CACHE:
            _CACHE.pop(next(iter(_CACHE)))
        _CACHE[cache_key] = dict(result)
    return result


def register_route() -> None:
    """Register one same-machine endpoint; only called after PromptServer exists."""
    try:
        from aiohttp import web
        from server import PromptServer

        server = PromptServer.instance
        if server is None or getattr(server, "_apex_lora_trigger_route_registered", False):
            return

        async def lookup_route(request):
            if request.remote not in {"127.0.0.1", "::1", "localhost"}:
                return web.json_response({"error": "This local-only helper can only be called from this machine."}, status=403)
            try:
                path = _resolved_local_path(request.query.get("name", ""))
                result = await asyncio.to_thread(_lookup, path)
                return web.json_response({"words": result["words"], "source": result["source"]})
            except (ValueError, FileNotFoundError) as exc:
                return web.json_response({"error": str(exc)}, status=400)
            except Exception:
                _LOG.exception("[Apex] Unexpected error in local LoRA trigger lookup.")
                return web.json_response({"error": "Trigger lookup failed. Check the ComfyUI log for details."}, status=500)

        # ComfyUI's route table wraps aiohttp RouteTableDef.get; unlike the
        # lower-level decorator it does not accept a `name` keyword here.
        server.routes.get("/apex/v2/lora-trigger-words")(lookup_route)
        server._apex_lora_trigger_route_registered = True
    except Exception:
        _LOG.exception("[Apex] Could not register local LoRA trigger lookup route.")
