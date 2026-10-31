"""Apex Pipeline Generator nodes.

V1 registers only the three nodes used by the Generator
workflow. Refinement, repair, upscale, and detailer nodes are intentionally not
part of this release.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import re
import secrets
import time

import torch
import folder_paths
import comfy.sd
import comfy.utils
import comfy.samplers
import comfy.model_management
import nodes as comfy_nodes

from . import recipe_core as core
from .model_optimizer import ApexModelOptimizer

CATEGORY = "Apex"
MAXSEED = 0xFFFFFFFFFFFFFFFF
SAMPLERS = list(comfy.samplers.KSampler.SAMPLERS)
SCHEDULERS = list(comfy.samplers.KSampler.SCHEDULERS)
MAX_LINES = {"recipe": 9, "generate": 5}


def _resolved_model_from_summary(summary):
    """Read the selected model filename from Apex Model Engine's status summary."""
    if not isinstance(summary, str):
        return ""
    for line in summary.splitlines():
        match = re.match(r"\s*(?:model|diffusion model)\s*:\s*(.+?)\s*$", line, re.IGNORECASE)
        if not match:
            continue
        filename = re.sub(r"\s+\(diffusion model\)\s*$", "", match.group(1), flags=re.IGNORECASE).strip()
        if filename and filename not in {"★ Recommended", "Recommended"}:
            return filename
    return ""

def _resolved_resources_from_summary(summary):
    """Return runtime-selected model, text encoder, and VAE filenames."""
    if not isinstance(summary, str):
        return {}
    labels = {
        "model": ("model", "diffusion model"),
        "text_encoder": ("text encoder", "clip", "encoder"),
        "vae": ("vae",),
    }
    found = {}
    file_re = re.compile(r"[^/\\\s,;]+\.(?:safetensors|sft|gguf|ckpt|pt|bin|pth)\b", re.IGNORECASE)
    for line in summary.splitlines():
        match = re.match(r"\s*([^:]+)\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        label, value = match.group(1).strip().lower(), match.group(2)
        key = next((key for key, names in labels.items() if label in names), None)
        if key and (file_match := file_re.search(value)):
            found[key] = file_match.group(0)
    return found

def _prompt_with_resolved_resources(prompt, summary):
    """Copy the execution prompt and replace Apex optimizer placeholders for LC123 hashing."""
    resources = _resolved_resources_from_summary(summary)
    if not resources or not isinstance(prompt, dict):
        return prompt
    result = json.loads(json.dumps(prompt))
    for node in result.values():
        if not isinstance(node, dict) or node.get("class_type") != "ApexModelOptimizer":
            continue
        inputs = node.get("inputs")
        if not isinstance(inputs, dict):
            continue
        for key, resource in (("model_file", "model"), ("text_encoder", "text_encoder"), ("vae", "vae")):
            if resources.get(resource):
                inputs[key] = resources[resource]
    return result

def _search_dirs():
    out = []
    for fn in ("get_input_directory", "get_output_directory", "get_temp_directory"):
        try:
            d = getattr(folder_paths, fn)()
            if d and d not in out:
                out.append(d)
        except Exception:
            pass
    return out

def locate_image(name):
    """Resolve the file name a Load Image node reports to a real path."""
    if not name:
        return None
    name = str(name).strip().strip('"')
    if os.path.isabs(name) and os.path.isfile(name):
        return name
    try:
        p = folder_paths.get_annotated_filepath(name)
        if p and os.path.isfile(p):
            return p
    except Exception:
        pass
    import re
    clean = re.sub(r"\s*\[(input|output|temp)\]\s*$", "", name)
    base = os.path.basename(clean.replace("\\", "/"))
    ext = os.path.splitext(base)[1].lower()
    cands = [clean] if ext in core.IMG_EXTS else [clean + e for e in core.IMG_EXTS]
    dirs = _search_dirs()
    for d in dirs:
        for c in cands:
            p = os.path.join(d, c)
            if os.path.isfile(p):
                return p
    wanted = [base] if ext in core.IMG_EXTS else [base + e for e in core.IMG_EXTS]
    for d in dirs:
        for root, _d, files in os.walk(d):
            for w in wanted:
                if w in files:
                    return os.path.join(root, w)
    return None

_LORA_CACHE = {}

def _load_lora_file(path):
    key = (path, os.path.getmtime(path))
    if key not in _LORA_CACHE:
        _LORA_CACHE.clear()
        _LORA_CACHE[key] = comfy.utils.load_torch_file(path, safe_load=True)
    return _LORA_CACHE[key]

class _Memo:
    """One-entry cache keyed on object IDENTITY of the inputs plus plain params.

    ComfyUI caches whole nodes, so when everything is fused into one node a new seed would
    re-run text encoding / VAE encode that the loose nodes used to skip. This restores that
    behaviour.
    """
    def __init__(self):
        self.refs, self.params, self.val = None, None, None

    def get(self, refs, params):
        if self.refs is not None and len(self.refs) == len(refs) and all(
            a is b for a, b in zip(self.refs, refs)
        ) and self.params == params:
            return self.val
        return None

    def put(self, refs, params, val):
        self.refs, self.params, self.val = tuple(refs), params, val
        return val

_HASH_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apex_hash_cache.json")
_HASH_MEM = {}

def lora_autov2(path):
    """Civitai AutoV2 = first 10 hex chars of file SHA256, cached by (path, size, mtime)."""
    st = os.stat(path)
    key = f"{path}|{st.st_size}|{int(st.st_mtime)}"
    if not _HASH_MEM:
        try:
            with open(_HASH_FILE, "r", encoding="utf-8") as f:
                _HASH_MEM.update(json.load(f))
        except Exception:
            pass
    if key not in _HASH_MEM:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        _HASH_MEM[key] = h.hexdigest()[:10]
        try:
            with open(_HASH_FILE, "w", encoding="utf-8") as f:
                json.dump(_HASH_MEM, f)
        except Exception:
            pass
    return _HASH_MEM[key]

def hash_line(loras):
    """A1111 `Lora hashes: \"name: hash, ...\"`; returns line and per-LoRA hashes."""
    available = folder_paths.get_filename_list("loras")
    parts, got = [], []
    for l in loras:
        hit = core.match_lora(l["name"], available)
        full = folder_paths.get_full_path("loras", hit) if hit else None
        if not full:
            got.append(None)
            continue
        hv = lora_autov2(full)
        got.append(hv)
        nm = core.tag_name(l["name"]).replace('"', " ").replace(",", " ").replace(":", " ")
        parts.append(f"{nm}: {hv}")
    return (f'Lora hashes: "{", ".join(parts)}"' if parts else ""), got

def _encode(clip, text):
    tokens = clip.tokenize(text)
    return clip.encode_from_tokens_scheduled(tokens)

def _zero_out(conditioning):
    out = []
    for t in conditioning:
        d = t[1].copy()
        if d.get("pooled_output") is not None:
            d["pooled_output"] = torch.zeros_like(d["pooled_output"])
        if d.get("conditioning_lyrics") is not None:
            d["conditioning_lyrics"] = torch.zeros_like(d["conditioning_lyrics"])
        out.append([torch.zeros_like(t[0]), d])
    return out

def _decode(vae, latent):
    images = vae.decode(latent["samples"])
    if len(images.shape) == 5:
        images = images.reshape(-1, images.shape[-3], images.shape[-2], images.shape[-1])
    return images

def _join(a, b, sep=", "):
    a, b = (a or "").strip().rstrip(","), (b or "").strip().lstrip(",")
    return (a + sep + b).strip() if a and b else (a or b)


def _meta_positive(text, tags):
    return _join(text, tags, " ")

def _ui(lines, result):
    return {"ui": {"apex_status": [str(x) for x in lines]}, "result": result}


def _rename_ui_images(payload, field_name):
    """Keep images available to Apex's DOM surface without Comfy's canvas thumbnail."""
    if not isinstance(payload, dict):
        return payload
    ui = dict(payload.get("ui") or {})
    ui[field_name] = ui.pop("images", [])
    return {**payload, "ui": ui}

def _clip_lines(lines, n):
    if len(lines) <= n:
        return lines
    return lines[: n - 1] + [f"… +{len(lines) - n + 1} more (see console)"]

_GEN_COND = _Memo()
_GEN_LORA = _Memo()

class ApexRecipe:
    """Reads a recipe and applies / reports LoRAs.

    `from image`: replay an image's LoRAs at exact strengths.
    `live stack`: read already-applied LoRAs from the upstream graph for metadata.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "source": (["from image", "live stack"], {"default": "from image",
                    "tooltip": "from image = replay LoRAs recorded in image_name. live stack = read the upstream stack."}),
                "allow_missing": ("BOOLEAN", {"default": False,
                    "tooltip": "Off = error if a recorded LoRA is missing. On = skip it and report it."}),
            },
            "optional": {
                "image_name": ("STRING", {"forceInput": True,
                    "tooltip": "Filename output of Load Image (from image mode)."}),
            },
            "hidden": {"graph": "PROMPT", "unique_id": "UNIQUE_ID"},
        }

    RETURN_TYPES = ("MODEL", "CLIP", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("model", "clip", "prompt", "lora_tags", "lora_hashes", "checkpoint")
    FUNCTION = "run"
    CATEGORY = CATEGORY
    DESCRIPTION = "Exact per-LoRA replay + <lora:name:model:clip> tags for Civitai."

    @classmethod
    def IS_CHANGED(cls, source, image_name=None, **kw):
        p = locate_image(image_name) if image_name else None
        return (os.path.getmtime(p) if p else 0, str(image_name), source)

    def run(self, model, clip, source, allow_missing, image_name=None, graph=None, unique_id=None):
        lines = []
        up_loras, up_ckpt = core.upstream_chain(graph or {}, unique_id)

        if source == "live stack":
            applied = [l for l in up_loras if l["on"]]
            lines.append(f"LIVE: {len(applied)} LoRA(s) feeding this model")
            hline, hv = hash_line(applied)
            for i, (l, h) in enumerate(zip(applied, hv), 1):
                lines.append(f" {i}. {l['name']}  {l['sm']:g} / {l['sc']:g}  #{h or 'NO FILE'}")
            if None in hv:
                lines.append("! a LoRA file was not found locally: no hash, Civitai cannot link it")
            if not applied:
                lines.append("! no LoRA loader found upstream of this node's model input")
            lines.append(f"checkpoint: {up_ckpt or '? (no loader found upstream)'}")
            print("[Apex Recipe]\n" + "\n".join(lines))
            return _ui(_clip_lines(lines, MAX_LINES["recipe"]),
                       (model, clip, "", core.format_tags(applied), hline, up_ckpt))

        if not image_name:
            raise ValueError(
                "Apex Recipe: source is 'from image' but image_name is not connected. "
                "Wire the filename output of the Load Image node."
            )
        path = locate_image(image_name)
        if not path:
            raise FileNotFoundError(
                f"Apex Recipe: image '{image_name}' not found in input/output/temp."
            )
        rec, trail = core.resolve_recipe(path, locate_image)
        c = rec["chunks"]
        if not (c["prompt"] or c["workflow"] or c["parameters"]):
            raise RuntimeError(
                "Apex Recipe: this image has NO embedded metadata. Load the PNG written by LC Save Image."
            )
        lines.append("SRC: " + " > ".join(trail[-3:]))
        available = folder_paths.get_filename_list("loras")
        applied, notes, missing = [], [], []
        for l in rec["loras"]:
            if not l["on"]:
                notes.append(f"{l['name']}: was OFF in the original, skipped")
                continue
            if core.EDIT_ADAPTER.search(l["name"]):
                notes.append(f"{l['name']}: edit adapter from a repair graph, skipped")
                continue
            hit = core.match_lora(l["name"], available)
            if not hit:
                missing.append(l["name"])
                continue
            applied.append((hit, l))
        if missing and not allow_missing:
            raise RuntimeError(
                "Apex Recipe: LoRA(s) recorded in the image are not installed: " + ", ".join(missing)
                + ". Install them, or switch allow_missing on to skip."
            )
        m, k = model, clip
        tags_src = []
        for hit, l in applied:
            if l["sm"] == 0 and l["sc"] == 0:
                notes.append(f"{hit}: strength 0, skipped")
                continue
            lora = _load_lora_file(folder_paths.get_full_path("loras", hit))
            m, k = comfy.sd.load_lora_for_models(m, k, lora, l["sm"], l["sc"])
            tags_src.append({"name": hit, "sm": l["sm"], "sc": l["sc"], "on": True})
        lines.append(f"{len(tags_src)} LoRA(s) APPLIED via {rec['source'] or 'none'}")
        hline, hv = hash_line(tags_src)
        for i, (l, h) in enumerate(zip(tags_src, hv), 1):
            lines.append(f" {i}. {l['name']}  {l['sm']:g} / {l['sc']:g}  #{h or 'NO FILE'}")
        if not rec["loras"]:
            lines.append("! metadata present but NO LoRA data in it; model left unchanged")
        if any(not l.get("exact", True) for l in rec["loras"]):
            lines.append("! source only records approximate strengths (Civitai/hash data)")
        for n in notes + [f"{x}: NOT INSTALLED, skipped" for x in missing]:
            lines.append("! " + n)
        src_ck = rec["checkpoint"]
        if src_ck and up_ckpt and os.path.basename(src_ck).lower() != os.path.basename(up_ckpt).lower():
            lines.append(f"! image was made with {os.path.basename(src_ck)}; this graph loads {os.path.basename(up_ckpt)}")
        print("[Apex Recipe]\n" + "\n".join(lines + ["chain: " + " | ".join(trail)]))
        return _ui(_clip_lines(lines, MAX_LINES["recipe"]),
                   (m, k, rec["prompt"], core.format_tags(tags_src), hline, up_ckpt or src_ck))

class ApexGenerate:
    """Encode -> empty latent -> LC Speed Boost sampler -> decode.

    Steps / CFG / sampler / scheduler remain in one place and feed metadata outputs.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",), "clip": ("CLIP",), "vae": ("VAE",),
                "prompt": ("STRING", {"forceInput": True}),
                "seed": ("INT", {"forceInput": True, "default": 0, "min": 0, "max": MAXSEED}),
                "width": ("INT", {"forceInput": True, "default": 896, "min": 64, "max": 16384}),
                "height": ("INT", {"forceInput": True, "default": 1344, "min": 64, "max": 16384}),
                "speed_boost": ("BOOLEAN", {"default": True, "tooltip": "LC Speed Boost (fresh generations only)."}),
                "steps": ("INT", {"default": 8, "min": 1, "max": 200}),
                "cfg": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 100.0, "step": 0.1}),
                "sampler_name": (SAMPLERS, {"default": "euler" if "euler" in SAMPLERS else SAMPLERS[0]}),
                "scheduler": (SCHEDULERS, {"default": "simple" if "simple" in SCHEDULERS else SCHEDULERS[0]}),
            },
            "optional": {"lora_tags": ("STRING", {"forceInput": True}), "lora_hashes": ("STRING", {"forceInput": True})},
            "hidden": {"graph": "PROMPT", "unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("IMAGE", "STRING", "INT", "INT", "FLOAT", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "metadata_positive", "seed", "steps", "cfg", "sampler", "scheduler", "extra_params")
    FUNCTION = "run"
    CATEGORY = CATEGORY

    def run(self, model, clip, vae, prompt, seed, width, height, speed_boost, steps, cfg,
            sampler_name, scheduler, lora_tags="", lora_hashes="", graph=None, unique_id=None,
            extra_pnginfo=None, batch_size=1):
        lines = []
        t0 = time.perf_counter()
        cond = _GEN_COND.get((clip,), prompt)
        c_hit = cond is not None
        if cond is None:
            positive = _encode(clip, prompt)
            cond = _GEN_COND.put((clip,), prompt, (positive, _zero_out(positive)))
        positive, negative = cond
        t1 = time.perf_counter()
        latent = {"samples": torch.zeros([int(batch_size), 4, int(height) // 8, int(width) // 8],
                                          device=comfy.model_management.intermediate_device())}
        lc = comfy_nodes.NODE_CLASS_MAPPINGS.get("LCSpeedBoostKSampler")
        if lc is None:
            lines.append("! LC123 sampler not installed: plain core sampler used (no Speed Boost)")
            out = comfy_nodes.common_ksampler(model, int(seed), int(steps), float(cfg), sampler_name, scheduler,
                                              positive, negative, latent, denoise=1.0)[0]
        else:
            fn = getattr(lc(), lc.FUNCTION)
            params = inspect.signature(fn).parameters
            has_kw = any(p.kind == p.VAR_KEYWORD for p in params.values())
            cand = dict(model=model, positive=positive, negative=negative, latent_image=latent,
                        speed_boost=bool(speed_boost), grow_at_step=4, seed=int(seed), steps=int(steps),
                        cfg=float(cfg), sampler_name=sampler_name, scheduler=scheduler, denoise=1.0,
                        start_at_step=0, end_at_step=10000, return_with_leftover_noise=False,
                        prompt=graph, unique_id=unique_id, extra_pnginfo=extra_pnginfo)
            res = fn(**{k: v for k, v in cand.items() if has_kw or k in params})
            if isinstance(res, dict):
                res = res.get("result", res)
            out = res[0] if isinstance(res, (tuple, list)) else res
            lines.append(f"LC Speed Boost: {'on' if speed_boost else 'off'}")
        t2 = time.perf_counter()
        image = _decode(vae, out)
        t3 = time.perf_counter()
        lines.append(f"time: text {t1-t0:.1f}s{' (cached)' if c_hit else ''} · sample {t2-t1:.1f}s · decode {t3-t2:.1f}s")
        lines.append(f"{width}x{height} · {steps} steps · cfg {cfg:g} · {sampler_name}/{scheduler} · seed {seed}")
        lines.append("tags: " + (lora_tags or "none connected"))
        print("[Apex Generate]\n" + "\n".join(lines))
        return _ui(_clip_lines(lines, MAX_LINES["generate"]),
                   (image, _meta_positive(prompt, lora_tags), int(seed), int(steps), float(cfg),
                    str(sampler_name), str(scheduler), lora_hashes or ""))


class ApexGenerationCore(ApexGenerate):
    """V2 generation console: prompt, a 64-row LoRA stack, canvas and sampling."""

    RETURN_TYPES = ApexGenerate.RETURN_TYPES + ("INT", "INT", "STRING", "STRING")
    RETURN_NAMES = ApexGenerate.RETURN_NAMES + ("width", "height", "model_name", "model_summary")

    @classmethod
    def INPUT_TYPES(cls):
        schema = ApexGenerate.INPUT_TYPES()
        required = dict(schema["required"])
        required["prompt"] = ("STRING", {
            "default": "",
            "multiline": True,
            "placeholder": "Describe the image you want to make…",
        })
        required["width"] = ("INT", {"default": 896, "min": 64, "max": 16384, "step": 8})
        required["height"] = ("INT", {"default": 1344, "min": 64, "max": 16384, "step": 8})
        required["resolution_ui"] = ("STRING", {"default": json.dumps({
            "mode": "preset", "ratio": "2:3", "w": 896, "h": 1344,
            "custom_w": 1024, "custom_h": 1024,
            "custom_ratio_w": 4, "custom_ratio_h": 3, "snap": 16,
        }, separators=(",", ":"))})
        required["batch_size"] = ("INT", {"default": 1, "min": 1, "max": 64})
        required["seed"] = ("INT", {
            "default": 0,
            "min": 0,
            "max": MAXSEED,
        })
        lora_names = ["(none)"]
        try:
            lora_names += list(folder_paths.get_filename_list("loras") or [])
        except Exception:
            pass
        # Pixaroma's previous stack allowed up to 64 ordered rows. Keep that
        # capacity while storing the whole editable stack as one workflow value.
        required["lora_stack"] = ("STRING", {"default": "[]"})
        required["lora_catalog"] = (lora_names, {"default": "(none)"})
        # LC123 reads this standard A1111 line to recover exact LoRA metadata.
        # The Apex surface mirrors the dynamic rows into this hidden widget.
        required["lora_tags"] = ("STRING", {"default": ""})
        ordered = {}
        for name, definition in required.items():
            if name == "seed":
                ordered["seed_mode"] = (["random", "fixed"], {"default": "random"})
            ordered[name] = definition
        schema["required"] = ordered
        schema["optional"] = {"model_summary": ("STRING", {"forceInput": True})}
        return schema

    @classmethod
    def IS_CHANGED(cls, seed_mode="random", seed=0, lora_stack="[]", **kwargs):
        # Random mode must execute for every queue. Fixed-seed runs also include
        # the editable LoRA stack and selected file revisions in their fingerprint,
        # so adding/toggling/changing a LoRA can never reuse a stale generation.
        if seed_mode == "random":
            return float("nan")
        try:
            rows = json.loads(lora_stack or "[]")
        except (TypeError, ValueError):
            rows = []
        available = folder_paths.get_filename_list("loras")
        revisions = []
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict) or row.get("on", True) is False:
                continue
            name = str(row.get("name") or "").strip()
            if not name or name == "(none)":
                continue
            hit = core.match_lora(name, available)
            if not hit:
                revisions.append((name, "missing"))
                continue
            path = folder_paths.get_full_path("loras", hit)
            try:
                stat = os.stat(path)
                revisions.append((hit, stat.st_size, stat.st_mtime_ns,
                                  float(row.get("sm", 1.0)), float(row.get("sc", 1.0))))
            except OSError:
                revisions.append((hit, "unavailable"))
        return (int(seed), str(lora_stack or "[]"), tuple(revisions))

    def run(self, model, clip, vae, prompt, seed_mode, seed, width, height,
            batch_size, speed_boost, steps, cfg, sampler_name, scheduler,
            lora_stack="[]", lora_catalog="(none)", **kwargs):
        # The Apex canvas editor stores its mode and exact dimensions as one
        # workflow value; width/height remain the native execution inputs.
        resolution_ui = kwargs.pop("resolution_ui", "")
        if resolution_ui:
            try:
                resolution = json.loads(resolution_ui)
                if not isinstance(resolution, dict):
                    raise ValueError
                width = int(resolution.get("w", width))
                height = int(resolution.get("h", height))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError("Apex Generation: canvas resolution state is invalid.") from exc
        width, height = int(width), int(height)
        if not (64 <= width <= 16384 and 64 <= height <= 16384):
            raise ValueError("Apex Generation: width and height must be from 64 to 16384 pixels.")
        available = folder_paths.get_filename_list("loras")
        loaded = []
        selected = []
        try:
            rows = json.loads(lora_stack or "[]")
        except (TypeError, ValueError) as exc:
            raise ValueError("Apex Generation: LoRA stack data is not valid JSON.") from exc
        if not isinstance(rows, list):
            raise ValueError("Apex Generation: LoRA stack must be a list of rows.")
        if len(rows) > 64:
            raise ValueError("Apex Generation: the LoRA stack supports up to 64 rows.")
        active_rows = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not row.get("on", True) or not name or name == "(none)":
                continue
            hit = core.match_lora(name, available)
            if not hit:
                raise FileNotFoundError(f"Apex Generation: selected LoRA is no longer installed: {name}")
            sm, sc = float(row.get("sm", 1.0)), float(row.get("sc", 1.0))
            if not math.isfinite(sm) or not math.isfinite(sc):
                raise ValueError(f"Apex Generation: LoRA strengths must be finite numbers ({name}).")
            trigger = str(row.get("trigger") or "").strip()
            path = folder_paths.get_full_path("loras", hit)
            stat = os.stat(path)
            selected.append((hit, path, stat.st_size, stat.st_mtime_ns, sm, sc))
            loaded.append({"name": hit, "sm": sm, "sc": sc, "on": True})
            active_rows.append((hit, trigger))
        cached_models = _GEN_LORA.get((model, clip), tuple(selected))
        if cached_models is None:
            applied_model, applied_clip = model, clip
            for _hit, path, _size, _mtime, sm, sc in selected:
                if sm == 0 and sc == 0:
                    continue
                lora = _load_lora_file(path)
                applied_model, applied_clip = comfy.sd.load_lora_for_models(applied_model, applied_clip, lora, sm, sc)
            cached_models = _GEN_LORA.put((model, clip), tuple(selected), (applied_model, applied_clip))
        model, clip = cached_models
        lora_tags = core.format_tags(loaded)
        kwargs.pop("lora_tags", None)  # use the backend-resolved, validated values
        lora_hashes, _ = hash_line(loaded)
        trigger_parts = []
        for _hit, trigger in active_rows:
            if trigger:
                trigger_parts.append(trigger)
        trigger_words = " ".join(trigger_parts)
        prompt = _join(prompt, trigger_words, " ")
        model_summary = kwargs.pop("model_summary", "")
        if seed_mode == "random":
            seed = secrets.randbelow(MAXSEED + 1)
        seed = int(seed)
        batch_size = int(batch_size)
        # Pass one latent batch through the established sampler and preserve seed semantics.
        result = super().run(
            model, clip, vae, prompt, seed, width, height, speed_boost,
            steps, cfg, sampler_name, scheduler, lora_tags, lora_hashes,
            batch_size=batch_size, **kwargs,
        )
        _loras, model_name = core.upstream_chain(kwargs.get("graph") or {}, kwargs.get("unique_id"))
        model_name = _resolved_model_from_summary(model_summary) or model_name
        return {"ui": result.get("ui", {}), "result": tuple(result["result"]) +
                (width, height, model_name or "", str(model_summary or ""))}

    CATEGORY = "Apex/Generation"
    DESCRIPTION = (
        "Apex Generation Console. Prompt, LoRA stack, canvas, seed and sampler share one control surface; the established Apex sampler and conditioning-cache path are retained."
    )


class ApexOutput:
    """Apex-branded output adapter around the installed LC123 metadata/saver nodes."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE",),
                "positive": ("STRING", {"forceInput": True}),
                "seed": ("INT", {"forceInput": True, "default": 0, "min": 0, "max": MAXSEED}),
                "steps": ("INT", {"forceInput": True, "default": 8, "min": 1, "max": 200}),
                "cfg": ("FLOAT", {"forceInput": True, "default": 1.0, "min": 0.0, "max": 100.0}),
                "sampler": ("STRING", {"forceInput": True}),
                "scheduler": ("STRING", {"forceInput": True}),
                "extra_params": ("STRING", {"forceInput": True}),
                "model_name": ("STRING", {"forceInput": True}),
                "model_summary": ("STRING", {"forceInput": True}),
                "width": ("INT", {"forceInput": True, "default": 896, "min": 64, "max": 16384}),
                "height": ("INT", {"forceInput": True, "default": 1344, "min": 64, "max": 16384}),
                "filename": ("STRING", {"default": "Apex_%seed", "placeholder": "Apex_%seed"}),
                "folder": ("STRING", {"default": "Apex"}),
                "format": (["png", "jpeg", "webp"], {"default": "png"}),
                "quality": ("INT", {"default": 100, "min": 1, "max": 100}),
                "embed_workflow": ("BOOLEAN", {"default": True}),
                "embed_civitai": ("BOOLEAN", {"default": True}),
                "hash_resources": ("BOOLEAN", {"default": True}),
                "negative": ("STRING", {"default": "", "multiline": True}),
                "civitai_air": ("STRING", {"default": "", "placeholder": "Optional Civitai AIR or URL"}),
                "denoise": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "hidden": {"graph": "PROMPT", "unique_id": "UNIQUE_ID", "extra_pnginfo": "EXTRA_PNGINFO", "execution_list": "EXECUTION_LIST"},
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("images", "saved_as")
    FUNCTION = "save"
    CATEGORY = "Apex/Output"
    OUTPUT_NODE = True
    DESCRIPTION = "Apex Output: save one PNG with embedded Comfy workflow, Civitai parameters, and resource hashes through the installed LC123 saver."

    def save(self, images, positive, seed, steps, cfg, sampler, scheduler, extra_params, model_name, model_summary,
             width, height, filename, folder, format, quality, embed_workflow, embed_civitai,
             hash_resources, negative="", civitai_air="", denoise=0.0, graph=None, unique_id=None,
             extra_pnginfo=None, execution_list=None):
        metadata_cls = comfy_nodes.NODE_CLASS_MAPPINGS.get("LCSaveImageMetadata")
        saver_cls = comfy_nodes.NODE_CLASS_MAPPINGS.get("LCSaveImage")
        if metadata_cls is None or saver_cls is None:
            raise RuntimeError("Apex Output requires LC123's LCSaveImageMetadata and LCSaveImage nodes to be installed.")
        # Keep LC123's metadata construction and PNG writing code as the runtime implementation.
        metadata, _parameters = metadata_cls().build(
            positive=positive, negative=negative, seed_value=int(seed), steps=int(steps), cfg=float(cfg),
            sampler=str(sampler), scheduler=str(scheduler), width=int(width), height=int(height),
            models=str(model_name or ""), civitai_air=str(civitai_air or ""), denoise=float(denoise),
            extra_params=str(extra_params or ""),
        )
        hash_prompt = _prompt_with_resolved_resources(graph, model_summary)
        saved = saver_cls().save(
            images=images, filename=filename or "Apex_%seed", path=folder or "",
            format=str(format or "png"), quality=int(quality),
            embed_workflow=bool(embed_workflow), embed_civitai=bool(embed_civitai),
            hash_resources=bool(hash_resources), metadata=metadata, prompt=hash_prompt,
            extra_pnginfo=extra_pnginfo, unique_id=unique_id,
            execution_list=execution_list,
        )
        return _rename_ui_images(saved, "apex_saved_images")


class ApexPreview:
    """Image-only, resizable Comfy preview node for the Apex workflow."""

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"image": ("IMAGE",)}}

    RETURN_TYPES = ()
    FUNCTION = "preview"
    CATEGORY = "Apex/Output"
    OUTPUT_NODE = True
    DESCRIPTION = "A minimal image display. Drag the lower-right corner to resize it."

    def preview(self, image):
        preview_cls = comfy_nodes.NODE_CLASS_MAPPINGS.get("PreviewImage")
        if preview_cls is None:
            raise RuntimeError("Apex Preview requires ComfyUI's built-in PreviewImage node.")
        result = preview_cls().save_images(image, filename_prefix="ApexPreview")
        return _rename_ui_images(result, "apex_preview_images")

NODE_CLASS_MAPPINGS = {
    "ApexModelOptimizer": ApexModelOptimizer,
    "ApexRecipe": ApexRecipe,
    "ApexGenerate": ApexGenerate,
    "ApexGenerationCore": ApexGenerationCore,
    "ApexLoraGenerationCore": ApexGenerationCore,
    "ApexOutput": ApexOutput,
    "ApexPreview": ApexPreview,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ApexModelOptimizer": "Apex Model Matrix",
    "ApexRecipe": "Apex Recipe",
    "ApexGenerate": "Apex Generate",
    "ApexGenerationCore": "Apex Generation Nexus",
    "ApexLoraGenerationCore": "Apex Generation Nexus",
    "ApexOutput": "Apex Archive",
    "ApexPreview": "Apex Image Preview",
}
