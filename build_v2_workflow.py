"""Build the clean four-node V2 canvas from the checked-in node contracts."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
# Keep one stable package-unique workflow ID, distinct from the V1 and prototype
# templates. Desktop tab restoration is separate and still requires investigation.
WORKFLOW_ID = "8ed55b30-3999-4ce2-af42-44b57121badd"
old = json.loads((ROOT / "workflows" / "Apex Generator V2 Prototype.json").read_text(encoding="utf-8"))
model = next(n for n in old["nodes"] if n["type"] == "ApexModelOptimizer")
model = json.loads(json.dumps(model))
model.update(id=1, pos=[60, 130], size=[500, 650], order=0)
model["title"] = "APEXLIGHTSPEED · APEX MODEL MATRIX"
model.setdefault("properties", {}).update(cnr_id="apex-pipeline", ver="2.0.4")
# Model choices are populated dynamically from the active install. Old positional
# values from the prototype may belong to different dropdown schemas.
model.pop("widgets_values", None)
model.pop("widgets_values_named", None)
for slot, link in enumerate((1, 2, 3)):
    model["outputs"][slot]["links"] = [link]
model["outputs"][3]["links"] = [15]

def props(node_type):
    return {
        "Node name for S&R": node_type,
        "cnr_id": "apex-pipeline",
        "ver": "2.0.4",
        "ue_properties": {"widget_ue_connectable": {}, "input_ue_unconnectable": {}, "version": "7.8"},
    }

gen_inputs = [
    {"name": "model", "type": "MODEL", "link": 1},
    {"name": "clip", "type": "CLIP", "link": 2},
    {"name": "vae", "type": "VAE", "link": 3},
    {"name": "model_summary", "type": "STRING", "link": 15},
]
gen_outputs = [
    ("image", "IMAGE", 4), ("metadata_positive", "STRING", 5), ("seed", "INT", 6),
    ("steps", "INT", 7), ("cfg", "FLOAT", 8), ("sampler", "STRING", 9),
    ("scheduler", "STRING", 10), ("extra_params", "STRING", 11),
    ("width", "INT", 12), ("height", "INT", 13), ("model_name", "STRING", 14),
    ("model_summary", "STRING", 16),
]
target_names = {
    "image": "images", "metadata_positive": "positive", "seed": "seed",
    "steps": "steps", "cfg": "cfg", "sampler": "sampler",
    "scheduler": "scheduler", "extra_params": "extra_params",
    "width": "width", "height": "height", "model_name": "model_name",
    "model_summary": "model_summary",
}
gen = {
    "id": 2, "type": "ApexLoraGenerationCore", "pos": [570, 130], "size": [560, 900],
    "flags": {}, "order": 1, "mode": 0, "inputs": gen_inputs,
    "outputs": [{"name": n, "type": t, "slot_index": i, "links": [link]} for i, (n, t, link) in enumerate(gen_outputs)],
    "title": "APEXLIGHTSPEED · APEX GENERATION NEXUS",
    "properties": props("ApexLoraGenerationCore"),
    # Dynamic option lists differ across ComfyUI installs. Omitting positional
    # widget values lets the current node schemas supply valid defaults.
    "color": "#361318", "bgcolor": "#090a0d",
}

out_names_types = [
    ("images", "IMAGE"), ("positive", "STRING"), ("seed", "INT"), ("steps", "INT"),
    ("cfg", "FLOAT"), ("sampler", "STRING"), ("scheduler", "STRING"),
    ("extra_params", "STRING"), ("model_name", "STRING"), ("width", "INT"), ("height", "INT"),
    ("model_summary", "STRING"),
]
source_links_by_target = {target_names[source]: link for source, _typ, link in gen_outputs}
out_inputs = []
for name, typ in out_names_types:
    out_inputs.append({"name": name, "type": typ, "link": source_links_by_target[name]})
out = {
    "id": 3, "type": "ApexOutput", "pos": [1140, 130], "size": [500, 500],
    "flags": {}, "order": 2, "mode": 0, "inputs": out_inputs,
    "outputs": [
        {"name": "images", "type": "IMAGE", "slot_index": 0, "links": []},
        {"name": "saved_as", "type": "STRING", "slot_index": 1, "links": []},
    ],
    "title": "APEXLIGHTSPEED · APEX ARCHIVE",
    "properties": props("ApexOutput"),
    # Let this install's live INPUT_TYPES define values and dynamic choices.
    "color": "#361318", "bgcolor": "#090a0d",
}

preview = {
    "id": 4, "type": "ApexPreview", "pos": [1650, 130], "size": [480, 640],
    "flags": {}, "order": 3, "mode": 0,
    "inputs": [{"name": "image", "type": "IMAGE", "link": 17}],
    "outputs": [], "title": "APEXLIGHTSPEED · APEX IMAGE PREVIEW",
    "properties": props("ApexPreview"), "color": "#230b0d", "bgcolor": "#080809",
}
gen["outputs"][0]["links"].append(17)

links = [
    [1, 1, 0, 2, 0, "MODEL"], [2, 1, 1, 2, 1, "CLIP"], [3, 1, 2, 2, 2, "VAE"],
    [15, 1, 3, 2, 3, "STRING"],
]
links.append([17, 2, 0, 4, 0, "IMAGE"])
target_slots = {name: slot for slot, (name, _typ) in enumerate(out_names_types)}
for source_slot, (name, typ, lid) in enumerate(gen_outputs):
    links.append([lid, 2, source_slot, 3, target_slots[target_names[name]], typ])
workflow = {
    "id": WORKFLOW_ID, "revision": 0,
    "last_node_id": 4, "last_link_id": 17, "nodes": [model, gen, out, preview],
    "links": links, "groups": [], "config": {},
    "extra": {"frontendVersion": "1.57.4", "workflow_notes": "Apex Generator V2 — four aligned Apex nodes. Generation Nexus feeds Archive and one image-only resizable Apex Preview. Native duplicate canvas thumbnails are suppressed."},
    "version": 0.4,
}
(ROOT / "workflows" / "Apex Generator V2.json").write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
