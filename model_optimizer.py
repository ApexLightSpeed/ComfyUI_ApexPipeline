"""Apex-owned Krea 2 model optimizer with a safe, native ComfyUI picker.

When LC123 is installed, this node delegates its mature model-selection,
recommendation and hardware-optimization execution to LC123's LCOptimizer
engine, but replaces the engine's unbounded local-file scan with ComfyUI's
registered, cached folder lists. The Apex node uses ordinary Combox widgets;
it does not call LC123's custom /choices endpoint or render its custom picker.

Without LC123, the node remains usable as a straightforward native Krea 2
loader. This module does not patch LC123 permanently: the safe list function is
installed only while the Apex node requests the schema or executes.
"""
from __future__ import annotations

import inspect
import logging
import threading
from contextlib import contextmanager
from typing import Iterable

import folder_paths
import nodes as comfy_nodes

_LOG = logging.getLogger("ComfyUI")
_PATCH_LOCK = threading.RLock()

_MODEL_EXTENSIONS = (".safetensors", ".ckpt", ".pt", ".bin", ".gguf")
_TEXT_EXTENSIONS = (".safetensors", ".sft", ".pt", ".bin", ".gguf")
_VAE_EXTENSIONS = (".safetensors", ".sft", ".pt", ".ckpt")
_EMPTY = "(no compatible files found — check the ComfyUI models folder)"

# These are the only categories Apex needs to expose for this image workflow.
# GGUF directories are included only when a GGUF extension registered them.
_SAFE_CATEGORIES = {
    "checkpoints", "diffusion_models", "text_encoders", "vae",
    "unet_gguf", "clip_gguf",
}
_GGUF_CATEGORY = {"diffusion_models": "unet_gguf", "text_encoders": "clip_gguf"}


def _safe_folder_list(category: str) -> list[str]:
    """Read one ComfyUI-registered model category without custom disk walks."""
    if category not in _SAFE_CATEGORIES:
        return []
    try:
        values = folder_paths.get_filename_list(category)
        # Return a new list so callers cannot mutate ComfyUI's cached listing.
        return list(values or ())
    except MemoryError:
        _LOG.exception(
            "[Apex Model Optimizer] MemoryError reading ComfyUI model category '%s'. "
            "Returning no local entries for this category; the node remains available.",
            category,
        )
    except Exception:
        _LOG.exception("[Apex Model Optimizer] Could not read model category '%s'.", category)
    return []


def _safe_lc_list(category: str) -> list[str]:
    """Replacement for LC123 engine._list, retaining registered GGUF support.

    LC123 currently performs a recursive os.walk(..., followlinks=True) for
    GGUF files when no GGUF category is registered. This adapter intentionally
    skips that fallback: it can follow Windows junctions and duplicate very
    large directory trees. Registered ComfyUI / GGUF category lists still work.
    """
    names = _safe_folder_list(category)
    extra_category = _GGUF_CATEGORY.get(category)
    if extra_category:
        try:
            registered = extra_category in getattr(folder_paths, "folder_names_and_paths", {})
        except Exception:
            registered = False
        if registered:
            for name in _safe_folder_list(extra_category):
                if name not in names:
                    names.append(name)
    return names


def _get_lc_optimizer():
    """Return (LCOptimizer class, its engine module), without importing LC123."""
    mappings = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {})
    lc_cls = mappings.get("LCOptimizer") if isinstance(mappings, dict) else None
    if lc_cls is None:
        return None, None
    module = inspect.getmodule(lc_cls)
    engine = getattr(module, "E", None) if module else None
    if engine is None or not callable(getattr(engine, "_list", None)):
        return None, None
    return lc_cls, engine


@contextmanager
def _safe_lc_scan(engine):
    """Temporarily constrain LC engine file enumeration to cached Comfy lists."""
    with _PATCH_LOCK:
        original = engine._list
        engine._list = _safe_lc_list
        try:
            yield
        finally:
            engine._list = original


def _native_files(category: str, extensions: Iterable[str]) -> list[str]:
    values = _safe_folder_list(category)
    allowed = tuple(ext.lower() for ext in extensions)
    try:
        found = sorted(
            (v for v in values if isinstance(v, str) and v.lower().endswith(allowed)),
            key=str.casefold,
        )
    except MemoryError:
        _LOG.exception("[Apex Model Optimizer] MemoryError filtering '%s'.", category)
        return [_EMPTY]
    return found or [_EMPTY]


def _native_input_types():
    """Compatible fallback schema when LC123 is not installed."""
    try:
        import nodes
        clip_cls = nodes.NODE_CLASS_MAPPINGS.get("CLIPLoader")
        clip_types = clip_cls.INPUT_TYPES()["required"]["type"][0] if clip_cls else []
    except Exception:
        clip_types = []
    if "krea2" not in clip_types:
        clip_types = ["krea2"] + list(clip_types)
    return {
        "required": {
            "base_model": (["Krea 2 (Turbo)", "Krea 2 (Raw)", "Custom"],
                           {"default": "Krea 2 (Turbo)"}),
            "goal": (["Quality", "Optimal", "Fast"], {"default": "Optimal", "tooltip": "Requires LC123 for report-based goals; ignored by the native fallback."}),
            "model_file": (_native_files("diffusion_models", _MODEL_EXTENSIONS), {}),
            "text_encoder": (_native_files("text_encoders", _TEXT_EXTENSIONS), {}),
            "vae": (_native_files("vae", _VAE_EXTENSIONS), {}),
            "speed_ups": (["Auto", "Manual"], {"default": "Auto", "tooltip": "Requires LC123 for hardware-aware Auto/Manual optimization; ignored by the native fallback."}),
            "attention": (["auto", "sdpa"], {"default": "auto", "tooltip": "Requires LC123; ignored by the native fallback."}),
            "fp16_accumulation": (["auto", "on", "off"], {"default": "auto", "tooltip": "Requires LC123; ignored by the native fallback."}),
            "step_cache": (["auto", "on", "off"], {"default": "auto", "tooltip": "Requires LC123; ignored by the native fallback."}),
            "torch_compile": (["off", "on"], {"default": "off", "tooltip": "Requires LC123; ignored by the native fallback."}),
            "qwen21_cache": (["auto", "off"], {"default": "auto", "tooltip": "Requires LC123; ignored by the native fallback."}),
            "clip_type": (clip_types, {"default": "krea2", "tooltip": "The native fallback always uses krea2. The selection is retained for compatibility."}),
        },
        "optional": {
            "spectrum": (["", "auto", "on", "off"], {"default": "off", "tooltip": "Requires LC123; disabled by default for compatibility."}),
            "veda": (["", "auto", "on", "off"], {"default": "", "tooltip": "Requires LC123; ignored by the native fallback."}),
        },
    }


def _native_load(model_file: str, text_encoder: str, vae: str, base_model: str):
    """Load Krea 2 through ComfyUI core if LC123 is unavailable."""
    if any(not v or str(v).startswith("(no compatible files") for v in (model_file, text_encoder, vae)):
        raise RuntimeError(
            "Apex Model Optimizer: choose a diffusion model, Qwen3-VL text encoder, "
            "and Qwen Image VAE from the dropdowns."
        )
    mappings = getattr(comfy_nodes, "NODE_CLASS_MAPPINGS", {})
    missing = [n for n in ("UNETLoader", "CLIPLoader", "VAELoader") if n not in mappings]
    if missing:
        raise RuntimeError("Apex Model Optimizer requires ComfyUI native loaders: " + ", ".join(missing))
    clip_cls = mappings["CLIPLoader"]
    try:
        clip_types = clip_cls.INPUT_TYPES()["required"]["type"][0]
    except Exception:
        clip_types = []
    if "krea2" not in clip_types:
        raise RuntimeError(
            "Apex Model Optimizer needs ComfyUI's native 'krea2' CLIP type. "
            "Update ComfyUI and restart it."
        )
    try:
        model = mappings["UNETLoader"]().load_unet(model_file, "default")[0]
        clip = clip_cls().load_clip(text_encoder, type="krea2")[0]
        vae_obj = mappings["VAELoader"]().load_vae(vae)[0]
    except Exception as exc:
        raise RuntimeError(
            "Apex Model Optimizer could not load the selected Krea 2 components. "
            "Check model compatibility and folder placement. Original error: " + str(exc)
        ) from exc
    summary = (
        f"Apex Model Optimizer · {base_model}\n"
        f"Diffusion model: {model_file}\nText encoder: {text_encoder} · krea2\n"
        f"VAE: {vae}\nLoad path: native ComfyUI loaders (LC123 optimizer unavailable)"
    )
    print("[Apex Model Optimizer]\n" + summary)
    return {"ui": {"apex_status": summary.splitlines()[:8]}, "result": (model, clip, vae_obj, summary)}


class ApexModelOptimizer:
    """Apex model picker + optimizer adapter for ComfyUI Krea 2 workflows."""

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING")
    RETURN_NAMES = ("model", "clip", "vae", "summary")
    FUNCTION = "run"
    CATEGORY = "Apex/Loaders"
    DESCRIPTION = (
        "Apex-owned Krea 2 loader with standard ComfyUI dropdowns. When LC123 is "
        "installed, preserves its Optimal/Quality/Fast recommendations and hardware-aware "
        "optimization options, while bypassing its custom recursive file-picker scan."
    )

    @classmethod
    def INPUT_TYPES(cls):
        lc_cls, engine = _get_lc_optimizer()
        if lc_cls is not None and engine is not None:
            try:
                with _safe_lc_scan(engine):
                    schema = lc_cls.INPUT_TYPES()
                # Spectrum is optional in LC123's optimizer. It can cause
                # compatibility/runtime failures on some Krea 2 setups, so
                # Apex defaults it to off while preserving the user control.
                schema = dict(schema)
                for section in ("required", "optional"):
                    if section in schema:
                        schema[section] = dict(schema[section])
                        entry = schema[section].get("spectrum")
                        if isinstance(entry, tuple) and len(entry) >= 2:
                            options = dict(entry[1] or {})
                            options["default"] = "off"
                            schema[section]["spectrum"] = (entry[0], options, *entry[2:])
                return schema
            except MemoryError:
                _LOG.exception(
                    "[Apex Model Optimizer] LC123 schema generation ran out of memory; "
                    "using the native fallback schema."
                )
            except Exception:
                _LOG.exception("[Apex Model Optimizer] Could not read LC123's optimizer schema; using native fallback.")
        return _native_input_types()

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        lc_cls, engine = _get_lc_optimizer()
        if lc_cls is not None and engine is not None:
            method = getattr(lc_cls, "IS_CHANGED", None)
            if callable(method):
                try:
                    with _safe_lc_scan(engine):
                        return method(**kwargs)
                except Exception:
                    _LOG.exception("[Apex Model Optimizer] LC123 change tracking failed; using input-based caching.")
        # Input values themselves are part of ComfyUI's normal cache key.
        return "native"

    def run(
        self,
        base_model,
        goal="Optimal",
        model_file=None,
        text_encoder=None,
        vae=None,
        **kwargs,
    ):
        lc_cls, engine = _get_lc_optimizer()
        if lc_cls is not None and engine is not None:
            try:
                with _safe_lc_scan(engine):
                    instance = lc_cls()
                    result = instance.run(base_model, goal, model_file=model_file,
                                          text_encoder=text_encoder, vae=vae, **kwargs)
                if not isinstance(result, dict):
                    result = {"result": tuple(result)}
                ui = result.setdefault("ui", {})
                outputs = result.get("result", ())
                summary = outputs[3] if isinstance(outputs, (list, tuple)) and len(outputs) > 3 else "Apex Model Optimizer completed."
                lines = [line.strip() for line in str(summary).splitlines() if line.strip()]
                ui["apex_status"] = lines[:8] or ["Apex Model Optimizer completed."]
                print("[Apex Model Optimizer] Used LC123 model optimization engine through Apex's safe picker adapter.")
                return result
            except MemoryError as exc:
                _LOG.exception("[Apex Model Optimizer] MemoryError while running LC123 optimizer engine.")
                raise RuntimeError(
                    "Apex Model Optimizer ran out of memory while loading or optimizing the selected model. "
                    "The dropdown scan has been constrained; check model load memory and the ComfyUI console."
                ) from exc
        return _native_load(model_file, text_encoder, vae, base_model)
