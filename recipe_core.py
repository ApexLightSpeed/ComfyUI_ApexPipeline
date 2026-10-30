"""Apex recipe core: reads / resolves generation recipes from image metadata.

No ComfyUI imports, so this module can be unit-tested independently.
"""
from __future__ import annotations

import json
import os
import re

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None

LORA_TAG = re.compile(r"<lora:([^:>]+):(-?[0-9.]+)(?::(-?[0-9.]+))?>", re.I)
RECIPE_CLASSES = ("ApexRecipe", "ApexImageRecipe", "ApexReferenceRecipe")
EDIT_ADAPTER = re.compile(r"(identity[_ \-]?edit|general[_ \-]?edit|krea2[_ \-]?edit)", re.I)
IMG_EXTS = (".png", ".webp", ".jpg", ".jpeg")
MAX_DEPTH = 6


# --------------------------------------------------------------------------- helpers
def _json_or_none(v):
    if isinstance(v, dict):
        return v
    if isinstance(v, str) and v.strip().startswith(("{", "[")):
        try:
            r = json.loads(v)
            return r if isinstance(r, dict) else None
        except Exception:
            return None
    return None


def _state_with(values, key):
    """First dict / JSON-string among values that contains key."""
    for v in values:
        st = _json_or_none(v)
        if st is not None and key in st:
            return st
    return None


def _node_values_ui(node):
    vals = list((node.get("properties") or {}).values())
    wv = node.get("widgets_values")
    if isinstance(wv, list):
        vals += wv
    elif isinstance(wv, dict):
        vals += list(wv.values())
    vals += list((node.get("widgets_values_named") or {}).values())
    return vals


def _lora(name, sm, sc, on=True, src="", exact=True):
    if not name:
        return None
    try:
        sm, sc = float(sm), float(sc)
    except Exception:
        return None
    return {"name": str(name), "sm": sm, "sc": sc, "on": bool(on), "src": src, "exact": exact}


def pix_loras(state, src):
    out = []
    for l in (state or {}).get("loras", []):
        if isinstance(l, dict) and l.get("name"):
            e = _lora(l["name"], l.get("sm", 1), l.get("sc", l.get("sm", 1)), l.get("on", True), src)
            if e:
                out.append(e)
    return out


def tag_name(name):
    n = str(name).replace("\\", "/")
    return re.sub(r"\.(safetensors|sft|pt|ckpt|bin)$", "", n, flags=re.I)


def format_tags(loras):
    """`<lora:name:model:clip>` for every ON LoRA, in application order."""
    return " ".join(
        f"<lora:{tag_name(l['name'])}:{l['sm']:g}:{l['sc']:g}>"
        for l in loras if l.get("on", True)
    )


def strip_tags(text):
    return LORA_TAG.sub("", text or "").strip(" ,\n")


# --------------------------------------------------------------------------- reading PNGs
def read_chunks(path):
    out = {"prompt": None, "workflow": None, "parameters": None, "keys": []}
    if Image is None:
        return out
    try:
        with Image.open(path) as im:
            info = dict(im.info or {})
    except Exception:
        return out
    out["keys"] = sorted(str(k) for k in info)
    for key in ("prompt", "workflow"):
        raw = info.get(key)
        if isinstance(raw, str):
            try:
                out[key] = json.loads(raw)
            except Exception:
                pass
    p = info.get("parameters")
    if isinstance(p, str):
        out["parameters"] = p
    return out


def find_parent_name(chunks):
    """If this image came from a graph with Apex Recipe, return the loaded parent filename."""
    p = chunks.get("prompt")
    if isinstance(p, dict):
        for node in p.values():
            if isinstance(node, dict) and node.get("class_type") in RECIPE_CLASSES:
                ref = (node.get("inputs") or {}).get("image_name")
                if isinstance(ref, str) and ref.strip():
                    return ref
                if isinstance(ref, list) and ref:
                    ins = ((p.get(str(ref[0])) or {}).get("inputs")) or {}
                    for k in ("image", "image_name", "filename", "file"):
                        if isinstance(ins.get(k), str) and ins[k].strip():
                            return ins[k]
    w = chunks.get("workflow")
    if isinstance(w, dict):
        nodes = {n.get("id"): n for n in w.get("nodes", [])}
        links = {l[0]: l for l in w.get("links", []) if isinstance(l, list) and len(l) >= 5}
        for n in w.get("nodes", []):
            if n.get("type") not in RECIPE_CLASSES:
                continue
            for i in n.get("inputs", []):
                if i.get("name") == "image_name" and i.get("link") in links:
                    src = nodes.get(links[i["link"]][1])
                    wv = (src or {}).get("widgets_values")
                    if isinstance(wv, list) and wv and isinstance(wv[0], str) and wv[0].strip():
                        return wv[0]
    return None


def extract_recipe(chunks):
    """Extract recipe metadata from one image's decoded PNG chunks."""
    loras, src = [], ""
    checkpoint = ""
    pix_prompt = ""

    p = chunks.get("prompt")
    if isinstance(p, dict):
        for node in p.values():
            if not isinstance(node, dict):
                continue
            ct, ins = node.get("class_type", ""), node.get("inputs", {}) or {}
            if ct == "PixaromaLoraLoader":
                loras += pix_loras(_state_with(ins.values(), "loras"), "prompt:Pixaroma")
            elif ct in ("LoraLoader", "LoraLoaderModelOnly"):
                sm = ins.get("strength_model", 1)
                sc = ins.get("strength_clip", sm) if ct == "LoraLoader" else 0
                if not isinstance(sm, list) and not isinstance(sc, list):
                    e = _lora(ins.get("lora_name"), sm, sc, True, "prompt:" + ct)
                    if e:
                        loras.append(e)
            elif ct == "PixaromaPrompt" and not pix_prompt:
                pix_prompt = (_state_with(ins.values(), "text") or {}).get("text", "") or ""
            elif ct.startswith("LCOptimizer") or ct == "ApexModelOptimizer":
                checkpoint = ins.get("model_file", "") or checkpoint
            elif ct == "CheckpointLoaderSimple" and not checkpoint:
                checkpoint = ins.get("ckpt_name", "") or ""
            elif ct == "UNETLoader" and not checkpoint:
                checkpoint = ins.get("unet_name", "") or ""
        if loras:
            src = "prompt chunk"

    w = chunks.get("workflow")
    if isinstance(w, dict):
        for n in w.get("nodes", []):
            if n.get("mode", 0) in (2, 4):
                continue
            t, wv = n.get("type", ""), n.get("widgets_values")
            if t == "PixaromaLoraLoader" and not loras:
                loras += pix_loras(_state_with(_node_values_ui(n), "loras"), "workflow:Pixaroma")
            elif t == "LoraLoader" and not loras and isinstance(wv, list) and len(wv) >= 3:
                e = _lora(wv[0], wv[1], wv[2], True, "workflow:LoraLoader")
                if e:
                    loras.append(e)
            elif t == "PixaromaPrompt" and not pix_prompt:
                pix_prompt = (_state_with(_node_values_ui(n), "text") or {}).get("text", "") or ""
            elif t.startswith("LCOptimizer") and isinstance(wv, list) and len(wv) >= 3 and not checkpoint:
                checkpoint = wv[2] or ""
            elif t == "ApexModelOptimizer" and isinstance(wv, list) and len(wv) >= 3 and not checkpoint:
                checkpoint = wv[2] or ""
        if loras and not src:
            src = "workflow chunk"

    params = chunks.get("parameters") or ""
    if not loras and params:
        for m in LORA_TAG.finditer(params):
            sm = float(m.group(2))
            sc = float(m.group(3)) if m.group(3) is not None else sm
            e = _lora(m.group(1), sm, sc, True, "parameters tag")
            if e:
                loras.append(e)
        if loras:
            src = "parameters <lora:> tags"
    if not loras and params:
        m = re.search(r"Civitai resources:\s*(\[.*?\])\s*(?:,\s*[A-Z][A-Za-z ]+:|$|\n)", params, re.S)
        if m:
            try:
                for r in json.loads(m.group(1)):
                    if str(r.get("type", "")).lower() == "lora":
                        e = _lora(r.get("modelName") or r.get("modelVersionName"), r.get("weight", 1),
                                  r.get("weight", 1), True, "civitai resources", exact=False)
                        if e:
                            loras.append(e)
            except Exception:
                pass
            if loras:
                src = "Civitai resources (model names, one weight each)"
    if not loras and params:
        m = re.search(r'Lora hashes:\s*"([^"]+)"', params)
        if m:
            for part in m.group(1).split(","):
                e = _lora(part.rsplit(":", 1)[0].strip(), 1.0, 1.0, True, "lora hashes", exact=False)
                if e:
                    loras.append(e)
            if loras:
                src = "Lora hashes (STRENGTH UNKNOWN, assumed 1.0)"

    prompt_text = ""
    if params:
        first = re.split(r"\nNegative prompt:|\nSteps:", params)[0].strip()
        if first and not first.startswith("Steps:"):
            prompt_text = strip_tags(first)
    if not prompt_text:
        prompt_text = strip_tags(pix_prompt)

    if not checkpoint and params:
        m = re.search(r"Model:\s*([^,\n]+)", params)
        if m:
            checkpoint = m.group(1).strip()

    settings = {}
    for key, rx in (
        ("steps", r"Steps:\s*([0-9]+)"),
        ("sampler", r"Sampler:\s*([^,\n]+)"),
        ("scheduler", r"Scheduler:\s*([^,\n]+)"),
        ("cfg", r"CFG scale:\s*([0-9.]+)"),
        ("seed", r"Seed:\s*([0-9]+)"),
        ("size", r"Size:\s*([0-9]+x[0-9]+)"),
        ("denoise", r"Denoising strength:\s*([0-9.]+)"),
    ):
        m = re.search(rx, params)
        if m:
            settings[key] = m.group(1).strip()

    return {"loras": loras, "checkpoint": checkpoint, "prompt": prompt_text, "settings": settings,
            "source": src, "parameters": params}


def resolve_recipe(path, locate, depth=0, trail=None):
    """Extract recipe and follow parent images, up to MAX_DEPTH generations."""
    trail = trail if trail is not None else []
    chunks = read_chunks(path)
    rec = extract_recipe(chunks)
    rec["chunks"] = {"keys": chunks["keys"], "prompt": bool(chunks["prompt"]),
                     "workflow": bool(chunks["workflow"]), "parameters": bool(chunks["parameters"])}
    trail.append(f"{os.path.basename(path)}: {len(rec['loras'])} LoRA(s) via {rec['source'] or 'none'}")
    parent = find_parent_name(chunks)
    if parent and depth < MAX_DEPTH:
        ppath = locate(parent)
        if not ppath:
            trail.append(f"parent '{os.path.basename(str(parent))}' NOT FOUND on disk, using this image's own metadata")
        elif os.path.abspath(ppath) == os.path.abspath(path):
            trail.append("parent is the same file, stopping")
        else:
            prec, _ = resolve_recipe(ppath, locate, depth + 1, trail)
            # Parent is authoritative: this stage replayed the parent's recipe.
            if prec["loras"]:
                rec["loras"], rec["source"] = prec["loras"], "parent: " + prec["source"]
            if prec["prompt"]:
                rec["prompt"] = prec["prompt"]
            rec["checkpoint"] = prec["checkpoint"] or rec["checkpoint"]
            rec["settings"] = prec["settings"] or rec["settings"]
    return rec, trail


# --------------------------------------------------------------------------- live mode (queued graph)
def upstream_chain(graph, node_id):
    """Walk the MODEL input upstream and return LoRAs in application order + checkpoint."""
    loras, ckpt, seen = [], "", set()
    link = ((graph or {}).get(str(node_id)) or {}).get("inputs", {}).get("model")
    while isinstance(link, list) and len(link) == 2:
        nid = str(link[0])
        if nid in seen or nid not in graph:
            break
        seen.add(nid)
        node = graph[nid]
        ct, ins = node.get("class_type", ""), node.get("inputs", {}) or {}
        found = []
        if ct == "PixaromaLoraLoader":
            found = pix_loras(_state_with(ins.values(), "loras"), "live:Pixaroma")
        elif ct in ("LoraLoader", "LoraLoaderModelOnly"):
            sm = ins.get("strength_model", 1)
            sc = ins.get("strength_clip", sm) if ct == "LoraLoader" else 0
            if not isinstance(sm, list) and not isinstance(sc, list):
                e = _lora(ins.get("lora_name"), sm, sc, True, "live:" + ct)
                found = [e] if e else []
        elif ct.startswith("LCOptimizer") or ct == "ApexModelOptimizer":
            ckpt = ins.get("model_file") or ckpt
        elif ct == "CheckpointLoaderSimple":
            ckpt = ins.get("ckpt_name") or ckpt
        elif ct == "UNETLoader":
            ckpt = ins.get("unet_name") or ckpt
        loras = found + loras  # farther nodes were applied first
        link = ins.get("model")
    return loras, ckpt


# --------------------------------------------------------------------------- matching
def _norm(s):
    s = os.path.basename(str(s).replace("\\", "/"))
    s = re.sub(r"\.(safetensors|sft|pt|ckpt|bin)$", "", s, flags=re.I)
    return re.sub(r"[\s_\-\.]+", "", s).lower()


def match_lora(name, available):
    """Exact path -> exact filename -> normalized name -> unique containment."""
    if not name:
        return None
    n = str(name).replace("\\", "/")
    for a in available:
        if a.replace("\\", "/").lower() == n.lower():
            return a
    for a in available:
        if os.path.basename(a.replace("\\", "/")).lower() == os.path.basename(n).lower():
            return a
    target = _norm(name)
    hits = [a for a in available if _norm(a) == target]
    if hits:
        return hits[0]
    if len(target) >= 5:
        hits = [a for a in available if target in _norm(a) or _norm(a) in target]
        if len(hits) == 1:
            return hits[0]
    return None
