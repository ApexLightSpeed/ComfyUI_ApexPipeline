"""Apex Pipeline Generator nodes.

V1 registers only the three nodes used by the Generator
workflow. Refinement, repair, upscale, and detailer nodes are intentionally not
part of this release.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
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

def _clip_lines(lines, n):
    if len(lines) <= n:
        return lines
    return lines[: n - 1] + [f"… +{len(lines) - n + 1} more (see console)"]

_GEN_COND = _Memo()

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
            extra_pnginfo=None):
        lines = []
        t0 = time.perf_counter()
        cond = _GEN_COND.get((clip,), prompt)
        c_hit = cond is not None
        if cond is None:
            positive = _encode(clip, prompt)
            cond = _GEN_COND.put((clip,), prompt, (positive, _zero_out(positive)))
        positive, negative = cond
        t1 = time.perf_counter()
        latent = {"samples": torch.zeros([1, 4, int(height) // 8, int(width) // 8],
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

NODE_CLASS_MAPPINGS = {
    "ApexModelOptimizer": ApexModelOptimizer,
    "ApexRecipe": ApexRecipe,
    "ApexGenerate": ApexGenerate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ApexModelOptimizer": "Apex Model Optimizer · Krea 2",
    "ApexRecipe": "Apex Recipe",
    "ApexGenerate": "Apex Generate",
}
